import asyncio
import random
import aiohttp
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from pyrogram import filters
from pyrogram.types import Message
from motor.motor_asyncio import AsyncIOMotorClient

import config
from config import BANNED_USERS, COMMAND_PREFIXES, MONGO_DB_URI
from BrandrdXMusic import app
from BrandrdXMusic.utils.stream.stream import stream

# --- [ 1. إعداد قاعدة البيانات ] ---
db_client = AsyncIOMotorClient(MONGO_DB_URI)
azan_collection = db_client.BrandrdX.azan_final_db

OWNER_ID = 8313557781

# --- [ 2. مكتبة الأذكار والأدعية الكاملة ] ---
MORNING_DUAS = [
    "اللهم بك أصبحنا، وبك أمسينا، وبك نحيا، وبك نموت، وإليك النشور. ☀️",
    "أصبحنا وأصبح الملك لله، والحمد لله، لا إله إلا الله وحده لا شريك له. ✨",
    "اللهم إني أسألك خير هذا اليوم، فتحه، ونصره، ونوره، وبركته، وهداه. 🤲",
    "رضيت بالله رباً، وبالإسلام ديناً، وبمحمد صلى الله عليه وسلم نبياً. 🤍",
    "يا حي يا قيوم برحمتك أستغيث، أصلح لي شأني كله ولا تكلني إلى نفسي طرفة عين. 🕊️",
    "اللهم أنت ربي لا إله إلا أنت، خلقتني وأنا عبدك، وأنا على عهدك ووعدك ما استطعت. 🛐",
    "اللهم إني أسألك علماً نافعاً، ورزقاً طيباً، وعملاً متقبلاً. 📖",
    "بسم الله الذي لا يضر مع اسمه شيء في الأرض ولا في السماء وهو السميع العليم. 🛡️",
    "اللهم عافني في بدني، اللهم عافني في سمعي، اللهم عافني في بصري. 🩺",
    "اللهم إني أسألك العفو والعافية في ديني ودنياي وأهلي ومالي. 🍀",
    "أصبحنا على فطرة الإسلام، وعلى كلمة الإخلاص، وعلى دين نبينا محمد. 🌙",
    "اللهم اجعل صباحنا هذا صباحاً مباركاً، تفتح لنا فيه أبواب رحمتك. 🚪",
    "ربي أسألك في هذا الصباح أن تريح قلبي وفكري. 🧘",
    "حسبي الله لا إله إلا هو، عليه توكلت وهو رب العرش العظيم. ⛰️"
]

# --- [ 3. بيانات الوسائط (الروابط والملصقات) ] ---
AZAN_RESOURCES = {
    "Fajr": {"name": "الفجر", "vidid": "r9AWBlpantg", "link": "https://youtu.be/watch?v=r9AWBlpantg", "sticker": "CAACAgQAAyEFAATHCHTJAAIJD2lOq8aLkRR49evBKiITWWhwtgEoAALoGgACp_FYUQuzqVH-JHS5HgQ"},
    "Dhuhr": {"name": "الظهر", "vidid": "21MuvFr7CK8", "link": "https://www.youtube.com/watch?v=21MuvFr7CK8", "sticker": "CAACAgQAAyEFAATHCHTJAAIJEWlOrFKzjSDZeWfl6U3F-lrKldRXAAJMGwACMVlYUa15CORC0p0xHgQ"},
    "Asr": {"name": "العصر", "vidid": "bb6cNncMdiM", "link": "https://www.youtube.com/watch?v=bb6cNncMdiM", "sticker": "CAACAgQAAyEFAATHCHTJAAIJE2lOrFRQIbcdLfnpdl5PtbdqNyR6AALFGQAC3ZZRUcK5YivXbwUAAR4E"},
    "Maghrib": {"name": "المغرب", "vidid": "hKPcNh7WHoM", "link": "https://youtu.be/watch?v=hKPcNh7WHoM", "sticker": "CAACAgQAAyEFAATHCHTJAAIJFWlOrFT4eOnPJDsSuU6Ya-V0WPQdAALfFwACcIVQUX6NcNNCxvdRHgQ"},
    "Isha": {"name": "العشاء", "vidid": "hKPcNh7WHoM", "link": "https://youtu.be/watch?v=hKPcNh7WHoM", "sticker": "CAACAgQAAyEFAATHCHTJAAIJF2lOrFVxhRGefHki3d4s-hLC9cKHAALqHAAC3oZQUWqQdvdwXnGLHgQ"}
}

# --- [ 4. وظائف جلب المواقيت والتشغيل ] ---

