import asyncio
import random
import aiohttp
import re
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from pyrogram import filters, enums
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from motor.motor_asyncio import AsyncIOMotorClient

import config
from config import BANNED_USERS, COMMAND_PREFIXES, MONGO_DB_URI, OWNER_ID
from BrandrdXMusic import app
from BrandrdXMusic.utils.stream.stream import stream

# ==========================================
# [ 1. إعدادات النظام ]
# ==========================================

REAL_OWNER_ID = OWNER_ID[0] if isinstance(OWNER_ID, list) else OWNER_ID

db_client = AsyncIOMotorClient(MONGO_DB_URI)
settings_db = db_client.BrandrdX.azan_pro_ultra_db
resources_db = db_client.BrandrdX.azan_resources_final_db

local_cache = {}
admin_state = {}
AZAN_GROUP = 57

# ==========================================
# [ 2. المحتوى (نظيف + إيموجي جمالي فقط) ]
# ==========================================

# تم حذف إيموجي النظام، والاحتفاظ بإيموجي الأدعية كما طلبت
MORNING_DUAS = [
    "اللهم بك أصبحنا، وبك أمسينا، وبك نحيا، وبك نموت، وإليك النشور. ☀️",
    "أصبحنا وأصبح الملك لله، والحمد لله، لا إله إلا الله وحده لا شريك له. ✨",
    "اللهم إني أسألك خير هذا اليوم، فتحه، ونصره، ونوره، وبركته، وهداه. 🤲",
    "رضيت بالله رباً، وبالإسلام ديناً، وبمحمد صلى الله عليه وسلم نبياً. 🤍",
    "يا حي يا قيوم برحمتك أستغيث، أصلح لي شأني كله ولا تكلني إلى نفسي طرفة عين. 🕊️"
]

NIGHT_DUAS = [
    "باسمك اللهم أموت وأحيا. 🌑",
    "اللهم بك أمسينا، وبك أصبحنا، وبك نحيا، وبك نموت، وإليك المصير. 🌌",
    "أمسينـا وأمسـى المـلك لله والحمد لله، لا إله إلا الله وحده لا شريك له. ✨",
    "أعوذ بكلمات الله التامات من شر ما خلق. "
]

DEFAULT_RESOURCES = {
    "Fajr": {"name": "الفجر", "vidid": "r9AWBlpantg", "link": "https://youtu.be/watch?v=r9AWBlpantg", "sticker": "CAACAgQAAyEFAATHCHTJAAIJD2lOq8aLkRR49evBKiITWWhwtgEoAALoGgACp_FYUQuzqVH-JHS5HgQ"},
    "Dhuhr": {"name": "الظهر", "vidid": "21MuvFr7CK8", "link": "https://www.youtube.com/watch?v=21MuvFr7CK8", "sticker": "CAACAgQAAyEFAATHCHTJAAIJEWlOrFKzjSDZeWfl6U3F-lrKldRXAAJMGwACMVlYUa15CORC0p0xHgQ"},
    "Asr": {"name": "العصر", "vidid": "bb6cNncMdiM", "link": "https://www.youtube.com/watch?v=bb6cNncMdiM", "sticker": "CAACAgQAAyEFAATHCHTJAAIJE2lOrFRQIbcdLfnpdl5PtbdqNyR6AALFGQAC3ZZRUcK5YivXbwUAAR4E"},
    "Maghrib": {"name": "المغرب", "vidid": "hKPcNh7WHoM", "link": "https://youtu.be/watch?v=hKPcNh7WHoM", "sticker": "CAACAgQAAyEFAATHCHTJAAIJFWlOrFT4eOnPJDsSuU6Ya-V0WPQdAALfFwACcIVQUX6NcNNCxvdRHgQ"},
    "Isha": {"name": "العشاء", "vidid": "hKPcNh7WHoM", "link": "https://youtu.be/watch?v=hKPcNh7WHoM", "sticker": "CAACAgQAAyEFAATHCHTJAAIJF2lOrFVxhRGefHki3d4s-hLC9cKHAALqHAAC3oZQUWqQdvdwXnGLHgQ"}
}

