import asyncio
import random
import aiohttp
import re
import logging
import os
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from pyrogram import filters, enums
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from motor.motor_asyncio import AsyncIOMotorClient

import config
from config import BANNED_USERS, COMMAND_PREFIXES, MONGO_DB_URI
from BrandrdXMusic import app
from BrandrdXMusic.utils.stream.stream import stream

# ==========================================
# [ 1. إعدادات النظام وقاعدة البيانات ]
# ==========================================

logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger("AzanSystem")

db_client = AsyncIOMotorClient(MONGO_DB_URI)
# قاعدة بيانات الإعدادات (تفعيل/تعطيل)
azan_collection = db_client.BrandrdX.azan_advanced_db 
# قاعدة بيانات الموارد (الروابط والاستيكرات)
resources_collection = db_client.BrandrdX.azan_resources_db

# كاش محلي لتسريع الأداء
settings_cache = {}
# حالة الأدمن (لانتظار الرد عند التغيير)
admin_state = {}

# سحب ايدي المطور من متغيرات البيئة
try:
    OWNER_ID = int(os.getenv("OWNER_ID"))
except:
    print("⚠️ تنبيه: لم يتم العثور على OWNER_ID في المتغيرات، يرجى إضافته.")
    OWNER_ID = 0 

# ==========================================
# [ 2. مكتبة الأذكار والأدعية ]
# ==========================================

MORNING_DUAS = [
    "اللهم بك أصبحنا، وبك أمسينا، وبك نحيا، وبك نموت، وإليك النشور.",
    "أصبحنا وأصبح الملك لله، والحمد لله، لا إله إلا الله وحده لا شريك له.",
    "اللهم إني أسألك خير هذا اليوم، فتحه، ونصره، ونوره، وبركته، وهداه.",
    "رضيت بالله رباً، وبالإسلام ديناً، وبمحمد صلى الله عليه وسلم نبياً.",
    "يا حي يا قيوم برحمتك أستغيث، أصلح لي شأني كله ولا تكلني إلى نفسي طرفة عين.",
    "أصبحنا على فطرة الإسلام، وعلى كلمة الإخلاص، وعلى دين نبينا محمد.",
    "اللهم عافني في بدني، اللهم عافني في سمعي، اللهم عافني في بصري.",
    "اللهم إني أعوذ بك من الكفر والفقر، وأعوذ بك من عذاب القبر.",
    "بسم الله الذي لا يضر مع اسمه شيء في الأرض ولا في السماء وهو السميع العليم.",
    "سبحان الله وبحمده عدد خلقه، ورضا نفسه، وزنة عرشه، ومداد كلماته.",
    "اللهم ما أصبح بي من نعمة أو بأحد من خلقك فمنك وحدك لا شريك لك.",
    "حسبي الله لا إله إلا هو عليه توكلت وهو رب العرش العظيم.",
    "اللهم إني أسألك العفو والعافية في الدنيا والآخرة.",
    "اللهم عالم الغيب والشهادة فاطر السماوات والأرض رب كل شيء ومليكه."
]

NIGHT_DUAS = [
    "باسمك اللهم أموت وأحيا.",
    "اللهم بك أمسينا، وبك أصبحنا، وبك نحيا، وبك نموت، وإليك المصير.",
    "أمسينـا وأمسـى المـلك لله والحمد لله، لا إله إلا الله وحده لا شريك له.",
    "اللهم إني أسألك خير هذه الليلة وفتحها ونصرها ونورها وبركتها.",
    "أعوذ بكلمات الله التامات من شر ما خلق.",
    "اللهم قني عذابك يوم تبعث عبادك.",
    "اللهم أنت ربي لا إله إلا أنت، خلقتني وأنا عبدك، وأنا على عهدك ووعدك ما استطعت.",
    "يا حي يا قيوم برحمتك أستغيث أصلح لي شأني كله ولا تكلني إلى نفسي طرفة عين.",
    "اللهم إني أعوذ بك من الهم والحزن، والعجز والكسل، والبخل والجبن.",
    "سبحان الله وبحمده، مائة مرة.",
    "أستغفر الله وأتوب إليه.",
    "اللهم رب السماوات ورب الأرض ورب العرش العظيم، ربنا ورب كل شيء.",
    "الحمد لله الذي أطعمنا وسقانا وكفانا وآوانا، فكم ممن لا كافي له ولا مؤوي.",
    "اللهم أسلمت نفسي إليك، وفوضت أمري إليك، وألجأت ظهري إليك."
]

