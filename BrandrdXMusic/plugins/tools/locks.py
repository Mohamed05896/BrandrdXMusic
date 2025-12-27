import asyncio
import re
import os
import requests
from pyrogram import filters, enums
from pyrogram.types import Message, ChatPermissions, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from fuzzywuzzy import fuzz # تأكد من تثبيتها: pip install fuzzywuzzy python-Levenshtein
from BrandrdXMusic import app
from BrandrdXMusic.misc import SUDOERS 

# --- [ 1. مخـازن البيـانـات والـذكـاء الاصـطـنـاعي ] ---
API_USER = "1800965377"
API_SECRET = "pp32KRVBbfQjJXqLYoah7goaU949hwjU"

smart_db = {} 
user_violations = {} 
warn_limits = {} 
last_msg_cache = {} 
whitelist = {} 

# خريطة الأقفال الشاملة (35 نوع قفل وتفصيل)
LOCK_MAP = {
    "الروابط": "links", "المعرفات": "usernames", "التاك": "hashtags",
    "الشارحه": "slashes", "التثبيت": "pin", "المتحركه": "animations",
    "الشات": "text", "الدردشه": "text", "الصور": "photos", "الملصقات": "stickers",
    "الملفات": "docs", "البوتات": "bots", "التكرار": "flood", "الكلايش": "long_msgs",
    "الانلاين": "inline", "الفيديو": "videos", "البصمات": "voice", "السيلفي": "video_notes",
    "الماركدوان": "markdown", "التوجيه": "forward", "الاغاني": "audio",
    "الصوت": "voice", "الجهات": "contacts", "الاشعارات": "service",
    "السب": "porn", "الفشار": "porn", "الاباحي": "porn", "الوسائط": "media",
    "الانكليزيه": "english", "الفارسيه": "persian", "دخول الايران": "persian",
    "الدخول": "join", "جمثون": "gmthon", "التعديل": "edit",
    "تعديل الميديا": "edit_media", "التفليش": "kick", "الحمايه": "antiraid", "المجموعة": "all"
}

# قائمة الجذور للرادار الذكي (كلام وحش وقريب منه)
BAD_WORDS = ["سكس", "نيك", "شرموط", "منيوك", "كسم", "زب", "فحل", "بورن", "متناق", "مص", "كس", "طيز", "قحبه", "عير", "نيج", "خنيث", "لوطي", "خول"]

# --- [ 2. دوال الـتـحـقـق والـحـمـاية والـرادار ] ---

def is_bad_context(text):
    """رادار كشف الكلام الوحش والتقارب والسياق"""
    if not text: return False
    clean = re.sub(r"[^\u0621-\u064A\s]", "", text)
    words = clean.split()
    for word in words:
        for bad in BAD_WORDS:
            if fuzz.ratio(word, bad) > 85: return True
    patterns = [r"تعال.*ننام", r"عايز.*انيك", r"هات.*صورة"]
    for p in patterns:
        if re.search(p, clean): return True
    return False

def check_nudity(image_path):
    params = {'models': 'nudity-2.0', 'api_user': API_USER, 'api_secret': API_SECRET}
    try:
        with open(image_path, 'rb') as img:
            r = requests.post('https://api.sightengine.com/1.0/check.json', files={'media': img}, data=params)
            output = r.json()
            if output.get('status') == 'success':
                n = output.get('nudity', {})
                score = n.get('sexual_display', 0) + n.get('sexual_activity', 0) + n.get('erotica', 0)
                return score > 0.40
    except: pass
    return False

async def is_admin(chat_id, user_id):
    if user_id in SUDOERS: return True
    try:
        member = await app.get_chat_member(chat_id, user_id)
        return member.status in [enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.OWNER]
    except: return False

async def has_permission(chat_id, user_id):
    if await is_admin(chat_id, user_id): return True
    if chat_id in whitelist and user_id in whitelist[chat_id]: return True
    return False

# --- [ 3. أوامـر الـسـمـاح والـكـتـم والـتـحـذيـر ] ---

@app.on_message(filters.command(["تحذير"], "") & filters.group)
async def set_warn_limit(_, message: Message):
    if not await is_admin(message.chat.id, message.from_user.id): return
    if len(message.command) < 2: return
    try:
        num = int(message.command[1])
        warn_limits[message.chat.id] = num
        await message.reply_text(f"<b>• تـم تـعـيـيـن حـد الـتـحـذيـرات : {num} 🤍 •</b>")
    except: pass

