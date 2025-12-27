import asyncio
from pyrogram import filters, enums
from pyrogram.types import Message, ChatPermissions
from BrandrdXMusic import app
from BrandrdXMusic.misc import SUDOERS 

# --- [ 1. مخازن البيانات الذكية ] ---
smart_db = {} 
user_violations = {} 
warn_limits = {} 
last_msg_cache = {} 

# خريطة الأقفال الشاملة
LOCK_MAP = {
    "الروابط": "links", "الملصقات": "stickers", "الصور": "photos",
    "الفيديو": "videos", "البصمات": "voice", "المتحركة": "gifs",
    "الموسيقى": "audio", "الملفات": "docs", "التوجيه": "forward",
    "المعرفات": "usernames", "التاجات": "hashtags", "البوتات": "bots",
    "الشات": "text", "المجموعة": "all"
}

# دالة فحص الرتبة (تتعرف على المطورين والأدمنية)
async def is_admin(chat_id, user_id):
    if user_id in SUDOERS: return True
    try:
        member = await app.get_chat_member(chat_id, user_id)
        return member.status in [enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.OWNER]
    except: return False

# --- [ 2. أوامر الإدارة والتحكم ] ---

@app.on_message(filters.command(["قفل", "فتح"], "") & filters.group)
async def lock_unlock_handler(_, message: Message):
    if not await is_admin(message.chat.id, message.from_user.id): return
    
    cmd = message.command[0] # قفل أو فتح
    chat_id = message.chat.id
    
    # ميزة القفل الذكي بالرد
    if cmd == "قفل" and message.reply_to_message:
        reply = message.reply_to_message
        target = "الملصقات" if reply.sticker else "الصور" if reply.photo else "الفيديو" if reply.video else "البصمات" if reply.voice else "المتحركة" if reply.animation else None
        if target:
            if chat_id not in smart_db: smart_db[chat_id] = set()
            smart_db[chat_id].add(target)
            return await message.reply_text(f"<b>✅ تم قفل {target} بنجاح.</b>")

    if len(message.command) < 2: return
    target = message.command[1]
    
    if target not in LOCK_MAP:
        return await message.reply_text("<b>⚠️ هذا النوع غير مدعوم، أرسل `انواع القفل` للتأكد.</b>")

    if chat_id not in smart_db: smart_db[chat_id] = set()

    if cmd == "قفل":
        smart_db[chat_id].add(target)
        await message.reply_text(f"<b>✅ تم قفل {target} بنجاح.</b>")
    else:
        if target in smart_db[chat_id]: smart_db[chat_id].remove(target)
        await message.reply_text(f"<b>🔓 تم فتح {target} بنجاح.</b>")

@app.on_message(filters.command(["تعيين التحذيرات", "setwarns"], "") & filters.group)
async def set_limit(_, message: Message):
    if not await is_admin(message.chat.id, message.from_user.id): return
    if len(message.command) < 2: return
    try:
        limit = int(message.command[1])
        warn_limits[message.chat.id] = limit
        await message.reply_text(f"<b>⚙️ تم تعيين الميوت بعد {limit} تحذيرات.</b>")
    except: pass

@app.on_message(filters.command(["تصفير التحذيرات", "unwarn"], "") & filters.group)
async def unwarn_user(_, message: Message):
    if not await is_admin(message.chat.id, message.from_user.id): return
    user_id = message.reply_to_message.from_user.id if message.reply_to_message else None
    if user_id:
        user_violations[f"{message.chat.id}:{user_id}"] = 0
        await message.reply_text("<b>✅ تم تصفير مخالفات العضو بنجاح.</b>")

# --- [ 3. لوحة الإعدادات الشاملة ] ---