# الموارد الافتراضية
DEFAULT_AZAN_RESOURCES = {
    "Fajr": {"name": "الفجر", "vidid": "r9AWBlpantg", "link": "https://youtu.be/watch?v=r9AWBlpantg", "sticker": "CAACAgQAAyEFAATHCHTJAAIJD2lOq8aLkRR49evBKiITWWhwtgEoAALoGgACp_FYUQuzqVH-JHS5HgQ"},
    "Dhuhr": {"name": "الظهر", "vidid": "21MuvFr7CK8", "link": "https://www.youtube.com/watch?v=21MuvFr7CK8", "sticker": "CAACAgQAAyEFAATHCHTJAAIJEWlOrFKzjSDZeWfl6U3F-lrKldRXAAJMGwACMVlYUa15CORC0p0xHgQ"},
    "Asr": {"name": "العصر", "vidid": "bb6cNncMdiM", "link": "https://www.youtube.com/watch?v=bb6cNncMdiM", "sticker": "CAACAgQAAyEFAATHCHTJAAIJE2lOrFRQIbcdLfnpdl5PtbdqNyR6AALFGQAC3ZZRUcK5YivXbwUAAR4E"},
    "Maghrib": {"name": "المغرب", "vidid": "hKPcNh7WHoM", "link": "https://youtu.be/watch?v=hKPcNh7WHoM", "sticker": "CAACAgQAAyEFAATHCHTJAAIJFWlOrFT4eOnPJDsSuU6Ya-V0WPQdAALfFwACcIVQUX6NcNNCxvdRHgQ"},
    "Isha": {"name": "العشاء", "vidid": "hKPcNh7WHoM", "link": "https://youtu.be/watch?v=hKPcNh7WHoM", "sticker": "CAACAgQAAyEFAATHCHTJAAIJF2lOrFVxhRGefHki3d4s-hLC9cKHAALqHAAC3oZQUWqQdvdwXnGLHgQ"}
}

# متغيرات التشغيل الحالية
CURRENT_RESOURCES = DEFAULT_AZAN_RESOURCES.copy()
CURRENT_DUA_STICKER = None

PRAYER_NAMES_AR = {
    "Fajr": "الفجـر", "Dhuhr": "الظهـر", "Asr": "العصـر",
    "Maghrib": "المغـرب", "Isha": "العشـاء"
}

# ==========================================
# [ 3. دوال التحميل والتحديث ]
# ==========================================

async def load_data():
    """تحميل الإعدادات والموارد من قاعدة البيانات للكاش"""
    # 1. إعدادات المجموعات
    async for entry in azan_collection.find({}):
        settings_cache[entry.get("chat_id")] = entry
        
    # 2. الموارد المخصصة (روابط/استيكرات)
    stored_res = await resources_collection.find_one({"type": "azan_data"})
    if stored_res:
        saved_data = stored_res.get("data", {})
        for key, val in saved_data.items():
            if key in CURRENT_RESOURCES:
                CURRENT_RESOURCES[key].update(val)
    
    # 3. استيكر الدعاء
    dua_res = await resources_collection.find_one({"type": "dua_sticker"})
    if dua_res:
        global CURRENT_DUA_STICKER
        CURRENT_DUA_STICKER = dua_res.get("sticker_id")

asyncio.get_event_loop().create_task(load_data())

def extract_vidid(url):
    regex = r"(?:v=|\/)([0-9A-Za-z_-]{11}).*"
    match = re.search(regex, url)
    return match.group(1) if match else None

