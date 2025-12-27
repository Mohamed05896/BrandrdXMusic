import asyncio
import re
import os
import requests
from pyrogram import filters, enums
from pyrogram.types import Message, ChatPermissions, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from fuzzywuzzy import fuzz
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

LOCK_MAP = {
    "الروابط": "links", "المعرفات": "usernames", "التاك": "hashtags",
    "الشارحه": "slashes", "التثبيت": "pin", "المتحركه": "animations",
    "الشات": "text", "الدردشه": "text", "الصور": "photos", "الملصقات": "stickers",
    "الملفات": "docs", "البوتات": "bots", "التكرار": "flood", "الكلايش": "long_msgs",
    "الانلاين": "inline", "الفيديو": "videos", "البصمات": "voice", "السيلفي": "video_notes",
    "الماركدوان": "markdown", "التوجيه": "forward", "الاغاني": "audio",
    "الصوت": "voice", "الجهات": "contacts", "الاشعارات": "service",
    "السب": "porn", "الفشار": "porn", "الاباحي": "porn", "الوسائط": "media",
    "الانكليزيه": "english", "الفارسيه": "persian", "الدخول": "join",
    "التعديل": "edit", "تعديل الميديا": "edit_media", "التفليش": "kick",
    "الحمايه": "antiraid", "المجموعة": "all"
}

BAD_WORDS = ["سكس", "نيك", "شرموط", "منيوك", "كسم", "زب", "فحل", "بورن", "متناق", "مص", "كس", "طيز", "قحبه", "عير", "نيج", "خنيث", "لوطي", "خول"]

# --- [ 2. الـدوال الـمـسـاعـدة والـتـحـقـق ] ---

def is_bad_context(text):
    if not text: return False
    clean = re.sub(r"[^\u0621-\u064A\s]", "", text)
    words = clean.split()
    for word in words:
        for bad in BAD_WORDS:
            if fuzz.ratio(word, bad) > 85: return True
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

# --- [ 3. بـنـاء الـكـيـبوردات ] ---

def get_settings_keyboard(chat_id, target_id=None):
    kb, row, active = [], [], smart_db.get(chat_id, set())
    keys = list(LOCK_MAP.items())
    for i in range(0, len(keys), 2):
        name1, k1 = keys[i]
        if k1 == "all": continue
        row = [InlineKeyboardButton(f"{name1} {'✅' if k1 in active else '❌'}", callback_data=f"trg_{k1}")]
        if i+1 < len(keys):
            name2, k2 = keys[i+1]
            if k2 != "all":
                row.append(InlineKeyboardButton(f"{name2} {'✅' if k2 in active else '❌'}", callback_data=f"trg_{k2}"))
        kb.append(row)
    
    all_cmd = "فـتـح الـكـل" if "all" in active else "قـفـل الـكـل"
    kb.append([InlineKeyboardButton(all_cmd, callback_data="trg_all")])
    
    if target_id:
        kb.append([InlineKeyboardButton("👤 إدارة الأعـضـاء 👤", callback_data=f"mng_{target_id}")])
    
    kb.append([InlineKeyboardButton("‹ إغـلاق الـلـوحـة ›", callback_data="close_settings")])
    return InlineKeyboardMarkup(kb)

def get_management_keyboard(target_id):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("كتم", callback_data=f"u_mute_{target_id}"), InlineKeyboardButton("فك كتم", callback_data=f"u_unmute_{target_id}")],
        [InlineKeyboardButton("سماح", callback_data=f"u_allow_{target_id}"), InlineKeyboardButton("شد سماح", callback_data=f"u_disallow_{target_id}")],
        [InlineKeyboardButton("🔙 الـعـودة لـلأقـفـال", callback_data=f"back_locks_{target_id}")],
        [InlineKeyboardButton("‹ إغـلاق الـلـوحـة ›", callback_data="close_settings")]
    ])

# --- [ 4. مـعـالـج الأوامـر (كـتـابـة) ] ---

@app.on_message(filters.command(["قفل", "فتح"], "") & filters.group)
async def toggle_lock_text(_, message: Message):
    if not await is_admin(message.chat.id, message.from_user.id): return
    if len(message.command) < 2: return
    cmd, target = message.command[0], message.text.split(None, 1)[1]
    if target in LOCK_MAP:
        key = LOCK_MAP[target]
        if message.chat.id not in smart_db: smart_db[message.chat.id] = set()
        if cmd == "قفل":
            if key == "all": smart_db[message.chat.id].update(LOCK_MAP.values())
            else: smart_db[message.chat.id].add(key)
        else:
            if key == "all": smart_db[message.chat.id].clear()
            else: smart_db[message.chat.id].discard(key)
        await message.reply_text(f"<b>• تـم {cmd} {target} بـنـجـاح 🤍 •</b>")

