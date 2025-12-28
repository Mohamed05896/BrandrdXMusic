import asyncio
import re
import os
import requests
from datetime import datetime, timedelta
from pyrogram import filters, enums
from pyrogram.types import Message, ChatPermissions, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from fuzzywuzzy import fuzz
from motor.motor_asyncio import AsyncIOMotorClient

# --- [ استيراد ملفات البوت الأساسية ] ---
from BrandrdXMusic import app
from BrandrdXMusic.misc import SUDOERS
from config import MONGO_DB_URI

# -------------------------------------------------------------------
# [ 1 ] إعدادات قاعدة البيانات والمتغيرات
# -------------------------------------------------------------------

mongo_client = AsyncIOMotorClient(MONGO_DB_URI)
db = mongo_client["Brandrd_Protect"]

# المجموعات (Collections)
locks_collection = db["locks"]
warns_collection = db["warns"]
max_warns_collection = db["max_warns"]
whitelist_collection = db["whitelist"]

# مفاتيح API (SightEngine)
API_USER = "1800965377"
API_SECRET = "pp32KRVBbfQjJXqLYoah7goaU949hwjU"

# ذاكرة الكاش للتكرار (Flood)
flood_cache = {}

# خريطة الأقفال
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

# -------------------------------------------------------------------
# [ 2 ] الدوال المساعدة (Helpers)
# -------------------------------------------------------------------

async def is_whitelisted(chat_id, user_id):
    """التحقق من القائمة البيضاء عبر MongoDB"""
    if user_id in SUDOERS: return True
    return bool(await whitelist_collection.find_one({"chat_id": chat_id, "user_id": user_id}))

async def has_permission(chat_id, user_id):
    """التحقق من صلاحيات الإدمن"""
    if user_id in SUDOERS: return True
    try:
        member = await app.get_chat_member(chat_id, user_id)
        return member.status in [enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.OWNER]
    except: return False

async def get_locks(chat_id):
    """جلب الأقفال من القاعدة"""
    doc = await locks_collection.find_one({"chat_id": chat_id})
    return set(doc["locks"]) if doc else set()

async def toggle_lock_db(chat_id, key, state: bool):
    """تحديث قفل في القاعدة"""
    doc = await locks_collection.find_one({"chat_id": chat_id})
    locks = set(doc["locks"]) if doc else set()
    if state: locks.add(key)
    else: locks.discard(key)
    await locks_collection.update_one({"chat_id": chat_id}, {"$set": {"locks": list(locks)}}, upsert=True)
    return locks

# --- دالة النسف (من الكود القديم) ---
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
        params = {'models': 'nudity-2.0', 'api_user': API_USER, 'api_secret': API_SECRET}
        with open(file_path, 'rb') as f:
            r = requests.post('https://api.sightengine.com/1.0/check.json', files={'media': f}, data=params)
        output = r.json()
        if output.get('status') == 'success':
            return output['nudity']['sexual_display'] > 0.5 or output['nudity']['erotica'] > 0.5
    except: pass
    return False

# -------------------------------------------------------------------
# [ 3 ] نظام التحذيرات (Warns) - تنسيق قديم
# -------------------------------------------------------------------