@app.on_message(filters.command(["سماح"], "") & filters.group)
async def allow_user_handler(_, message: Message):
    if not await is_admin(message.chat.id, message.from_user.id): return
    u_id = message.reply_to_message.from_user.id if message.reply_to_message else None
    if u_id:
        if message.chat.id not in whitelist: whitelist[message.chat.id] = set()
        whitelist[message.chat.id].add(u_id)
        await message.reply_text(f"<b>• تـم إعـطـاء سـمـاح لـلـعـضـو بـنـجـاح 🧚🤍 •</b>")

@app.on_message(filters.command(["شد سماح"], "") & filters.group)
async def revoke_allow_handler(_, message: Message):
    if not await is_admin(message.chat.id, message.from_user.id): return
    u_id = message.reply_to_message.from_user.id if message.reply_to_message else None
    if u_id and message.chat.id in whitelist:
        whitelist[message.chat.id].discard(u_id)
        await message.reply_text(f"<b>• تـم شـد الـسـمـاح مـن الـعـضـو 🤍 •</b>")

@app.on_message(filters.command(["ميوت", "كتم"], "") & filters.group)
async def mute_user_handler(_, message: Message):
    if not await is_admin(message.chat.id, message.from_user.id): return
    u_id = message.reply_to_message.from_user.id if message.reply_to_message else None
    if u_id and not await is_admin(message.chat.id, u_id):
        await app.restrict_chat_member(message.chat.id, u_id, ChatPermissions(can_send_messages=False))
        await message.reply_text(f"<b>• تـم كـتـم الـعـضـو بـنـجـاح 🔇🤍 •</b>")

@app.on_message(filters.command(["شد ميوت", "فك ميوت"], "") & filters.group)
async def unmute_user_handler(_, message: Message):
    if not await is_admin(message.chat.id, message.from_user.id): return
    u_id = message.reply_to_message.from_user.id if message.reply_to_message else None
    if u_id:
        await app.restrict_chat_member(message.chat.id, u_id, ChatPermissions(can_send_messages=True, can_send_media_messages=True, can_send_other_messages=True, can_add_web_page_previews=True))
        await message.reply_text(f"<b>• تـم فـك الـكـتـم عـن الـعـضـو 🔊🤍 •</b>")

# --- [ 4. لـوحـة الإعـدادات الـمـزخـرفـة (انـلايـن) ] ---

@app.on_message(filters.command(["الاعدادات", "locks"], "") & filters.group)
async def settings_keyboard(_, message: Message):
    if not await is_admin(message.chat.id, message.from_user.id): return
    kb, row, active = [], [], smart_db.get(message.chat.id, set())
    for name, key in LOCK_MAP.items():
        if key == "all": continue
        status = "مـقـفـول" if key in active else "مـفـتـوح"
        row.append(InlineKeyboardButton(f"• {name} ⤶ {status} •", callback_data=f"trg_{key}"))
        if len(row) == 2: kb.append(row); row = []
    if row: kb.append(row)
    all_cmd = "فـتـح الـكـل" if "all" in active else "قـفـل الـكـل"
    kb.append([InlineKeyboardButton(f"‹ {all_cmd} ›", callback_data="trg_all")])
    kb.append([InlineKeyboardButton("‹ إغـلاق الـلـوحـة ›", callback_data="close_settings")])
    await message.reply_text(f"<b>• تـم فـتـح لـوحـة تـحـكـم : {message.chat.title} 🦋</b>", reply_markup=InlineKeyboardMarkup(kb))

@app.on_callback_query(filters.regex("^trg_") | filters.regex("close_settings"))
async def handle_callback(_, cb: CallbackQuery):
    c_id, u_id = cb.message.chat.id, cb.from_user.id
    if not await is_admin(c_id, u_id): return await cb.answer("• لـلـمـشـرفـيـن فـقـط 🤍", show_alert=True)
    if cb.data == "close_settings":
        await cb.message.delete()
        return await cb.answer("• تـم إغـلاق الإعـدادات •")
    key = cb.data.replace("trg_", "")
    if c_id not in smart_db: smart_db[c_id] = set()
    if key == "all":
        if "all" in smart_db[c_id]: smart_db[c_id].clear()
        else: smart_db[c_id].update(LOCK_MAP.values())
    else:
        if key in smart_db[c_id]: smart_db[c_id].discard(key)
        else: smart_db[c_id].add(key)
    # تحديث الكيبورد
    kb, row, active = [], [], smart_db.get(c_id, set())
    for name, k in LOCK_MAP.items():
        if k == "all": continue
        row.append(InlineKeyboardButton(f"• {name} ⤶ {'مـقـفـول' if k in active else 'مـفـتـوح'} •", callback_data=f"trg_{k}"))
        if len(row) == 2: kb.append(row); row = []
    if row: kb.append(row)
    kb.append([InlineKeyboardButton(f"‹ {'فـتـح الـكـل' if 'all' in active else 'قـفـل الـكـل'} ›", callback_data="trg_all")])
    kb.append([InlineKeyboardButton("‹ إغـلاق الـلـوحـة ›", callback_data="close_settings")])
    await cb.message.edit_reply_markup(reply_markup=InlineKeyboardMarkup(kb))
    await cb.answer("• تـم تـحـديـث الـحـالـة •")

