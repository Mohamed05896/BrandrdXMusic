import asyncio
import re
import requests
import os
import time
from datetime import datetime, timedelta
from pyrogram import filters, enums
from pyrogram.types import (
    Message, ChatPermissions, ChatPrivileges, 
    InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
)
from fuzzywuzzy import fuzz
from motor.motor_asyncio import AsyncIOMotorClient

# --- استيراد كائن البوت وقائمة المطورين من ملفات السورس ---
from BrandrdXMusic import app
from BrandrdXMusic.misc import SUDOERS

# =========================================================
# [ 1 ] إعدادات الاتصال والبيانات (Data Configuration)
# =========================================================

# بيانات API لفحص الصور (Sightengine)
API_USER = "1800965377"
API_SECRET = "pp32KRVBbfQjJXqLYoah7goaU949hwjU"

# سحب رابط قاعدة البيانات من المتغيرات (أو استخدام الافتراضي)
MONGO_DB_URI = os.getenv("MONGO_DB_URI") or "mongodb://localhost:27017"
mongo_client = AsyncIOMotorClient(MONGO_DB_URI) # إنشاء اتصال غير متزامن
db = mongo_client.protection_bot # اسم قاعدة البيانات

# تعريف المجموعات (Collections)
db_locks = db.locks   # لتخزين حالة الأقفال
db_warns = db.warns   # لتخزين التحذيرات

# ذاكرة مؤقتة (RAM) لفحص التكرار بسرعة عالية
flood_cache = {} 

# ذاكرة لمنع تكرار الرد (Double Reply Fix)
processed_cache = {}

# خريطة الأقفال (الاسم العربي : المفتاح البرمجي)
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

# قائمة الكلمات المحظورة
BAD_WORDS = ["سكس", "نيك", "شرموط", "منيوك", "كسمك", "زب", "فحل", "بورن", "متناك", "مص", "كس", "طيز", "قحبه", "فاجره", "احاا", "متناكه", "خول"]

# =========================================================
# [ 2 ] دوال قاعدة البيانات (Database Logic)
# =========================================================

async def get_locks(chat_id):
    doc = await db_locks.find_one({"chat_id": chat_id})
    return set(doc.get("locks", [])) if doc else set()

async def update_lock(chat_id, key, lock=True):
    if lock:
        await db_locks.update_one({"chat_id": chat_id}, {"$addToSet": {"locks": key}}, upsert=True)
    else:
        await db_locks.update_one({"chat_id": chat_id}, {"$pull": {"locks": key}}, upsert=True)

async def get_warn_limit(chat_id):
    doc = await db_warns.find_one({"chat_id": chat_id})
    return doc.get("limit", 3) if doc else 3

async def set_warn_limit_db(chat_id, limit):
    await db_warns.update_one({"chat_id": chat_id}, {"$set": {"limit": limit}}, upsert=True)

async def get_current_warns(chat_id, user_id):
    doc = await db_warns.find_one({"chat_id": chat_id})
    if doc and "users" in doc:
        return doc["users"].get(str(user_id), 0)
    return 0

async def update_user_warns(chat_id, user_id, count):
    await db_warns.update_one({"chat_id": chat_id}, {"$set": {f"users.{user_id}": count}}, upsert=True)

# =========================================================
# [ 3 ] الدوال المساعدة والمنطق (Helpers)
# =========================================================

async def has_permission(chat_id, user_id):
    if user_id in SUDOERS: return True
    try:
        member = await app.get_chat_member(chat_id, user_id)
        if member.status in [enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.OWNER]: return True
    except: return False
    return False

async def force_delete(chat_id, current_id, limit):
    count = 0
    msg_ids = list(range(current_id, current_id - (limit + 50), -1))
    for i in range(0, len(msg_ids), 100):
        if count >= limit: break
        try:
            await app.delete_messages(chat_id, msg_ids[i:i+100])
            count += 100 # تقريبي
        except: continue
    return count

def check_porn_api(file_path):
    try:
        params = {'models': 'nudity-2.0', 'api_user': API_USER, 'api_secret': API_SECRET}
        with open(file_path, 'rb') as f:
            r = requests.post('https://api.sightengine.com/1.0/check.json', files={'media': f}, data=params)
        output = r.json()
        if output.get('status') == 'success':
            n = output.get('nudity', {})
            return n.get('sexual_display', 0) > 0.5 or n.get('erotica', 0) > 0.5
    except: pass
    return False