# ==========================================
# [ 4. دوال مساعدة ]
# ==========================================

async def is_admin(chat_id, user_id):
    if user_id == OWNER_ID: return True
    try:
        member = await app.get_chat_member(chat_id, user_id)
        return member.status in [enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.OWNER]
    except: return False

async def get_chat_settings(chat_id):
    if chat_id in settings_cache: return settings_cache[chat_id]
    doc = await azan_collection.find_one({"chat_id": chat_id})
    if not doc:
        # إنشاء إعدادات افتراضية
        doc = {
            "chat_id": chat_id, 
            "azan_master": True, 
            "dua_active": True, 
            "night_dua_active": True,
            "prayers": {k: True for k in CURRENT_RESOURCES.keys()}
        }
        await azan_collection.insert_one(doc)
    settings_cache[chat_id] = doc
    return doc

async def update_chat_setting(chat_id, key, value, sub_key=None):
    update_query = {f"prayers.{sub_key}": value} if sub_key else {key: value}
    await azan_collection.update_one({"chat_id": chat_id}, {"$set": update_query}, upsert=True)
    # تحديث الكاش
    if chat_id not in settings_cache:
        settings_cache[chat_id] = await azan_collection.find_one({"chat_id": chat_id})
    else:
        if sub_key: settings_cache[chat_id]["prayers"][sub_key] = value
        else: settings_cache[chat_id][key] = value

# ==========================================
# [ 5. أوامر تغيير الموارد (للمطور فقط) ]
# ==========================================

def get_prayers_keyboard(action_type):
    kb = []
    row = []
    for key, ar_name in PRAYER_NAMES_AR.items():
        row.append(InlineKeyboardButton(ar_name, callback_data=f"res_{action_type}_{key}"))
        if len(row) == 2:
            kb.append(row)
            row = []
    if row: kb.append(row)
    kb.append([InlineKeyboardButton("الـغـاء", callback_data="cancel_admin")])
    return InlineKeyboardMarkup(kb)

@app.on_message(filters.command(["تغيير استيكر الاذان"], COMMAND_PREFIXES) & filters.user(OWNER_ID))
async def change_azan_sticker_cmd(_, message: Message):
    await message.reply("<b>اخـتـر الـصـلاة الـتـي تـريـد تـغـيـيـر اسـتـيـكـرهـا :</b>", reply_markup=get_prayers_keyboard("sticker"))

@app.on_message(filters.command(["تغيير رابط الاذان"], COMMAND_PREFIXES) & filters.user(OWNER_ID))
async def change_azan_link_cmd(_, message: Message):
    await message.reply("<b>اخـتـر الـصـلاة الـتـي تـريـد تـغـيـيـر رابـطـهـا :</b>", reply_markup=get_prayers_keyboard("link"))

@app.on_message(filters.command(["تغيير استيكر الدعاء"], COMMAND_PREFIXES) & filters.user(OWNER_ID))
async def change_dua_sticker_cmd(_, message: Message):
    admin_state[message.from_user.id] = {"action": "wait_dua_sticker"}
    await message.reply("<b>الآن ارسـل لـي ايـدي الاسـتـيـكـر</b>")

@app.on_callback_query(filters.regex(r"^res_"))
async def resource_callback(_, query: CallbackQuery):
    data = query.data.split("_")
    action_type = data[1] 
    prayer_key = data[2]
    
    admin_state[query.from_user.id] = {
        "action": f"wait_azan_{action_type}",
        "prayer": prayer_key
    }
    
    ar_name = PRAYER_NAMES_AR[prayer_key]
    if action_type == "sticker":
        text = f"<b>جـيـد ، الآن ارسـل لـي اسـتـيـكـر صـلاة {ar_name}</b>"
    else:
        text = f"<b>جـيـد ، الآن ارسـل لـي رابـط الاذان ( صـلاة {ar_name} )</b>"
    
    await query.message.edit_text(text)

