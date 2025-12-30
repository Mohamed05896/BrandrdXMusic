import asyncio
import random
import aiohttp
import re
import time
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from pyrogram import filters, enums
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from motor.motor_asyncio import AsyncIOMotorClient

import config
from config import BANNED_USERS, COMMAND_PREFIXES, MONGO_DB_URI, OWNER_ID
from BrandrdXMusic import app
# [هام جداً] استدعاء دالة الستريم ليدخل المساعد صوتياً
from BrandrdXMusic.utils.stream.stream import stream

# ==========================================
# [ 1. إعدادات النظام والمطورين ]
# ==========================================

MY_ID = 8313557781

if isinstance(OWNER_ID, list):
    DEVS = [int(x) for x in OWNER_ID]
else:
    DEVS = [int(OWNER_ID)]

if MY_ID not in DEVS:
    DEVS.append(MY_ID)

# نحتاج ايدي المالك لتمريره لدالة الستريم
STREAM_OWNER_ID = DEVS[0]

db_client = AsyncIOMotorClient(MONGO_DB_URI)
settings_db = db_client.BrandrdX.azan_final_pro_db
resources_db = db_client.BrandrdX.azan_resources_final_db

# قاعدة بيانات سجلات الأذان (للمراقبة)
azan_logs_db = db_client.BrandrdX.admin_system_v3_db.azan_logs

local_cache = {}
admin_state = {}
AZAN_GROUP = 57

# ==========================================
# [ 2. مكتبة الأذكار والأدعية (كاملة) ]
# ==========================================

MORNING_DUAS = [
    "اللهم بك أصبحنا، وبك أمسينا، وبك نحيا، وبك نموت، وإليك النشور 🤍",
    "أصبحنا وأصبح الملك لله، والحمد لله، لا إله إلا الله وحده لا شريك له، له الملك وله الحمد وهو على كل شيء قدير 🤎",
    "اللهم إني أسألك خير هذا اليوم، فتحه، ونصره، ونوره، وبركته، وهداه 🤍",
    "رضيت بالله رباً، وبالإسلام ديناً، وبمحمد صلى الله عليه وسلم نبياً 🤎",
    "يا حي يا قيوم برحمتك أستغيث، أصلح لي شأني كله ولا تكلني إلى نفسي طرفة عين 🤍",
    "اللهم أنت ربي لا إله إلا أنت، خلقتني وأنا عبدك، وأنا على عهدك ووعدك ما استطعت، أعوذ بك من شر ما صنعت، أبوء لك بنعمتك علي، وأبوء بذنبي فاغفر لي فإنه لا يغفر الذنوب إلا أنت 🤎",
    "اللهم إني أسألك علماً نافعاً، ورزقاً طيباً، وعملاً متقبلاً 🤍",
    "بسم الله الذي لا يضر مع اسمه شيء في الأرض ولا في السماء وهو السميع العليم 🤎",
    "اللهم عافني في بدني، اللهم عافني في سمعي، اللهم عافني في بصري، لا إله إلا أنت 🤍",
    "اللهم إني أسألك العفو والعافية في ديني ودنياي وأهلي ومالي 🤎",
    "أصبحنا على فطرة الإسلام، وعلى كلمة الإخلاص، وعلى دين نبينا محمد صلى الله عليه وسلم، وعلى ملة أبينا إبراهيم حنيفاً مسلماً وما كان من المشركين 🤍",
    "اللهم اجعل صباحنا هذا صباحاً مباركاً، تفتح لنا فيه أبواب رحمتك 🤎",
    "ربي أسألك في هذا الصباح أن تريح قلبي وفكري 🤍",
    "حسبي الله لا إله إلا هو، عليه توكلت وهو رب العرش العظيم (7 مرات) 🤎",
    "سبحان الله وبحمده عدد خلقه، ورضا نفسه، وزنة عرشه، ومداد كلماته 🤍",
    "لا إله إلا الله وحده لا شريك له، له الملك وله الحمد وهو على كل شيء قدير 🤎",
    "أستغفر الله وأتوب إليه 🤍",
    "اللهم عالم الغيب والشهادة، فاطر السماوات والأرض، رب كل شيء ومليكه، أشهد أن لا إله إلا أنت، أعوذ بك من شر نفسي ومن شر الشيطان وشركه 🤎"
]

