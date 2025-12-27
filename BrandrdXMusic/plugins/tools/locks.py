import asyncio
import re
import requests
import os
from datetime import datetime, timedelta
from pyrogram import filters, enums
from pyrogram.types import Message, ChatPermissions, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from fuzzywuzzy import fuzz
from BrandrdXMusic import app
from BrandrdXMusic.misc import SUDOERS 

# --- [ 1. إعـدادات الـبـيـانـات والـمـخـازن ] ---

API_USER = "1800965377"
API_SECRET = "pp32KRVBbfQjJXqLYoah7goaU949hwjU"

# مخازن البيانات لضمان السرعة القصوى في الرد والحماية
smart_db = {}       # لتخزين حالات الأقفال (قفل/فتح)
warns_db = {}       # لسجل تحذيرات الأعضاء في كل مجموعة
max_warns = {}      # لتحديد سقف التحذيرات العادية بواسطة المشرفين

# قاموس الربط بين الأوامر النصية والمفاتيح البرمجية
LOCK_MAP = {
    "الروابط": "links",
    "المعرفات": "usernames",
    "التاك": "hashtags",
    "الشارحه": "slashes",
    "التثبيت": "pin",
    "المتحركه": "animations",
    "الشات": "all",
    "الصور": "photos",
    "الملصقات": "stickers",
    "الملفات": "docs",
    "البوتات": "bots",
    "التكرار": "flood",
    "الكلايش": "long_msgs",
    "الانلاين": "inline",
    "الفيديو": "videos",
    "البصمات": "voice",
    "السيلفي": "video_notes",
    "الماركدوان": "markdown",
    "التوجيه": "forward",
    "الاغاني": "audio",
    "الصوت": "voice",
    "الجهات": "contacts",
    "الاشعارات": "service",
    "السب": "porn_text",
    "الاباحي": "porn_media"
}

# قائمة الكلمات المحظورة لفحص السب والشتائم
BAD_WORDS = ["سكس", "نيك", "شرموط", "منيوك", "كسمك", "زب", "فحل", "بورن", "متناك", "مص", "كس", "طيز", "قحبه", "فاجره", "احاا", "متناكه", "خول"]

# --- [ 2. الـدوال الـمـسـاعـدة والـفـحـص ] ---

async def has_permission(chat_id, user_id):
    """الـتـحـقـق مـن صـلاحـيـات الـمـشـرفـيـن"""
    if user_id in SUDOERS:
        return True
    try:
        member = await app.get_chat_member(chat_id, user_id)
        if member.status in [enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.OWNER]:
            return True
    except Exception:
        return False
    return False

def check_porn_api(file_path):
    """فحص الصور عبر API خارجي للذكاء الاصطناعي"""
    try:
        params = {
            'models': 'nudity-2.0',
            'api_user': API_USER,
            'api_secret': API_SECRET
        }
        with open(file_path, 'rb') as f:
            r = requests.post('https://api.sightengine.com/1.0/check.json', files={'media': f}, data=params)
        output = r.json()
        if output.get('status') == 'success':
            return output['nudity']['sexual_display'] > 0.5 or output['nudity']['erotica'] > 0.5
    except Exception as e:
        print(f"API Error: {e}")
    return False

async def add_warn(message: Message, reason="normal"):
    """نـظـام الـتـحـذيـرات والـعـقـوبـات الـمـطـور"""
    c_id = message.chat.id
    u_id = message.from_user.id
    mention = message.from_user.mention
    
    # تعديل الحد إلى 4 تحذيرات للسب والإباحي كما طلبت
    if reason == "religious":
        limit = 4
        mute_days = 7 
    else:
        limit = max_warns.get(c_id, 3)
        mute_days = 1 

    if c_id not in warns_db:
        warns_db[c_id] = {}
    
    warns_db[c_id][u_id] = warns_db[c_id].get(u_id, 0) + 1
    current = warns_db[c_id][u_id]
    
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("🧚 • فـك الـكـتـم • 🧚", callback_data=f"u_unmute_{u_id}")]])
    
    if current > limit:
        warns_db[c_id][u_id] = 0
        try:
            await app.restrict_chat_member(
                c_id, u_id, 
                ChatPermissions(can_send_messages=False),
                until_date=datetime.now() + timedelta(days=mute_days)
            )
            await message.reply(
                f"<b>• الـعـضـو : {mention}\n"
                f"• تـخـطى حـد الـتـحـذيرات ({limit})\n"
                f"• تـم كـتـمـه تـلـقـائـيـاً لـمـدة {mute_days} أيـام 🤍🥀</b>",
                reply_markup=kb
            )
        except: pass
    else:
        if reason == "religious":
            await message.reply(
                f"<b>يـا {mention} ، تـذكـر قـول الله تـعـالـي : ( مَا يَلْفِظُ مِنْ قَوْلٍ إِلَّا لَدَيْهِ رَقِيبٌ عَتِيدٌ ) وأن هذه الدنيا فانية\n\n"
                f"• تـحـذيـراتـك الـحـالـيـة : ({current}/{limit}) 🤍🥀</b>",
                reply_markup=kb
            )
        else:
            await message.reply(
                f"<b>• تـم حـذف رسـالـتـك لـمـخـالـفـة الـقـوانـيـن\n"
                f"• تـحـذيـراتـك الـحـالـيـة : ({current}/{limit})</b>"
            )

# --- [ 3. أوامـر الـتـحـكـم الـنـصـي ] ---

