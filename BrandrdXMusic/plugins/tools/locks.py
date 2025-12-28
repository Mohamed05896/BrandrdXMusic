import asyncio
import re
import requests
import os
from datetime import datetime, timedelta
from pyrogram import filters, enums
from pyrogram.types import Message, ChatPermissions, ChatPrivileges, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from fuzzywuzzy import fuzz
from BrandrdXMusic import app
from BrandrdXMusic.misc import SUDOERS

# --- [ 1. إعدادات البيانات والمخازن ] ---

API_USER = "1800965377"
API_SECRET = "pp32KRVBbfQjJXqLYoah7goaU949hwjU"

smart_db = {}
warns_db = {}
max_warns = {}

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

BAD_WORDS = ["سكس", "نيك", "شرموط", "منيوك", "كسمك", "زب", "فحل", "بورن", "متناك", "مص", "كس", "طيز", "قحبه", "فاجره", "احاا", "متناكه", "خول"]

# --- [ 2. الدوال المساعدة والفحص ] ---

async def has_permission(chat_id, user_id):
    if user_id in SUDOERS: return True
    try:
        member = await app.get_chat_member(chat_id, user_id)
        if member.status in [enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.OWNER]: return True
    except: return False
    return False

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

async def add_warn(message: Message, reason="normal"):
    c_id = message.chat.id
    u_id = message.from_user.id
    mention = message.from_user.mention

    if reason == "religious":  
        limit = 4  
        mute_days = 7   
        msg_text = f"<b>يـا {mention} ، تـذكـر قـول الله تـعـالـي : ( مَا يَلْفِظُ مِنْ قَوْلٍ إِلَّا لَدَيْهِ رَقِيبٌ عَتِيدٌ ) وأن هذه الدنيا فانية 🥀</b>"  
    else:  
        limit = max_warns.get(c_id, 3)  
        mute_days = 1   
        msg_text = f"<b>يـا {mention} ، تـم حـذف رسـالـتـك لـمـخـالـفـة قـوانـيـن الـحـمـايـة</b>"  

    if c_id not in warns_db: warns_db[c_id] = {}  
    warns_db[c_id][u_id] = warns_db[c_id].get(u_id, 0) + 1  
    current = warns_db[c_id][u_id]  
      
    if current > limit:  
        warns_db[c_id][u_id] = 0  
        kb = InlineKeyboardMarkup([[InlineKeyboardButton("فـك الـكـتـم", callback_data=f"u_unmute_{u_id}")]])  
        try:  
            await app.restrict_chat_member(c_id, u_id, ChatPermissions(can_send_messages=False), until_date=datetime.now() + timedelta(days=mute_days))  
            await message.reply(f"{msg_text}\n\n<b>• تم كتمك لمدة {mute_days} أيام لتخطي التحذيرات ({limit})</b>", reply_markup=kb)  
        except: pass  
    else:  
        await message.reply(f"{msg_text}\n\n<b>• تحذيراتك الحالية : ({current}/{limit})</b>")

# --- [ 3. أوامر الإدارة ] ---

@app.on_message(filters.command(["سماح", "شد سماح", "اكتم", "شد ميوت", "فك الكتم"], "") & filters.group)
async def admin_cmds_handler(_, message: Message):
    if not await has_permission(message.chat.id, message.from_user.id): return
    cmd = message.command[0]
    if message.reply_to_message:
        user_id = message.reply_to_message.from_user.id; mention = message.reply_to_message.from_user.mention
    else:
        if len(message.command) < 2: return
        try:
            user = await app.get_users(message.command[1]); user_id = user.id; mention = user.mention
        except: return
    try:
        if cmd == "سماح":
            await app.promote_chat_member(message.chat.id, user_id, privileges=ChatPrivileges(can_manage_chat=True, can_delete_messages=True, can_restrict_members=True))
            await message.reply(f"<b>• تم منح السماح لـ {mention}</b>")
        elif cmd == "شد سماح":
            await app.promote_chat_member(message.chat.id, user_id, privileges=ChatPrivileges(can_manage_chat=False))
            await message.reply(f"<b>• تم سحب السماح من {mention}</b>")
        elif cmd == "اكتم":
            await app.restrict_chat_member(message.chat.id, user_id, ChatPermissions(can_send_messages=False))
            await message.reply(f"<b>• تم كتم {mention}</b>")
        elif cmd in ["شد ميوت", "فك الكتم"]:
            await app.restrict_chat_member(message.chat.id, user_id, ChatPermissions(can_send_messages=True))
            await message.reply(f"<b>• تم فك كتم {mention}</b>")
    except: pass

@app.on_message(filters.command("تحذيرات", "") & filters.group)
async def set_warns_limit(_, message: Message):
    if not await has_permission(message.chat.id, message.from_user.id): return
    if len(message.command) < 2: return
    try:
        num = int(message.command[1])
        max_warns[message.chat.id] = num
        await message.reply(f"<b>• تم تحديد التحذيرات بـ {num}</b>")
    except: pass

