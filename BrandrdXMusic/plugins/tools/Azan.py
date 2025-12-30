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

if isinstance(OWNER_ID, list):
    DEVS = [int(x) for x in OWNER_ID]
elif isinstance(OWNER_ID, int):
    DEVS = [OWNER_ID]
else:
    try:
        DEVS = [int(OWNER_ID)]
    except:
        DEVS = []

db_client = AsyncIOMotorClient(MONGO_DB_URI)
settings_db = db_client.BrandrdX.azan_final_pro_db
resources_db = db_client.BrandrdX.azan_resources_final_db
azan_logs_db = db_client.BrandrdX.admin_system_v3_db.azan_logs

local_cache = {}
admin_state = {}
AZAN_GROUP = 57

MORNING_DUAS = [
    "اللهم بك أصبحنا، وبك أمسينا، وبك نحيا، وبك نموت، وإليك النشور 🤍",
    "أصبحنا وأصبح الملك لله، والحمد لله، لا إله إلا الله وحده لا شريك له 🤎",
    "اللهم إني أسألك خير هذا اليوم، فتحه، ونصره، ونوره، وبركته، وهداه 💕",
    "رضيت بالله رباً، وبالإسلام ديناً، وبمحمد صلى الله عليه وسلم نبياً 🤍",
    "يا حي يا قيوم برحمتك أستغيث، أصلح لي شأني كله ولا تكلني إلى نفسي طرفة عين 🤎",
    "اللهم أنت ربي لا إله إلا أنت، خلقتني وأنا عبدك، وأنا على عهدك ووعدك ما استطعت 💕",
    "اللهم إني أسألك علماً نافعاً، ورزقاً طيباً، وعملاً متقبلاً 🤍",
    "بسم الله الذي لا يضر مع اسمه شيء في الأرض ولا في السماء وهو السميع العليم 🤎",
    "اللهم عافني في بدني، اللهم عافني في سمعي، اللهم عافني في بصري 💕",
    "اللهم إني أسألك العفو والعافية في ديني ودنياي وأهلي ومالي 🤍",
    "أصبحنا على فطرة الإسلام، وعلى كلمة الإخلاص، وعلى دين نبينا محمد 🤎",
    "اللهم اجعل صباحنا هذا صباحاً مباركاً، تفتح لنا فيه أبواب رحمتك 💕",
    "ربي أسألك في هذا الصباح أن تريح قلبي وفكري 🤍",
    "حسبي الله لا إله إلا هو، عليه توكلت وهو رب العرش العظيم (7 مرات) 🤎"
]

