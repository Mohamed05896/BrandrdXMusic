import asyncio
import random
import aiohttp
import re
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from pyrogram import filters, enums
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from motor.motor_asyncio import AsyncIOMotorClient

import config
from config import BANNED_USERS, COMMAND_PREFIXES, MONGO_DB_URI
from BrandrdXMusic import app
from BrandrdXMusic.utils.stream.stream import stream

# ==========================================
# [ 1. إعدادات النظام وقواعد البيانات ]
# ==========================================

# تعريف ايدي المالك يدوياً لضمان الصلاحيات
OWNER_ID = 8313557781

# الاتصال بقاعدة البيانات
db_client = AsyncIOMotorClient(MONGO_DB_URI)
# قاعدة لحفظ إعدادات المجموعات (تفعيل/قفل)
settings_db = db_client.BrandrdX.azan_settings_pro
# قاعدة لحفظ الموارد (الروابط والاستيكرات الجديدة)
resources_db = db_client.BrandrdX.azan_resources_pro

# متغيرات التشغيل
local_cache = {} # لتسريع الاستجابة
admin_state = {} # لحفظ حالة المطور عند تغيير الروابط

# ==========================================
# [ 2. المحتوى والموارد الافتراضية ]
# ==========================================

MORNING_DUAS = [
    "اللهم بك أصبحنا، وبك أمسينا، وبك نحيا، وبك نموت، وإليك النشور.",
    "أصبحنا وأصبح الملك لله، والحمد لله، لا إله إلا الله وحده لا شريك له.",
    "اللهم إني أسألك خير هذا اليوم، فتحه، ونصره، ونوره، وبركته، وهداه.",
    "رضيت بالله رباً، وبالإسلام ديناً، وبمحمد صلى الله عليه وسلم نبياً.",
    "يا حي يا قيوم برحمتك أستغيث، أصلح لي شأني كله ولا تكلني إلى نفسي طرفة عين.",
    "أصبحنا على فطرة الإسلام، وعلى كلمة الإخلاص، وعلى دين نبينا محمد.",
    "اللهم عافني في بدني، اللهم عافني في سمعي، اللهم عافني في بصري."
]

NIGHT_DUAS = [
    "باسمك اللهم أموت وأحيا.",
    "اللهم بك أمسينا، وبك أصبحنا، وبك نحيا، وبك نموت، وإليك المصير.",
    "أمسينـا وأمسـى المـلك لله والحمد لله، لا إله إلا الله وحده لا شريك له.",
    "أعوذ بكلمات الله التامات من شر ما خلق.",
    "اللهم قني عذابك يوم تبعث عبادك.",
    "يا حي يا قيوم برحمتك أستغيث أصلح لي شأني كله ولا تكلني إلى نفسي طرفة عين."
]

# الموارد الافتراضية (سيتم تحديثها من القاعدة إذا قمت بتغييرها)
DEFAULT_RESOURCES = {
    "Fajr": {"name": "الفجر", "vidid": "r9AWBlpantg", "link": "https://youtu.be/watch?v=r9AWBlpantg", "sticker": "CAACAgQAAyEFAATHCHTJAAIJD2lOq8aLkRR49evBKiITWWhwtgEoAALoGgACp_FYUQuzqVH-JHS5HgQ"},
    "Dhuhr": {"name": "الظهر", "vidid": "21MuvFr7CK8", "link": "https://www.youtube.com/watch?v=21MuvFr7CK8", "sticker": "CAACAgQAAyEFAATHCHTJAAIJEWlOrFKzjSDZeWfl6U3F-lrKldRXAAJMGwACMVlYUa15CORC0p0xHgQ"},
    "Asr": {"name": "العصر", "vidid": "bb6cNncMdiM", "link": "https://www.youtube.com/watch?v=bb6cNncMdiM", "sticker": "CAACAgQAAyEFAATHCHTJAAIJE2lOrFRQIbcdLfnpdl5PtbdqNyR6AALFGQAC3ZZRUcK5YivXbwUAAR4E"},
    "Maghrib": {"name": "المغرب", "vidid": "hKPcNh7WHoM", "link": "https://youtu.be/watch?v=hKPcNh7WHoM", "sticker": "CAACAgQAAyEFAATHCHTJAAIJFWlOrFT4eOnPJDsSuU6Ya-V0WPQdAALfFwACcIVQUX6NcNNCxvdRHgQ"},
    "Isha": {"name": "العشاء", "vidid": "hKPcNh7WHoM", "link": "https://youtu.be/watch?v=hKPcNh7WHoM", "sticker": "CAACAgQAAyEFAATHCHTJAAIJF2lOrFVxhRGefHki3d4s-hLC9cKHAALqHAAC3oZQUWqQdvdwXnGLHgQ"}
}

