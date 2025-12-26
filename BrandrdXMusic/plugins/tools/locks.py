import asyncio
from pyrogram import filters, enums
from pyrogram.types import Message
from BrandrdXMusic import app
from BrandrdXMusic.misc import SUDOERS 

# مخزن الأقفال والتحذيرات (في الرام)
smart_db = {} 
user_warns = {}

# قائمة كل الأوامر المتاحة في الكود
LOCK_TYPES = {
    "الروابط": "links",
    "المعرفات": "usernames",
    "التاجات": "hashtags",
    "الملصقات": "stickers",
    "الصور": "photos",
    "الفيديو": "videos",
    "البصمات": "voice",
    "الموسيقى": "audio",
    "المتحركة": "gifs",
    "الملفات": "docs",
    "التوجيه": "forward",
    "البوتات": "bots",
    "الموقع": "location",
    "الاتصال": "contact",
    "المجموعة": "full_lock",
    "الشات": "text_lock"
}

# دالة التحقق من رتبة المستخدم (رسمي)
async def is_admin(chat_id, user_id):
    if user_id in SUDOERS: return True
    try:
        member = await app.get_chat_member(chat_id, user_id)
        return member.status in [enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.OWNER]
    except: return False

# --- 1. أوامر القفل ---
@app.on_message(filters.command(["قفل", "lock"], "") & filters.group)
async def lock_cmd(_, message: Message):
    if not await is_admin(message.chat.id, message.from_user.id):
        return
    
    if len(message.command) < 2:
        return await message.reply_text("<b>⚠️ يرجى تحديد نوع القفل.\n• مثال: <code>قفل المجموعة</code> أو <code>قفل الروابط</code></b>")
    
    target = message.command[1]
    if target not in LOCK_TYPES:
        return await message.reply_text("<b>❌ هذا النوع غير موجود. اكتب <code>انواع القفل</code> لرؤية القائمة.</b>")
    
    chat_id = message.chat.id
    if chat_id not in smart_db: smart_db[chat_id] = set()
    
    smart_db[chat_id].add(target)
    await message.reply_text(f"<b>✅ تم قفل {target} بنجاح.</b>")

# --- 2. أوامر الفتح ---
@app.on_message(filters.command(["فتح", "unlock"], "") & filters.group)
async def unlock_cmd(_, message: Message):
    if not await is_admin(message.chat.id, message.from_user.id):
        return
    
    if len(message.command) < 2:
        return await message.reply_text("<b>⚠️ يرجى تحديد النوع لفتحه.\n• مثال: <code>فتح الشات</code></b>")
    
    target = message.command[1]
    chat_id = message.chat.id
    if chat_id in smart_db and target in smart_db[chat_id]:
        smart_db[chat_id].remove(target)
        await message.reply_text(f"<b>🔓 تم فتح {target} بنجاح.</b>")
    else:
        await message.reply_text(f"<b>⚠️ {target} غير مقفل بالفعل.</b>")

# --- 3. محرك الحماية والحذف الذكي ---
@app.on_message(filters.group & ~filters.me, group=1)
async def smart_watcher(client, message: Message):
    chat_id = message.chat.id
    user_id = message.from_user.id if message.from_user else None
    
    if chat_id not in smart_db or not user_id or await is_admin(chat_id, user_id):
        return

    locks = smart_db[chat_id]
    reason = None

    # أولوية القفل الشامل (المجموعة)
    if "المجموعة" in locks:
        reason = "المجموعة مقفولة حالياً 🔒"
    
    # أولوية قفل الشات (النصوص)
    elif "الشات" in locks and message.text:
        reason = "إرسال الرسائل النصية مقفل 📵"

    # الأقفال الفرعية
    else:
        if "الروابط" in locks and (message.entities or message.caption_entities):
            for e in (message.entities or message.caption_entities or []):
                if e.type in [enums.MessageEntityType.URL, enums.MessageEntityType.TEXT_LINK]:
                    reason = "الروابط ممنوعة حالياً 🚫"
        
        if "الملصقات" in locks and message.sticker: reason = "الملصقات مقفولة 🖼️"
        if "الصور" in locks and message.photo: reason = "إرسال الصور ممنوع 📸"
        if "الفيديو" in locks and message.video: reason = "الفيديو مقفول 🎥"
        if "التوجيه" in locks and message.forward_date: reason = "التوجيه غير مسموح 🔄"
        if "البصمات" in locks and message.voice: reason = "البصمات الصوتية مقفولة 🎤"
        if "الموسيقى" in locks and message.audio: reason = "الموسيقى مقفولة 🎵"
        if "المتحركة" in locks and message.animation: reason = "الصور المتحركة مقفولة 👾"
        if "المعطيات" in locks and message.contact: reason = "تبادل جهات الاتصال مقفل 📞"
        if "الموقع" in locks and message.location: reason = "مشاركة الموقع مقفولة 📍"
        if "المعرفات" in locks and any(e.type == enums.MessageEntityType.MENTION for e in (message.entities or [])):
            reason = "المعرفات ممنوعة 📧"

    if reason:
        try:
            await message.delete()
            warn_key = f"{chat_id}:{user_id}"
            if warn_key not in user_warns:
                alert = await message.reply_text(f"<b>⚠️ عذراً {message.from_user.mention}، {reason}</b>")
                user_warns[warn_key] = True
                await asyncio.sleep(4) 
                await alert.delete()
                await asyncio.sleep(6)
                user_warns.pop(warn_key, None)
        except: pass

# --- 4. طرد البوتات التلقائي ---
@app.on_message(filters.group & filters.new_chat_members)
async def auto_bot_kick(client, message: Message):
    chat_id = message.chat.id
    if chat_id in smart_db and "البوتات" in smart_db[chat_id]:
        for member in message.new_chat_members:
            if member.is_bot:
                try:
                    await message.chat.ban_member(member.id)
                    await message.reply_text(f"<b>🚫 تم طرد البوت {member.mention} بنجاح.</b>")
                except: pass

# --- 5. عرض الإعدادات والأنواع ---
@app.on_message(filters.command(["الاعدادات", "locks"], "") & filters.group)
async def list_locks_status(_, message: Message):
    chat_id = message.chat.id
    if chat_id not in smart_db or not smart_db[chat_id]:
        return await message.reply_text("<b>🛡️ لا توجد أقفال نشطة، المجموعة مفتوحة بالكامل.</b>")
    
    active = " ، ".join([f"<code>{l}</code>" for l in smart_db[chat_id]])
    await message.reply_text(f"<b>🛡️ الأقفال النشطة حالياً:\n\n{active}</b>")

@app.on_message(filters.command(["انواع القفل", "locktypes"], ""))
async def lock_types_list(_, message: Message):
    text = "<b>🔒 أنواع الأقفال المتاحة في البوت:</b>\n\n"
    text += "• <code>" + "</code>\n• <code>".join(LOCK_TYPES.keys()) + "</code>\n\n"
    text += "<b>✅ مثال: <code>قفل المجموعة</code></b>"
    await message.reply_text(text)
