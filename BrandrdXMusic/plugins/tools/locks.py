import asyncio
import re
import os
from datetime import datetime, timedelta
import requests
from pyrogram import filters, enums
from pyrogram.types import Message, ChatPermissions, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from fuzzywuzzy import fuzz
from BrandrdXMusic import app
from BrandrdXMusic.misc import SUDOERS
from motor.motor_asyncio import AsyncIOMotorClient

# --- [ 1. MongoDB الإعدادات من السكرتس ] ---
from config import MONGO_DB_URI
mongo_client = AsyncIOMotorClient(MONGO_DB_URI)
db = mongo_client["Brandrd_Protect"]
locks_collection = db["locks"]
warns_collection = db["warns"]
max_warns_collection = db["max_warns"]
whitelist_collection = db["whitelist"]

API_USER = "1800965377"
API_SECRET = "pp32KRVBbfQjJXqLYoah7goaU949hwjU"

flood_cache = {}

LOCK_MAP = {
    "الروابط": "links", "المعرفات": "usernames", "التاك": "hashtags",
    "الشارحه": "slashes", "التثبيت": "pin", "المتحركه": "animations",
    "الشات": "all", "الصور": "photos", "الملصقات": "stickers",
    "الملفات": "docs", "البوتات": "bots", "التكرار": "flood",
    "الكلايش": "long_msgs", "الانلاين": "inline", "الفيديو": "videos",
    "البصمات": "voice", "السيلفي": "video_notes", "الماركدوان": "markdown",
    "التوجيه": "forward", "الاغاني": "audio", "الصوت": "voice",
    "الجهات": "contacts", "الاشعارات": "service", "السب": "porn_text",
    "الاباحي": "porn_media"
}

BAD_WORDS = ["سكس","نيك","شرموط","منيوك","كسمك","زب","فحل","بورن","متناك","مص","كس","طيز","قحبه","فاجره","احاا","متناكه","خول"]

# --- [ 2. دوال مساعدة ] ---
async def is_whitelisted(chat_id, user_id):
    if user_id in SUDOERS: return True
    found = await whitelist_collection.find_one({"chat_id": chat_id, "user_id": user_id})
    return True if found else False

async def has_permission(chat_id, user_id):
    if user_id in SUDOERS: return True
    try:
        member = await app.get_chat_member(chat_id, user_id)
        return member.status in [enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.OWNER]
    except: return False

async def force_delete(chat_id, current_id, limit):
    count = 0
    for i in range(current_id, current_id - (limit + 200), -1):
        if count >= limit: break
        try:
            if await app.delete_messages(chat_id, i):
                count += 1
        except: continue
    return count

def check_porn_api(file_path):
    try:
        params = {'models':'nudity-2.0','api_user':API_USER,'api_secret':API_SECRET}
        with open(file_path,'rb') as f:
            r = requests.post('https://api.sightengine.com/1.0/check.json', files={'media':f}, data=params)
        output = r.json()
        if output.get('status') == 'success':
            return output['nudity']['sexual_display']>0.5 or output['nudity']['erotica']>0.5
    except: pass
    return False

# --- [ 3. تحذيرات المستخدمين ] ---
async def add_warn(message: Message, reason="normal"):
    c_id, u_id = message.chat.id, message.from_user.id
    mention = message.from_user.mention

    max_warn_doc = await max_warns_collection.find_one({"chat_id": c_id})  
    limit = max_warn_doc["limit"] if max_warn_doc else 3  

    mute_days = 7 if reason=="religious" else 1  
    
    if reason == "religious":
        msg_text = f"<b>⌯ يـا {mention} تـذكـر قـول الله : ﴿ مَا يَلْفِظُ مِنْ قَوْلٍ إِلَّا لَدَيْهِ رَقِيبٌ عَتِيدٌ ﴾\n⌯ وان هذه الدنيا فانية 🥀</b>"
    else:
        msg_text = f"<b>⌯ يـا {mention} عذراً سيتم حذف الرسالة لمخالفة القوانين</b>"

    warn_doc = await warns_collection.find_one({"chat_id":c_id,"user_id":u_id})  
    current = (warn_doc["count"] + 1) if warn_doc else 1  
    await warns_collection.update_one({"chat_id":c_id,"user_id":u_id},{"$set":{"count":current}}, upsert=True)  

    if current > limit:  
        await warns_collection.update_one({"chat_id":c_id,"user_id":u_id},{"$set":{"count":0}})  
        kb = InlineKeyboardMarkup([[InlineKeyboardButton("فك الكتم", callback_data=f"u_unmute_{u_id}")]])  
        try:  
            await app.restrict_chat_member(c_id, u_id, ChatPermissions(can_send_messages=False), until_date=datetime.now()+timedelta(days=mute_days))  
            await message.reply(f"{msg_text}\n\n<b>⌯ تم كتمك بسب تجاوز التحذيرات ({limit})</b>", reply_markup=kb)  
        except: pass  
    else:  
        await message.reply(f"{msg_text}\n<b>⌯ تحذيراتك الحالية : ({current}/{limit})</b>")