# دالة مساعدة لمد النصوص ديناميكياً للأزرار
def extend_text(text):
    return text.replace("", "ـ").strip("ـ").replace("ـ ـ", " ")

async def add_warn(message: Message, reason="normal"):
    c_id = message.chat.id
    u_id = message.from_user.id
    mention = message.from_user.mention

    if reason == "religious":  
        limit = 4  
        mute_days = 7   
        msg_text = f"<b>يـا {mention} ، تـذكـر قـول الله تـعـالـي : ( مَا يَلْفِظُ مِنْ قَوْلٍ إِلَّا لَدَيْهِ رَقِيبٌ عَتِيدٌ ) وأن هذه الدنيا فانية 🥀</b>"  
    else:  
        limit = await get_warn_limit(c_id)  
        mute_days = 1   
        msg_text = f"<b>يـا {mention} ، تـم حـذف رسـالـتـك لـمـخـالـفـة قـوانـيـن الـحـمـايـة</b>"  

    current = await get_current_warns(c_id, u_id)
    current += 1
      
    if current > limit:  
        await update_user_warns(c_id, u_id, 0)
        kb = InlineKeyboardMarkup([[InlineKeyboardButton("• فـك الـكـتـم 🧚 •", callback_data=f"u_unmute_{u_id}")]])  
        try:  
            await app.restrict_chat_member(c_id, u_id, ChatPermissions(can_send_messages=False), until_date=datetime.now() + timedelta(days=mute_days))
            await message.reply(f"{msg_text}\n\n<b>• تـم كـتـمـك لـمـدة {mute_days} أيـام لـتـخـطـي الـتـحـذيـرات</b>", reply_markup=kb)  
        except: pass  
    else:  
        await update_user_warns(c_id, u_id, current)
        await message.reply(f"{msg_text}\n\n<b>• تـحـذيـراتـك الـحـالـيـة : ({current}/{limit})</b>")

# =========================================================
# [ 4 ] أوامر الإدارة (Admin Commands)
# =========================================================

@app.on_message(filters.command(["سماح", "شد سماح", "كتم", "شد ميوت", "فك الكتم"], "") & filters.group)
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
            await message.reply(f"<b>• تـم مـنـح الـسـمـاح لـ {mention}</b>")
        elif cmd == "شد سماح":
            await app.promote_chat_member(message.chat.id, user_id, privileges=ChatPrivileges(can_manage_chat=False))
            await message.reply(f"<b>• تـم سـحـب الـسـمـاح مـن {mention}</b>")
        elif cmd == "كتم":
            await app.restrict_chat_member(message.chat.id, user_id, ChatPermissions(can_send_messages=False))
            await message.reply(f"<b>• تـم كـتـم {mention}</b>")
        elif cmd in ["شد ميوت", "فك الكتم"]:
            await app.restrict_chat_member(message.chat.id, user_id, ChatPermissions(can_send_messages=True))
            await message.reply(f"<b>• تـم فـك كـتـم {mention}</b>")
    except: pass

@app.on_message(filters.command("تحذيرات", "") & filters.group)
async def set_warns_cmd(_, message: Message):
    if not await has_permission(message.chat.id, message.from_user.id): return
    if len(message.command) < 2: return
    try:
        num = int(message.command[1])
        await set_warn_limit_db(message.chat.id, num)
        await message.reply(f"<b>• تـم تـحـديـد الـتـحـذيـرات بـ {num}</b>")
    except: pass

# =========================================================
# [ 5 ] أوامر المسح والتدمير (Cleaning)
# =========================================================

@app.on_message(filters.command(["مسح", "تنظيف"], "") & filters.group)
async def destructive_clear(_, message: Message):
    if not await has_permission(message.chat.id, message.from_user.id): return
    if message.reply_to_message:  
        start_id = message.reply_to_message.id; end_id = message.id  
        msg_ids = list(range(start_id, end_id + 1))  
        for i in range(0, len(msg_ids), 100):  
            try: await app.delete_messages(message.chat.id, msg_ids[i:i+100])  
            except: continue  
        deleted = len(msg_ids)  
    else:  
        try: num = int(message.command[1]) if len(message.command) > 1 else 100  
        except: num = 100  
        deleted = await force_delete(message.chat.id, message.id, num)  
    temp = await message.reply(f"<b>• تـم مـسـح {deleted} رسـالـة</b>")  
    await asyncio.sleep(3); await temp.delete()