CURRENT_RESOURCES = DEFAULT_RESOURCES.copy()
CURRENT_DUA_STICKER = None

PRAYER_NAMES_AR = {"Fajr": "الفجـر", "Dhuhr": "الظهـر", "Asr": "العصـر", "Maghrib": "المغـرب", "Isha": "العشـاء"}

# ==========================================
# [ 3. دوال النظام ]
# ==========================================

async def load_resources():
    stored_res = await resources_db.find_one({"type": "azan_data"})
    if stored_res:
        saved_data = stored_res.get("data", {})
        for key, val in saved_data.items():
            if key in CURRENT_RESOURCES: CURRENT_RESOURCES[key].update(val)
    dua_res = await resources_db.find_one({"type": "dua_sticker"})
    if dua_res:
        global CURRENT_DUA_STICKER
        CURRENT_DUA_STICKER = dua_res.get("sticker_id")

def extract_vidid(url):
    match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11}).*", url)
    return match.group(1) if match else None

async def get_chat_doc(chat_id):
    if chat_id in local_cache: return local_cache[chat_id]
    doc = await settings_db.find_one({"chat_id": chat_id})
    if not doc:
        doc = {"chat_id": chat_id, "azan_active": True, "dua_active": True, "night_dua_active": True, "prayers": {k: True for k in CURRENT_RESOURCES.keys()}}
        await settings_db.insert_one(doc)
    local_cache[chat_id] = doc
    return doc

async def update_doc(chat_id, key, value, sub_key=None):
    if sub_key: await settings_db.update_one({"chat_id": chat_id}, {"$set": {f"prayers.{sub_key}": value}}, upsert=True)
    else: await settings_db.update_one({"chat_id": chat_id}, {"$set": {key: value}}, upsert=True)
    if chat_id in local_cache: del local_cache[chat_id]

async def check_rights(user_id, chat_id):
    if user_id == REAL_OWNER_ID or user_id in config.OWNER_ID: return True
    try:
        mem = await app.get_chat_member(chat_id, user_id)
        if mem.status in [enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.OWNER]: return True
    except: pass
    return False

# ==========================================
# [ 4. نظام التشغيل الذكي (Multi-Method) ]
# ==========================================

async def start_azan_smart(chat_id, prayer_key):
    res = CURRENT_RESOURCES[prayer_key]
    caption = f"<b>حان الآن موعد اذان {res['name']}</b>\n<b>بالتوقيت المحلي لمدينة القاهره 🕌🤍</b>"
    
    # 1. إرسال الاستيكر والرسالة أولاً (تنبيه بصري)
    try:
        await app.send_sticker(chat_id, res["sticker"])
        msg = await app.send_message(chat_id, caption)
    except:
        return # إذا لم يستطع الإرسال، غالباً البوت ليس مشرفاً

    # 2. الطريقة الأولى: التشغيل عبر الكول (Stream)
    try:
        fake_result = {
            "link": res["link"], "vidid": res["vidid"], 
            "title": f"أذان {res['name']}", "duration_min": "05:00", 
            "thumb": f"https://img.youtube.com/vi/{res['vidid']}/hqdefault.jpg"
        }
        # رسائل التشغيل (بدون ايموجي)
        _ = {"queue_4": "الترتيب: #{}", "stream_1": "جاري التشغيل...", "play_3": "فشل التشغيل."}
        
        await stream(_, msg, REAL_OWNER_ID, fake_result, chat_id, "خدمة الأذان", chat_id, video=False, streamtype="youtube", forceplay=True)
        return # نجحت الطريقة الأولى

    except Exception as e:
        print(f"Azan Stream Failed: {e}")
        # إذا فشل، ننتقل للطريقة الثانية فوراً
    
    # 3. الطريقة الثانية: (Fallback) إرسال الرابط كتنبيه صوتي
    try:
        fallback_text = f"<b>تعذر تشغيل المكالمة، استمع للأذان من هنا:</b>\n{res['link']}"
        await app.send_message(chat_id, fallback_text, disable_web_page_preview=False)
    except: pass

async def get_azan_times():
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("http://api.aladhan.com/v1/timingsByCity?city=Cairo&country=Egypt&method=5") as response:
                if response.status == 200:
                    data = await response.json()
                    return data["data"]["timings"]
    except: return None