# --- [ 4. الهاندلرز ] ---
@app.on_message(filters.command(["سماح","شد سماح","كتم","شد ميوت","فك الكتم"], "") & filters.group)
async def admin_cmds_handler(_, message: Message):
    if not await has_permission(message.chat.id,message.from_user.id): return
    cmd = message.command[0]
    if message.reply_to_message:
        user_id = message.reply_to_message.from_user.id
        mention = message.reply_to_message.from_user.mention
    else:
        if len(message.command)<2: return
        try:
            user = await app.get_users(message.command[1])
            user_id, mention = user.id, user.mention
        except: return

    try:  
        if cmd=="سماح":  
            await whitelist_collection.update_one({"chat_id": message.chat.id, "user_id": user_id}, {"$set": {"trusted": True}}, upsert=True)  
            res_text = f"<b>⌯ تم منح السماح لـ {mention}</b>"  
        elif cmd=="شد سماح":  
            await whitelist_collection.delete_one({"chat_id": message.chat.id, "user_id": user_id})  
            res_text = f"<b>⌯ تم سحب السماح من {mention}</b>"  
        elif cmd=="كتم":  
            await app.restrict_chat_member(message.chat.id,user_id,ChatPermissions(can_send_messages=False))  
            res_text = f"<b>⌯ تم كتم العضو {mention}</b>"  
        elif cmd in ["شد ميوت","فك الكتم"]:  
            await app.restrict_chat_member(message.chat.id,user_id,ChatPermissions(can_send_messages=True))  
            res_text = f"<b>⌯ تم فك كتم {mention}</b>"  
        await message.reply(res_text)  
    except: pass

@app.on_message(filters.command(["مسح","تنظيف"], "") & filters.group)
async def destructive_clear_cmd(_, message: Message):
    if not await has_permission(message.chat.id,message.from_user.id): return
    if message.reply_to_message:
        start_id, end_id = message.reply_to_message.id, message.id
        msg_ids = list(range(start_id, end_id+1))
        for i in range(0,len(msg_ids),100):
            try: await app.delete_messages(message.chat.id,msg_ids[i:i+100])
            except: continue
        deleted=len(msg_ids)
    else:
        try: num=int(message.command[1]) if len(message.command)>1 else 100
        except: num=100
        deleted = await force_delete(message.chat.id,message.id,num)
    temp = await message.reply(f"<b>⌯ تم تنظيف ({deleted}) رسالة</b>")
    await asyncio.sleep(3)
    await temp.delete()

# --- [ 5. محرك الحماية والقفل ] ---
async def get_locks(chat_id):
    doc = await locks_collection.find_one({"chat_id":chat_id})
    return set(doc["locks"]) if doc else set()

async def toggle_lock(chat_id,key,state:bool):
    doc = await locks_collection.find_one({"chat_id":chat_id})
    locks = set(doc["locks"]) if doc else set()
    if state: locks.add(key)
    else: locks.discard(key)
    await locks_collection.update_one({"chat_id":chat_id},{"$set":{"locks":list(locks)}},upsert=True)
    return locks