CURRENT_RESOURCES = DEFAULT_RESOURCES.copy()
CURRENT_DUA_STICKER = None

PRAYER_NAMES_AR = {
    "Fajr": "الفجـر", "Dhuhr": "الظهـر", "Asr": "العصـر",
    "Maghrib": "المغـرب", "Isha": "العشـاء"
}

# ==========================================
# [ 3. دوال التحميل والتحديث (Core) ]
# ==========================================

async def load_resources():
    """تحميل الروابط والاستيكرات المحفوظة عند التشغيل"""
    # الأذان
    stored_res = await resources_db.find_one({"type": "azan_data"})
    if stored_res:
        saved_data = stored_res.get("data", {})
        for key, val in saved_data.items():
            if key in CURRENT_RESOURCES:
                CURRENT_RESOURCES[key].update(val)
    # استيكر الدعاء
    dua_res = await resources_db.find_one({"type": "dua_sticker"})
    if dua_res:
        global CURRENT_DUA_STICKER
        CURRENT_DUA_STICKER = dua_res.get("sticker_id")

# تشغيل التحميل فوراً
asyncio.get_event_loop().create_task(load_resources())

def extract_vidid(url):
    """استخراج ايدي الفيديو من رابط يوتيوب"""
    regex = r"(?:v=|\/)([0-9A-Za-z_-]{11}).*"
    match = re.search(regex, url)
    return match.group(1) if match else None

# ==========================================
# [ 4. دوال التشغيل والمواقيت ]
# ==========================================

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
    """دالة التشغيل الرئيسية"""
    res = CURRENT_RESOURCES[prayer_key]
    fake_result = {
        "link": res["link"], 
        "vidid": res["vidid"], 
        "title": f"أذان {res['name']}", 
        "duration_min": "05:00", 
        "thumb": f"https://img.youtube.com/vi/{res['vidid']}/hqdefault.jpg"
    }
    _ = {"queue_4": "<b>الترتيب: #{}</b>", "stream_1": "<b>جاري التشغيل...</b>", "play_3": "<b>فشل التشغيل.</b>"}
    
    try:
        await app.send_sticker(chat_id, res["sticker"])
        caption = f"<b>حان الآن موعد اذان {res['name']}</b>\n<b>بالتوقيت المحلي لمدينة القاهره</b>"
        mystic = await app.send_message(chat_id, caption)
        
        # [ هام جداً ] استخدام OWNER_ID كطالب للتشغيل
        await stream(
            _, 
            mystic, 
            OWNER_ID, 
            fake_result, 
            chat_id, 
            "خدمة الأذان", 
            chat_id, 
            video=False, 
            streamtype="youtube", 
            forceplay=True
        )
    except Exception as e:
        print(f"Azan Stream Error: {e}")
        pass

async def broadcast_azan(prayer_key):
    """البث الجماعي"""
    async for entry in settings_db.find({"azan_active": True}):
        c_id = entry.get("chat_id")
        prayers = entry.get("prayers", {})
        if c_id and prayers.get(prayer_key, True):
            await start_azan_stream(c_id, prayer_key)
            await asyncio.sleep(3) # منع الفلود

async def send_duas_batch(dua_list, setting_key, title):
    """إرسال الأذكار"""
    selected = random.sample(dua_list, min(3, len(dua_list)))
    text = f"<b>{title}</b>\n\n"
    for d in selected:
        text += f"• {d}\n\n"
    
    async for entry in settings_db.find({setting_key: True}):
        try:
            c_id = entry.get("chat_id")
            if c_id:
                if CURRENT_DUA_STICKER:
                    await app.send_sticker(c_id, CURRENT_DUA_STICKER)
                await app.send_message(c_id, text)
                await asyncio.sleep(1)
        except:
            continue