NIGHT_DUAS = [
    "اللهم بك أمسينا، وبك أصبحنا، وبك نحيا، وبك نموت، وإليك المصير 🤍",
    "أمسينا وأمسى الملك لله، والحمد لله، لا إله إلا الله وحده لا شريك له 🤎",
    "اللهم أنت ربي لا إله إلا أنت، خلقتني وأنا عبدك، وأنا على عهدك ووعدك ما استطعت 💕",
    "اللهم إني أسألك العفو والعافية في الدنيا والآخرة 🤍",
    "اللهم استر عوراتي وآمن روعاتي، اللهم احفظني من بين يدي ومن خلفي 🤎",
    "اللهم عافني في بدني، اللهم عافني في سمعي، اللهم عافني في بصري 💕",
    "اللهم إني أعوذ بك من الكفر والفقر، وأعوذ بك من عذاب القبر 🤍",
    "حسبي الله لا إله إلا هو عليه توكلت وهو رب العرش العظيم 🤎",
    "بسم الله الذي لا يضر مع اسمه شيء في الأرض ولا في السماء 💕",
    "يا حي يا قيوم برحمتك أستغيث، أصلح لي شأني كله ولا تكلني إلى نفسي طرفة عين 🤍",
    "أمسينا على فطرة الإسلام، وعلى كلمة الإخلاص، وعلى دين نبينا محمد 🤎"
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
PRAYER_NAMES_AR = {"Fajr": "الفجر", "Dhuhr": "الظهر", "Asr": "العصر", "Maghrib": "المغرب", "Isha": "العشاء"}

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
            "kb_active": True, 
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

async def start_azan_stream(chat_id, prayer_key, force_test=False):
    res = CURRENT_RESOURCES[prayer_key]
    
    try:
        if res.get("sticker"):
            await app.send_sticker(chat_id, res["sticker"])
    except: pass

    caption = f"<b>حان الآن موعد اذان {res['name']} 🤍</b>\n<b>بالتوقيت المحلي لمدينة القاهره 🕌🤎</b>"
    
    try:
        await app.send_message(chat_id, caption)
    except:
        return

    try:
        now = datetime.now()
        log_key = f"{chat_id}_{now.strftime('%Y-%m-%d_%H:%M')}" 
        if not await azan_logs_db.find_one({"key": log_key}):
            await azan_logs_db.insert_one({
                "chat_id": chat_id,
                "chat_title": "مجموعة",
                "date": now.strftime("%Y-%m-%d"),
                "time": now.strftime("%I:%M %p"),
                "timestamp": time.time(),
                "key": log_key
            })
    except Exception as e:
        print(f"[Azan Log Error]: {e}")

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
            asyncio.create_task(start_azan_stream(c_id, prayer_key, force_test=False))
            await asyncio.sleep(2)

async def send_duas_batch(dua_list, setting_key, title):
    selected = random.sample(dua_list, min(4, len(dua_list)))
    text = f"<b>{title}</b>\n\n"
    for d in selected: text += f"• {d}\n\n"
    text += "<b>تقبل الله منا ومنكم صالح الاعمال</b>"
    
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
scheduler.add_job(lambda: asyncio.create_task(send_duas_batch(MORNING_DUAS, "dua_active", "أذكار الصباح")), "cron", hour=7, minute=0)
scheduler.add_job(lambda: asyncio.create_task(send_duas_batch(NIGHT_DUAS, "night_dua_active", "أذكار المساء")), "cron", hour=20, minute=0)
if not scheduler.running: scheduler.start()
asyncio.get_event_loop().create_task(update_scheduler())

@app.on_message(filters.command("تفعيل الاذان", COMMAND_PREFIXES) & filters.group & ~BANNED_USERS, group=AZAN_GROUP)
async def admin_enable_azan(_, m):
    if not await check_rights(m.from_user.id, m.chat.id): return
    doc = await get_chat_doc(m.chat.id)
    if doc.get("azan_active"): return await m.reply_text("الاذان مفعل بالفعل 🤍")
    await update_doc(m.chat.id, "azan_active", True)
    await m.reply_text("تم تفعيل الاذان بنجاح 🤍")

@app.on_message(filters.command("قفل الاذان", COMMAND_PREFIXES) & filters.group & ~BANNED_USERS, group=AZAN_GROUP)
async def admin_disable_azan(_, m):
    if not await check_rights(m.from_user.id, m.chat.id): return
    doc = await get_chat_doc(m.chat.id)
    if not doc.get("azan_active"): return await m.reply_text("الاذان معطل بالفعل 🤎")
    await update_doc(m.chat.id, "azan_active", False)
    await m.reply_text("تم قفل الاذان بنجاح 🤎")

@app.on_message(filters.command("تفعيل الاذكار", COMMAND_PREFIXES) & filters.group & ~BANNED_USERS, group=AZAN_GROUP)
async def admin_enable_duas(_, m):
    if not await check_rights(m.from_user.id, m.chat.id): return
    await update_doc(m.chat.id, "dua_active", True)
    await update_doc(m.chat.id, "night_dua_active", True)
    await m.reply_text("تم تفعيل الاذكار بنجاح 💕")

@app.on_message(filters.command("قفل الاذكار", COMMAND_PREFIXES) & filters.group & ~BANNED_USERS, group=AZAN_GROUP)
async def admin_disable_duas(_, m):
    if not await check_rights(m.from_user.id, m.chat.id): return
    await update_doc(m.chat.id, "dua_active", False)
    await update_doc(m.chat.id, "night_dua_active", False)
    await m.reply_text("تم قفل الاذكار بنجاح 🤎")

@app.on_message(filters.command(["اعدادات الاذان", "انلاين الاذان", "الاذان", "أوامر الاذان", "اوامر الاذان"], COMMAND_PREFIXES) & filters.group & ~BANNED_USERS, group=AZAN_GROUP)
async def azan_commands_panel(_, m):
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("أوامر المالك", callback_data="cmd_owner")],
        [InlineKeyboardButton("أوامر المشرفين", callback_data="cmd_admin")],
        [InlineKeyboardButton("• اغــلاق •", callback_data="cmd_close")]
    ])
    await m.reply_text("<b>مرحباً بك في قائمة أوامر الأذان</b>\n<b>اختر القائمة المناسبة لرتبتك:</b>", reply_markup=kb)

