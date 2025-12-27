import asyncio
import re
import requests
import os
from datetime import datetime, timedelta
from pyrogram import filters, enums
from pyrogram.types import Message, ChatPermissions, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from fuzzywuzzy import fuzz
from BrandrdXMusic import app
from BrandrdXMusic.misc import SUDOERS 

# --- [ 1. مخـازن البيـانـات ] ---
API_USER = "1800965377"
API_SECRET = "pp32KRVBbfQjJXqLYoah7goaU949hwjU"

smart_db = {} 
whitelist = {} 
warns_db = {}     # لتخزين تحذيرات الأعضاء
max_warns = {}    # لتخزين الحد الأقصى لكل مجموعة (الافتراضي 3)
last_msg_cache = {} 

LOCK_MAP = {
    "الروابط": "links", "المعرفات": "usernames", "التاك": "hashtags",
    "الشارحه": "slashes", "التثبيت": "pin", "المتحركه": "animations",
    "الشات": "text", "الدردشه": "text", "الصور": "photos", "الملصقات": "stickers",
    "الملفات": "docs", "البوتات": "bots", "التكرار": "flood", "الكلايش": "long_msgs",
    "الانلاين": "inline", "الفيديو": "videos", "البصمات": "voice", "السيلفي": "video_notes",
    "الماركدوان": "markdown", "التوجيه": "forward", "الاغاني": "audio",
    "الصوت": "voice", "الجهات": "contacts", "الاشعارات": "service",
    "السب": "porn", "الاباحي": "porn", "الوسائط": "media", "المجموعة": "all"
}

BAD_WORDS = ["سكس", "نيك", "شرموط", "منيوك", "كسم", "زب", "فحل", "بورن", "متناق", "مص", "كس", "طيز", "قحبه", "عير", "نيج", "خنيث", "لوطي", "خول"]

# --- [ 2. الدوال المساعدة ] ---

async def has_permission(chat_id, user_id):
    if user_id in SUDOERS: return True
    try:
        member = await app.get_chat_member(chat_id, user_id)
        return member.status in [enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.OWNER]
    except: return False

def check_porn_api(file_path):
    try:
        params = {'models': 'nudity-2.0', 'api_user': API_USER, 'api_secret': API_SECRET}
        with open(file_path, 'rb') as f:
            r = requests.post('https://api.sightengine.com/1.0/check.json', files={'media': f}, data=params)
        output = r.json()
        if output.get('status') == 'success':
            return output['nudity']['sexual_display'] > 0.5 or output['nudity']['erotica'] > 0.5
    except: return False
    return False

async def add_warn(message: Message):
    """دالة إضافة التحذير والعقاب"""
    c_id, u_id = message.chat.id, message.from_user.id
    limit = max_warns.get(c_id, 3)
    
    if c_id not in warns_db: warns_db[c_id] = {}
    warns_db[c_id][u_id] = warns_db[c_id].get(u_id, 0) + 1
    
    current = warns_db[c_id][u_id]
    if current >= limit:
        warns_db[c_id][u_id] = 0 # تصفير
        until = datetime.now() + timedelta(hours=24)
        await app.restrict_chat_member(c_id, u_id, ChatPermissions(can_send_messages=False), until_date=until)
        await message.reply(f"<b>• الـعـضـو {message.from_user.mention}\n• وصـل لـحـد الـتـحـذيرات ({current}/{limit})\n• تـم كـتـمـه 24 سـاعـة تلقائياً 🤍</b>")
    else:
        await message.reply(f"<b>• تـم حـذف رسـالـتـك لـمـخـالـفـة الـقـوانـيـن 🤍\n• تـحـذيـراتـك : ({current}/{limit})</b>")

# --- [ 3. أوامر التحذيرات والإدارة ] ---

@app.on_message(filters.command("وضع التحذيرات", "") & filters.group)
async def set_warns_cmd(_, message: Message):
    if not await has_permission(message.chat.id, message.from_user.id): return
    if len(message.command) < 3: return await message.reply("• مثال: وضع التحذيرات 3")
    num = int(message.command[2])
    max_warns[message.chat.id] = num
    await message.reply(f"<b>• تـم تـعـيين حد الـتـحـذيرات لـ : {num} 🤍</b>")

@app.on_message(filters.command(["قفل", "فتح"], "") & filters.group)
async def toggle_lock_text(_, message: Message):
    if not await has_permission(message.chat.id, message.from_user.id): return
    if len(message.command) < 2: return
    cmd, target = message.command[0], message.text.split(None, 1)[1]
    if message.chat.id not in smart_db: smart_db[message.chat.id] = set()
    if target in LOCK_MAP:
        key = LOCK_MAP[target]
        if cmd == "قفل": smart_db[message.chat.id].add(key)
        else: smart_db[message.chat.id].discard(key)
        await message.reply_text(f"<b>• تـم {cmd} {target} بـنـجـاح 🤍 •</b>")

@app.on_message(filters.command(["كتم", "ميوت", "شد ميوت"], "") & filters.group)
async def mute_handler(_, message: Message):
    if not await has_permission(message.chat.id, message.from_user.id): return
    if not message.reply_to_message: return await message.reply("• رد على العضو لكتمه 24 ساعة 🤍")
    u_id = message.reply_to_message.from_user.id
    if await has_permission(message.chat.id, u_id): return
    until = datetime.now() + timedelta(hours=24)
    await app.restrict_chat_member(message.chat.id, u_id, ChatPermissions(can_send_messages=False), until_date=until)
    await message.reply("<b>• تـم كـتـم الـعـضـو 24 سـاعـة 🤍 •</b>")