NIGHT_DUAS = [
    "اللهم بك أمسينا، وبك أصبحنا، وبك نحيا، وبك نموت، وإليك المصير 🤎",
    "أمسينا وأمسى الملك لله، والحمد لله، لا إله إلا الله وحده لا شريك له، له الملك وله الحمد وهو على كل شيء قدير 🤍",
    "اللهم أنت ربي لا إله إلا أنت، خلقتني وأنا عبدك، وأنا على عهدك ووعدك ما استطعت، أعوذ بك من شر ما صنعت، أبوء لك بنعمتك علي، وأبوء بذنبي فاغفر لي فإنه لا يغفر الذنوب إلا أنت 🤎",
    "اللهم إني أسألك العفو والعافية في الدنيا والآخرة، اللهم إني أسألك العفو والعافية في ديني ودنياي وأهلي ومالي 🤍",
    "اللهم استر عوراتي وآمن روعاتي، اللهم احفظني من بين يدي ومن خلفي وعن يميني وعن شمالي ومن فوقي، وأعوذ بعظمتك أن أغتال من تحتي 🤎",
    "اللهم عافني في بدني، اللهم عافني في سمعي، اللهم عافني في بصري، لا إله إلا أنت 🤍",
    "اللهم إني أعوذ بك من الكفر والفقر، وأعوذ بك من عذاب القبر، لا إله إلا أنت 🤎",
    "حسبي الله لا إله إلا هو عليه توكلت وهو رب العرش العظيم 🤍",
    "بسم الله الذي لا يضر مع اسمه شيء في الأرض ولا في السماء وهو السميع العليم 🤎",
    "يا حي يا قيوم برحمتك أستغيث، أصلح لي شأني كله ولا تكلني إلى نفسي طرفة عين 🤍",
    "أمسينا على فطرة الإسلام، وعلى كلمة الإخلاص، وعلى دين نبينا محمد صلى الله عليه وسلم، وعلى ملة أبينا إبراهيم حنيفاً مسلماً وما كان من المشركين 🤎",
    "أعوذ بكلمات الله التامات من شر ما خلق 🤍",
    "لا إله إلا الله وحده لا شريك له، له الملك وله الحمد وهو على كل شيء قدير 🤎",
    "أستغفر الله وأتوب إليه 🤍",
    "اللهم قني عذابك يوم تبعث عبادك 🤎"
]

# ==========================================
# [ 3. الموارد والبيانات (روابط واستيكرات) ]
# ==========================================

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
# [ 4. دوال النظام المساعدة ]
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
        doc = {
            "chat_id": chat_id, 
            "azan_active": True, 
            "dua_active": True, 
            "night_dua_active": True, 
            "prayers": {k: True for k in CURRENT_RESOURCES.keys()}
        }
        await settings_db.insert_one(doc)
    local_cache[chat_id] = doc
    return doc

async def update_doc(chat_id, key, value, sub_key=None):
    if sub_key:
        await settings_db.update_one(
            {"chat_id": chat_id}, 
            {"$set": {f"prayers.{sub_key}": value}}, 
            upsert=True
        )
        if chat_id in local_cache:
            if "prayers" not in local_cache[chat_id]:
                local_cache[chat_id]["prayers"] = {}
            local_cache[chat_id]["prayers"][sub_key] = value
    else:
        await settings_db.update_one(
            {"chat_id": chat_id}, 
            {"$set": {key: value}}, 
            upsert=True
        )
        if chat_id in local_cache: 
            local_cache[chat_id][key] = value

async def check_rights(user_id, chat_id):
    if user_id in DEVS: return True
    try:
        mem = await app.get_chat_member(chat_id, user_id)
        if mem.status in [enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.OWNER]: return True
    except: pass
    return False

# ==========================================
# [ 5. نظام التشغيل ودخول المساعد (Stream Logic) ]
# ==========================================