@app.on_callback_query(filters.regex("cancel_admin"))
async def cancel_admin(_, query: CallbackQuery):
    if query.from_user.id in admin_state:
        del admin_state[query.from_user.id]
    await query.message.delete()

@app.on_message((filters.sticker | filters.text) & filters.user(OWNER_ID))
async def handle_admin_input(_, message: Message):
    user_id = message.from_user.id
    if user_id not in admin_state: return

    state = admin_state[user_id]
    action = state["action"]

    if action == "wait_dua_sticker":
        if not message.sticker: return await message.reply("<b>يـجـب ارسـال اسـتـيـكـر فـقـط .</b>")
        file_id = message.sticker.file_id
        global CURRENT_DUA_STICKER
        CURRENT_DUA_STICKER = file_id
        await resources_collection.update_one({"type": "dua_sticker"}, {"$set": {"sticker_id": file_id}}, upsert=True)
        del admin_state[user_id]
        await message.reply("<b>تـم حـفـظ اسـتـيـكـر الـدعـاء الـجـديـد .</b>")

    elif action == "wait_azan_sticker":
        if not message.sticker: return await message.reply("<b>يـجـب ارسـال اسـتـيـكـر فـقـط .</b>")
        prayer = state["prayer"]
        file_id = message.sticker.file_id
        CURRENT_RESOURCES[prayer]["sticker"] = file_id
        await resources_collection.update_one({"type": "azan_data"}, {"$set": {f"data.{prayer}.sticker": file_id}}, upsert=True)
        del admin_state[user_id]
        await message.reply(f"<b>تـم حـفـظ اسـتـيـكـر صـلاة {PRAYER_NAMES_AR[prayer]} .</b>")

    elif action == "wait_azan_link":
        if not message.text: return await message.reply("<b>يـجـب ارسـال رابـط نـصـي .</b>")
        link = message.text
        vidid = extract_vidid(link)
        if not vidid: return await message.reply("<b>الـرابـط خـطـأ ، حـاول مـرة اخـري .</b>")
        prayer = state["prayer"]
        CURRENT_RESOURCES[prayer]["link"] = link
        CURRENT_RESOURCES[prayer]["vidid"] = vidid
        await resources_collection.update_one({"type": "azan_data"}, {"$set": {f"data.{prayer}.link": link, f"data.{prayer}.vidid": vidid}}, upsert=True)
        del admin_state[user_id]
        await message.reply(f"<b>تـم حـفـظ رابـط صـلاة {PRAYER_NAMES_AR[prayer]} .</b>")

# ==========================================
# [ 6. المحرك الذكي للأذان ]
# ==========================================

async def get_azan_times():
    url = "http://api.aladhan.com/v1/timingsByCity?city=Cairo&country=Egypt&method=5"
    for _ in range(3):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as response:
                    if response.status == 200:
                        res_json = await response.json()
                        return res_json["data"]["timings"]
        except:
            await asyncio.sleep(2)
    return None

async def play_azan_in_chat(chat_id, res, fake_result, semaphore):
    async with semaphore:
        try:
            await app.send_sticker(chat_id, res["sticker"])
            caption = f"<b>حـان الآن مـوعـد اذان {res['name']}</b>\n<b>بـالـتـوقـيـت الـمـحـلـي لـمـديـنـة الـقـاهـرة 🕌</b>"
            mystic = await app.send_message(chat_id, caption)
            await stream(_, mystic, app.id, fake_result, chat_id, "خدمة الأذان", chat_id, video=False, streamtype="youtube", forceplay=True)
        except:
            pass

async def broadcast_azan(prayer_key):
    res = CURRENT_RESOURCES[prayer_key]
    fake_result = {
        "link": res["link"], "vidid": res["vidid"], "title": f"أذان {res['name']}", 
        "duration_min": "05:00", "thumb": f"https://img.youtube.com/vi/{res['vidid']}/hqdefault.jpg"
    }
    
    target_chats = []
    for chat_id, settings in settings_cache.items():
        if settings.get("azan_master", True):
            prayers = settings.get("prayers", {})
            if prayers.get(prayer_key, True):
                target_chats.append(chat_id)

    if not target_chats: return
    semaphore = asyncio.Semaphore(5)
    tasks = [play_azan_in_chat(cid, res, fake_result, semaphore) for cid in target_chats]
    await asyncio.gather(*tasks)