async def update_azan_scheduler():
    times = await get_azan_times()
    if not times: return
    
    # تنظيف المهام القديمة
    for job in scheduler.get_jobs():
        if job.id.startswith("azan_"): job.remove()
            
    # إضافة مهام جديدة
    for key in CURRENT_RESOURCES.keys():
        if key in times:
            h, m = map(int, times[key].split(" ")[0].split(":"))
            scheduler.add_job(broadcast_azan, "cron", hour=h, minute=m, args=[key], id=f"azan_{key}")

# ==========================================
# [ 5. المجدول الزمني ]
# ==========================================

scheduler = AsyncIOScheduler(timezone="Africa/Cairo")
scheduler.add_job(update_azan_scheduler, "cron", hour=0, minute=5)
scheduler.add_job(lambda: asyncio.create_task(send_duas_batch(MORNING_DUAS, "dua_active", "أذكار الصباح")), "cron", hour=7, minute=0)
scheduler.add_job(lambda: asyncio.create_task(send_duas_batch(NIGHT_DUAS, "night_dua_active", "أذكار المساء")), "cron", hour=20, minute=0)

if not scheduler.running:
    scheduler.start()
    asyncio.get_event_loop().create_task(update_azan_scheduler())

# ==========================================
# [ 6. دوال مساعدة ]
# ==========================================

async def check_rights(message):
    if message.from_user.id == OWNER_ID: return True
    try:
        member = await app.get_chat_member(message.chat.id, message.from_user.id)
        if member.status in [enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.OWNER]:
            return True
    except: pass
    return False

async def get_chat_doc(chat_id):
    if chat_id in local_cache: return local_cache[chat_id]
    doc = await settings_db.find_one({"chat_id": chat_id})
    if not doc:
        doc = {
            "chat_id": chat_id, 
            "azan_active": True, "dua_active": True, "night_dua_active": True,
            "prayers": {k: True for k in CURRENT_RESOURCES.keys()}
        }
        await settings_db.insert_one(doc)
    local_cache[chat_id] = doc
    return doc

async def update_doc(chat_id, key, value, sub_key=None):
    if sub_key:
        await settings_db.update_one({"chat_id": chat_id}, {"$set": {f"prayers.{sub_key}": value}}, upsert=True)
    else:
        await settings_db.update_one({"chat_id": chat_id}, {"$set": {key: value}}, upsert=True)
    if chat_id in local_cache: del local_cache[chat_id]

# ==========================================
# [ 7. أوامر المطور (التغيير والتعديل) ]
# ==========================================

@app.on_message(filters.command(["تغيير استيكر الاذان"], COMMAND_PREFIXES) & filters.user(OWNER_ID), group=57)
async def ch_sticker_cmd(_, message: Message):
    kb = []
    row = []
    for key, ar_name in PRAYER_NAMES_AR.items():
        row.append(InlineKeyboardButton(ar_name, callback_data=f"set_sticker_{key}"))
        if len(row) == 2:
            kb.append(row)
            row = []
    if row: kb.append(row)
    kb.append([InlineKeyboardButton("• الغاء •", callback_data="cancel_dev")])
    await message.reply("<b>اختر الصلاة التي تريد تغيير استيكرها :</b>", reply_markup=InlineKeyboardMarkup(kb))

@app.on_message(filters.command(["تغيير رابط الاذان"], COMMAND_PREFIXES) & filters.user(OWNER_ID), group=57)
async def ch_link_cmd(_, message: Message):
    kb = []
    row = []
    for key, ar_name in PRAYER_NAMES_AR.items():
        row.append(InlineKeyboardButton(ar_name, callback_data=f"set_link_{key}"))
        if len(row) == 2:
            kb.append(row)
            row = []
    if row: kb.append(row)
    kb.append([InlineKeyboardButton("• الغاء •", callback_data="cancel_dev")])
    await message.reply("<b>اختر الصلاة التي تريد تغيير رابطها :</b>", reply_markup=InlineKeyboardMarkup(kb))

