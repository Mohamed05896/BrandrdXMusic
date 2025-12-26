import asyncio
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from pyrogram import filters
from pyrogram.types import Message
from motor.motor_asyncio import AsyncIOMotorClient

# استدعاء ملفات السورس
import config
from config import BANNED_USERS, COMMAND_PREFIXES, MONGO_DB_URI
from BrandrdXMusic import app
from BrandrdXMusic.utils.database import get_served_chats
from BrandrdXMusic.utils.stream.stream import stream

# --- إعداد قاعدة البيانات (الحل الدائم) ---
mongodb = AsyncIOMotorClient(MONGO_DB_URI)
azan_db = mongodb.BrandrdX.azan_chats

async def is_azan_on(chat_id: int) -> bool:
    chat = await azan_db.find_one({"chat_id": chat_id})
    return bool(chat)

async def add_azan(chat_id: int):
    await azan_db.update_one({"chat_id": chat_id}, {"$set": {"chat_id": chat_id}}, upsert=True)

async def remove_azan(chat_id: int):
    await azan_db.delete_one({"chat_id": chat_id})

async def get_all_azan_chats():
    chats = []
    async for chat in azan_db.find():
        chats.append(chat["chat_id"])
    return chats

# 🕌 بيانات الأذان
AZAN_DATA = {
    "الفجر": {"time": "05:19", "url": "https://youtu.be/4vV5aV6YK14", "video": True, "sticker": "CAACAgQAAyEFAATHCHTJAAIJD2lOq8aLkRR49evBKiITWWhwtgEoAALoGgACp_FYUQuzqVH-JHS5HgQ"},
    "الظهر": {"time": "11:58", "url": "https://youtu.be/21MuvFr7CK8", "video": False, "sticker": "CAACAgQAAyEFAATHCHTJAAIJEWlOrFKzjSDZeWfl6U3F-lrKldRXAAJMGwACMVlYUa15CORC0p0xHgQ"},
    "العصر": {"time": "14:45", "url": "https://youtu.be/bb6cNncMdiM", "video": False, "sticker": "CAACAgQAAyEFAATHCHTJAAIJE2lOrFRQIbcdLfnpdl5PtbdqNyR6AALFGQAC3ZZRUcK5YivXbwUAAR4E"},
    "المغرب": {"time": "16:59", "url": "https://youtu.be/bb6cNncMdiM", "video": False, "sticker": "CAACAgQAAyEFAATHCHTJAAIJFWlOrFT4eOnPJDsSuU6Ya-V0WPQdAALfFwACcIVQUX6NcNNCxvdRHgQ"},
    "العشاء": {"time": "18:22", "url": "https://youtu.be/7xau5N3GYAo", "video": False, "sticker": "CAACAgQAAyEFAATHCHTJAAIJF2lOrFVxhRGefHki3d4s-hLC9cKHAALqHAAC3oZQUWqQdvdwXnGLHgQ"}
}

async def broadcast_azan(prayer_name):
    details = AZAN_DATA[prayer_name]
    active_chats = await get_all_azan_chats()
    
    for chat_id in active_chats:
        try:
            await app.send_sticker(chat_id, details["sticker"])
            await app.send_message(chat_id, f"<b>🕌 حان الآن وقت أذان {prayer_name} حسب توقيت القاهرة</b>")
            
            await stream(
                None, app.id, details["url"], chat_id, f"أذان {prayer_name}", 
                None, chat_id, video=details["video"], streamtype="youtube", forceplay=True
            )
            await asyncio.sleep(2)
        except:
            continue

# المجدول الزمني
scheduler = AsyncIOScheduler(timezone="Africa/Cairo")
for prayer, info in AZAN_DATA.items():
    h, m = map(int, info["time"].split(":"))
    scheduler.add_job(broadcast_azan, "cron", hour=h, minute=m, args=[prayer])

if not scheduler.running:
    scheduler.start()

# --- أوامر التحكم ---

@app.on_message(filters.command(["تفعيل الاذان", "تفعيل الصلاة"], COMMAND_PREFIXES) & filters.group & ~BANNED_USERS)
async def azan_on_cmd(_, message: Message):
    if await is_azan_on(message.chat.id):
        return await message.reply_text("<b>⚠️ الأذان مفعل بالفعل في هذا الجروب.</b>")
    await add_azan(message.chat.id)
    await message.reply_text(f"<b>✅ تم تفعيل الأذان التلقائي بنجاح.\n\nسيتم البث في مواقيت الصلاة بتوقيت القاهرة.</b>")

@app.on_message(filters.command(["تعطيل الاذان", "ايقاف الاذان"], COMMAND_PREFIXES) & filters.group & ~BANNED_USERS)
async def azan_off_cmd(_, message: Message):
    if not await is_azan_on(message.chat.id):
        return await message.reply_text("<b>⚠️ الأذان غير مفعل هنا.</b>")
    await remove_azan(message.chat.id)
    await message.reply_text("<b>❌ تم تعطيل الأذان التلقائي.</b>")

@app.on_message(filters.command("تست اذان", COMMAND_PREFIXES) & filters.group & ~BANNED_USERS)
async def azan_test(client, message: Message):
    details = AZAN_DATA["الفجر"]
    await message.reply_text("<b>⚙️ جاري التجربة... انتظر دخول المساعد</b>")
    try:
        await stream(
            client, 
            message.from_user.id if message.from_user else 0, 
            details["url"], 
            message.chat.id, 
            "تجربة الأذان", 
            None, 
            message.chat.id, 
            video=details["video"], 
            streamtype="youtube", 
            forceplay=True
        )
    except Exception as e:
        await message.reply_text(f"❌ حدث خطأ: {e}")
