import asyncio
from pyrogram import filters, enums
from pyrogram.types import Message, ChatPermissions
from BrandrdXMusic import app
from BrandrdXMusic.misc import SUDOERS 

# --- مخازن البيانات المؤقتة ( InMemory ) ---
smart_db = {} 
user_violations = {} 
warn_limits = {} 
last_msg_cache = {} 

# قائمة الأقفال المدعومة بالكامل
LOCK_TYPES = {
    "الروابط": "links", "المعرفات": "usernames", "التاجات": "hashtags",
    "الملصقات": "stickers", "الصور": "photos", "الفيديو": "videos",
    "البصمات": "voice", "الموسيقى": "audio", "المتحركة": "gifs",
    "الملفات": "docs", "التوجيه": "forward", "البوتات": "bots", 
    "الموقع": "location", "الاتصال": "contact",
    "المجموعة": "full_lock", "الشات": "text_lock"
}

# دالة التحقق من رتبة المشرف
async def is_admin(chat_id, user_id):
    if user_id in SUDOERS: return True
    try:
        member = await app.get_chat_member(chat_id, user_id)
        return member.status in [enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.OWNER]
    except: return False

# --- 1. أوامر المسح والتحكم بالشات ---

@app.on_message(filters.command(["مسح", "مسح الشات"], "") & filters.group)
async def clear_chat_cmd(_, message: Message):
    if not await is_admin(message.chat.id, message.from_user.id): return
    num = 100
    if len(message.command) > 1:
        try: num = int(message.command[1])
        except: num = 100
    await message.delete()
    messages = []
    async for msg in app.get_chat_history(message.chat.id, limit=num):
        messages.append(msg.id)
        if len(messages) >= 100: 
            await app.delete_messages(message.chat.id, messages)
            messages = []
    if messages:
        await app.delete_messages(message.chat.id, messages)
    temp = await message.reply_text(f"<b>🧹 تم مسح {num} رسالة من الشات.</b>")
    await asyncio.sleep(4)
    await temp.delete()

# --- 2. أوامر الأقفال والفتح والتحذيرات ---

@app.on_message(filters.command(["قفل", "lock"], "") & filters.group)
async def lock_cmd(_, message: Message):
    if not await is_admin(message.chat.id, message.from_user.id): return
    # ميزة القفل بالرد
    if message.reply_to_message:
        reply = message.reply_to_message
        target = "الملصقات" if reply.sticker else "الصور" if reply.photo else "الفيديو" if reply.video else "البصمات" if reply.voice else None
        if target:
            if message.chat.id not in smart_db: smart_db[message.chat.id] = set()
            smart_db[message.chat.id].add(target)
            return await message.reply_text(f"<b>✅ تم قفل {target} بالرد.</b>")
    
    if len(message.command) < 2: return
    target = message.command[1]
    if target not in LOCK_TYPES: return
    if message.chat.id not in smart_db: smart_db[message.chat.id] = set()
    smart_db[message.chat.id].add(target)
    await message.reply_text(f"<b>✅ تم قفل {target} بنجاح.</b>")

@app.on_message(filters.command(["فتح", "unlock"], "") & filters.group)
async def unlock_cmd(_, message: Message):
    if not await is_admin(message.chat.id, message.from_user.id): return
    target = message.command[1] if len(message.command) > 1 else None
    if target in smart_db.get(message.chat.id, set()):
        smart_db[message.chat.id].remove(target)
        await message.reply_text(f"<b>🔓 تم فتح {target}.</b>")

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

# --- 3. محرك المراقبة الذكي ( الأقفال + منع التكرار ) ---

@app.on_message(filters.group & ~filters.me, group=1)
async def security_watcher(client, message: Message):
    chat_id = message.chat.id
    user_id = message.from_user.id if message.from_user else None
    if not user_id or await is_admin(chat_id, user_id): return

    locks = smart_db.get(chat_id, set())
    v_type = None

    # كشف التكرار (Anti-Spam)
    if message.text:
        last_msg = last_msg_cache.get(f"{chat_id}:{user_id}")
        if last_msg == message.text: v_type = "تكرار الكلام"
        last_msg_cache[f"{chat_id}:{user_id}"] = message.text

    # كشف الأقفال بالتفصيل
    if not v_type:
        if "المجموعة" in locks: v_type = "المجموعة مقفولة"
        elif "الشات" in locks and message.text: v_type = "الشات مقفول"
        elif "الروابط" in locks and (message.entities or message.caption_entities): v_type = "الروابط"
        elif "الملصقات" in locks and message.sticker: v_type = "الملصقات"
        elif "الصور" in locks and message.photo: v_type = "الصور"
        elif "الفيديو" in locks and message.video: v_type = "الفيديو"
        elif "البصمات" in locks and message.voice: v_type = "البصمات"
        elif "المتحركة" in locks and message.animation: v_type = "المتحركة"
        elif "الموسيقى" in locks and message.audio: v_type = "الموسيقى"
        elif "التوجيه" in locks and message.forward_date: v_type = "التوجيه"
        elif "المعرفات" in locks and any(e.type == enums.MessageEntityType.MENTION for e in (message.entities or [])): v_type = "المعرفات"

    if v_type:
        try:
            await message.delete() 
            v_key = f"{chat_id}:{user_id}"
            limit = warn_limits.get(chat_id, 3)
            count = user_violations.get(v_key, 0) + 1
            user_violations[v_key] = count

            if count >= limit:
                # الرد عند التقييد النهائي
                await app.restrict_chat_member(chat_id, user_id, ChatPermissions(can_send_messages=False))
                user_violations[v_key] = 0
                await message.reply_text(f"<b>تم التقييد بسبب مخالفة قوانين الشات 🧚🤍</b>\n\n<b>👤 العضو:</b> {message.from_user.mention}")
            else:
                # الرد التنبيهي الحنين
                alert = await message.reply_text(
                    f"<b>عذراً {message.from_user.mention}، {v_type} مقفول ✨\n"
                    f"تحذير رقم ({count}/{limit})</b>"
                )
                await asyncio.sleep(4)
                await alert.delete()
        except: pass

# --- 4. طرد البوتات المضافة ---
@app.on_message(filters.group & filters.new_chat_members)
async def auto_bot_kick(client, message: Message):
    if message.chat.id in smart_db and "البوتات" in smart_db[message.chat.id]:
        for member in message.new_chat_members:
            if member.is_bot:
                try: await message.chat.ban_member(member.id)
                except: pass

# --- 5. عرض الإعدادات والأنواع ---
@app.on_message(filters.command(["الاعدادات", "locks"], "") & filters.group)
async def list_locks_status(_, message: Message):
    if not await is_admin(message.chat.id, message.from_user.id): return
    active = " ، ".join([f"<code>{l}</code>" for l in smart_db.get(message.chat.id, [])]) or "لا يوجد"
    limit = warn_limits.get(message.chat.id, 3)
    await message.reply_text(f"<b>🛡️ الأقفال النشطة: {active}\n⚠️ الميوت بعد: {limit} تحذيرات.</b>")

@app.on_message(filters.command(["انواع القفل"], ""))
async def lock_types_list(_, message: Message):
    text = "<b>🔒 أنواع الأقفال المتاحة:</b>\n\n"
    text += "• <code>" + "</code>\n• <code>".join(LOCK_TYPES.keys()) + "</code>\n\n"
    text += "<b>✅ مثال: <code>قفل الشات</code></b>"
    await message.reply_text(text)