@app.on_message(filters.command("تدمير ذاتي", "") & filters.group)
async def self_destruct(_, message: Message):
    if not await has_permission(message.chat.id, message.from_user.id): return
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("تـدمـيـر ذاتـي (500)", callback_data="total_destruction")]])
    await message.reply("<b>اضـغـط لـلـبـدء فـي تـدمـيـر آخـر 500 رسـالـة</b>", reply_markup=kb)

# =========================================================
# [ 6 ] محرك الحماية الشامل (Full Protection Engine)
# =========================================================

@app.on_message(filters.group & ~filters.me, group=-1)
async def protector_engine(_, message: Message):
    c_id = message.chat.id
    user_id = message.from_user.id if message.from_user else 0
    
    # 1. منع تكرار معالجة نفس الرسالة
    if c_id not in processed_cache: processed_cache[c_id] = []
    if message.id in processed_cache[c_id]: return 
    processed_cache[c_id].append(message.id)
    if len(processed_cache[c_id]) > 50: processed_cache[c_id].pop(0)

    # 2. استثناء المشرفين
    if user_id and await has_permission(c_id, user_id): return
    
    locks = await get_locks(c_id)
    if not locks: return

    # --- القفل العام (الشات) ---
    if "all" in locks:  
        try: await message.delete()  
        except: pass  
        return  

    # --- التكرار (Flood) ---
    if "flood" in locks:
        now = time.time()
        key = f"{c_id}:{user_id}"
        hist = flood_cache.get(key, [])
        hist = [t for t in hist if now - t < 5] # آخر 5 ثواني
        hist.append(now); flood_cache[key] = hist
        if len(hist) > 5:
            try: await message.delete(); flood_cache[key] = []; return await add_warn(message, reason="flood")
            except: pass

    # --- الخدمة والبوتات ---
    if message.service:
        if "service" in locks: 
            try: await message.delete()
            except: pass
        if message.new_chat_members and "bots" in locks:
            for m in message.new_chat_members:
                if m.is_bot and m.id != (await app.get_me()).id:
                    try: await app.ban_chat_member(c_id, m.id); await message.delete()
                    except: pass
        if message.pinned_message and "pin" in locks:
            try: await message.unpin_all_messages()
            except: pass
        return

    # --- النصوص والميديا ---
    text = message.text or message.caption or ""
    should_delete = False; is_religious = False
    
    # فحص النصوص
    if text:
        if "porn_text" in locks: # فحص السب
            clean = re.sub(r"[^\u0621-\u064A\s]", "", text)
            if any(fuzz.ratio(bad, word) > 85 for word in clean.split() for bad in BAD_WORDS):
                should_delete = True; is_religious = True
        
        if not should_delete and "links" in locks and ("http" in text or ".com" in text or "www" in text): should_delete = True
        if not should_delete and "usernames" in locks and "@" in text: should_delete = True
        if not should_delete and "hashtags" in locks and "#" in text: should_delete = True
        if not should_delete and "markdown" in locks and ("**" in text or "__" in text or "`" in text): should_delete = True
        if not should_delete and "slashes" in locks and text.startswith("/"): should_delete = True
        if not should_delete and "long_msgs" in locks and len(text) > 800: should_delete = True

    # فحص أنواع الميديا
    if not should_delete:
        if "photos" in locks and message.photo: should_delete = True
        elif "videos" in locks and message.video: should_delete = True
        elif "animations" in locks and message.animation: should_delete = True
        elif "stickers" in locks and message.sticker: should_delete = True
        elif "docs" in locks and message.document: should_delete = True
        elif "voice" in locks and (message.voice or message.audio): should_delete = True
        elif "audio" in locks and message.audio: should_delete = True
        elif "video_notes" in locks and message.video_note: should_delete = True 
        elif "contacts" in locks and message.contact: should_delete = True
        elif "inline" in locks and message.via_bot: should_delete = True
        elif "forward" in locks and (message.forward_date or message.forward_from): should_delete = True

    # تنفيذ الحذف
    if should_delete:
        try: await message.delete()
        except: pass
        return await add_warn(message, reason="religious" if is_religious else "normal")

    # فحص الإباحية المتقدم (API)
    if "porn_media" in locks and (message.photo or (message.video and message.video.file_size < 50*1024*1024)):
        try:
            path = await message.download()
            is_porn = await asyncio.get_event_loop().run_in_executor(None, check_porn_api, path)
            os.remove(path)
            if is_porn:
                try: await message.delete(); return await add_warn(message, reason="religious")
                except: pass
        except: pass