@app.on_message(filters.command(["مسح", "مسح الشات"], "") & filters.group)
async def clear_chat_cmd(_, message: Message):
    if not await is_admin(message.chat.id, message.from_user.id): return
    num = int(message.command[1]) if len(message.command) > 1 and message.command[1].isdigit() else 100
    await message.delete()
    async for msg in app.get_chat_history(message.chat.id, limit=num):
        try: await msg.delete()
        except: pass
    t = await message.reply_text(f"<b>• تـم مـسـح {num} رسـالـة بـنـجـاح 🧹🤍 •</b>")
    await asyncio.sleep(2); await t.delete()

# --- [ 5. الـمـحـرك الـحـديـدي والـرادار الـذكي ] ---

@app.on_message(filters.group & ~filters.me, group=-1)
async def protector_engine(client, message: Message):
    c_id, u_id = message.chat.id, message.from_user.id if message.from_user else None
    if not u_id or await has_permission(c_id, u_id): return
    locks = smart_db.get(c_id, set())
    if not locks: return

    text_content = message.text or message.caption or ""

    # فحص القفل الشامل
    if "all" in locks: return await message.delete()
    if "text" in locks and message.text: return await message.delete()

    # فحص الإباحية والسب (الرادار والرد المزخرف)
    if "porn" in locks:
        if is_bad_context(text_content):
            await message.delete()
            return await message.reply_text("<b>اقـفـل بـوقـك يـا حـمـار 🧚🤍</b>")
        if message.photo:
            path = await message.download()
            if check_nudity(path): 
                os.remove(path); await message.delete()
                return await message.reply_text(f"<b>• عـذراً {message.from_user.mention}، الـصـور الإبـاحـيـة مـمـنـوعـة ❌ •</b>")
            os.remove(path)

    v_type = None
    if "links" in locks and (message.entities or message.caption_entities): v_type = "الروابط"
    elif "photos" in locks and message.photo: v_type = "الصور"
    elif "stickers" in locks and message.sticker: v_type = "الملصقات"
    elif "videos" in locks and message.video: v_type = "الفيديو"
    elif "voice" in locks and message.voice: v_type = "البصمات"
    elif "flood" in locks and message.text:
        if last_msg_cache.get(f"{c_id}:{u_id}") == message.text: v_type = "التكرار"
        last_msg_cache[f"{c_id}:{u_id}"] = message.text

    if v_type:
        try:
            await message.delete()
            v_key = f"{c_id}:{u_id}"
            limit = warn_limits.get(c_id, 3)
            user_violations[v_key] = user_violations.get(v_key, 0) + 1
            if user_violations[v_key] >= limit:
                await app.restrict_chat_member(c_id, u_id, ChatPermissions(can_send_messages=False))
                user_violations[v_key] = 0
                await message.reply_text(f"<b>• تـم تـقـيـيـدك لـتـكـرار الـمـخـالـفـات 🧚🤍\n👤: {message.from_user.mention} •</b>")
            else:
                a = await message.reply_text(f"<b>• عـذراً {message.from_user.mention}، {v_type} مـقـفـول 🧚🤍 ({user_violations[v_key]}/{limit}) •</b>")
                await asyncio.sleep(2); await a.delete()
        except: pass

# --- [ 6. مـنـع الـبـوتـات ] ---
@app.on_message(filters.group & filters.new_chat_members)
async def anti_bot(client, message: Message):
    if "bots" in smart_db.get(message.chat.id, set()):
        for m in message.new_chat_members:
            if m.is_bot:
                try: await message.chat.ban_member(m.id)
                except: pass