async def start_azan_stream(chat_id, prayer_key):
    """
    الدالة الرئيسية لتشغيل الأذان
    تم فصل كود المراقبة لضمان عمل دالة stream دائماً
    """
    res = CURRENT_RESOURCES[prayer_key]
    
    # 1. إرسال الاستيكر
    try:
        await app.send_sticker(chat_id, res["sticker"])
    except: pass

    # 2. إرسال النص
    caption = f"<b>حان الآن موعد اذان {res['name']} 🤍</b>\n<b>بالتوقيت المحلي لمدينة القاهره 🕌🤎</b>"
    mystic = None
    try:
        mystic = await app.send_message(chat_id, caption)
    except:
        # إذا فشل إرسال الرسالة، لا يمكن الرد عليها لتشغيل الستريم، لذلك نخرج
        return

    # 3. [كود المراقبة المعزول]
    # محمي بـ Try/Except خاص به لكي لا يؤثر على تشغيل الصوت
    try:
        now = datetime.now()
        log_key = f"{chat_id}_{now.strftime('%Y-%m-%d_%H:%M')}" 
        
        # التأكد من عدم التكرار
        if not await azan_logs_db.find_one({"key": log_key}):
            await azan_logs_db.insert_one({
                "chat_id": chat_id,
                "chat_title": "مجموعة (تلقائي)",
                "date": now.strftime("%Y-%m-%d"),
                "time": now.strftime("%I:%M %p"),
                "timestamp": time.time(),
                "key": log_key
            })
    except Exception as e:
        # طباعة الخطأ في الكونسول فقط، والاستمرار في تشغيل الأذان
        print(f"[Azan Log Error]: {e}")

    # 4. إعداد بيانات الستريم
    fake_result = {
        "link": res["link"], 
        "vidid": res["vidid"], 
        "title": f"أذان {res['name']}", 
        "duration_min": "05:00", 
        "thumb": f"https://img.youtube.com/vi/{res['vidid']}/hqdefault.jpg"
    }
    
    _ = {
        "queue_4": "<b>🔢 الترتيب: #{}</b>", 
        "stream_1": "<b>🔘 جاري التشغيل...</b>", 
        "play_3": "<b>❌ فشل.</b>"
    }

    # 5. استدعاء دالة الستريم
    try:
        await stream(
            _, 
            mystic, 
            app.id, 
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

async def get_azan_times():
    try:
        timeout = aiohttp.ClientTimeout(total=10)
        async with aiohttp.ClientSession(timeout=timeout) as session:
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
            asyncio.create_task(start_azan_stream(c_id, prayer_key))
            await asyncio.sleep(0.5)

async def send_duas_batch(dua_list, setting_key, title):
    selected = random.sample(dua_list, min(4, len(dua_list)))
    text = f"<b>{title}</b>\n\n"
    for d in selected: text += f"• {d}\n\n"
    text += "<b>تقبـل اللـه منـا ومنكـم صالـح الاعمـال 🤎</b>"
    
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
scheduler.add_job(lambda: asyncio.create_task(send_duas_batch(MORNING_DUAS, "dua_active", "أذكـار الصبـاح")), "cron", hour=7, minute=0)
scheduler.add_job(lambda: asyncio.create_task(send_duas_batch(NIGHT_DUAS, "night_dua_active", "أذكـار المسـاء")), "cron", hour=20, minute=0)
if not scheduler.running: scheduler.start()
asyncio.get_event_loop().create_task(update_scheduler())

# ==========================================
# [ 6. أوامر المشرفين (تفعيل/قفل) ]
# ==========================================

# تفعيل الأذان (للمشرفين)
@app.on_message(filters.command("تفعيل الاذان", COMMAND_PREFIXES) & filters.group & ~BANNED_USERS, group=AZAN_GROUP)
async def admin_enable_azan(_, m):
    if not await check_rights(m.from_user.id, m.chat.id): return
    doc = await get_chat_doc(m.chat.id)
    if doc.get("azan_active"):
        return await m.reply_text("• الأمـر مـفعل بالفعل")
    await update_doc(m.chat.id, "azan_active", True)
    await m.reply_text("• تـم تـفـعـيـل الاذان بـنـجـاح 🤍")

# قفل الأذان (للمشرفين)
@app.on_message(filters.command("قفل الاذان", COMMAND_PREFIXES) & filters.group & ~BANNED_USERS, group=AZAN_GROUP)
async def admin_disable_azan(_, m):
    if not await check_rights(m.from_user.id, m.chat.id): return
    doc = await get_chat_doc(m.chat.id)
    if not doc.get("azan_active"):
        return await m.reply_text("• الأمـر مـفعل بالفعل")
    await update_doc(m.chat.id, "azan_active", False)
    await m.reply_text("•  تـم قـفـل الاذان بـنـجـاح")

# تفعيل الأذكار (للمشرفين)
@app.on_message(filters.command("تفعيل الاذكار", COMMAND_PREFIXES) & filters.group & ~BANNED_USERS, group=AZAN_GROUP)
async def admin_enable_duas(_, m):
    if not await check_rights(m.from_user.id, m.chat.id): return
    # تفعيل الصباح والمساء معا
    await update_doc(m.chat.id, "dua_active", True)
    await update_doc(m.chat.id, "night_dua_active", True)
    await m.reply_text("• تـم تـفـعـيـل الاذكـار (صباح/مساء) بـنـجـاح 🤍")

# قفل الأذكار (للمشرفين)
@app.on_message(filters.command("قفل الاذكار", COMMAND_PREFIXES) & filters.group & ~BANNED_USERS, group=AZAN_GROUP)
async def admin_disable_duas(_, m):
    if not await check_rights(m.from_user.id, m.chat.id): return
    # قفل الصباح والمساء معا
    await update_doc(m.chat.id, "dua_active", False)
    await update_doc(m.chat.id, "night_dua_active", False)
    await m.reply_text("• تـم قـفـل الاذكـار بـنـجـاح")

# ==========================================
# [ 7. لوحة التحكم (للمالك فقط) ]
# ==========================================

@app.on_message(filters.command(["اعدادات الاذان", "انلاين الاذان", "الاذان"], COMMAND_PREFIXES) & filters.group & ~BANNED_USERS, group=AZAN_GROUP)
async def azan_settings_entry(_, m):
    if m.from_user.id not in DEVS:
        return await m.reply_text("• الامـر مـتـاح فـقـط لـلــمـالـك الاسـاسـي")
        
    bot_user = (await app.get_me()).username
    link = f"https://t.me/{bot_user}?start=azset_{m.chat.id}"
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("اضغـط هنـا للدخـول للاعـدادات", url=link)]])
    await m.reply_text("<b>لإعـداد الأذان ، يرجـى الضغـط علـى الـزر :</b>", reply_markup=kb)