# ==========================================
# [ 7. دالة إرسال الأدعية (4 أدعية عشوائية) ]
# ==========================================

async def send_duas_batch(dua_list, setting_key, title):
    # اختيار 4 أدعية عشوائية
    selected_duas = random.sample(dua_list, 4)
    
    message_text = f"<b>✨ {title}</b>\n\n"
    for dua in selected_duas:
        message_text += f"• {dua}\n\n"
    message_text += "<b>🕌 تـقـبـل الـلـه مـنـا ومـنـكـم صـالـح الأعـمـال</b>"

    target_chats = []
    for chat_id, settings in settings_cache.items():
        if settings.get(setting_key, True):
            target_chats.append(chat_id)

    if not target_chats: return

    async def send_one(c_id):
        try: 
            # استيكر الدعاء يرسل فقط في الصباح (اختياري)
            if setting_key == "dua_active" and CURRENT_DUA_STICKER:
                await app.send_sticker(c_id, CURRENT_DUA_STICKER)
            await app.send_message(c_id, message_text)
        except: pass

    batch_size = 20
    for i in range(0, len(target_chats), batch_size):
        batch = target_chats[i:i + batch_size]
        await asyncio.gather(*(send_one(cid) for cid in batch))
        await asyncio.sleep(0.5)

async def trigger_morning_duas():
    await send_duas_batch(MORNING_DUAS, "dua_active", "أذكـار الـصـبـاح")

async def trigger_night_duas():
    await send_duas_batch(NIGHT_DUAS, "night_dua_active", "أذكـار الـمـسـاء والـنـوم")

async def update_azan_scheduler():
    times = await get_azan_times()
    if not times: return
    
    # حذف الوظائف القديمة
    for job in scheduler.get_jobs():
        if job.id.startswith("azan_"): job.remove()

    # جدولة المواعيد الجديدة
    for key in CURRENT_RESOURCES.keys():
        if key in times:
            h, m = map(int, times[key].split(" ")[0].split(":"))
            scheduler.add_job(broadcast_azan, "cron", hour=h, minute=m, args=[key], id=f"azan_{key}")

# ==========================================
# [ 8. المجدول ]
# ==========================================

scheduler = AsyncIOScheduler(timezone="Africa/Cairo")
scheduler.add_job(update_azan_scheduler, "cron", hour=0, minute=5)
# الصباح: 7:00
scheduler.add_job(trigger_morning_duas, "cron", hour=7, minute=0)
# المساء: 12:00 منتصف الليل
scheduler.add_job(trigger_night_duas, "cron", hour=0, minute=0)

if not scheduler.running:
    scheduler.start()
    asyncio.get_event_loop().create_task(update_azan_scheduler())

# ==========================================
# [ 9. لوحة التحكم والأوامر ]
# ==========================================

def get_settings_keyboard(settings):
    prayers = settings.get("prayers", {})
    kb = []
    
    dua_status = "〔 مـفـعـل 〕" if settings.get("dua_active", True) else "〔 مـقـفـول 〕"
    kb.append([InlineKeyboardButton(f"أذكـار الـصـبـاح ↢ {dua_status}", callback_data="toggle_dua")])
    
    night_status = "〔 مـفـعـل 〕" if settings.get("night_dua_active", True) else "〔 مـقـفـول 〕"
    kb.append([InlineKeyboardButton(f"أذكـار الـمـسـاء ↢ {night_status}", callback_data="toggle_night_dua")])
    
    row = []
    for key, ar_name in PRAYER_NAMES_AR.items():
        status = "〔 مـفـعـل 〕" if prayers.get(key, True) else "〔 مـقـفـول 〕"
        btn_text = f"{ar_name} ↢ {status}"
        row.append(InlineKeyboardButton(btn_text, callback_data=f"toggle_p_{key}"))
        if len(row) == 2:
            kb.append(row)
            row = []
    if row: kb.append(row)
    
    kb.append([InlineKeyboardButton("اغـلاق", callback_data="close_settings")])
    return InlineKeyboardMarkup(kb)

