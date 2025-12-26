import asyncio
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from pyrogram import filters
from pyrogram.types import Message

# استدعاء ملفات السورس الأساسية
import config
from config import BANNED_USERS, COMMAND_PREFIXES
from BrandrdXMusic import app
from BrandrdXMusic.utils.database import get_served_chats
from BrandrdXMusic.utils.stream.stream import stream

# 🕌 بيانات الأذان (توقيت القاهرة) - محدثة 2025
AZAN_DATA = {
    "الفجر": {"time": "05:19", "url": "https://youtu.be/4vV5aV6YK14", "video": True, "sticker": "CAACAgQAAyEFAATHCHTJAAIJD2lOq8aLkRR49evBKiITWWhwtgEoAALoGgACp_FYUQuzqVH-JHS5HgQ"},
    "الظهر": {"time": "11:58", "url": "https://youtu.be/21MuvFr7CK8", "video": False, "sticker": "CAACAgQAAyEFAATHCHTJAAIJEWlOrFKzjSDZeWfl6U3F-lrKldRXAAJMGwACMVlYUa15CORC0p0xHgQ"},
    "العصر": {"time": "14:45", "url": "https://youtu.be/bb6cNncMdiM", "video": False, "sticker": "CAACAgQAAyEFAATHCHTJAAIJE2lOrFRQIbcdLfnpdl5PtbdqNyR6AALFGQAC3ZZRUcK5YivXbwUAAR4E"},
    "المغرب": {"time": "16:59", "url": "https://youtu.be/bb6cNncMdiM", "video": False, "sticker": "CAACAgQAAyEFAATHCHTJAAIJFWlOrFT4eOnPJDsSuU6Ya-V0WPQdAALfFwACcIVQUX6NcNNCxvdRHgQ"},
    "العشاء": {"time": "18:22", "url": "https://youtu.be/7xau5N3GYAo", "video": False, "sticker": "CAACAgQAAyEFAATHCHTJAAIJF2lOrFVxhRGefHki3d4s-hLC9cKHAALqHAAC3oZQUWqQdvdwXnGLHgQ"}
}

# ذاكرة الجروبات المفعلة (تُصفر عند ريستارت Fly.io)
active_azan_chats = set()

async def broadcast_azan(prayer_name):
    """دالة إرسال الأذان لكل الجروبات المفعلة"""
    details = AZAN_DATA[prayer_name]
    all_chats = await get_served_chats()
    
    for chat in all_chats:
        # استخراج ID الجروب بدقة
        chat_id = chat["chat_id"] if isinstance(chat, dict) else chat
        
        if chat_id in active_azan_chats:
            try:
                # 1. إرسال الملصق والرسالة التنبيهية
                await app.send_sticker(chat_id, details["sticker"])
                await app.send_message(chat_id, f"<b>🕌 حان الآن وقت أذان {prayer_name} حسب توقيت القاهرة</b>")
                
                # 2. تشغيل البث الصوتي (الترتيب المطابق لسورس بودا)
                # البراميترات: client, user_id, link, chat_id, title, duration, original_chat_id
                await stream(
                    None,              # client
                    app.id,            # user_id
                    details["url"],    # link
                    chat_id,           # chat_id
                    f"أذان {prayer_name}", # title
                    None,              # duration (مهم لضبط الترتيب)
                    chat_id,           # original_chat_id
                    video=details["video"],
                    streamtype="youtube",
                    forceplay=True
                )
                await asyncio.sleep(1) # تأخير بسيط لتجنب الحظر
            except Exception:
                continue

# ضبط المجدول الزمني على توقيت مصر
scheduler = AsyncIOScheduler(timezone="Africa/Cairo")
for prayer, info in AZAN_DATA.items():
    hour, minute = map(int, info["time"].split(":"))
    scheduler.add_job(broadcast_azan, "cron", hour=hour, minute=minute, args=[prayer])

if not scheduler.running:
    scheduler.start()

# --- أوامر التفعيل والتحكم ---

@app.on_message(filters.command(["تفعيل الاذان", "تفعيل الصلاة"], COMMAND_PREFIXES) & filters.group & ~BANNED_USERS)
async def azan_enable(_, message: Message):
    active_azan_chats.add(message.chat.id)
    await message.reply_text(f"<b>✅ تم تفعيل الأذان التلقائي في: {message.chat.title}</b>")

@app.on_message(filters.command(["تعطيل الاذان"], COMMAND_PREFIXES) & filters.group & ~BANNED_USERS)
async def azan_disable(_, message: Message):
    active_azan_chats.discard(message.chat.id)
    await message.reply_text(f"<b>❌ تم تعطيل الأذان التلقائي في: {message.chat.title}</b>")

@app.on_message(filters.command(["تست اذان", "تجربة الاذان"], COMMAND_PREFIXES) & filters.group & ~BANNED_USERS)
async def azan_test(client, message: Message):
    """أمر لتجربة تشغيل الأذان فوراً"""
    details = AZAN_DATA["الفجر"] # نستخدم الفجر كنموذج للتجربة
    
    await message.reply_text("<b>⚙️ جاري محاكاة الأذان وتجربة البث...</b>")
    
    try:
        await message.reply_sticker(details["sticker"])
        
        # استدعاء دالة الـ stream بالترتيب الذي وجدناه في سورس محمد
        await stream(
            client,                                           # client
            message.from_user.id if message.from_user else 0, # user_id
            details["url"],                                   # link
            message.chat.id,                                  # chat_id
            "تجربة الأذان التلقائي",                            # title
            None,                                             # duration
            message.chat.id,                                  # original_chat_id
            video=details["video"],
            streamtype="youtube",
            forceplay=True
        )
    except Exception as e:
        await message.reply_text(f"<b>❌ حدث خطأ أثناء التست:</b>\n<code>{e}</code>")