@app.on_message(filters.command(["كتم", "ميوت", "فك ميوت", "شد ميوت", "سماح", "شد سماح"], "") & filters.group)
async def admin_text_cmds(_, message: Message):
    if not await is_admin(message.chat.id, message.from_user.id): return
    u_id = message.reply_to_message.from_user.id if message.reply_to_message else None
    if not u_id: return
    cmd = message.command[0]
    if cmd in ["كتم", "ميوت"]:
        await app.restrict_chat_member(message.chat.id, u_id, ChatPermissions(can_send_messages=False))
        await message.reply("<b>• تـم كـتـم الـعـضـو 🤍 •</b>")
    elif cmd in ["فك ميوت", "شد ميوت"]:
        await app.restrict_chat_member(message.chat.id, u_id, ChatPermissions(can_send_messages=True, can_send_media_messages=True, can_send_other_messages=True))
        await message.reply("<b>• تـم فـك الـكـتـم 🤍 •</b>")
    elif cmd == "سماح":
        if message.chat.id not in whitelist: whitelist[message.chat.id] = set()
        whitelist[message.chat.id].add(u_id)
        await message.reply("<b>• تـم إعـطـاء سـمـاح 🧚🤍 •</b>")
    elif cmd == "شد سماح":
        if message.chat.id in whitelist: whitelist[message.chat.id].discard(u_id)
        await message.reply("<b>• تـم شـد الـسـمـاح 🤍 •</b>")

@app.on_message(filters.command(["الاعدادات", "locks"], "") & filters.group)
async def settings_cmd(_, message: Message):
    if not await is_admin(message.chat.id, message.from_user.id): return
    t_id = message.reply_to_message.from_user.id if message.reply_to_message else None
    await message.reply_text(f"<b>• إعـدادات مـجـمـوعـة : {message.chat.title} 🦋</b>", reply_markup=get_settings_keyboard(message.chat.id, t_id))

# --- [ 5. مـعـالـج الـكـول بـاك (انـلايـن) ] ---

@app.on_callback_query(filters.regex("^(trg_|mng_|u_|back_locks_|close_settings)"))
async def cb_handler(_, cb: CallbackQuery):
    c_id, u_id = cb.message.chat.id, cb.from_user.id
    if not await is_admin(c_id, u_id): return await cb.answer("• للمشرفين فقط 🤍", show_alert=True)
    if cb.data == "close_settings": return await cb.message.delete()
    
    if cb.data.startswith("trg_"):
        key = cb.data.replace("trg_", "")
        if c_id not in smart_db: smart_db[c_id] = set()
        if key == "all":
            if "all" in smart_db[c_id]: smart_db[c_id].clear()
            else: smart_db[c_id].update(LOCK_MAP.values())
        else:
            if key in smart_db[c_id]: smart_db[c_id].discard(key)
            else: smart_db[c_id].add(key)
        await cb.message.edit_reply_markup(reply_markup=get_settings_keyboard(c_id))
        await cb.answer("• تم التحديث •")

    elif cb.data.startswith("mng_"):
        t_id = cb.data.split("_")[1]
        await cb.message.edit_text(f"<b>• إدارة الـعـضـو : {t_id} 👤</b>", reply_markup=get_management_keyboard(t_id))

    elif cb.data.startswith("back_locks_"):
        t_id = cb.data.split("_")[2]
        await cb.message.edit_text(f"<b>• إعـدادات مـجـمـوعـة : {cb.message.chat.title} 🦋</b>", reply_markup=get_settings_keyboard(c_id, t_id))

    elif cb.data.startswith("u_"):
        parts = cb.data.split("_")
        act, target = parts[1], int(parts[2])
        if act == "mute": await app.restrict_chat_member(c_id, target, ChatPermissions(can_send_messages=False))
        elif act == "unmute": await app.restrict_chat_member(c_id, target, ChatPermissions(can_send_messages=True, can_send_media_messages=True, can_send_other_messages=True))
        elif act == "allow":
            if c_id not in whitelist: whitelist[c_id] = set()
            whitelist[c_id].add(target)
        elif act == "disallow":
            if c_id in whitelist: whitelist[c_id].discard(target)
        await cb.answer("• تم تنفيذ الإجراء •", show_alert=True)

# --- [ 6. الـمـحـرك الـحـمـايـة ] ---

@app.on_message(filters.group & ~filters.me, group=-1)
async def protector_engine(client, message: Message):
    c_id, u_id = message.chat.id, message.from_user.id if message.from_user else None
    if not u_id or await has_permission(c_id, u_id): return
    locks = smart_db.get(c_id, set())
    if not locks: return
    text = message.text or message.caption or ""

    if "all" in locks or ("text" in locks and message.text): return await message.delete()
    if "links" in locks and (message.entities or message.caption_entities): return await message.delete()
    if "photos" in locks and message.photo: return await message.delete()
    if "videos" in locks and message.video: return await message.delete()
    if "stickers" in locks and message.sticker: return await message.delete()
    if "voice" in locks and message.voice: return await message.delete()
    if "bots" in locks and message.new_chat_members:
        for m in message.new_chat_members:
            if m.is_bot: await app.ban_chat_member(c_id, m.id)
    if "porn" in locks and is_bad_context(text):
        await message.delete()
        return await message.reply_text("<b>• عـذراً، الـسـب مـمـنـوع 🧚🤍 •</b>")

@app.on_message(filters.command(["مسح"], "") & filters.group)
async def clear_chat_cmd(_, message: Message):
    if not await is_admin(message.chat.id, message.from_user.id): return
    num = int(message.command[1]) if len(message.command) > 1 else 100
    await message.delete()
    async for m in app.get_chat_history(message.chat.id, limit=num):
        try: await m.delete()
        except: pass
    t = await message.reply("<b>• تم المسح 🧹 •</b>")
    await asyncio.sleep(2); await t.delete()