@app.on_message(filters.command(["تغيير استيكر الدعاء"], COMMAND_PREFIXES) & filters.user(OWNER_ID), group=57)
async def ch_dua_sticker(_, message: Message):
    admin_state[message.from_user.id] = {"action": "wait_dua_sticker"}
    await message.reply("<b>ارسل الآن استيكر الدعاء الجديد :</b>")

@app.on_message(filters.command(["تفعيل الاذان الاجباري"], COMMAND_PREFIXES) & filters.user(OWNER_ID), group=57)
async def force_enable_all(_, message: Message):
    msg = await message.reply("<b>جاري التفعيل في جميع المجموعات...</b>")
    c = 0
    async for doc in settings_db.find({}):
        await settings_db.update_one({"_id": doc["_id"]}, {"$set": {"azan_active": True, "dua_active": True, "night_dua_active": True}})
        c += 1
    local_cache.clear()
    await msg.edit_text(f"<b>تم التفعيل في {c} مجموعة.</b>")

# استقبال المدخلات من المطور (الروابط والاستيكرات)
@app.on_message((filters.text | filters.sticker) & filters.user(OWNER_ID), group=57)
async def dev_input_handler(_, message: Message):
    uid = message.from_user.id
    if uid not in admin_state: return
    
    state = admin_state[uid]
    action = state["action"]

    if action == "wait_dua_sticker":
        if not message.sticker: return await message.reply("<b>يجب ارسال استيكر فقط.</b>")
        fid = message.sticker.file_id
        global CURRENT_DUA_STICKER
        CURRENT_DUA_STICKER = fid
        await resources_db.update_one({"type": "dua_sticker"}, {"$set": {"sticker_id": fid}}, upsert=True)
        del admin_state[uid]
        await message.reply("<b>تم حفظ استيكر الدعاء الجديد.</b>")
    
    elif action == "wait_azan_sticker":
        if not message.sticker: return await message.reply("<b>يجب ارسال استيكر فقط.</b>")
        fid = message.sticker.file_id
        pkey = state["key"]
        CURRENT_RESOURCES[pkey]["sticker"] = fid
        await resources_db.update_one({"type": "azan_data"}, {"$set": {f"data.{pkey}.sticker": fid}}, upsert=True)
        del admin_state[uid]
        await message.reply(f"<b>تم تغيير استيكر صلاة {PRAYER_NAMES_AR[pkey]}.</b>")

    elif action == "wait_azan_link":
        if not message.text: return
        link = message.text
        vidid = extract_vidid(link)
        if not vidid: return await message.reply("<b>رابط يوتيوب غير صحيح، حاول مرة أخرى.</b>")
        pkey = state["key"]
        CURRENT_RESOURCES[pkey]["link"] = link
        CURRENT_RESOURCES[pkey]["vidid"] = vidid
        await resources_db.update_one({"type": "azan_data"}, {"$set": {f"data.{pkey}.link": link, f"data.{pkey}.vidid": vidid}}, upsert=True)
        del admin_state[uid]
        await message.reply(f"<b>تم تغيير رابط صلاة {PRAYER_NAMES_AR[pkey]}.</b>")

# ==========================================
# [ 8. الأوامر العامة والتحكم ]
# ==========================================

@app.on_message(filters.command(["اوامر الاذان", "أوامر الاذان"], COMMAND_PREFIXES) & ~BANNED_USERS, group=57)
async def azan_menu(_, message: Message):
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("اوامر المشرفين", callback_data="help_admin"),
         InlineKeyboardButton("اوامر المطور", callback_data="help_dev")],
        [InlineKeyboardButton("• الاغلاق •", callback_data="close_azan_panel")]
    ])
    await message.reply_text("<b>اهلا بك في اوامر الاذان</b>", reply_markup=kb)

