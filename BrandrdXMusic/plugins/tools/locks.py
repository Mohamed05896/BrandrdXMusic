import asyncio
import re
import os
import requests
from pyrogram import filters, enums
from pyrogram.types import Message, ChatPermissions
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

# قائمة الكلمات المحظورة (الرد المزخرف)
PORN_ROOTS = r"(سكس|نيك|شرموط|منيوك|كسم|زب|فحل|بورن|متناق|تعال مص|مـص|كس|هنيك|مصم|طيز|كسختك|قحبه|شرموطه|عير|منيوكه|نيج)"

# --- [ 2. دوال الـتـحـقـق والـحـمـاية ] ---

def check_nudity(image_path):
    """فحص الصور الإباحية عبر Sightengine"""
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
    """فحص رتبة المشرف"""
    if user_id in SUDOERS: return True
    try:
        member = await app.get_chat_member(chat_id, user_id)
        return member.status in [enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.OWNER]
    except: return False

async def has_permission(chat_id, user_id):
    """فحص الحصانة (أدمن أو سماح)"""
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
        await message.reply_text(f"<b>⚙️ تم تعيين حد التحذيرات بـ: {num} 🤍</b>")
    except: pass

@app.on_message(filters.command(["سماح"], "") & filters.group)
async def allow_user_handler(_, message: Message):
    if not await is_admin(message.chat.id, message.from_user.id): return
    user_id, mention = None, None
    if message.reply_to_message:
        user_id, mention = message.reply_to_message.from_user.id, message.reply_to_message.from_user.mention
    elif len(message.command) > 1:
        try:
            u = await app.get_users(message.command[1])
            user_id, mention = u.id, u.mention
        except: return await message.reply_text("<b>⚠️ العضو غير موجود</b>")
    if user_id:
        if message.chat.id not in whitelist: whitelist[message.chat.id] = set()
        whitelist[message.chat.id].add(user_id)
        await message.reply_text(f"<b>✅ تم إعطاء سماح لـ: {mention} 🧚🤍</b>")

@app.on_message(filters.command(["شد سماح"], "") & filters.group)
async def revoke_allow_handler(_, message: Message):
    if not await is_admin(message.chat.id, message.from_user.id): return
    u_id = message.reply_to_message.from_user.id if message.reply_to_message else None
    if u_id and message.chat.id in whitelist:
        whitelist[message.chat.id].discard(u_id)
        await message.reply_text(f"<b>❌ تم شد السماح من العضو 🤍</b>")

@app.on_message(filters.command(["ميوت", "كتم"], "") & filters.group)
async def mute_user_handler(_, message: Message):
    if not await is_admin(message.chat.id, message.from_user.id): return
    u_id = message.reply_to_message.from_user.id if message.reply_to_message else None
    if u_id and not await is_admin(message.chat.id, u_id):
        await app.restrict_chat_member(message.chat.id, u_id, ChatPermissions(can_send_messages=False))
        await message.reply_text(f"<b>🔇 تم كتم العضو بنجاح 🧚🤍</b>")

@app.on_message(filters.command(["شد ميوت", "فك ميوت", "شد كتم"], "") & filters.group)
async def unmute_user_handler(_, message: Message):
    if not await is_admin(message.chat.id, message.from_user.id): return
    u_id = message.reply_to_message.from_user.id if message.reply_to_message else None
    if u_id:
        await app.restrict_chat_member(message.chat.id, u_id, ChatPermissions(can_send_messages=True, can_send_media_messages=True, can_send_other_messages=True, can_add_web_page_previews=True))
        await message.reply_text(f"<b>🔊 تم فك الكتم (شد الميوت) 🤍</b>")

# --- [ 4. أوامـر الـقـفـل والـفـتـح والـمـسـح ] ---

