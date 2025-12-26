import asyncio
from pyrogram import filters, enums
from pyrogram.types import Message
from BrandrdXMusic import app
from BrandrdXMusic.misc import SUDO_USERS
from BrandrdXMusic.utils.database import is_group_admin

# --- قاموس الأوامر والأنواع (كلها فعالة ومجربة) ---
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
    "الكل": "all"
}

# تخزين البيانات (يفضل ربطها بـ Mongo لاحقاً لضمان الثبات)
locked_db = {}

# 1. أمر القفل
@app.on_message(filters.command(["قفل", "lock"], "") & filters.group)
async def lock_cmd(client, message: Message):
    chat_id = message.chat.id
    if not await is_group_admin(chat_id, message.from_user.id) and message.from_user.id not in SUDO_USERS:
        return await message.reply_text("<b>⚠️ عذراً، هذا الأمر للمشرفين فقط!</b>")

    if len(message.command) < 2:
        return await message.reply_text("<b>⚠️ يرجى تحديد نوع القفل.\nمثال: `قفل الروابط`</b>")

    target = message.command[1]
    if target not in LOCK_TYPES:
        return await message.reply_text("<b>❌ نوع غير صحيح! استعرض الأنواع عبر: `انواع القفل`</b>")

    if chat_id not in locked_db:
        locked_db[chat_id] = set()

    locked_db[chat_id].add(target)
    await message.reply_text(f"<b>✅ تم قفل {target} بنجاح.</b>")

# 2. أمر الفتح
@app.on_message(filters.command(["فتح", "unlock"], "") & filters.group)
async def unlock_cmd(client, message: Message):
    chat_id = message.chat.id
    if not await is_group_admin(chat_id, message.from_user.id) and message.from_user.id not in SUDO_USERS:
        return await message.reply_text("<b>⚠️ هذا الأمر للمشرفين فقط!</b>")

    if len(message.command) < 2:
        return await message.reply_text("<b>⚠️ حدد النوع لفتحه.\nمثال: `فتح الروابط`</b>")

    target = message.command[1]
    if chat_id in locked_db and target in locked_db[chat_id]:
        locked_db[chat_id].remove(target)
        return await message.reply_text(f"<b>🔓 تم فتح {target} بنجاح.</b>")
    
    await message.reply_text("<b>⚠️ هذا النوع غير مقفل أصلاً.</b>")

# 3. عرض الأقفال النشطة
@app.on_message(filters.command(["الاعدادات", "locks"], "") & filters.group)
async def list_locked(client, message: Message):
    chat_id = message.chat.id
    if chat_id not in locked_db or not locked_db[chat_id]:
        return await message.reply_text("<b>🛡️ المجموعة مفتوحة بالكامل، لا توجد أقفال.</b>")
    
    active = "\n".join([f"• <code>{l}</code>" for l in locked_db[chat_id]])
    await message.reply_text(f"<b>🛡️ الأقفال النشطة حالياً:</b>\n\n{active}")

# 4. محرك الحذف (أهم جزء ليكون البوت فعالاً)
@app.on_message(filters.group & ~filters.me, group=5)
async def watcher(client, message: Message):
    chat_id = message.chat.id
    if chat_id not in locked_db or not locked_db[chat_id]:
        return

    # المشرفين لا يطبق عليهم الحذف
    if message.from_user:
        if await is_group_admin(chat_id, message.from_user.id) or message.from_user.id in SUDO_USERS:
            return

    locks = locked_db[chat_id]
    delete = False

    # فحص المحتوى
    if "الكل" in locks: delete = True
    if "الروابط" in locks and (message.entities or message.caption_entities):
        for e in (message.entities or message.caption_entities or []):
            if e.type in [enums.MessageEntityType.URL, enums.MessageEntityType.TEXT_LINK]: delete = True
    if "المعرفات" in locks and any(e.type == enums.MessageEntityType.MENTION for e in (message.entities or [])): delete = True
    if "التاجات" in locks and any(e.type == enums.MessageEntityType.HASHTAG for e in (message.entities or [])): delete = True
    
    if "الملصقات" in locks and message.sticker: delete = True
    if "الصور" in locks and message.photo: delete = True
    if "الفيديو" in locks and message.video: delete = True
    if "المتحركة" in locks and message.animation: delete = True
    if "الموسيقى" in locks and message.audio: delete = True
    if "البصمات" in locks and message.voice: delete = True
    if "الملفات" in locks and message.document: delete = True
    if "التوجيه" in locks and message.forward_date: delete = True
    if "الموقع" in locks and message.location: delete = True
    if "الاتصال" in locks and message.contact: delete = True

    # التعامل مع البوتات (طرد فوري)
    if "البوتات" in locks and message.new_chat_members:
        for m in message.new_chat_members:
            if m.is_bot:
                try:
                    await message.chat.ban_member(m.id)
                    await message.reply_text(f"<b>🚫 طردت البوت {m.mention} (قفل البوتات مفعل).</b>")
                except: pass
                delete = True

    if delete:
        try:
            await message.delete()
        except Exception:
            pass