@app.on_message(filters.regex("^/start azset_") & filters.private, group=AZAN_GROUP)
async def open_panel_private(_, m):
    try: target_cid = int(m.text.split("azset_")[1])
    except: return
    if not await check_rights(m.from_user.id, target_cid): return await m.reply("عذرا لست مشرفا في ذلك الجروب")
    await show_panel(m, target_cid)

async def show_panel(m, chat_id):
    if chat_id in local_cache: del local_cache[chat_id]
    doc = await get_chat_doc(chat_id)
    prayers = doc.get("prayers", {})
    if not prayers: prayers = {k: True for k in CURRENT_RESOURCES.keys()}
    
    kb = []
    
    st_main = "『 مــفــعــل 』" if doc.get("azan_active", True) else "『 مــعــطــل 』"
    kb.append([InlineKeyboardButton(f"الاذان العام : {st_main}", callback_data=f"set_main_{chat_id}")])
    
    st_dua = "『 مــفــعــل 』" if doc.get("dua_active", True) else "『 مــعــطــل 』"
    kb.append([InlineKeyboardButton(f"دعاء الصباح : {st_dua}", callback_data=f"set_dua_{chat_id}")])
    
    st_ndua = "『 مــفــعــل 』" if doc.get("night_dua_active", True) else "『 مــعــطــل 』"
    kb.append([InlineKeyboardButton(f"دعاء المساء : {st_ndua}", callback_data=f"set_ndua_{chat_id}")])

    row = []
    for k, name in PRAYER_NAMES_AR.items():
        is_active = prayers.get(k, True)
        pst = "『 مــفــعــل 』" if is_active else "『 مــعــطــل 』"
        row.append(InlineKeyboardButton(f"{name} : {pst}", callback_data=f"set_p_{k}_{chat_id}"))
        if len(row) == 2: kb.append(row); row = []
    if row: kb.append(row)

    kb.append([InlineKeyboardButton("تجربة الاذان (تست)", callback_data=f"test_azan_{chat_id}")])
    kb.append([InlineKeyboardButton("اغلاق", callback_data="close_panel")])
    text = f"<b>لوحة تحكم الأذان ( للجروب {chat_id} ) :</b>"
    
    try:
        if isinstance(m, Message): await m.reply_text(text, reply_markup=InlineKeyboardMarkup(kb))
        else: await m.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb))
    except: pass

