import asyncio
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from pyrogram import filters
from pyrogram.types import Message

# استدعاء الملفات المطلوبة من السورس
try:
    import config
    from config import BANNED_USERS, COMMAND_PREFIXES
    from BrandrdXMusic import app
    from BrandrdXMusic.utils.database import get_served_chats
    from BrandrdXMusic.utils.stream.stream import stream
except ImportError:
    pass

# 🕌 بيانات الأذان (توقيت القاهرة)
AZAN_DATA = {
    "الفجر": {
        "time": "05:19",
        "url": "https://youtu.be/4vV5aV6YK14",
        "video": True,
        "sticker": "CAACAgQAAyEFAATHCHTJAAIJD2lOq8aLkRR49evBKiITWWhwtgEoAALoGgACp_FYUQuzqVH-JHS5HgQ"
    },
    "الظهر": {
        "time": "11:58",
        "url": "https://youtu.be/21MuvFr7CK8",
        "video": False,
        "sticker": "CAACAgQAAyEFAATHCHTJAAIJEWlOrFKzjSDZeWfl6U3F-lrKldRXAAJMGwACMVlYUa15CORC0p0xHgQ"
    },
    "العصر": {
        "time": "14:45",
        "url": "https://youtu.be/bb6cNncMdiM",
        "video": False,
        "sticker": "CAACAgQAAyEFAATHCHTJAAIJE2lOrFRQIbcdLfnpdl5PtbdqNyR6AALFGQAC3ZZRUcK5YivXbwUAAR4E"
    },
    "المغرب": {
        "time": "16:59",
        "url": "https://youtu.be/bb6cNncMdiM",
        "video": False,
        "sticker": "CAACAgQAAyEFAATHCHTJAAIJFWlOrFT4eOnPJDsSuU6Ya-V0WPQdAALfFwACcIVQUX6NcNNCxvdRHgQ"
    },
    "العشاء": {
        "time": "18:22",
        "url": "https://youtu.be/7xau5N3GYAo",
        "video": False,
        "sticker": "CAACAgQAAyEFAATHCHTJAAIJF2lOrFVxhRGefHki3d4s-hLC9cKHAALqHAAC3oZQUWqQdvdwXnGLHgQ"
    }
}

active_azan_chats = set()

async def broadcast_azan(prayer_name):
    details = AZAN_DATA[prayer_name]
    served_chats = await get_served_chats()
    
    for chat in served_chats:
        # تصحيح الخطأ: التأكد من نوع البيانات المستلمة من الداتابيز
        if isinstance(chat, dict):
            chat_id = chat.get("chat_id")
        else:
            chat_id = chat # إذا كان رقم آيدي مباشر
            
        if chat_id and chat_id in active_azan_chats:
            try:
                await app.send_sticker(chat_id, details["sticker"])
                await app.send_message(
                    chat_id, 
                    f"<b>🕌 حان الآن وقت أذان {prayer_name} حسب توقيت القاهرة</b>"
                )
                await stream(
                    None, None, app.id, details["url"], chat_id, "نظام الأذان", chat_id,
                    video=details["video"],
                    streamtype="youtube",
                    forceplay=True
                )
            except Exception:
                continue

scheduler = AsyncIOScheduler(timezone="Africa/Cairo")
for prayer, info in AZAN_DATA.items():
    hour, minute = map(int, info["time"].split(":"))
    scheduler.add_job(broadcast_azan, "cron", hour=hour, minute=minute, args=[prayer])

if not scheduler.running:
    scheduler.start()

# --- أوامر التحكم ---

@app.on_message(filters.command(["تفعيل الاذان", "تفعيل بث الصلاة"], COMMAND_PREFIXES) & filters.group & ~BANNED_USERS)
async def azan_enable_cmd(_, message: Message):
    active_azan_chats.add(message.chat.id)
    await message.reply_text("<b>✅ تم تفعيل نظام بث الأذان التلقائي بنجاح.</b>")

@app.on_message(filters.command(["تعطيل الاذان", "إيقاف بث الصلاة"], COMMAND_PREFIXES) & filters.group & ~BANNED_USERS)
async def azan_disable_cmd(_, message: Message):
    if message.chat.id in active_azan_chats:
        active_azan_chats.remove(message.chat.id)
    await message.reply_text("<b>❌ تم إيقاف نظام بث الأذان.</b>")

@app.on_message(filters.command(["تست صلاة"], COMMAND_PREFIXES) & filters.group & ~BANNED_USERS)
async def azan_test_cmd(_, message: Message):
    prayer = "الفجر"
    details = AZAN_DATA[prayer]
    await message.reply_sticker(details["sticker"])
    await message.reply_text(f"<b>⚙️ تجربة نظام الأذان (صلاة {prayer})</b>")
    try:
        # تصحيح البراميتر الأول في دالة stream ليتوافق مع السورس
        await stream(
            _, message, None, details["url"], message.chat.id, "تجربة الأذان", message.chat.id,
            video=details["video"],
            streamtype="youtube",
            forceplay=True
        )
    except Exception as e:
        await message.reply_text(f"❌ حدث خطأ أثناء البث: {e}")