async def broadcast_azan(prayer_key):
    async for entry in settings_db.find({"azan_active": True}):
        c_id = entry.get("chat_id")
        prayers = entry.get("prayers", {})
        if c_id and prayers.get(prayer_key, True):
            await start_azan_smart(c_id, prayer_key)
            await asyncio.sleep(3)

async def send_duas_batch(dua_list, setting_key, title):
    selected = random.sample(dua_list, min(4, len(dua_list)))
    text = f"<b>{title}</b>\n\n"
    for d in selected: text += f"• {d}\n\n"
    text += "<b>تقبل الله منا ومنكم صالح الأعمال ✨</b>"
    async for entry in settings_db.find({setting_key: True}):
        try:
            c_id = entry.get("chat_id")
            if c_id:
                if CURRENT_DUA_STICKER: await app.send_sticker(c_id, CURRENT_DUA_STICKER)
                await app.send_message(c_id, text)
                await asyncio.sleep(1)
        except: continue

async def update_scheduler():
    await load_resources()
    times = await get_azan_times()
    if not times: return
    for job in scheduler.get_jobs():
        if job.id.startswith("azan_"): job.remove()
    for key in CURRENT_RESOURCES.keys():
        if key in times:
            t = times[key].split(" ")[0]
            h, m = map(int, t.split(":"))
            scheduler.add_job(broadcast_azan, "cron", hour=h, minute=m, args=[key], id=f"azan_{key}")

scheduler = AsyncIOScheduler(timezone="Africa/Cairo")
scheduler.add_job(update_scheduler, "cron", hour=0, minute=5)
scheduler.add_job(lambda: asyncio.create_task(send_duas_batch(MORNING_DUAS, "dua_active", "أذكار الصباح ☀️")), "cron", hour=7, minute=0)
scheduler.add_job(lambda: asyncio.create_task(send_duas_batch(NIGHT_DUAS, "night_dua_active", "أذكار المساء 🌌")), "cron", hour=20, minute=0)
if not scheduler.running: scheduler.start()
asyncio.get_event_loop().create_task(update_scheduler())

# ==========================================
# [ 5. لوحة التحكم (نصوص رسمية فقط) ]
# ==========================================

@app.on_message(filters.command(["اعدادات الاذان", "انلاين الاذان", "الاذان"], COMMAND_PREFIXES) & filters.group & ~BANNED_USERS, group=AZAN_GROUP)
async def azan_settings_entry(_, m):
    if not await check_rights(m.from_user.id, m.chat.id): return
    bot_user = (await app.get_me()).username
    link = f"https://t.me/{bot_user}?start=azset_{m.chat.id}"
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("اضغط هنا للدخول للاعدادات", url=link)]])
    await m.reply_text("<b>لإعداد الأذان، يرجى الضغط على الزر:</b>", reply_markup=kb)

@app.on_message(filters.regex("^/start azset_") & filters.private, group=AZAN_GROUP)
async def open_panel_private(_, m):
    try: target_cid = int(m.text.split("azset_")[1])
    except: return
    if not await check_rights(m.from_user.id, target_cid): return await m.reply("عذرا، لست مشرفا في ذلك الجروب.")
    await show_panel(m, target_cid)

async def show_panel(m, chat_id):
    doc = await get_chat_doc(chat_id)
    prayers = doc.get("prayers", {})
    kb = []
    
    # نصوص نظيفة تماماً بدون أي إيموجي نظام
    st_main = "〔 مفعل 〕" if doc.get("azan_active", True) else "〔 معطل 〕"
    kb.append([InlineKeyboardButton(f"الأذان العام ↢ {st_main}", callback_data=f"set_main_{chat_id}")])
    
    st_dua = "〔 مفعل 〕" if doc.get("dua_active", True) else "〔 معطل 〕"
    kb.append([InlineKeyboardButton(f"دعاء الصباح ↢ {st_dua}", callback_data=f"set_dua_{chat_id}")])
    
    st_ndua = "〔 مفعل 〕" if doc.get("night_dua_active", True) else "〔 معطل 〕"
    kb.append([InlineKeyboardButton(f"دعاء المساء ↢ {st_ndua}", callback_data=f"set_ndua_{chat_id}")])

    row = []
    for k, name in PRAYER_NAMES_AR.items():
        pst = "〔 مفعل 〕" if prayers.get(k, True) else "〔 معطل 〕"
        row.append(InlineKeyboardButton(f"{name} ↢ {pst}", callback_data=f"set_p_{k}_{chat_id}"))
        if len(row) == 2: kb.append(row); row = []
    if row: kb.append(row)
    
    kb.append([InlineKeyboardButton("• الاغلاق •", callback_data="close_panel")])
    text = f"<b>لوحة تحكم الأذان (للجروب {chat_id}) :</b>"
    if isinstance(m, Message): await m.reply_text(text, reply_markup=InlineKeyboardMarkup(kb))
    else: await m.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb))