@app.on_message(filters.command(["قفل", "فتح"], "") & filters.group)
async def lock_unlock_handler(_, message: Message):
    if not await is_admin(message.chat.id, message.from_user.id): return
    cmd, c_id = message.command[0], message.chat.id
    target = message.text.split(None, 1)[1] if len(message.command) > 1 else None
    
    if cmd == "قفل" and message.reply_to_message and not target:
        r = message.reply_to_message
        target = "الملصقات" if r.sticker else "الصور" if r.photo else "الفيديو" if r.video else "البصمات" if r.voice else "المتحركه" if r.animation else None

    if not target: return
    if c_id not in smart_db: smart_db[c_id] = set()

    if target == "الكل":
        if cmd == "قفل": smart_db[c_id].update(LOCK_MAP.values())
        else: smart_db[c_id].clear()
        return await message.reply_text(f"<b>🛡️ تم {cmd} الكل بنجاح 🧚🤍</b>")

    if target in LOCK_MAP:
        key = LOCK_MAP[target]
        if cmd == "قفل": smart_db[c_id].add(key)
        else: smart_db[c_id].discard(key)
        await message.reply_text(f"<b>✅ تم {cmd} {target} بنجاح 🧚🤍</b>")

@app.on_message(filters.command(["الاعدادات", "locks"], "") & filters.group)
async def settings_manager(_, message: Message):
    if not await is_admin(message.chat.id, message.from_user.id): return
    active, limit = smart_db.get(message.chat.id, set()), warn_limits.get(message.chat.id, 3)
    text = f"<b>🛠️ إعدادات المجموعة: {message.chat.title}</b>\n<b>⚠️ التحذيرات: {limit}</b>\n"
    text += "──────────────────\n"
    for name, key in list(LOCK_MAP.items())[:20]: # عرض عينة
        text += f"• {name} ⤶ {'❌' if key in active else '✅'}\n"
    await message.reply_text(text)

@app.on_message(filters.command(["مسح", "مسح الشات"], "") & filters.group)
async def clear_chat_cmd(_, message: Message):
    if not await is_admin(message.chat.id, message.from_user.id): return
    num = int(message.command[1]) if len(message.command) > 1 and message.command[1].isdigit() else 100
    await message.delete()
    async for msg in app.get_chat_history(message.chat.id, limit=num):
        try: await msg.delete()
        except: pass
    t = await message.reply_text(f"<b>🧹 تم مسح {num} رسالة 🧚🤍</b>")
    await asyncio.sleep(2); await t.delete()

# --- [ 5. الـمـحـرك الـحـديـدي والـرد الـمـزخـرف ] ---

@app.on_message(filters.group & ~filters.me, group=-1)
async def protector_engine(client, message: Message):
    c_id, u_id = message.chat.id, message.from_user.id if message.from_user else None
    if not u_id or await has_permission(c_id, u_id): return
    locks = smart_db.get(c_id, set())
    if not locks: return

    v_type, is_porn_text = None, False

    # فحص القفل الشامل (صامت)
    if "all" in locks: return await message.delete()
    if "text" in locks and message.text: return await message.delete()

    # فحص الإباحية والسب (الرد المزخرف)
    if "porn" in locks:
        if message.text and re.search(PORN_ROOTS, message.text, re.IGNORECASE):
            await message.delete()
            return await message.reply_text("<b>اقـفـل بـوقـك يـا حـمـار 🧚🤍</b>")
        if message.photo:
            path = await message.download()
            if check_nudity(path): 
                os.remove(path); await message.delete()
                return await message.reply_text(f"<b>عذراً {message.from_user.mention}، الصور الإباحية ممنوعة ❌</b>")
            os.remove(path)

    # فحص تفصيلي لكل حالة
    if "links" in locks and (message.entities or message.caption_entities):
        for e in (message.entities or message.caption_entities or []):
            if e.type in [enums.MessageEntityType.URL, enums.MessageEntityType.TEXT_LINK]: v_type = "الروابط"
    
    if not v_type:
        if "photos" in locks and message.photo: v_type = "الصور"
        elif "stickers" in locks and message.sticker: v_type = "الملصقات"
        elif "videos" in locks and message.video: v_type = "الفيديو"
        elif "voice" in locks and message.voice: v_type = "البصمات"
        elif "forward" in locks and message.forward_date: v_type = "التوجيه"
        elif "usernames" in locks and "@" in (message.text or message.caption or ""): v_type = "المعرفات"
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
                await message.reply_text(f"<b>🔇 تم تقييدك (ميوت) بسبب التكرار 🧚🤍\n👤: {message.from_user.mention}</b>")
            else:
                a = await message.reply_text(f"<b>عذراً {message.from_user.mention}، {v_type} مقفول 🧚🤍 ({user_violations[v_key]}/{limit})</b>")
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