@app.on_message(filters.regex("^/start azset_") & filters.private, group=AZAN_GROUP)
async def open_panel_private(_, m):
    try: target_cid = int(m.text.split("azset_")[1])
    except: return
    
    if m.from_user.id not in DEVS: 
        return await m.reply("• الامـر مـتـاح فـقـط لـلــمـالـك الاسـاسـي")
    
    if not await check_rights(m.from_user.id, target_cid): return await m.reply("عـذرا ، لسـت مشرفـا فـي ذلـك الجـروب")
    await show_panel(m, target_cid)

async def show_panel(m, chat_id):
    if chat_id in local_cache: del local_cache[chat_id]
    doc = await get_chat_doc(chat_id)
    prayers = doc.get("prayers", {})
    if not prayers: prayers = {k: True for k in CURRENT_RESOURCES.keys()}
    
    kb = []
    
    st_main = "『 مـفعـل 』" if doc.get("azan_active", True) else "『 مـعطـل 』"
    kb.append([InlineKeyboardButton(f"الأذان العـام ↢ {st_main}", callback_data=f"set_main_{chat_id}")])
    
    st_dua = "『 مـفعـل 』" if doc.get("dua_active", True) else "『 مـعطـل 』"
    kb.append([InlineKeyboardButton(f"دعـاء الصبـاح ↢ {st_dua}", callback_data=f"set_dua_{chat_id}")])
    
    st_ndua = "『 مـفعـل 』" if doc.get("night_dua_active", True) else "『 مـعطـل 』"
    kb.append([InlineKeyboardButton(f"دعـاء المسـاء ↢ {st_ndua}", callback_data=f"set_ndua_{chat_id}")])

    row = []
    for k, name in PRAYER_NAMES_AR.items():
        is_active = prayers.get(k, True)
        pst = "『 مـفعـل 』" if is_active else "『 مـعطـل 』"
        row.append(InlineKeyboardButton(f"{name} ↢ {pst}", callback_data=f"set_p_{k}_{chat_id}"))
        if len(row) == 2: kb.append(row); row = []
    if row: kb.append(row)
    
    kb.append([InlineKeyboardButton("• الاغـلاق •", callback_data="close_panel")])
    text = f"<b>لوحـة تحكـم الأذان ( للجروب {chat_id} ) :</b>"
    
    try:
        if isinstance(m, Message): await m.reply_text(text, reply_markup=InlineKeyboardMarkup(kb))
        else: await m.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb))
    except: pass

# ==========================================
# [ 9. معالجة الكيبورد والردود ]
# ==========================================

