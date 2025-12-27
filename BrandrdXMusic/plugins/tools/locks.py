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
warns_db = {}     
max_warns = {}    
last_msg_cache = {} 

LOCK_MAP = {
    "الروابط": "links", "المعرفات": "usernames", "التاك": "hashtags",
    "الشارحه": "slashes", "التثبيت": "pin", "المتحركه": "animations",
    "الشات": "all", "الصور": "photos", "الملصقات": "stickers",
    "الملفات": "docs", "البوتات": "bots", "التكرار": "flood", "الكلايش": "long_msgs",
    "الانلاين": "inline", "الفيديو": "videos", "البصمات": "voice", "السيلفي": "video_notes",
    "الماركدوان": "markdown", "التوجيه": "forward", "الاغاني": "audio",
    "الصوت": "voice", "الجهات": "contacts", "الاشعارات": "service",
    "السب": "porn", "الاباحي": "porn"
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
    c_id, u_id = message.chat.id, message.from_user.id
    limit = max_warns.get(c_id, 3)
    if c_id not in warns_db: warns_db[c_id] = {}
    warns_db[c_id][u_id] = warns_db[c_id].get(u_id, 0) + 1
    current = warns_db[c_id][u_id]
    
    if current >= limit:
        warns_db[c_id][u_id] = 0
        await app.restrict_chat_member(c_id, u_id, ChatPermissions(can_send_messages=False), until_date=datetime.now()+timedelta(hours=24))
        kb = InlineKeyboardMarkup([[InlineKeyboardButton("فـك الـكـتـم", callback_data=f"u_unmute_{u_id}")]])
        await message.reply(f"<b>•الـعـضـو:{message.from_user.mention}\n•وصـل لـحـد الـتـحـذيرات({current}/{limit})\n•تـم كـتـمـه 24 سـاعـة تـلـقـائـيـاً 🤍🥀</b>", reply_markup=kb)
    else:
        await message.reply(f"<b>•تـم حـذف رسـالـتـك لـم_خـالـفـة الـقـوانـيـن\n•تـحـذيـراتـك:({current}/{limit}) 🤍🥀</b>")

# --- [ 3. أوامر الإدارة والتحذيرات ] ---

@app.on_message(filters.command("وضع التحذيرات", "") & filters.group)
async def set_warns_cmd(_, message: Message):
    if not await has_permission(message.chat.id, message.from_user.id): return
    if len(message.command) < 3: return
    try:
        num = int(message.command[2])
        max_warns[message.chat.id] = num
        await message.reply(f"<b>•تـم تـعـيـيـن حـد الـتـحـذيرات لـ:{num}</b>")
    except: pass

@app.on_message(filters.command(["قفل", "فتح"], "") & filters.group)
async def toggle_lock_text(_, message: Message):
    if not await has_permission(message.chat.id, message.from_user.id): return
    if len(message.command) < 2: return
    cmd, target = message.command[0], message.text.split(None, 1)[1]
    
    if target in LOCK_MAP:
        key = LOCK_MAP[target]
        if message.chat.id not in smart_db: smart_db[message.chat.id] = set()
        is_locked = key in smart_db[message.chat.id]
        
        if cmd == "قفل":
            if is_locked:
                return await message.reply("<b>•تـم قـفـل هـذا الأمـر بـالـفـعـل</b>")
            smart_db[message.chat.id].add(key)
        else:
            if not is_locked:
                return await message.reply("<b>•الأمـر هـذا مـفـتـوح بـالـفـعـل</b>")
            smart_db[message.chat.id].discard(key)
        await message.reply_text(f"<b>•تـم {cmd} {target} بـنـجـاح</b>")

@app.on_message(filters.command(["كتم", "ميوت", "شد ميوت"], "") & filters.group)
async def admin_mute_cmds(_, message: Message):
    if not await has_permission(message.chat.id, message.from_user.id): return
    if not message.reply_to_message: return
    u_id = message.reply_to_message.from_user.id
    await app.restrict_chat_member(message.chat.id, u_id, ChatPermissions(can_send_messages=False), until_date=datetime.now()+timedelta(hours=24))
    await message.reply("<b>•تـم كـتـم الـعـضـو 24 سـاعـة</b>")

@app.on_message(filters.command(["فك كتم", "فك ميوت"], "") & filters.group)
async def admin_unmute_cmds(_, message: Message):
    if not await has_permission(message.chat.id, message.from_user.id): return
    if not message.reply_to_message: return
    u_id = message.reply_to_message.from_user.id
    await app.restrict_chat_member(message.chat.id, u_id, ChatPermissions(can_send_messages=True, can_send_media_messages=True))
    await message.reply("<b>•تـم فـك الـكـتـم</b>")

# --- [ 4. لوحة الإعدادات والـ Callback ] ---

def get_kb(chat_id):
    kb, active = [], smart_db.get(chat_id, set())
    unique = list(dict.fromkeys(LOCK_MAP.values()))
    names = {v: k for k, v in LOCK_MAP.items()}
    for i in range(0, len(unique), 2):
        k1 = unique[i]
        n1 = names[k1].replace(" ", "ـ")
        row = [InlineKeyboardButton(f"{n1} ⤶ {'مـقـفـول' if k1 in active else 'مـفـتـوح'}", callback_data=f"trg_{k1}")]
        if i+1 < len(unique):
            k2 = unique[i+1]
            n2 = names[k2].replace(" ", "ـ")
            row.append(InlineKeyboardButton(f"{n2} ⤶ {'مـقـفـول' if k2 in active else 'مـفـتـوح'}", callback_data=f"trg_{k2}"))
        kb.append(row)
    kb.append([InlineKeyboardButton("إغـلاق الـلـوحـة", callback_data="close")])
    return InlineKeyboardMarkup(kb)

@app.on_message(filters.command(["الاعدادات", "locks"], "") & filters.group)
async def settings_cmd(_, message: Message):
    if not await has_permission(message.chat.id, message.from_user.id): return
    await message.reply_text(f"<b>•إعـدادات مـجـمـوعـة:{message.chat.title}</b>", reply_markup=get_kb(message.chat.id))

@app.on_callback_query(filters.regex("^(trg_|u_|close)"))
async def cb_handler(_, cb: CallbackQuery):
    if cb.data == "close": 
        if not await has_permission(cb.message.chat.id, cb.from_user.id): return
        return await cb.message.delete()
    
    if cb.data.startswith("u_unmute_"):
        if not await has_permission(cb.message.chat.id, cb.from_user.id):
            return await cb.answer("هـذا الأمـر لـلـمـشـرفـيـن فـقـط", show_alert=True)
        u_id = int(cb.data.split("_")[2])
        await app.restrict_chat_member(cb.message.chat.id, u_id, ChatPermissions(can_send_messages=True, can_send_media_messages=True))
        await cb.message.edit_text(f"<b>•تـم فـك الـك_تـم عـن الـعـضـو بـواسـطـة {cb.from_user.mention}</b>")
        return await cb.answer("تـم فـك الـكـتـم")

    if not await has_permission(cb.message.chat.id, cb.from_user.id): return
    if cb.data.startswith("trg_"):
        key, c_id = cb.data.replace("trg_", ""), cb.message.chat.id
        if c_id not in smart_db: smart_db[c_id] = set()
        if key in smart_db[c_id]: smart_db[c_id].discard(key)
        else: smart_db[c_id].add(key)
        await cb.message.edit_reply_markup(reply_markup=get_kb(c_id))

# --- [ 5. محرك الحماية والردود التأديبية ] ---

@app.on_message(filters.group & ~filters.me, group=-1)
async def protector_engine(_, message: Message):
    c_id, u_id = message.chat.id, message.from_user.id if message.from_user else None
    if not u_id or await has_permission(c_id, u_id) or (c_id in whitelist and u_id in whitelist[c_id]): return
    locks = smart_db.get(c_id, set())
    if not locks: return
    text = message.text or message.caption or ""

    if "all" in locks:
        try: return await message.delete()
        except: pass

    if "porn" in locks and text:
        clean = re.sub(r"[^\u0621-\u064A\s]", "", text)
        if any(fuzz.ratio(bad, word) > 85 for word in clean.split() for bad in BAD_WORDS):
            await message.delete()
            await message.reply(f"<b>•يـا {message.from_user.mention}، تـذكـر قـول الله تـعـالـي: (مَا يَلْفِظُ مِنْ قَوْلٍ إِلَّا لَدَيْهِ رَقِيبٌ عَتِيدٌ).. وتـذكـر أن هـذه الـحـيـاة فـانـيـة 🤍🥀</b>")
            return await add_warn(message)

    if "porn" in locks and message.photo:
        path = await message.download()
        is_porn = check_porn_api(path)
        if os.path.exists(path): os.remove(path)
        if is_porn:
            await message.delete()
            await message.reply(f"<b>•اتـقِ الله يـا {message.from_user.mention} فـكـل نـظـرة مـحـرمـة هـي سـهـم مـسـمـوم فـي قـلـبـك وتـذكـر ان هـذه الـحـيـاه فـانـيـه 🤍🥀</b>")
            return await add_warn(message)

    check = [
        ("links", message.entities or message.caption_entities),
        ("photos", message.photo), ("videos", message.video),
        ("stickers", message.sticker), ("voice", message.voice)
    ]
    for key, val in check:
        if key in locks and val:
            await message.delete()
            return await add_warn(message)

# --- [ 6. أمر المسح المعدل ] ---

@app.on_message(filters.command("مسح", "") & filters.group)
async def clear_chat_cmd(_, message: Message):
    if not await has_permission(message.chat.id, message.from_user.id): return
    try:
        num = int(message.command[1]) if len(message.command) > 1 else 100
    except: num = 100
    
    await message.delete() # حذف رسالة "مسح"
    
    msg_ids = []
    # جلب الرسائل وحذفها جماعياً للسرعة وحذف رسائل الجميع
    async for m in app.get_chat_history(message.chat.id, limit=num):
        msg_ids.append(m.id)
        if len(msg_ids) == 100:
            await app.delete_messages(message.chat.id, msg_ids)
            msg_ids = []
            
    if msg_ids:
        await app.delete_messages(