async def add_warn(message: Message, reason="normal"):
    c_id, u_id = message.chat.id, message.from_user.id
    mention = message.from_user.mention

    max_warn_doc = await max_warns_collection.find_one({"chat_id": c_id})
    limit = max_warn_doc["limit"] if max_warn_doc else 3
    
    # النصوص والتوقيت حسب الكود القديم
    if reason == "religious":
        mute_days = 7
        msg_text = f"<b>يـا {mention} ، تـذكـر قـول الله تـعـالـي : ( مَا يَلْفِظُ مِنْ قَوْلٍ إِلَّا لَدَيْهِ رَقِيبٌ عَتِيدٌ ) وأن هذه الدنيا فانية 🥀 ـ</b>"
    else:
        mute_days = 1
        msg_text = f"<b>يـا {mention} ، تـم حـذف رسـالـتـك لـمـخـالـفـة قـوانـيـن الـحـمـايـة ـ</b>"

    warn_doc = await warns_collection.find_one({"chat_id": c_id, "user_id": u_id})
    current = (warn_doc["count"] + 1) if warn_doc else 1
    await warns_collection.update_one({"chat_id": c_id, "user_id": u_id}, {"$set": {"count": current}}, upsert=True)

    if current > limit:
        await warns_collection.update_one({"chat_id": c_id, "user_id": u_id}, {"$set": {"count": 0}})
        kb = InlineKeyboardMarkup([[InlineKeyboardButton("🧚 • فـك الـكـتـم • 🧚", callback_data=f"u_unmute_{u_id}")]])
        try:
            await app.restrict_chat_member(c_id, u_id, ChatPermissions(can_send_messages=False), until_date=datetime.now() + timedelta(days=mute_days))
            await message.reply(f"{msg_text}\n\n<b>• تم كتمك تلقائياً لمدة {mute_days} أيام\n• السبب : تخطي حد التحذيرات ({limit}) 🤍🥀 ـ</b>", reply_markup=kb)
        except: pass
    else:
        await message.reply(f"{msg_text}\n\n<b>• تحذيراتك الحالية : ({current}/{limit}) ـ</b>")

# -------------------------------------------------------------------
# [ 4 ] أوامر الإدارة (Admin)
# -------------------------------------------------------------------

@app.on_message(filters.command(["سماح", "شد سماح", "كتم", "اكتم", "شد ميوت", "فك الكتم"], "") & filters.group)
async def admin_cmds_handler(_, message: Message):
    if not await has_permission(message.chat.id, message.from_user.id): return
    cmd = message.command[0]
    
    if message.reply_to_message:
        user_id = message.reply_to_message.from_user.id
        mention = message.reply_to_message.from_user.mention
    else:
        if len(message.command) < 2: return
        try:
            user = await app.get_users(message.command[1])
            user_id, mention = user.id, user.mention
        except: return

    try:
        if cmd == "سماح":
            await whitelist_collection.update_one({"chat_id": message.chat.id, "user_id": user_id}, {"$set": {"trusted": True}}, upsert=True)
            res_text = f"<b>• تم منح السماح للعضو : {mention} بنجاح ـ</b>"
        
        elif cmd == "شد سماح":
            await whitelist_collection.delete_one({"chat_id": message.chat.id, "user_id": user_id})
            res_text = f"<b>• تم سحب السماح من العضو : {mention} بنجاح ـ</b>"
        
        elif cmd in ["كتم", "اكتم"]:
            await app.restrict_chat_member(message.chat.id, user_id, ChatPermissions(can_send_messages=False))
            res_text = f"<b>• تم كتم العضو : {mention} بنجاح ـ</b>"
        
        elif cmd in ["شد ميوت", "فك الكتم"]:
            await app.restrict_chat_member(message.chat.id, user_id, ChatPermissions(can_send_messages=True))
            res_text = f"<b>• تم فك كتم العضو : {mention} بنجاح ـ</b>"
            
        await message.reply(res_text)
    except: pass

@app.on_message(filters.command("تحذيرات", "") & filters.group)
async def set_warns_limit(_, message: Message):
    if not await has_permission(message.chat.id, message.from_user.id): return
    if len(message.command) < 2: return
    try:
        num = int(message.command[1])
        await max_warns_collection.update_one({"chat_id": message.chat.id}, {"$set": {"limit": num}}, upsert=True)
        await message.reply(f"<b>• تم تحديد عدد التحذيرات في هذه المجموعة إلى : {num} تحذير ـ</b>")
    except: pass

# -------------------------------------------------------------------
# [ 5 ] أوامر التنظيف (Cleaner)
# -------------------------------------------------------------------

