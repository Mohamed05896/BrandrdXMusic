import asyncio
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from pyrogram import filters
from pyrogram.types import Message

# استدعاء ملفات السورس الأساسية من مستودعك
import config
from config import BANNED_USERS, COMMAND_PREFIXES
from BrandrdXMusic import app
from BrandrdXMusic.utils.database import get_served_chats
from BrandrdXMusic.utils.stream.stream import stream

# 🕌 بيانات الأذان (توقيت القاهرة)
AZAN_DATA = {
    "الفجر": {"time": "05:19", "url": "https://youtu.be/4vV5aV6YK14", "video": True, "sticker": "CAACAgQAAyEFAATHCHTJAAIJD2lOq8aLkRR49evBKiITWWhwtgEoAALoGgACp_FYUQuzqVH-JHS5HgQ"},
    "الظهر": {"time": "11:58", "url": "https://youtu.be/21MuvFr7CK8", "video": False, "sticker": "CAACAgQAAyEFAATHCHTJAAIJEWlOrFKzjSDZeWfl6U3F-lrKldRXAAJMGwACMVlYUa15CORC0p0xHgQ"},
    "العصر": {"time": "14:45", "url": "https://youtu.be/bb6cNncMdiM", "video": False, "sticker": "CAACAgQAAyEFAATHCHTJAAIJE2lOrFRQIbcdLfnpdl5PtbdqNyR6AALFGQAC3ZZRUcK5YivXbwUAAR4E"},
    "المغرب": {"time": "16:59", "url": "https://youtu.be/bb6cNncMdiM", "video": False, "sticker": "CAACAgQAAyEFAATHCHTJAAIJFWlOrFT4eOnPJDsSuU6Ya-V0WPQdAALfFwACcIVQUX6NcNNCxvdRHgQ"},
    "العشاء": {"time": "18:22", "url": "https://youtu.be/7xau5N3GYAo", "video": False, "sticker": "CAACAgQAAyEFAATHCHTJAAIJF2lOrFVxhRGefHki3d4s-hLC9cKHAALqHAAC3oZQUWqQdvdwXnGLHgQ"}
}

# ذاكرة تخزين الجروبات المفعلة
active_azan_chats = set()

async def broadcast_azan(prayer_name):
    """دالة البث التلقائي"""
    details = AZAN_DATA[prayer_name]
    all_chats = await get_served_chats()
    
    for chat in all_chats:
        # فحص إذا كان chat عبارة عن قاموس أو رقم آيدي مباشرة
        chat_id = chat["chat_id"] if isinstance(chat, dict) else chat
        
        if chat_id in active_azan_chats:
            try:
                await app.send_sticker(chat_id, details["sticker"])
                await app.send_message(chat_id, f"<b>🕌 حان الآن وقت أذان {prayer_name} حسب توقيت القاهرة</b>")
                
                # ترتيب البراميترات حسب سورس BrandrdXMusic
                await stream(
                    _ , # الـ client (سيتم استخدامه تلقائياً)
                    app.id, # mystic / user_id
                    details["url"], 
                    chat_id, 
                    f"أذان {prayer_name}", 
                    chat_id,
                    video=details["video"],
                    streamtype="youtube",
                    forceplay=True
                )
            except Exception as e:
                print(f"Error in Azan broadcast for {chat_id}: {e}")

# ضبط المجدول
scheduler = AsyncIOScheduler(timezone="Africa/Cairo")
for prayer, info in AZAN_DATA.items():
    h, m = map(int, info["time"].split(":"))
    scheduler.add_job(broadcast_azan, "cron", hour=h, minute=m, args=[prayer])

if not scheduler.running:
    scheduler.start()

# --- أوامر التحكم ---

@app.on_message(filters.command(["تفعيل الاذان", "تفعيل بث الصلاة"], COMMAND_PREFIXES) & filters.group & ~BANNED_USERS)
async def azan_on(_, message: Message):
    active_azan_chats.add(message.chat.id)
    await message.reply_text("<b>✅ تم تفعيل نظام الأذان التلقائي في هذا الجروب.</b>")

@app.on_message(filters.command(["تعطيل الاذان", "إيقاف بث الصلاة"], COMMAND_PREFIXES) & filters.group & ~BANNED_USERS)
async def azan_off(_, message: Message):
    active_azan_chats.discard(message.chat.id)
    await message.reply_text("<b>❌ تم إيقاف نظام الأذان في هذا الجروب.</b>")

@app.on_message(filters.command("تست اذان", COMMAND_PREFIXES) & filters.group & ~BANNED_USERS)
async def azan_test(client, message: Message):
    details = AZAN_DATA["الفجر"]
    await message.reply_sticker(details["sticker"])
    await message.reply_text("<b>⚙️ جاري تجربة بث الأذان... انتظر دخول المساعد</b>")
    
    try:
        # التعديل البرمجي ليتناسب مع ملف stream.py في سورسك
        await stream(
            client,
            message.from_user.id if message.from_user else 0,
            details["url"],
            message.chat.id,
            "تجربة الأذان",
            message.chat.id,
            video=details["video"],
            streamtype="youtube",
            forceplay=True
        )
    except Exception as e:
        await message.reply_text(f"❌ خطأ: {e}")