@app.on_message(filters.command(["الاعدادات", "locks"], "") & filters.group)
async def settings_manager(_, message: Message):
    if not await is_admin(message.chat.id, message.from_user.id): return
    chat_id = message.chat.id
    active_locks = smart_db.get(chat_id, set())
    limit = warn_limits.get(chat_id, 3)
    
    text = f"<b>🛠️ إعدادات الحماية لـ {message.chat.title}</b>\n"
    text += f"<b>⚠️ الميوت بعد:</b> <code>{limit}</code> تحذيرات\n"
    text += "──────────────────\n"
    for name in LOCK_MAP.keys():
        status = "❌ مقفول" if name in active_locks else "✅ مفتوح"
        text += f"• {name} ⤶ {status}\n"
    text += "──────────────────\n"
    text += "<b>💡 للتحكم استخدم:</b>\n<code>قفل + النوع</code> | <code>فتح + النوع</code>"
    await message.reply_text(text)

# --- [ 4. محرك المسح (Cleaning) ] ---

@app.on_message(filters.command(["مسح", "مسح الشات"], "") & filters.group)
async def clear_chat_cmd(_, message: Message):
    if not await is_admin(message.chat.id, message.from_user.id): return
    num = 100
    if len(message.command) > 1:
        try: num = int(message.command[1])
        except: num = 100
    await message.delete()
    async for msg in app.get_chat_history(message.chat.id, limit=num):
        try: await msg.delete()
        except: pass
    temp = await message.reply_text(f"<b>🧹 تم مسح {num} رسالة من الشات.</b>")
    await asyncio.sleep(4)
    await temp.delete()

# --- [ 5. محرك الحماية الفوري (الأولوية القصوى) ] ---

@app.on_message(filters.group & ~filters.me, group=-1)
async def protector_engine(client, message: Message):
    chat_id = message.chat.id
    user_id = message.from_user.id if message.from_user else None
    if not user_id or await is_admin(chat_id, user_id): return
    if chat_id not in smart_db: return

    locks = smart_db[chat_id]
    v_type = None

    # كشف التكرار (Anti-Spam)
    if message.text:
        last_msg = last_msg_cache.get(f"{chat_id}:{user_id}")
        if last_msg == message.text: v_type = "تكرار الكلام"
        last_msg_cache[f"{chat_id}:{user_id}"] = message.text

    # فحص الأقفال (الصور، الروابط، الملصقات...)
    if not v_type:
        if "المجموعة" in locks: v_type = "المجموعة مقفولة"
        elif "الشات" in locks and message.text: v_type = "الشات"
        elif "الصور" in locks and message.photo: v_type = "الصور"
        elif "الملصقات" in locks and message.sticker: v_type = "الملصقات"
        elif "الروابط" in locks and (message.entities or message.caption_entities):
            for e in (message.entities or message.caption_entities or []):
                if e.type in [enums.MessageEntityType.URL, enums.MessageEntityType.TEXT_LINK]:
                    v_type = "الروابط"
                    break
        elif "الفيديو" in locks and message.video: v_type = "الفيديو"
        elif "البصمات" in locks and message.voice: v_type = "البصمات"
        elif "المتحركة" in locks and message.animation: v_type = "المتحركة"

    if v_type:
        try:
            await message.delete() # الحذف الإجباري الفوري
            v_key = f"{chat_id}:{user_id}"
            limit = warn_limits.get(chat_id, 3)
            count = user_violations.get(v_key, 0) + 1
            user_violations[v_key] = count

            if count >= limit:
                await app.restrict_chat_member(chat_id, user_id, ChatPermissions(can_send_messages=False))
                user_violations[v_key] = 0
                await message.reply_text(f"<b>تم التقييد بسبب مخالفة قوانين الشات 🧚🤍</b>\n<b>👤 العضو:</b> {message.from_user.mention}")
            else:
                alert = await message.reply_text(f"<b>عذراً {message.from_user.mention}، {v_type} مقفول ✨\nتحذير رقم ({count}/{limit})</b>")
                await asyncio.sleep(4)
                await alert.delete()
        except: pass

# --- [ 6. منع دخول البوتات ] ---

@app.on_message(filters.group & filters.new_chat_members)
async def anti_bot_kick(client, message: Message):
    if message.chat.id in smart_db and "البوتات" in smart_db[message.chat.id]:
        for member in message.new_chat_members:
            if member.is_bot:
                try: await message.chat.ban_member(member.id)
                except: pass