@app.on_message(filters.command(["مسح", "تنظيف"], "") & filters.group)
async def destructive_clear_cmd(_, message: Message):
    if not await has_permission(message.chat.id, message.from_user.id): return

    if message.reply_to_message:
        start_id = message.reply_to_message.id
        end_id = message.id
        msg_ids = list(range(start_id, end_id + 1))
        for i in range(0, len(msg_ids), 100):
            try: await app.delete_messages(message.chat.id, msg_ids[i:i+100])
            except: continue
        deleted = len(msg_ids)
    else:
        try: num = int(message.command[1]) if len(message.command) > 1 else 100
        except: num = 100
        deleted = await force_delete(message.chat.id, message.id, num)

    temp = await message.reply(f"<b>• تم بنجاح مسح {deleted} رسالة من المجموعة 🧚 ـ</b>")
    await asyncio.sleep(3); await temp.delete()

@app.on_message(filters.command("تدمير ذاتي", "") & filters.group)
async def self_destruct_cmd(_, message: Message):
    if not await has_permission(message.chat.id, message.from_user.id): return
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("• تـدمـيـر ذاتـي (500) • 🧚", callback_data="total_destruction")]])
    await message.reply("<b>اضغط على الزر أدناه لبدء تدمير آخر 500 رسالة بنظام النسف التنازلي ـ</b>", reply_markup=kb)

# -------------------------------------------------------------------
# [ 6 ] محرك الحماية (Protector Engine)
# -------------------------------------------------------------------

@app.on_message(filters.group & ~filters.me, group=-1)
async def protector_engine(_, message: Message):
    c_id = message.chat.id
    if not message.from_user: return 
    if await is_whitelisted(c_id, message.from_user.id): return
    if await has_permission(c_id, message.from_user.id): return
    
    locks = await get_locks(c_id)
    if not locks: return

    if "all" in locks:
        try: await message.delete()
        except: pass
        return

    text = message.text or message.caption or ""

    # فحوصات النصوص
    if "links" in locks and re.search(r"(?:https?://|www\.|t\.me/)", text):
        await message.delete(); return await add_warn(message)
    if "usernames" in locks and re.search(r"@[A-Za-z0-9_]{5,32}", text):
        await message.delete(); return await add_warn(message)
    if "hashtags" in locks and "#" in text:
        await message.delete(); return await add_warn(message)

    # فحص السب
    if "porn_text" in locks and text:
        clean = re.sub(r"[^\u0621-\u064A\s]", "", text)
        if any(fuzz.ratio(bad, word) > 85 for bad in BAD_WORDS for word in clean.split()):
            await message.delete(); return await add_warn(message, reason="religious")
            
    # فحوصات الميديا
    media_locks = ["photos","videos","animations","stickers","voice","audio","video_notes","docs","contacts"]
    for m in media_locks:
        if m in locks and getattr(message, m, None):
            # فحص الإباحية
            if m in ["photos", "videos"] and "porn_media" in locks:
                file_path = await message.download()
                if check_porn_api(file_path):
                    os.remove(file_path)
                    await message.delete()
                    return await add_warn(message, reason="religious")
                os.remove(file_path)
            
            await message.delete()
            return await add_warn(message)

    # فحص التكرار
    if "flood" in locks:
        user_id = message.from_user.id
        now = datetime.now()
        flood_key = f"{c_id}_{user_id}"
        if flood_key not in flood_cache:
            flood_cache[flood_key] = {"count": 1, "time": now}
        else:
            data = flood_cache[flood_key]
            if (now - data["time"]).seconds < 5:
                data["count"] += 1
                if data["count"] > 4:
                    del flood_cache[flood_key]
                    await message.delete()
                    return await add_warn(message)
            else:
                flood_cache[flood_key] = {"count": 1, "time": now}