@app.on_message(filters.command(["انلاين الاذان"], COMMAND_PREFIXES) & filters.group & ~BANNED_USERS, group=57)
async def inline_settings(_, message: Message):
    if not await check_rights(message): return await message.reply("<b>للمشرفين فقط.</b>")
    doc = await get_chat_doc(message.chat.id)
    
    prayers = doc.get("prayers", {})
    kb = []
    
    st_azan = "〔 مفعل 〕" if doc.get("azan_active", True) else "〔 مقفل 〕"
    kb.append([InlineKeyboardButton(f"الأذان العام ↢ {st_azan}", callback_data="tog_main_azan")])
    
    st_dua = "〔 مفعل 〕" if doc.get("dua_active", True) else "〔 مقفل 〕"
    kb.append([InlineKeyboardButton(f"دعاء الصباح ↢ {st_dua}", callback_data="tog_dua")])
    
    st_ndua = "〔 مفعل 〕" if doc.get("night_dua_active", True) else "〔 مقفل 〕"
    kb.append([InlineKeyboardButton(f"دعاء المساء ↢ {st_ndua}", callback_data="tog_ndua")])
    
    row = []
    for k, name in PRAYER_NAMES_AR.items():
        pst = "〔 مفعل 〕" if prayers.get(k, True) else "〔 مقفل 〕"
        row.append(InlineKeyboardButton(f"{name} ↢ {pst}", callback_data=f"tog_p_{k}"))
        if len(row) == 2:
            kb.append(row)
            row = []
    if row: kb.append(row)
    kb.append([InlineKeyboardButton("• الاغلاق •", callback_data="close_azan_panel")])
    
    await message.reply_text("<b>لوحة تحكم الأذان :</b>", reply_markup=InlineKeyboardMarkup(kb))

# أوامر نصية
@app.on_message(filters.command(["تفعيل الاذان"], COMMAND_PREFIXES) & filters.group & ~BANNED_USERS, group=57)
async def txt_azan_on(_, m):
    if await check_rights(m):
        await update_doc(m.chat.id, "azan_active", True)
        await m.reply("<b>تم تفعيل الاذان التلقائي.</b>")

@app.on_message(filters.command(["قفل الاذان"], COMMAND_PREFIXES) & filters.group & ~BANNED_USERS, group=57)
async def txt_azan_off(_, m):
    if await check_rights(m):
        await update_doc(m.chat.id, "azan_active", False)
        await m.reply("<b>تم قفل الاذان التلقائي.</b>")

@app.on_message(filters.command(["تفعيل الدعاء"], COMMAND_PREFIXES) & filters.group & ~BANNED_USERS, group=57)
async def txt_dua_on(_, m):
    if await check_rights(m):
        await update_doc(m.chat.id, "dua_active", True)
        await m.reply("<b>تم تفعيل أدعية الصباح.</b>")

@app.on_message(filters.command(["قفل الدعاء"], COMMAND_PREFIXES) & filters.group & ~BANNED_USERS, group=57)
async def txt_dua_off(_, m):
    if await check_rights(m):
        await update_doc(m.chat.id, "dua_active", False)
        await m.reply("<b>تم قفل أدعية الصباح.</b>")

@app.on_message(filters.command("تست اذان", COMMAND_PREFIXES) & filters.user(OWNER_ID), group=57)
async def test_run(_, m):
    await m.reply("<b>جاري تجربة أذان الفجر...</b>")
    await start_azan_stream(m.chat.id, "Fajr")

# ==========================================
# [ 9. معالجة الكيبورد (Callbacks) ]
# ==========================================