@app.on_callback_query(filters.regex(r"^(set_|help_|close_)"), group=AZAN_GROUP)
async def cb_handler(_, q):
    data = q.data
    uid = q.from_user.id
    if data == "close_panel": return await q.message.delete()

    if data.startswith("set_"):
        parts = data.split("_")
        chat_id = int(parts[-1])
        if not await check_rights(uid, chat_id): return await q.answer("للمشرفين فقط", show_alert=True)
        doc = await get_chat_doc(chat_id)

        if "main" in data: await update_doc(chat_id, "azan_active", not doc.get("azan_active", True))
        elif "_dua_" in data: await update_doc(chat_id, "dua_active", not doc.get("dua_active", True))
        elif "ndua" in data: await update_doc(chat_id, "night_dua_active", not doc.get("night_dua_active", True))
        elif "_p_" in data:
            pkey = parts[2]
            current = doc.get("prayers", {}).get(pkey, True)
            await update_doc(chat_id, not current, sub_key=pkey)
        await show_panel(q, chat_id)
    
    elif data == "help_admin":
        text = "<b>اوامر المشرفين :</b>\n\n• <code>اعدادات الاذان</code>\n• <code>تفعيل الاذان</code>\n• <code>قفل الاذان</code>"
        await q.message.edit_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("رجوع", callback_data="help_back")]]))
    elif data == "help_dev":
        text = "<b>اوامر المطور :</b>\n\n• <code>تغيير استيكر الاذان</code>\n• <code>تغيير رابط الاذان</code>\n• <code>تغيير استيكر الدعاء</code>\n• <code>تفعيل الاذان الاجباري</code>"
        await q.message.edit_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("رجوع", callback_data="help_back")]]))
    elif data == "help_back":
        kb = InlineKeyboardMarkup([[InlineKeyboardButton("اوامر المشرفين", callback_data="help_admin"), InlineKeyboardButton("اوامر المطور", callback_data="help_dev")], [InlineKeyboardButton("• الاغلاق •", callback_data="close_panel")]])
        await q.message.edit_text("<b>اهلا بك يا مطوري في ازرار اوامر الاذان</b>", reply_markup=kb)

# ==========================================
# [ 6. أوامر المطور ]
# ==========================================

@app.on_message(filters.command(["اوامر الاذان"], COMMAND_PREFIXES) & ~BANNED_USERS, group=AZAN_GROUP)
async def azan_menu(_, m):
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("اوامر المشرفين", callback_data="help_admin"), InlineKeyboardButton("اوامر المطور", callback_data="help_dev")], [InlineKeyboardButton("• الاغلاق •", callback_data="close_panel")]])
    await m.reply_text("<b>اهلا بك يا مطوري في ازرار اوامر الاذان</b>", reply_markup=kb)

@app.on_message(filters.command(["تغيير استيكر الاذان", "تغيير رابط الاذان"], COMMAND_PREFIXES) & filters.user(REAL_OWNER_ID), group=AZAN_GROUP)
async def dev_select_prayer(_, m):
    ctype = "sticker" if "استيكر" in m.text else "link"
    kb = []
    row = []
    for k, n in PRAYER_NAMES_AR.items():
        row.append(InlineKeyboardButton(n, callback_data=f"devset_{ctype}_{k}"))
        if len(row) == 2: kb.append(row); row = []
    if row: kb.append(row)
    kb.append([InlineKeyboardButton("• الغاء •", callback_data="dev_cancel")])
    await m.reply(f"<b>اختر الصلاة التي تريد تغيير {('الاستيكر' if ctype=='sticker' else 'الرابط')} لها :</b>", reply_markup=InlineKeyboardMarkup(kb))