# --- [ 4. أوامر المسح والتدمير ] ---

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
    temp = await message.reply(f"<b>• تم مسح {deleted} رسالة</b>")  
    await asyncio.sleep(3); await temp.delete()

@app.on_message(filters.command("تدمير ذاتي", "") & filters.group)
async def self_destruct_cmd(_, message: Message):
    if not await has_permission(message.chat.id, message.from_user.id): return
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("تـدمـيـر ذاتـي (500)", callback_data="total_destruction")]])
    await message.reply("<b>اضغط للبدء في تدمير آخر 500 رسالة</b>", reply_markup=kb)

# --- [ 5. محرك الحماية ولوحة الإعدادات ] ---

@app.on_message(filters.group & ~filters.me, group=-1)
async def protector_engine(_, message: Message):
    c_id = message.chat.id
    if not message.from_user or await has_permission(c_id, message.from_user.id): return
    locks = smart_db.get(c_id, set())

    if "all" in locks:  
        try: await message.delete()  
        except: pass  
        return  

    text = message.text or message.caption or ""  
    if "porn_text" in locks and text:  
        clean = re.sub(r"[^\u0621-\u064A\s]", "", text)  
        if any(fuzz.ratio(bad, word) > 85 for word in clean.split() for bad in BAD_WORDS):  
            await message.delete(); return await add_warn(message, reason="religious")  
  
    if "porn_media" in locks and message.photo:  
        file_path = await message.download()  
        if check_porn_api(file_path):  
            os.remove(file_path); await message.delete(); return await add_warn(message, reason="religious")  
        os.remove(file_path)  
  
    if "photos" in locks and message.photo: await message.delete(); return await add_warn(message)

@app.on_message(filters.command(["قفل", "فتح"], "") & filters.group)
async def toggle_lock_cmds(_, message: Message):
    if not await has_permission(message.chat.id, message.from_user.id): return
    if len(message.command) < 2: return
    cmd, input_text = message.command[0], message.text.split(None, 1)[1].strip()
    key = LOCK_MAP.get(input_text)
    if not key: return
    if message.chat.id not in smart_db: smart_db[message.chat.id] = set()
    if cmd == "قفل":
        smart_db[message.chat.id].add(key)
        await message.reply(f"<b>• تم قفل ({input_text})</b>")
    else:
        smart_db[message.chat.id].discard(key)
        await message.reply(f"<b>• تم فتح ({input_text})</b>")

def get_kb(chat_id):
    kb = []
    active = smart_db.get(chat_id, set())
    items = list(LOCK_MAP.items())
    for i in range(0, len(items), 2):
        row = []
        n1, k1 = items[i]; s1 = "مقفل" if k1 in active else "مفتوح"
        row.append(InlineKeyboardButton(f"{n1} ⇽ {s1}", callback_data=f"trg_{k1}"))
        if i + 1 < len(items):
            n2, k2 = items[i+1]; s2 = "مقفل" if k2 in active else "مفتوح"
            row.append(InlineKeyboardButton(f"{n2} ⇽ {s2}", callback_data=f"trg_{k2}"))
        kb.append(row)
    kb.append([InlineKeyboardButton("إغـلاق اللوحة", callback_data="close")])
    return InlineKeyboardMarkup(kb)

@app.on_message(filters.command(["الاعدادات", "locks"], "") & filters.group)
async def settings_cmd(_, message: Message):
    if not await has_permission(message.chat.id, message.from_user.id): return
    await message.reply_text(f"<b>• إعدادات مجموعة : {message.chat.title}</b>", reply_markup=get_kb(message.chat.id))

# --- [ 6. التفاعل مع الكيبورد ] ---

@app.on_callback_query(filters.regex("^(trg_|u_|close|total_destruction)"))
async def cb_handler(_, cb: CallbackQuery):
    if not await has_permission(cb.message.chat.id, cb.from_user.id): return
    if cb.data == "close": return await cb.message.delete()  
    if cb.data == "total_destruction":  
        await cb.answer("جاري النسف...", show_alert=True)  
        await cb.message.edit("<b>جاري التدمير...</b>")  
        deleted = await force_delete(cb.message.chat.id, cb.message.id, 500)  
        await app.send_message(cb.message.chat.id, f"<b>تم تدمير {deleted} رسالة</b>")  
        await cb.message.delete()  
    elif cb.data.startswith("trg_"):  
        key = cb.data.replace("trg_", "")  
        if cb.message.chat.id not in smart_db: smart_db[cb.message.chat.id] = set()  
        if key in smart_db[cb.message.chat.id]: smart_db[cb.message.chat.id].discard(key)  
        else: smart_db[cb.message.chat.id].add(key)  
        await cb.message.edit_reply_markup(reply_markup=get_kb(cb.message.chat.id))  
    elif cb.data.startswith("u_unmute_"):  
        u_id = int(cb.data.split("_")[2])  
        await app.restrict_chat_member(cb.message.chat.id, u_id, ChatPermissions(can_send_messages=True))  
        await cb.message.edit(f"<b>• تم فك الكتم</b>")