# -------------------------------------------------------------------
# [ 7 ] الأقفال والكيبورد (Locks & KB)
# -------------------------------------------------------------------

@app.on_message(filters.command(["قفل", "فتح"], "") & filters.group)
async def toggle_lock_cmds(_, message: Message):
    if not await has_permission(message.chat.id, message.from_user.id): return
    if len(message.command) < 2: return
    
    cmd, msg_text = message.command[0], message.text.split(None, 1)[1].strip()
    key = LOCK_MAP.get(msg_text)
    if not key: return
    
    state = True if cmd == "قفل" else False
    await toggle_lock_db(message.chat.id, key, state)
    await message.reply(f"<b>• تم {cmd} {msg_text} بنجاح في المجموعة ـ</b>")

def get_kb(chat_id, set_locks=None):
    kb = []
    set_locks = set_locks or set()
    items = list(LOCK_MAP.items())
    for i in range(0, len(items), 2):
        row = []
        n1, k1 = items[i]; s1 = "مقفل" if k1 in set_locks else "مفتوح"
        row.append(InlineKeyboardButton(f"• {n1} ⇽ {s1} •", callback_data=f"trg_{k1}"))
        if i + 1 < len(items):
            n2, k2 = items[i+1]; s2 = "مقفل" if k2 in set_locks else "مفتوح"
            row.append(InlineKeyboardButton(f"• {n2} ⇽ {s2} •", callback_data=f"trg_{k2}"))
        kb.append(row)
    kb.append([InlineKeyboardButton("• إغـلاق الـلـوحـة •", callback_data="close")])
    return InlineKeyboardMarkup(kb)

@app.on_message(filters.command(["الاعدادات", "locks"], "") & filters.group)
async def settings_cmd(_, message: Message):
    if not await has_permission(message.chat.id, message.from_user.id): return
    locks = await get_locks(message.chat.id)
    await message.reply_text(
        f"<b>• إعدادات مجموعة : {message.chat.title} ـ</b>",
        reply_markup=get_kb(message.chat.id, locks)
    )

# -------------------------------------------------------------------
# [ 8 ] التفاعل مع الأزرار (Callbacks)
# -------------------------------------------------------------------

@app.on_callback_query(filters.regex("^(trg_|u_|close|total_destruction)"))
async def cb_handler(_, cb: CallbackQuery):
    if not await has_permission(cb.message.chat.id, cb.from_user.id): return

    if cb.data == "close":
        return await cb.message.delete()
        
    elif cb.data == "total_destruction":
        await cb.answer("جاري النسف الشامل...", show_alert=True)
        await cb.message.edit("<b>جاري تدمير 500 رسالة من المجموعة... 🧚 ـ</b>")
        deleted = await force_delete(cb.message.chat.id, cb.message.id, 500)
        await app.send_message(cb.message.chat.id, f"<b>تم تدمير {deleted} رسالة بنجاح 🧚 ـ</b>")
        await cb.message.delete()
        
    elif cb.data.startswith("trg_"):
        key = cb.data.replace("trg_", "")
        current_locks = await get_locks(cb.message.chat.id)
        new_state = key not in current_locks
        locks = await toggle_lock_db(cb.message.chat.id, key, new_state)
        await cb.message.edit_reply_markup(reply_markup=get_kb(cb.message.chat.id, locks))
        
    elif cb.data.startswith("u_unmute_"):
        u_id = int(cb.data.split("_")[2])
        await app.restrict_chat_member(cb.message.chat.id, u_id, ChatPermissions(can_send_messages=True))
        await cb.message.edit(f"<b>• تم فك الكتم بنجاح بواسطة {cb.from_user.mention} ـ</b>")

# -------------------------------------------------------------------
# [ 9 ] مهام الخلفية
# -------------------------------------------------------------------

async def clear_flood_cache_task():
    while True:
        await asyncio.sleep(3600)
        flood_cache.clear()

asyncio.create_task(clear_flood_cache_task())
                