@app.on_message(filters.group & ~filters.me, group=-1)
async def protector_engine(_, message: Message):
    c_id = message.chat.id
    if not message.from_user: return
    if await is_whitelisted(c_id, message.from_user.id): return  
    if await has_permission(c_id, message.from_user.id): return  
    locks = await get_locks(c_id)  
    if not locks: return  

    text = message.text or message.caption or ""  
    if "all" in locks:  
        await message.delete(); return  

    if "links" in locks and re.search(r"(?:https?://|www\.|t\.me/)", text):  
        await add_warn(message); await message.delete(); return  
    
    if "porn_text" in locks and text:  
        clean=re.sub(r"[^\u0621-\u064A\s]","",text)  
        if any(fuzz.ratio(bad,word)>85 for bad in BAD_WORDS for word in clean.split()):  
            await add_warn(message,reason="religious")  
            await message.delete(); return  

    media_locks=["photos","videos","animations","stickers","voice","audio","video_notes","docs"]  
    for m in media_locks:  
        if m in locks and getattr(message,m,None):  
            await add_warn(message)  
            await message.delete(); return

# --- [ 6. أوامر القفل واللوحة ] ---
@app.on_message(filters.command(["قفل","فتح"],"") & filters.group)
async def toggle_lock_cmds(_,message:Message):
    if not await has_permission(message.chat.id,message.from_user.id): return
    if len(message.command)<2: return
    cmd,msg_text=message.command[0],message.text.split(None,1)[1].strip()
    key=LOCK_MAP.get(msg_text)
    if not key: return
    state = True if cmd=="قفل" else False
    await toggle_lock(message.chat.id,key,state)
    await message.reply(f"<b>⌯ تم {cmd} ({msg_text})</b>")

def get_kb(chat_id,set_locks):
    kb=[]
    items=list(LOCK_MAP.items())
    for i in range(0,len(items),2):
        row=[]
        n1,k1=items[i]; s1="مقفل" if k1 in set_locks else "مفتوح"
        row.append(InlineKeyboardButton(f"{n1} ⇽ {s1}",callback_data=f"trg_{k1}"))
        if i+1<len(items):
            n2,k2=items[i+1]; s2="مقفل" if k2 in set_locks else "مفتوح"
            row.append(InlineKeyboardButton(f"{n2} ⇽ {s2}",callback_data=f"trg_{k2}"))
        kb.append(row)
    kb.append([InlineKeyboardButton("إغـلاق اللوحة",callback_data="close")])
    return InlineKeyboardMarkup(kb)

@app.on_message(filters.command(["الاعدادات","locks"],"") & filters.group)
async def settings_cmd(_,message:Message):
    if not await has_permission(message.chat.id,message.from_user.id): return
    locks = await get_locks(message.chat.id)
    await message.reply_text(f"<b>⌯ إعـدادات الـمـجـمـوعـة</b>",reply_markup=get_kb(message.chat.id,locks))

@app.on_callback_query(filters.regex("^(trg_|u_|close)"))
async def cb_handler(_,cb:CallbackQuery):
    if not await has_permission(cb.message.chat.id,cb.from_user.id): return
    if cb.data=="close": return await cb.message.delete()
    if cb.data.startswith("trg_"):
        key=cb.data.replace("trg_","")
        current_locks = await get_locks(cb.message.chat.id)
        locks = await toggle_lock(cb.message.chat.id,key,key not in current_locks)
        await cb.message.edit_reply_markup(reply_markup=get_kb(cb.message.chat.id,locks))
    elif cb.data.startswith("u_unmute_"):
        u_id=int(cb.data.split("_")[2])
        await app.restrict_chat_member(cb.message.chat.id,u_id,ChatPermissions(can_send_messages=True))
        await cb.message.edit(f"<b>⌯ تم فك الكتم</b>")

# --- [ 9. المهمة الدورية ] ---
async def clear_flood_cache_task():
    while True:
        now=datetime.now()
        for key in list(flood_cache.keys()):
            if (now-flood_cache[key]["time"]).seconds>3600:
                del flood_cache[key]
        await asyncio.sleep(3600)

asyncio.create_task(clear_flood_cache_task())