@app.on_message(filters.command(["فك كتم", "فك ميوت", "سماح", "شد سماح"], "") & filters.group)
async def allow_handler(_, message: Message):
    if not await has_permission(message.chat.id, message.from_user.id): return
    if not message.reply_to_message: return
    u_id = message.reply_to_message.from_user.id
    if "شد سماح" in message.text:
        if message.chat.id in whitelist: whitelist[message.chat.id].discard(u_id)
        await message.reply("• تـم شـد الـسـمـاح 🤍")
    elif "سماح" in message.text:
        if message.chat.id not in whitelist: whitelist[message.chat.id] = set()
        whitelist[message.chat.id].add(u_id)
        await message.reply("• تـم الـسـمـاح 🧚🤍")
    else:
        await app.restrict_chat_member(message.chat.id, u_id, ChatPermissions(can_send_messages=True, can_send_media_messages=True))
        await message.reply("• تـم فـك الـكـتـم 🤍")

# --- [ 4. لوحة الإعدادات ] ---

def get_kb(chat_id, t_id=None):
    kb, active = [], smart_db.get(chat_id, set())
    unique = list(dict.fromkeys(LOCK_MAP.values()))
    names = {v: k for k, v in LOCK_MAP.items()}
    for i in range(0, len(unique), 2):
        k1 = unique[i]
        row = [InlineKeyboardButton(f"• {names[k1]} ⤶ {'مـقـفـول' if k1 in active else 'مـفـتـوح'} •", callback_data=f"trg_{k1}")]
        if i+1 < len(unique):
            k2 = unique[i+1]
            row.append(InlineKeyboardButton(f"• {names[k2]} ⤶ {'مـقـفـول' if k2 in active else 'مـفـتـوح'} •", callback_data=f"trg_{k2}"))
        kb.append(row)
    if t_id: kb.append([InlineKeyboardButton("── إدارة العضو (كتم 24س) ──", callback_data=f"mng_{t_id}")])
    kb.append([InlineKeyboardButton("‹ إغـلاق الـلـوحـة ›", callback_data="close")])
    return InlineKeyboardMarkup(kb)

@app.on_message(filters.command(["الاعدادات", "locks"], "") & filters.group)
async def settings_cmd(_, message: Message):
    if not await has_permission(message.chat.id, message.from_user.id): return
    t_id = message.reply_to_message.from_user.id if message.reply_to_message else None
    await message.reply_text(f"<b>• إعـدادات مـجـمـوعـة : {message.chat.title} 🦋</b>", reply_markup=get_kb(message.chat.id, t_id))

@app.on_callback_query(filters.regex("^(trg_|mng_|close)"))
async def cb_handler(_, cb: CallbackQuery):
    if not await has_permission(cb.message.chat.id, cb.from_user.id): return
    if cb.data == "close": return await cb.message.delete()
    if cb.data.startswith("trg_"):
        key, c_id = cb.data.replace("trg_", ""), cb.message.chat.id
        if c_id not in smart_db: smart_db[c_id] = set()
        if key in smart_db[c_id]: smart_db[c_id].discard(key)
        else: smart_db[c_id].add(key)
        await cb.message.edit_reply_markup(reply_markup=get_kb(c_id))
    elif cb.data.startswith("mng_"):
        t_id = int(cb.data.split("_")[1])
        await app.restrict_chat_member(cb.message.chat.id, t_id, ChatPermissions(can_send_messages=False), until_date=datetime.now()+timedelta(hours=24))
        await cb.answer("تم كتم العضو 24 ساعة", show_alert=True)

# --- [ 5. محرك الحماية والتحذيرات ] ---

@app.on_message(filters.group & ~filters.me, group=-1)
async def protector_engine(_, message: Message):
    c_id, u_id = message.chat.id, message.from_user.id if message.from_user else None
    if not u_id or await has_permission(c_id, u_id) or (c_id in whitelist and u_id in whitelist[c_id]): return
    locks = smart_db.get(c_id, set())
    if not locks: return
    
    text = message.text or message.caption or ""
    delete = False

    # التكرار
    if "flood" in locks and text:
        if c_id not in last_msg_cache: last_msg_cache[c_id] = {}
        if last_msg_cache[c_id].get(u_id) == text: delete = True
        last_msg_cache[c_id][u_id] = text

    # السب والاباحي (نصوص)
    if "porn" in locks and text:
        clean = re.sub(r"[^\u0621-\u064A\s]", "", text)
        if any(fuzz.ratio(bad, word) > 85 for word in clean.split() for bad in BAD_WORDS):
            await message.delete()
            return await add_warn(message)

    # فحص الصور بالـ API
    if "porn" in locks and message.photo:
        path = await message.download()
        is_porn = check_porn_api(path)
        if os.path.exists(path): os.remove(path)
        if is_porn:
            await message.delete()
            return await add_warn(message)

    # الأقفال العامة
    if "all" in locks: delete = True
    check = [
        ("links", message.entities or message.caption_entities),
        ("photos", message.photo), ("videos", message.video),
        ("stickers", message.sticker), ("voice", message.voice),
        ("docs", message.document), ("forward", message.forward_from_chat)
    ]
    if any(k in locks and v for k, v in check): delete = True

    if delete:
        try:
            await message.delete()
            await add_warn(message)
        except: pass

@app.on_message(filters.command("مسح", "") & filters.group)
async def clear_chat(_, message: Message):
    if not await has_permission(message.chat.id, message.from_user.id): return
    num = int(message.command[1]) if len(message.command) > 1 else 100
    await message.delete()
    async for m in app.get_chat_history(message.chat.id, limit=num):
        try: await m.delete()
        except: pass
    t = await message.reply("• تم التنظيف 🧹")
    await asyncio.sleep(2); await t.delete()