@app.on_callback_query(filters.regex(r"^(set_|help_|close_|devset_|dev_cancel)"), group=AZAN_GROUP)
async def cb_handler(_, q):
    data = q.data
    uid = q.from_user.id
    
    if data == "close_panel": return await q.message.delete()

    if data.startswith("set_"):
        parts = data.split("_")
        
        if "_p_" in data:
            try:
                pkey = parts[2]
                chat_id = int(parts[3])
            except: return await q.answer("خطأ في البيانات", show_alert=True)

            if not await check_rights(uid, chat_id): return await q.answer("للمشرفيـن فقـط", show_alert=True)
            
            doc = await get_chat_doc(chat_id)
            prayers = doc.get("prayers", {})
            current_status = prayers.get(pkey, True)
            new_status = not current_status
            
            await update_doc(chat_id, new_status, new_status, sub_key=pkey)
            await show_panel(q, chat_id)
            return

        chat_id = int(parts[-1])
        if not await check_rights(uid, chat_id): return await q.answer("للمشرفيـن فقـط", show_alert=True)
        doc = await get_chat_doc(chat_id)

        if "main" in data: await update_doc(chat_id, "azan_active", not doc.get("azan_active", True))
        elif "_dua_" in data: await update_doc(chat_id, "dua_active", not doc.get("dua_active", True))
        elif "ndua" in data: await update_doc(chat_id, "night_dua_active", not doc.get("night_dua_active", True))
        
        await show_panel(q, chat_id)
    
    elif data == "help_admin":
        text = (
            "<b>اوامـر المشرفيـن :</b>\n\n"
            "• <code>اعدادات الاذان</code>\n"
            "• <code>تفعيل الاذان</code> | <code>قفل الاذان</code>\n"
            "• <code>تفعيل الاذكار</code> | <code>قفل الاذكار</code>"
        )
        kb = InlineKeyboardMarkup([[InlineKeyboardButton("رجـوع", callback_data="help_back")]])
        await q.message.edit_text(text, reply_markup=kb)

    elif data == "help_dev":
        text = (
            "<b>اوامـر المطـور :</b>\n\n"
            "• <code>تغيير استيكر الاذان</code> | <code>تغيير رابط الاذان</code>\n"
            "• <code>تغيير استيكر الدعاء</code>\n"
            "• <code>تفعيل الاذان الاجباري</code> | <code>قفل الاذان الاجباري</code>\n"
            "• <code>تفعيل الاذكار الاجباري</code> | <code>قفل الاذكار الاجباري</code>\n"
            "• <code>تست اذان</code>"
        )
        kb = InlineKeyboardMarkup([[InlineKeyboardButton("رجـوع", callback_data="help_back")]])
        await q.message.edit_text(text, reply_markup=kb)

    elif data == "help_back":
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("اوامـر المشرفيـن", callback_data="help_admin"), 
             InlineKeyboardButton("اوامـر المطـور", callback_data="help_dev")],
            [InlineKeyboardButton("• الاغـلاق •", callback_data="close_panel")]
        ])
        await q.message.edit_text("<b>اهـلا بـك فـي قائمـة اوامـر الاذان</b>", reply_markup=kb)

    elif data == "dev_cancel":
        if uid in admin_state: del admin_state[uid]
        return await q.message.delete()
    
    elif data.startswith("devset_"):
        if uid not in DEVS: return await q.answer("للمطوريـن فقـط", show_alert=True)
        parts = data.split("_")
        atype, pkey = parts[1], parts[2]
        admin_state[uid] = {"action": f"wait_azan_{atype}", "key": pkey}
        req = "استيكـر" if atype == "sticker" else "رابـط"
        await q.message.edit_text(f"<b>ارسـل الآن {req} صـلاة {PRAYER_NAMES_AR[pkey]} الجديـد 🤍 :</b>")

