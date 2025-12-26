import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from pyrogram import filters
from pyrogram.types import Message
from motor.motor_asyncio import AsyncIOMotorClient

import config
from config import BANNED_USERS, COMMAND_PREFIXES, MONGO_DB_URI
from BrandrdXMusic import app
from BrandrdXMusic.utils.stream.stream import stream

# --- إعداد قاعدة البيانات ---
db_client = AsyncIOMotorClient(MONGO_DB_URI)
azan_collection = db_client.BrandrdX.azan_final_db

# معرف صاحب البوت للتست
OWNER_ID = 8313557781

# --- مواقيت الأذان (روابط يوتيوب) ---
AZAN_DATA = {
    "الفجر": {"time": "05:19", "vidid": "4vV5aV6YK14", "link": "https://www.youtube.com/watch?v=4vV5aV6YK14", "sticker": "CAACAgQAAyEFAATHCHTJAAIJD2lOq8aLkRR49evBKiITWWhwtgEoAALoGgACp_FYUQuzqVH-JHS5HgQ"},
    "الظهر": {"time": "11:58", "vidid": "21MuvFr7CK8", "link": "https://www.youtube.com/watch?v=21MuvFr7CK8", "sticker": "CAACAgQAAyEFAATHCHTJAAIJEWlOrFKzjSDZeWfl6U3F-lrKldRXAAJMGwACMVlYUa15CORC0p0xHgQ"},
    "العصر": {"time": "14:45", "vidid": "bb6cNncMdiM", "link": "https://www.youtube.com/watch?v=bb6cNncMdiM", "sticker": "CAACAgQAAyEFAATHCHTJAAIJE2lOrFRQIbcdLfnpdl5PtbdqNyR6AALFGQAC3ZZRUcK5YivXbwUAAR4E"},
    "المغرب": {"time": "16:59", "vidid": "bb6cNncMdiM", "link": "https://www.youtube.com/watch?v=bb6cNncMdiM", "sticker": "CAACAgQAAyEFAATHCHTJAAIJFWlOrFT4eOnPJDsSuU6Ya-V0WPQdAALfFwACcIVQUX6NcNNCxvdRHgQ"},
    "العشاء": {"time": "18:22", "vidid": "7xau5N3GYAo", "link": "https://www.youtube.com/watch?v=7xau5N3GYAo", "sticker": "CAACAgQAAyEFAATHCHTJAAIJF2lOrFVxhRGefHki3d4s-hLC9cKHAALqHAAC3oZQUWqQdvdwXnGLHgQ"}
}

async def start_azan_stream(chat_id, prayer_name):
    """تشغيل فيديو الأذان من يوتيوب في المكالمة"""
    data = AZAN_DATA[prayer_name]
    
    # القاموس الذي يطلبه سورس بودا لتشغيل يوتيوب
    fake_result = {
        "link": data["link"],
        "vidid": data["vidid"],
        "title": f"أذان {prayer_name}",
        "duration_min": "05:00",
        "thumb": f"https://img.youtube.com/vi/{data['vidid']}/maxresdefault.jpg" # سحب صورة الفيديو من يوتيوب
    }
    
    _ = {
        "queue_4": "<b>🔢 الترتيب: #{}</b>\n<b>🎵 الاسم: {}</b>\n<b>⏳ الوقت: {}</b>\n<b>👤 بواسطة: {}</b>",
        "stream_1": "<b>🔘 جاري التشغيل...</b>",
        "play_3": "<b>❌ فشل تشغيل فيديو الأذان.</b>"
    }

    try:
        # إرسال الاستيكر
        await app.send_sticker(chat_id, data["sticker"])
        
        # رسالة الموعد
        caption_text = (
            f"<b>حان الآن موعد اذان {prayer_name}</b>\n"
            f"<b>بالتوقيت المحلي لمدينة القاهره 🕌🤍</b>"
        )
        mystic = await app.send_message(chat_id, caption_text)
        
        # استدعاء البث بنمط يوتيوب
        await stream(
            _, 
            mystic, 
            app.id, 
            fake_result, 
            chat_id, 
            "خدمة الأذان", 
            chat_id, 
            video=False, # سيقوم بتشغيل الصوت فقط من فيديو اليوتيوب
            streamtype="youtube", 
            forceplay=True
        )
    except Exception as e:
        print(f"خطأ في أذان {prayer_name}: {e}")

# --- وظيفة الجدولة التلقائية ---
async def broadcast_job(prayer):
    async for entry in azan_collection.find({"active": True}):
        c_id = entry.get("chat_id")
        if c_id:
            await start_azan_stream(c_id, prayer)
            await asyncio.sleep(2)

scheduler = AsyncIOScheduler(timezone="Africa/Cairo")
for p, d in AZAN_DATA.items():
    h, m = map(int, d["time"].split(":"))
    scheduler.add_job(broadcast_job, "cron", hour=h, minute=m, args=[p])

if not scheduler.running:
    scheduler.start()

# --- الأوامر ---

@app.on_message(filters.command(["تفعيل الاذان"], COMMAND_PREFIXES) & filters.group & ~BANNED_USERS)
async def activate_azan(_, message: Message):
    await azan_collection.update_one({"chat_id": message.chat.id}, {"$set": {"active": True}}, upsert=True)
    await message.reply_text("<b>✅ تم تفعيل الأذان التلقائي.</b>")

@app.on_message(filters.command("تست اذان", COMMAND_PREFIXES) & filters.user(OWNER_ID))
async def azan_test(client, message: Message):
    """تست الفجر لصاحب البوت فقط"""
    await message.reply_text("<b>🛠 جاري تجربة تشغيل فيديو أذان الفجر...</b>")
    await start_azan_stream(message.chat.id, "الفجر")