@app.on_message(filters.command("تغيير استيكر الدعاء", COMMAND_PREFIXES) & filters.user(REAL_OWNER_ID), group=AZAN_GROUP)
async def dev_dua_st(_, m):
    admin_state[m.from_user.id] = {"action": "wait_dua_sticker"}
    await m.reply("<b>ارسل الآن استيكر الدعاء الجديد :</b>")

@app.on_message(filters.command("تفعيل الاذان الاجباري", COMMAND_PREFIXES) & filters.user(REAL_OWNER_ID), group=AZAN_GROUP)
async def force_enable(_, m):
    msg = await m.reply("<b>جاري التفعيل...</b>")
    c = 0
    async for doc in settings_db.find({}):
        await settings_db.update_one({"_id": doc["_id"]}, {"$set": {"azan_active": True, "dua_active": True, "night_dua_active": True}})
        c += 1
    local_cache.clear()
    await msg.edit_text(f"<b>[ تم ] التفعيل في {c} مجموعة.</b>")

@app.on_callback_query(filters.regex(r"^(devset_|dev_cancel)"), group=AZAN_GROUP)
async def dev_cb(_, q):
    if q.data == "dev_cancel":
        if q.from_user.id in admin_state: del admin_state[q.from_user.id]
        return await q.message.delete()
    parts = q.data.split("_")
    atype, pkey = parts[1], parts[2]
    admin_state[q.from_user.id] = {"action": f"wait_azan_{atype}", "key": pkey}
    req = "استيكر" if atype == "sticker" else "رابط"
    await q.message.edit_text(f"<b>ارسل الآن {req} صلاة {PRAYER_NAMES_AR[pkey]} الجديد :</b>")

@app.on_message((filters.text | filters.sticker) & filters.user(REAL_OWNER_ID), group=AZAN_GROUP)
async def dev_input_wait(_, m):
    uid = m.from_user.id
    if uid not in admin_state: return
    state = admin_state[uid]
    action = state["action"]

    if action == "wait_dua_sticker":
        if not m.sticker: return await m.reply("استيكر فقط!")
        global CURRENT_DUA_STICKER
        CURRENT_DUA_STICKER = m.sticker.file_id
        await resources_db.update_one({"type": "dua_sticker"}, {"$set": {"sticker_id": CURRENT_DUA_STICKER}}, upsert=True)
        await m.reply("[ تم ] الحفظ.")
        del admin_state[uid]

    elif action.startswith("wait_azan_"): 
        pkey = state["key"]
        if "sticker" in action:
            if not m.sticker: return await m.reply("استيكر فقط!")
            CURRENT_RESOURCES[pkey]["sticker"] = m.sticker.file_id
            await resources_db.update_one({"type": "azan_data"}, {"$set": {f"data.{pkey}.sticker": m.sticker.file_id}}, upsert=True)
            await m.reply(f"[ تم ] تغيير استيكر {PRAYER_NAMES_AR[pkey]}.")
        else: # link
            if not m.text: return
            vid = extract_vidid(m.text)
            if not vid: return await m.reply("رابط يوتيوب خطأ!")
            CURRENT_RESOURCES[pkey]["link"] = m.text
            CURRENT_RESOURCES[pkey]["vidid"] = vid
            await resources_db.update_one({"type": "azan_data"}, {"$set": {f"data.{pkey}.link": m.text, f"data.{pkey}.vidid": vid}}, upsert=True)
            await m.reply(f"[ تم ] تغيير رابط {PRAYER_NAMES_AR[pkey]}.")
        del admin_state[uid]

@app.on_message(filters.command("تست اذان", COMMAND_PREFIXES) & filters.user(REAL_OWNER_ID), group=AZAN_GROUP)
async def tst(_, m):
    await start_azan_smart(m.chat.id, "Fajr")