@app.on_message((filters.text | filters.sticker) & filters.user(DEVS), group=AZAN_GROUP)
async def dev_input_wait(_, m):
    uid = m.from_user.id
    if uid not in admin_state: return
    state = admin_state[uid]
    action = state["action"]

    if action == "wait_dua_sticker":
        if not m.sticker: return await m.reply("استيكـر فقـط")
        global CURRENT_DUA_STICKER
        CURRENT_DUA_STICKER = m.sticker.file_id
        await resources_db.update_one({"type": "dua_sticker"}, {"$set": {"sticker_id": CURRENT_DUA_STICKER}}, upsert=True)
        await m.reply("تـم الحفـظ 🤍")
        del admin_state[uid]

    elif action.startswith("wait_azan_"): 
        pkey = state["key"]
        if "sticker" in action:
            if not m.sticker: return await m.reply("استيكـر فقـط")
            CURRENT_RESOURCES[pkey]["sticker"] = m.sticker.file_id
            await resources_db.update_one({"type": "azan_data"}, {"$set": {f"data.{pkey}.sticker": m.sticker.file_id}}, upsert=True)
            await m.reply(f"تـم تغييـر استيكـر {PRAYER_NAMES_AR[pkey]} 🤍")
        else: # link
            if not m.text: return
            vid = extract_vidid(m.text)
            if not vid: return await m.reply("رابـط يوتيـوب خطـأ")
            CURRENT_RESOURCES[pkey]["link"] = m.text
            CURRENT_RESOURCES[pkey]["vidid"] = vid
            await resources_db.update_one({"type": "azan_data"}, {"$set": {f"data.{pkey}.link": m.text, f"data.{pkey}.vidid": vid}}, upsert=True)
            await m.reply(f"تـم تغييـر رابـط {PRAYER_NAMES_AR[pkey]} 🤍")
        del admin_state[uid]

# أوامر المطور (DEVS) فقط

@app.on_message(filters.command("تست اذان", COMMAND_PREFIXES) & filters.user(DEVS), group=AZAN_GROUP)
async def tst(_, m):
    msg = await m.reply("<b>جـاري تشغيـل تجربـة الأذان (ستريم)...</b>")
    await start_azan_stream(m.chat.id, "Fajr")
    await msg.delete()

@app.on_message(filters.command("تفعيل الاذان الاجباري", COMMAND_PREFIXES) & filters.user(DEVS), group=AZAN_GROUP)
async def force_enable(_, m):
    msg = await m.reply("<b>جـاري التفعيـل والبـث...</b>")
    c = 0
    async for doc in settings_db.find({}):
        chat_id = doc.get("chat_id")
        await settings_db.update_one({"_id": doc["_id"]}, {"$set": {"azan_active": True}})
        try:
            await app.send_message(chat_id, "<b>تـم تـفـعـيـل بـث الاذان الاجـبـاري من قـبـل المطور 🤍</b>")
        except: pass
        c += 1
    local_cache.clear()
    await msg.edit_text(f"<b>تـم التفعيـل العـام فـي {c} مجموعـة 🤍</b>")

@app.on_message(filters.command("قفل الاذان الاجباري", COMMAND_PREFIXES) & filters.user(DEVS), group=AZAN_GROUP)
async def force_disable(_, m):
    msg = await m.reply("<b>جـاري القفـل العـام...</b>")
    c = 0
    async for doc in settings_db.find({}):
        await settings_db.update_one({"_id": doc["_id"]}, {"$set": {"azan_active": False}})
        c += 1
    local_cache.clear()
    await msg.edit_text(f"<b>تـم قفـل الأذان فـي {c} مجموعـة</b>")

@app.on_message(filters.command("تفعيل الاذكار الاجباري", COMMAND_PREFIXES) & filters.user(DEVS), group=AZAN_GROUP)
async def force_enable_duas(_, m):
    msg = await m.reply("<b>جـاري تفعيل الأذكار للجميع...</b>")
    c = 0
    async for doc in settings_db.find({}):
        await settings_db.update_one({"_id": doc["_id"]}, {"$set": {"dua_active": True, "night_dua_active": True}})
        c += 1
    local_cache.clear()
    await msg.edit_text(f"<b>تـم تفعيل الأذكار (صباح/مساء) فـي {c} مجموعـة 🤍</b>")

@app.on_message(filters.command("قفل الاذكار الاجباري", COMMAND_PREFIXES) & filters.user(DEVS), group=AZAN_GROUP)
async def force_disable_duas(_, m):
    msg = await m.reply("<b>جـاري قفل الأذكار للجميع...</b>")
    c = 0
    async for doc in settings_db.find({}):
        await settings_db.update_one({"_id": doc["_id"]}, {"$set": {"dua_active": False, "night_dua_active": False}})
        c += 1
    local_cache.clear()
    await msg.edit_text(f"<b>تـم قفل الأذكار فـي {c} مجموعـة</b>")