async def get_azan_times():
    url = "http://api.aladhan.com/v1/timingsByCity?city=Cairo&country=Egypt&method=5"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    res_json = await response.json()
                    return res_json["data"]["timings"]
    except:
        return None

async def start_azan_stream(chat_id, prayer_key):
    res = AZAN_RESOURCES[prayer_key]
    fake_result = {
        "link": res["link"], 
        "vidid": res["vidid"], 
        "title": f"أذان {res['name']}", 
        "duration_min": "05:00", 
        "thumb": f"https://img.youtube.com/vi/{res['vidid']}/hqdefault.jpg"
    }
    _ = {"queue_4": "<b>🔢 الترتيب: #{}</b>", "stream_1": "<b>🔘 جاري التشغيل...</b>", "play_3": "<b>❌ فشل.</b>"}
    try:
        await app.send_sticker(chat_id, res["sticker"])
        caption = f"<b>حان الآن موعد اذان {res['name']}</b>\n<b>بالتوقيت المحلي لمدينة القاهره 🕌🤍</b>"
        mystic = await app.send_message(chat_id, caption)
        await stream(_, mystic, app.id, fake_result, chat_id, "خدمة الأذان", chat_id, video=False, streamtype="youtube", forceplay=True)
    except:
        pass

async def broadcast_azan(prayer_key):
    async for entry in azan_collection.find({"azan_active": True}):
        c_id = entry.get("chat_id")
        if c_id:
            await start_azan_stream(c_id, prayer_key)
            await asyncio.sleep(3)

async def update_azan_scheduler():
    times = await get_azan_times()
    if not times:
        return
    for job in scheduler.get_jobs():
        if job.id.startswith("azan_"):
            job.remove()
    for key in AZAN_RESOURCES.keys():
        h, m = map(int, times[key].split(":"))
        scheduler.add_job(broadcast_azan, "cron", hour=h, minute=m, args=[key], id=f"azan_{key}")

async def send_morning_dua():
    dua = random.choice(MORNING_DUAS)
    text = f"<b>☀️ دعاء الصباح</b>\n\n{dua}\n\n<b>صباحكم طاعة ورضا ✨</b>"
    async for entry in azan_collection.find({"dua_active": True}):
        try:
            chat_id = entry.get("chat_id")
            if chat_id:
                await app.send_message(chat_id, text)
                await asyncio.sleep(2)
        except:
            continue

# --- [ 5. إعداد المجدول الزمني ] ---
scheduler = AsyncIOScheduler(timezone="Africa/Cairo")
scheduler.add_job(update_azan_scheduler, "cron", hour=0, minute=5)
scheduler.add_job(send_morning_dua, "cron", hour=7, minute=0)

if not scheduler.running:
    scheduler.start()
    asyncio.get_event_loop().create_task(update_azan_scheduler())

# --- [ 6. أوامر التحكم ] ---

@app.on_message(filters.command(["تفعيل الاذان"], COMMAND_PREFIXES) & filters.group & ~BANNED_USERS)
async def azan_on(_, message: Message):
    await azan_collection.update_one({"chat_id": message.chat.id}, {"$set": {"azan_active": True}}, upsert=True)
    await message.reply_text("<b>تم تفعيل الاذان التلقائي 🤍</b>")

@app.on_message(filters.command(["قفل الاذان"], COMMAND_PREFIXES) & filters.group & ~BANNED_USERS)
async def azan_off(_, message: Message):
    await azan_collection.update_one({"chat_id": message.chat.id}, {"$set": {"azan_active": False}}, upsert=True)
    await message.reply_text("<b>❌ تم قفل الأذان التلقائي.</b>")

@app.on_message(filters.command(["تفعيل الدعاء"], COMMAND_PREFIXES) & filters.group & ~BANNED_USERS)
async def dua_on(_, message: Message):
    await azan_collection.update_one({"chat_id": message.chat.id}, {"$set": {"dua_active": True}}, upsert=True)
    await message.reply_text("<b>✅ تم تفعيل أدعية الصباح (7:00 ص).</b>")

@app.on_message(filters.command(["قفل الدعاء"], COMMAND_PREFIXES) & filters.group & ~BANNED_USERS)
async def dua_off(_, message: Message):
    await azan_collection.update_one({"chat_id": message.chat.id}, {"$set": {"dua_active": False}}, upsert=True)
    await message.reply_text("<b>❌ تم قفل أدعية الصباح.</b>")

@app.on_message(filters.command("تست اذان", COMMAND_PREFIXES) & filters.user(OWNER_ID))
async def test_a(_, message: Message):
    await start_azan_stream(message.chat.id, "Fajr")