@app.on_callback_query(filters.regex(r"^(help_|tog_|set_|close_|cancel_)"), group=57)
async def cb_handler(_, query: CallbackQuery):
    data = query.data
    uid = query.from_user.id
    chat_id = query.message.chat.id
    
    if data == "close_azan_panel":
        try: await query.message.delete()
        except: pass
        return

    # قوائم المساعدة
    if data == "help_admin":
        text = (
            "<b>اوامر المشرفين (داخل المجموعة) :</b>\n\n"
            "• <code>انلاين الاذان</code> : لفتح لوحة التحكم .\n"
            "• <code>تفعيل الاذان</code> : لتشغيل الخدمة .\n"
            "• <code>قفل الاذان</code> : لإيقاف الخدمة .\n"
            "• <code>تفعيل الدعاء</code> : لتشغيل الأدعية .\n"
            "• <code>قفل الدعاء</code> : لإيقاف الأدعية ."
        )
        await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("رجوع", callback_data="help_back")]]))
        return
    if data == "help_dev":
        text = (
            "<b>اوامر المطور (الاساسي) :</b>\n\n"
            "• <code>تغيير استيكر الاذان</code>\n"
            "• <code>تغيير رابط الاذان</code>\n"
            "• <code>تغيير استيكر الدعاء</code>\n"
            "• <code>تفعيل الاذان الاجباري</code>\n"
            "• <code>تست اذان</code>"
        )
        await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("رجوع", callback_data="help_back")]]))
        return
    if data == "help_back":
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("اوامر المشرفين", callback_data="help_admin"),
             InlineKeyboardButton("اوامر المطور", callback_data="help_dev")],
            [InlineKeyboardButton("• الاغلاق •", callback_data="close_azan_panel")]
        ])
        await query.message.edit_text("<b>اهلا بك في اوامر الاذان</b>", reply_markup=kb)
        return

    # أوامر التعديل (للمطور فقط)
    if data.startswith("set_") or data == "cancel_dev":
        if uid != OWNER_ID: return await query.answer("للمطور فقط", show_alert=True)
        if data == "cancel_dev":
            if uid in admin_state: del admin_state[uid]
            await query.message.delete()
            return
        
        action_type = data.split("_")[1] # sticker or link
        key = data.split("_")[2]
        admin_state[uid] = {"action": f"wait_azan_{action_type}", "key": key}
        req = "استيكر" if action_type == "sticker" else "رابط"
        await query.message.edit_text(f"<b>ارسل الآن {req} صلاة {PRAYER_NAMES_AR[key]} الجديد :</b>")
        return

    # أوامر التبديل (للمشرفين)
    is_admin = False
    if uid == OWNER_ID: is_admin = True
    else:
        try:
            mem = await app.get_chat_member(chat_id, uid)
            if mem.status in [enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.OWNER]:
                is_admin = True
        except: pass
    
    if not is_admin: return await query.answer("للمشرفين فقط", show_alert=True)
    
    doc = await get_chat_doc(chat_id)
    if data == "tog_main_azan":
        await update_doc(chat_id, "azan_active", not doc.get("azan_active", True))
    elif data == "tog_dua":
        await update_doc(chat_id, "dua_active", not doc.get("dua_active", True))
    elif data == "tog_ndua":
        await update_doc(chat_id, "night_dua_active", not doc.get("night_dua_active", True))
    elif data.startswith("tog_p_"):
        key = data.split("_")[2]
        curr = doc.get("prayers", {}).get(key, True)
        await update_doc(chat_id, None, not curr, sub_key=key)

    # تحديث الكيبورد
    new_doc = await get_chat_doc(chat_id)
    prayers = new_doc.get("prayers", {})
    kb = []
    st_azan = "〔 مفعل 〕" if new_doc.get("azan_active", True) else "〔 مقفل 〕"
    kb.append([InlineKeyboardButton(f"الأذان العام ↢ {st_azan}", callback_data="tog_main_azan")])
    st_dua = "〔 مفعل 〕" if new_doc.get("dua_active", True) else "〔 مقفل 〕"
    kb.append([InlineKeyboardButton(f"دعاء الصباح ↢ {st_dua}", callback_data="tog_dua")])
    st_ndua = "〔 مفعل 〕" if new_doc.get("night_dua_active", True) else "〔 مقفل 〕"
    kb.append([InlineKeyboardButton(f"دعاء المساء ↢ {st_ndua}", callback_data="tog_ndua")])
    row = []
    for k, name in PRAYER_NAMES_AR.items():
        pst = "〔 مفعل 〕" if prayers.get(k, True) else "〔 مقفل 〕"
        row.append(InlineKeyboardButton(f"{name} ↢ {pst}", callback_data=f"tog_p_{k}"))
        if len(row) == 2: kb.append(row); row = []
    if row: kb.append(row)
    kb.append([InlineKeyboardButton("• الاغلاق •", callback_data="close_azan_panel")])
    
    try: await query.message.edit_reply_markup(reply_markup=InlineKeyboardMarkup(kb))
    except: pass