@app.on_message(filters.command(["قفل", "فتح"], "") & filters.group)
async def toggle_lock_cmds(_, message: Message):
    if not await has_permission(message.chat.id, message.from_user.id):
        return
    if len(message.command) < 2:
        return await message.reply("<b>• يـرجـي كـتـابـة مـا تـريـد الـتـحـكـم فـيـه بـعـد الأمـر</b>")
    
    cmd = message.command[0]
    input_text = message.text.split(None, 1)[1].strip()
    key = LOCK_MAP.get(input_text)
    
    if not key: return
    
    c_id = message.chat.id
    if c_id not in smart_db: smart_db[c_id] = set()
    
    if cmd == "قفل":
        if key in smart_db[c_id]:
            return await message.reply(f"<b>• {input_text} بـالـفـعـل مـقـفـول فـي الـمـجـمـوعـة</b>")
        smart_db[c_id].add(key)
        await message.reply(f"<b>• تـم قـفـل {input_text} بـنـجـاح تـام</b>")
    else:
        if key not in smart_db[c_id]:
            return await message.reply(f"<b>• {input_text} بـالـفـعـل مـفـتـوح فـي الـم_جـمـوعـة</b>")
        smart_db[c_id].discard(key)
        await message.reply(f"<b>• تـم فـتـح {input_text} بـنـج_اح تـام</b>")

# --- [ 4. لـوحـة الإعـدادات والـكـيـبـورد ] ---

def get_kb(chat_id):
    kb = []
    active = smart_db.get(chat_id, set())
    items = list(LOCK_MAP.items())
    for i in range(0, len(items), 2):
        row = []
        n1, k1 = items[i]
        s1 = "مـقـفـول" if k1 in active else "مـفـتـوح"
        row.append(InlineKeyboardButton(f"• {n1} ⇽ {s1} •", callback_data=f"trg_{k1}"))
        if i + 1 < len(items):
            n2, k2 = items[i+1]
            s2 = "مـقـفـول" if k2 in active else "مـفـتـوح"
            row.append(InlineKeyboardButton(f"• {n2} ⇽ {s2} •", callback_data=f"trg_{k2}"))
        kb.append(row)
    kb.append([InlineKeyboardButton("• إغـلاق الـلـوحـة •", callback_data="close")])
    return InlineKeyboardMarkup(kb)

@app.on_message(filters.command(["الاعدادات", "locks"], "") & filters.group)
async def settings_cmd(_, message: Message):
    if not await has_permission(message.chat.id, message.from_user.id): return
    await message.reply_text(f"<b>• إعـدادات مـجـمـوعـة : {message.chat.title}</b>", reply_markup=get_kb(message.chat.id))

@app.on_callback_query(filters.regex("^(trg_|u_|close)"))
async def cb_handler(_, cb: CallbackQuery):
    c_id = cb.message.chat.id
    if not await has_permission(c_id, cb.from_user.id): return
    if cb.data == "close": return await cb.message.delete()
    if cb.data.startswith("trg_"):
        key = cb.data.replace("trg_", "")
        if c_id not in smart_db: smart_db[c_id] = set()
        if key in smart_db[c_id]: smart_db[c_id].discard(key)
        else: smart_db[c_id].add(key)
        await cb.message.edit_reply_markup(reply_markup=get_kb(c_id))
    elif cb.data.startswith("u_unmute_"):
        u_id = int(cb.data.split("_")[2])
        await app.restrict_chat_member(c_id, u_id, ChatPermissions(can_send_messages=True))
        await cb.message.edit(f"<b>• تـم فـك الـكـتـم بـنـجـاح تـام بـواسطـة {cb.from_user.mention}</b>")

# --- [ 5. مـحـرك الـحـمـايـة والـفـحـص الـذكـي ] ---

@app.on_message(filters.group & ~filters.me, group=-1)
async def protector_engine(_, message: Message):
    c_id = message.chat.id
    if not message.from_user or await has_permission(c_id, message.from_user.id): return
    
    locks = smart_db.get(c_id, set())
    if not locks: return
    
    text = message.text or message.caption or ""

    if "porn_text" in locks and text:
        clean = re.sub(r"[^\u0621-\u064A\s]", "", text)
        if any(fuzz.ratio(bad, word) > 85 for word in clean.split() for bad in BAD_WORDS):
            await message.delete()
            return await add_warn(message, reason="religious")

    if "porn_media" in locks and message.photo:
        file_path = await message.download()
        if check_porn_api(file_path):
            os.remove(file_path)
            await message.delete()
            return await add_warn(message, reason="religious")
        os.remove(file_path)

    if "photos" in locks and message.photo:
        await message.delete()
        return await add_warn(message)

    if "links" in locks and (message.entities or message.caption_entities):
        await message.delete()
        return await add_warn(message)

# --- [ 6. الـتـنـظـيـف ] ---

@app.on_message(filters.command(["مسح", "تنظيف"], "") & filters.group)
async def clear_chat_cmd(_, message: Message):
    if not await has_permission(message.chat.id, message.from_user.id): return
    num = int(message.command[1]) if len(message.command) > 1 else 100
    await message.delete()
    count = 0
    async for m in app.get_chat_history(message.chat.id, limit=num):
        try:
            await m.delete()
            count += 1
            if count % 25 == 0: await asyncio.sleep(1)
        except: pass
    temp = await message.reply(f"<b>• تـم مـسـح {count} رسـالـة مـن الـشـات بـنـجـاح</b>")
    await asyncio.sleep(3)
    await temp.delete()
