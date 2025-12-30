import asyncio
import aiohttp
import random
import re
import time
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from pyrogram import enums
from BrandrdXMusic import app
from BrandrdXMusic.utils.stream.stream import stream

# استدعاء المتغيرات من ملف az_conf
from .az_conf import (
    settings_db, resources_db, azan_logs_db, local_cache, 
    CURRENT_RESOURCES, CURRENT_DUA_STICKER, DEVS, 
    MORNING_DUAS, NIGHT_DUAS
)

# --- [ الدوال المساعدة ] ---

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
            "forced_active": False,
            "dua_active": True,
            "forced_dua_active": False,
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

# --- [ دالة تشغيل الأذان ] ---
async def start_azan_stream(chat_id, prayer_key, force_test=False):
    res = CURRENT_RESOURCES[prayer_key]
    
    fake_result = {
        "link": res["link"], 
        "vidid": res["vidid"], 
        "title": f"أذان {res['name']}", 
        "duration_min": "05:00", 
        "thumb": f"https://img.youtube.com/vi/{res['vidid']}/hqdefault.jpg"
    }
    
    _ = {"queue_4": "<b>🔢 الترتيب: #{}</b>", "stream_1": "<b>🔘 جاري التشغيل...</b>", "play_3": "<b>❌ فشل.</b>"}

    try:
        if res.get("sticker"):
            await app.send_sticker(chat_id, res["sticker"])
    except: pass

    caption = f"<b>حان الآن موعد اذان {res['name']}</b>\n<b>بالتوقيت المحلي لمدينة القاهره 🕌</b>"
    
    try:
        mystic = await app.send_message(chat_id, caption)
        try:
            await stream(_, mystic, app.id, fake_result, chat_id, "خدمة الأذان", chat_id, video=False, streamtype="youtube", forceplay=True)
        except Exception as e:
            if "CLOSE_BUTTON" in str(e) or "EditMessage" in str(e):
                return
            if force_test:
                await app.send_message(chat_id, f"خطأ غير متوقع في الستريم: {e}")
            
    except Exception as e:
        if force_test:
            try: await app.send_message(chat_id, f"خطأ في الارسال: {e}")
            except: pass
        return

    if not force_test:
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
        except: pass

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
            await asyncio.sleep(3)

async def send_duas_batch(dua_list, setting_key, title, target_chat_id=None):
    selected = random.sample(dua_list, min(4, len(dua_list)))
    dua_emojis = ["💕", "🤍", "🤎"]
    text = f"<b>{title}</b>\n\n"
    for d in selected: 
        emo = random.choice(dua_emojis)
        text += f"• {d} {emo}\n\n"
    text += "<b>تقبل الله منا ومنكم صالح الاعمال</b>"
    
    if target_chat_id:
        if CURRENT_DUA_STICKER: await app.send_sticker(target_chat_id, CURRENT_DUA_STICKER)
        await app.send_message(target_chat_id, text)
        return

    async for entry in settings_db.find({setting_key: True}):
        try:
            c_id = entry.get("chat_id")
            if c_id:
                if CURRENT_DUA_STICKER: await app.send_sticker(c_id, CURRENT_DUA_STICKER)
                await app.send_message(c_id, text)
                await asyncio.sleep(2)
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

# --- [ إعداد المجدول ] ---
scheduler = AsyncIOScheduler(timezone="Africa/Cairo")
scheduler.add_job(update_scheduler, "cron", hour=0, minute=5)
scheduler.add_job(lambda: asyncio.create_task(send_duas_batch(MORNING_DUAS, "dua_active", "أذكار الصباح")), "cron", hour=7, minute=0)
scheduler.add_job(lambda: asyncio.create_task(send_duas_batch(NIGHT_DUAS, "night_dua_active", "أذكار المساء")), "cron", hour=20, minute=0)
if not scheduler.running: scheduler.start()
asyncio.get_event_loop().create_task(update_scheduler())