@app.on_callback_query(filters.regex(r"^(set_|help_|close_|devset_|dev_cancel|test_azan|cmd_)"), group=AZAN_GROUP)
async def cb_handler(_, q):
    data = q.data
    uid = q.from_user.id
    
    if data == "cmd_close":
        return await q.message.delete()
        
    if data == "cmd_back_main":
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("أوامر المالك", callback_data="cmd_owner")],
            [InlineKeyboardButton("أوامر المشرفين", callback_data="cmd_admin")],
            [InlineKeyboardButton("• اغــلاق •", callback_data="cmd_close")]
        ])
        return await q.edit_message_text("<b>مرحباً بك في قائمة أوامر الأذان</b>\n<b>اختر القائمة المناسبة لرتبتك:</b>", reply_markup=kb)

    if data == "cmd_owner":
        if uid not in DEVS:
            return await q.answer("• الامـر مـتـاح فـقـط لـلــمـالـك الاسـاسـي", show_alert=True)
        
        text = (
            "<b>قائمة أوامر المالك:</b>\n\n"
            "• <code>تغيير استيكر الاذان</code>\n"
            "• <code>تست اذان</code> (تجربة البث)\n"
            "• <code>تست اذان نصي</code> (تجربة الرسالة فقط)\n"
            "• <code>تفعيل الاذان الاجباري</code>"
        )
        kb = InlineKeyboardMarkup([[InlineKeyboardButton("رجوع", callback_data="cmd_back_main")]])
        return await q.edit_message_text(text, reply_markup=kb)

    if data == "cmd_admin":
        if not await check_rights(uid, q.message.chat.id):
            return await q.answer("• الامـر مـتـاح فـقـط لـلـمـشـرفـيـن فـقـط 💕", show_alert=True)
            
        bot_username = (await app.get_me()).username
        settings_link = f"https://t.me/{bot_username}?start=azset_{q.message.chat.id}"
        
        text = (
            "<b>قائمة أوامر المشرفين:</b>\n\n"
            "• <code>تفعيل الاذان</code>\n"
            "• <code>قفل الاذان</code>\n"
            "• <code>تفعيل الاذكار</code>\n"
            "• <code>قفل الاذكار</code>\n"
            "• <code>اعدادات الاذان</code> (لفتح لوحة التحكم)"
        )
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("الاعدادات الانلاين", url=settings_link)],
            [InlineKeyboardButton("رجوع", callback_data="cmd_back_main")]
        ])
        return await q.edit_message_text(text, reply_markup=kb)

    if data == "close_panel": return await q.message.delete()

    if data.startswith("test_azan_"):
        chat_id = int(data.split("_")[2])
        if not await check_rights(uid, chat_id): return await q.answer("للمشرفين فقط", show_alert=True)
        if uid not in DEVS:
             return await q.answer("• الأمـر مـحـدود فـقـط لـلــمـالـك الاسـاسـي والـمـشـرف 🤎", show_alert=True)

        await q.answer("جاري الارسال...", show_alert=False)
        await start_azan_stream(chat_id, "Fajr", force_test=True)
        return

    if data.startswith("set_"):
        parts = data.split("_")
        if "_p_" in data:
            try:
                pkey = parts[2]
                chat_id = int(parts[3])
            except: return await q.answer("خطأ", show_alert=True)
            if not await check_rights(uid, chat_id): return await q.answer("للمشرفين فقط", show_alert=True)
            doc = await get_chat_doc(chat_id)
            prayers = doc.get("prayers", {})
            new_status = not prayers.get(pkey, True)
            await update_doc(chat_id, new_status, new_status, sub_key=pkey)
            await show_panel(q, chat_id)
            return

        chat_id = int(parts[-1])
        if not await check_rights(uid, chat_id): return await q.answer("للمشرفين فقط", show_alert=True)
        doc = await get_chat_doc(chat_id)

        if "main" in data: await update_doc(chat_id, "azan_active", not doc.get("azan_active", True))
        elif "_dua_" in data: await update_doc(chat_id, "dua_active", not doc.get("dua_active", True))
        elif "ndua" in data: await update_doc(chat_id, "night_dua_active", not doc.get("night_dua_active", True))
        
        await show_panel(q, chat_id)
    
    elif data == "dev_cancel":
        if uid in admin_state: del admin_state[uid]
        return await q.message.delete()
    
    elif data.startswith("devset_"):
        if uid not in DEVS: return await q.answer("للمطورين فقط", show_alert=True)
        parts = data.split("_")
        atype, pkey = parts[1], parts[2]
        admin_state[uid] = {"action": f"wait_azan_{atype}", "key": pkey}
        req = "استيكر" if atype == "sticker" else "رابط"
        await q.message.edit_text(f"<b>ارسل الان {req} صلاة {PRAYER_NAMES_AR[pkey]} :</b>")

@app.on_message((filters.text | filters.sticker) & filters.user(DEVS), group=AZAN_GROUP)
async def dev_input_wait(_, m):
    uid = m.from_user.id
    if uid not in admin_state: return
    state = admin_state[uid]
    action = state["action"]

    if action == "wait_dua_sticker":
        if not m.sticker: return await m.reply("استيكر فقط")
        global CURRENT_DUA_STICKER
        CURRENT_DUA_STICKER = m.sticker.file_id
        await resources_db.update_one({"type": "dua_sticker"}, {"$set": {"sticker_id": CURRENT_DUA_STICKER}}, upsert=True)
        await m.reply("تم الحفظ 💕")
        del admin_state[uid]

    elif action.startswith("wait_azan_"): 
        pkey = state["key"]
        if "sticker" in action:
            if not m.sticker: return await m.reply("استيكر فقط")
            CURRENT_RESOURCES[pkey]["sticker"] = m.sticker.file_id
            await resources_db.update_one({"type": "azan_data"}, {"$set": {f"data.{pkey}.sticker": m.sticker.file_id}}, upsert=True)
            await m.reply(f"تم التغيير 💕")
        else:
            if not m.text: return
            vid = extract_vidid(m.text)
            if not vid: return await m.reply("رابط خطأ")
            CURRENT_RESOURCES[pkey]["link"] = m.text
            CURRENT_RESOURCES[pkey]["vidid"] = vid
            await resources_db.update_one({"type": "azan_data"}, {"$set": {f"data.{pkey}.link": m.text, f"data.{pkey}.vidid": vid}}, upsert=True)
            await m.reply(f"تم التغيير 💕")
        del admin_state[uid]