# =========================================================
# [ 7 ] أوامر القفل والفتح (Lock Commands)
# =========================================================

@app.on_message(filters.command(["قفل", "فتح"], "") & filters.group)
async def toggle_lock(_, message: Message):
    if not await has_permission(message.chat.id, message.from_user.id): return
    if len(message.command) < 2: return
    cmd, input_text = message.command[0], message.text.split(None, 1)[1].strip()
    key = LOCK_MAP.get(input_text)
    if not key: return
    
    if cmd == "قفل":
        await update_lock(message.chat.id, key, True)
        # تمديد نص الرد
        ex_text = extend_text(input_text)
        await message.reply(f"<b>• تـم قـفـل ({ex_text})</b>")
    else:
        await update_lock(message.chat.id, key, False)
        # تمديد نص الرد
        ex_text = extend_text(input_text)
        await message.reply(f"<b>• تـم فـتـح ({ex_text})</b>")

async def get_kb(chat_id):
    kb = []
    active = await get_locks(chat_id)
    items = list(LOCK_MAP.items())
    for i in range(0, len(items), 2):
        row = []
        n1, k1 = items[i]; s1 = "مـقـفـل" if k1 in active else "مـفـتـوح"
        ex_n1 = extend_text(n1)
        row.append(InlineKeyboardButton(f"• {ex_n1} ← {s1} •", callback_data=f"trg_{k1}"))
        
        if i + 1 < len(items):
            n2, k2 = items[i+1]; s2 = "مـقـفـل" if k2 in active else "مـفـتـوح"
            ex_n2 = extend_text(n2)
            row.append(InlineKeyboardButton(f"• {ex_n2} ← {s2} •", callback_data=f"trg_{k2}"))
        kb.append(row)
    kb.append([InlineKeyboardButton("إغـلاق اللـوحـة", callback_data="close")])
    return InlineKeyboardMarkup(kb)

@app.on_message(filters.command(["الاعدادات", "locks"], "") & filters.group)
async def settings(_, message: Message):
    if not await has_permission(message.chat.id, message.from_user.id): return
    await message.reply_text(f"<b>• إعـدادات مـجـمـوعـة : {message.chat.title}</b>", reply_markup=await get_kb(message.chat.id))

# =========================================================
# [ 8 ] التفاعل مع الكيبورد (Callbacks)
# =========================================================

@app.on_callback_query(filters.regex("^(trg_|u_|close|total_destruction)"))
async def callback(_, cb: CallbackQuery):
    if not await has_permission(cb.message.chat.id, cb.from_user.id): return
    if cb.data == "close": 
        try: return await cb.message.delete()
        except: pass
        
    if cb.data == "total_destruction":  
        await cb.answer("جـاري الـنـسـف...", show_alert=True)  
        await cb.message.edit("<b>جـاري الـتـدمـيـر...</b>")  
        deleted = await force_delete(cb.message.chat.id, cb.message.id, 500)  
        await app.send_message(cb.message.chat.id, f"<b>تـم تـدمـيـر {deleted} رسـالـة</b>")  
        await cb.message.delete()  
    elif cb.data.startswith("trg_"):  
        key = cb.data.replace("trg_", "")
        locks = await get_locks(cb.message.chat.id)
        if key in locks: await update_lock(cb.message.chat.id, key, False)
        else: await update_lock(cb.message.chat.id, key, True)
        try: await cb.message.edit_reply_markup(reply_markup=await get_kb(cb.message.chat.id))
        except: pass
    elif cb.data.startswith("u_unmute_"):  
        u_id = int(cb.data.split("_")[2])  
        try:
            await app.restrict_chat_member(cb.message.chat.id, u_id, ChatPermissions(can_send_messages=True))  
            await cb.message.edit(f"<b>• تـم فـك الـكـتـم</b>")
        except: pass