@app.on_message(filters.command(["اعدادات الاذان"], COMMAND_PREFIXES) & filters.group & ~BANNED_USERS)
async def open_settings(_, message: Message):
    if not await is_admin(message.chat.id, message.from_user.id):
        return await message.reply("<b>هـذا الامـر لـلـمـشـرفـيـن فـقـط .</b>")
    settings = await get_chat_settings(message.chat.id)
    await message.reply_text("<b>إعـدادات الأذان والأدعيـة :</b>", reply_markup=get_settings_keyboard(settings))

@app.on_callback_query(filters.regex(r"^(toggle_|close_)"))
async def azan_callbacks(_, query: CallbackQuery):
    if not await is_admin(query.message.chat.id, query.from_user.id):
        return await query.answer("للادمـن بـس يـا حـلـو 🧚", show_alert=True)
    
    if query.data == "close_settings":
        try: await query.message.delete()
        except: pass
        return

    chat_id = query.message.chat.id
    settings = await get_chat_settings(chat_id)

    if query.data == "toggle_dua":
        await update_chat_setting(chat_id, "dua_active", not settings.get("dua_active", True))
        await query.answer("تـم الـتـعـديـل")
        
    elif query.data == "toggle_night_dua":
        await update_chat_setting(chat_id, "night_dua_active", not settings.get("night_dua_active", True))
        await query.answer("تـم الـتـعـديـل")
        
    elif query.data.startswith("toggle_p_"):
        key = query.data.split("_")[2]
        await update_chat_setting(chat_id, "prayers", not settings.get("prayers", {}).get(key, True), sub_key=key)
        await query.answer(f"تـم تـعـديـل {PRAYER_NAMES_AR[key]}")

    updated = await get_chat_settings(chat_id)
    try: await query.message.edit_reply_markup(reply_markup=get_settings_keyboard(updated))
    except: pass

@app.on_message(filters.command(["تفعيل الاذان"], COMMAND_PREFIXES) & filters.group & ~BANNED_USERS)
async def azan_on_cmd(_, message: Message):
    if not await is_admin(message.chat.id, message.from_user.id): return await message.reply("<b>لـلـمـشـرفـيـن فـقـط .</b>")
    await update_chat_setting(message.chat.id, "azan_master", True)
    await message.reply_text("<b>تـم تـفـعـيـل الأذان الـتـلـقـائـي .</b>")

@app.on_message(filters.command(["قفل الاذان"], COMMAND_PREFIXES) & filters.group & ~BANNED_USERS)
async def azan_off_cmd(_, message: Message):
    if not await is_admin(message.chat.id, message.from_user.id): return await message.reply("<b>لـلـمـشـرفـيـن فـقـط .</b>")
    await update_chat_setting(message.chat.id, "azan_master", False)
    await message.reply_text("<b>تـم تـعـطـيـل الأذان بـالـكـامـل .</b>")

@app.on_message(filters.command(["تفعيل الاذان الاجباري"], COMMAND_PREFIXES) & filters.user(OWNER_ID))
async def force_enable_all(_, message: Message):
    status = await message.reply_text("<b>جـاري تـفـعـيـل الأذان والأدعيـة الإجـبـاري ...</b>")
    count = 0
    async for doc in azan_collection.find({}):
        await azan_collection.update_one(
            {"_id": doc["_id"]}, 
            {"$set": {"azan_master": True, "dua_active": True, "night_dua_active": True}}
        )
        if doc["chat_id"] in settings_cache:
            settings_cache[doc["chat_id"]]["azan_master"] = True
            settings_cache[doc["chat_id"]]["dua_active"] = True
            set