@app.on_message(filters.regex("^تست اذان$") & filters.group, group=AZAN_GROUP)
async def tst(client, message):
    user_id = message.from_user.id
    if user_id not in DEVS:
        return await message.reply("• الأمـر مـحـدود فـقـط لـلــمـالـك الاسـاسـي والـمـشـرف 🤎")

    chat_id = message.chat.id
    msg = await message.reply(f"<b>أهلاً بك عزيزي المطور/المشرف</b>\n<b>جـاري تشغيـل الأذان التجريبي...</b>")
    try:
        await start_azan_stream(chat_id, "Fajr", force_test=True)
        await msg.edit_text("<b>تم إرسال أمر التشغيل للمساعد 💕</b>")
    except Exception as e:
        await msg.edit_text(f"<b>حدث خطأ:</b>\n`{e}`")

@app.on_message(filters.regex("^تست اذان نصي$") & filters.group, group=AZAN_GROUP)
async def text_azan_test(client, message):
    user_id = message.from_user.id
    if user_id not in DEVS:
        return await message.reply("• الأمـر مـحـدود فـقـط لـلــمـالـك الاسـاسـي والـمـشـرف 🤎")
    
    chat_id = message.chat.id
    await message.reply("<b>جاري تجربة الأذان (نصي فقط)...</b>")
    res = CURRENT_RESOURCES["Fajr"]
    try: await app.send_sticker(chat_id, res["sticker"])
    except: pass
    await app.send_message(chat_id, f"<b>حان الآن موعد اذان {res['name']} 🤍</b>\n<b>بالتوقيت المحلي لمدينة القاهره 🕌🤎</b>")

@app.on_message(filters.command("تفعيل الاذان الاجباري", COMMAND_PREFIXES) & filters.user(DEVS), group=AZAN_GROUP)
async def force_enable(_, m):
    msg = await m.reply("<b>جاري التفعيل...</b>")
    c = 0
    async for doc in settings_db.find({}):
        chat_id = doc.get("chat_id")
        await settings_db.update_one({"_id": doc["_id"]}, {"$set": {"azan_active": True}})
        try: await app.send_message(chat_id, "<b>تم تفعيل بث الاذان الاجباري من قبل المطور</b>")
        except: pass
        c += 1
    local_cache.clear()
    await msg.edit_text(f"<b>تم التفعيل في {c} مجموعة 💕</b>")

@app.on_message(filters.command("قفل الاذان الاجباري", COMMAND_PREFIXES) & filters.user(DEVS), group=AZAN_GROUP)
async def force_disable(_, m):
    msg = await m.reply("<b>جاري القفل...</b>")
    c = 0
    async for doc in settings_db.find({}):
        await settings_db.update_one({"_id": doc["_id"]}, {"$set": {"azan_active": False}})
        c += 1
    local_cache.clear()
    await msg.edit_text(f"<b>تم القفل في {c} مجموعة 🤎</b>")

@app.on_message(filters.command("تفعيل الاذكار الاجباري", COMMAND_PREFIXES) & filters.user(DEVS), group=AZAN_GROUP)
async def force_enable_duas(_, m):
    msg = await m.reply("<b>جاري التفعيل...</b>")
    c = 0
    async for doc in settings_db.find({}):
        await settings_db.update_one({"_id": doc["_id"]}, {"$set": {"dua_active": True, "night_dua_active": True}})
        c += 1
    local_cache.clear()
    await msg.edit_text(f"<b>تم التفعيل في {c} مجموعة 💕</b>")

@app.on_message(filters.command("قفل الاذكار الاجباري", COMMAND_PREFIXES) & filters.user(DEVS), group=AZAN_GROUP)
async def force_disable_duas(_, m):
    msg = await m.reply("<b>جاري القفل...</b>")
    c = 0
    async for doc in settings_db.find({}):
        await settings_db.update_one({"_id": doc["_id"]}, {"$set": {"dua_active": False, "night_dua_active": False}})
        c += 1
    local_cache.clear()
    await msg.edit_text(f"<b>تم القفل في {c} مجموعة 🤎</b>")

@app.on_message(filters.regex("^فحص الاذان$"), group=1)
async def debug_azan_file(client, message):
    debug_text = "**النظام يعمل بشكل جيد 🤍**\n"
    msg = await message.reply_text(debug_text)
