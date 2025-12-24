import platform
from sys import version as pyver

import psutil
from pyrogram import __version__ as pyrover
from pyrogram import filters
from pyrogram.errors import MessageIdInvalid
from pyrogram.types import InputMediaPhoto, Message
from pytgcalls.__version__ import __version__ as pytgver

import config
from BrandrdXMusic import app
from BrandrdXMusic.core.userbot import assistants
from BrandrdXMusic.misc import SUDOERS, mongodb
from BrandrdXMusic.plugins import ALL_MODULES
from BrandrdXMusic.utils.database import get_served_chats, get_served_users, get_sudoers, get_queries
from BrandrdXMusic.utils.decorators.language import language, languageCB
from BrandrdXMusic.utils.inline.stats import back_stats_buttons, stats_buttons
from config import BANNED_USERS

# ➻ sᴏᴜʀᴄᴇ : بُودَا | ʙᴏᴅᴀ

@app.on_message(filters.command(["stats", "gstats"]) & filters.group & ~BANNED_USERS)
@language
async def stats_global(client, message: Message, _):
    upl = stats_buttons(_, True if message.from_user.id in SUDOERS else False)
    await message.reply_photo(
        photo=config.STATS_IMG_URL,
        caption=f"**📊 إحـصـائـيـات بـوت {app.mention}**\n\nانقر على الأزرار بالأسفل لعرض تفاصيل النظام أو الإحصائيات العامة.",
        reply_markup=upl,
    )


@app.on_callback_query(filters.regex("stats_back") & ~BANNED_USERS)
@languageCB
async def home_stats(client, CallbackQuery, _):
    upl = stats_buttons(_, True if CallbackQuery.from_user.id in SUDOERS else False)
    await CallbackQuery.edit_message_text(
        text=f"**📊 إحـصـائـيـات بـوت {app.mention}**\n\nانقر على الأزرار بالأسفل لعرض تفاصيل النظام أو الإحصائيات العامة.",
        reply_markup=upl,
    )


@app.on_callback_query(filters.regex("TopOverall") & ~BANNED_USERS)
@languageCB
async def overall_stats(client, CallbackQuery, _):
    await CallbackQuery.answer()
    upl = back_stats_buttons(_)
    try:
        await CallbackQuery.answer()
    except:
        pass
    
    served_chats = len(await get_served_chats())
    served_users = len(await get_served_users())
    total_queries = await get_queries()
    
    text = f"""
**📊 إحصائيات التشغيل العام لـ {app.mention} :**

**✧ الـمـوديلات :** {len(ALL_MODULES)}
**✧ الـمـسـاعـديـن :** {len(assistants)}
**✧ الـمـحـظـوريـن :** {len(BANNED_USERS)}
**✧ الـمـطـوريـن :** {len(SUDOERS)}

**✧ الـمـجـمـوعـات :** {served_chats}
**✧ الـمـسـتـخـدمـيـن :** {served_users}
**✧ إجـمـالـي الـطـلـبـات :** {total_queries}

**✧ مـغادرة الـمـسـاعـد آلـيـاً :** {"نعم" if config.AUTO_LEAVING_ASSISTANT == str(True) else "لا"}
**✧ حـد الـتـشـغـيـل الـمـسـمـوح :** {config.DURATION_LIMIT_MIN} دقيقة
"""
    med = InputMediaPhoto(media=config.STATS_IMG_URL, caption=text)
    try:
        await CallbackQuery.edit_message_media(media=med, reply_markup=upl)
    except MessageIdInvalid:
        await CallbackQuery.message.reply_photo(photo=config.STATS_IMG_URL, caption=text, reply_markup=upl)


@app.on_callback_query(filters.regex("bot_stats_sudo"))
@languageCB
async def bot_stats(client, CallbackQuery, _):
    if CallbackQuery.from_user.id not in SUDOERS:
        return await CallbackQuery.answer("هذا القسم مخصص للمطورين فقط يا حُب.", show_alert=True)
    upl = back_stats_buttons(_)
    try:
        await CallbackQuery.answer()
    except:
        pass

    p_core = psutil.cpu_count(logical=False)
    t_core = psutil.cpu_count(logical=True)
    ram = str(round(psutil.virtual_memory().total / (1024.0**3))) + " GB"
    
    try:
        cpu_freq = psutil.cpu_freq().current
        if cpu_freq >= 1000:
            cpu_freq = f"{round(cpu_freq / 1000, 2)} GHz"
        else:
            cpu_freq = f"{round(cpu_freq, 2)} MHz"
    except:
        cpu_freq = "تعذر الجلب"

    hdd = psutil.disk_usage("/")
    total = hdd.total / (1024.0**3)
    used = hdd.used / (1024.0**3)
    free = hdd.free / (1024.0**3)
    
    call = await mongodb.command("dbstats")
    datasize = call["dataSize"] / 1024
    storage = call["storageSize"] / 1024
    served_chats = len(await get_served_chats())
    served_users = len(await get_served_users())
    
    text = f"""
**🖥️ إحـصـائـيـات خـادم الـسـورس :**

**✧ الـنـظـام :** {platform.system()}
**✧ الـرامـات :** {ram}
**✧ الـمـعـالـج :** {p_core} نـواة حـقـيـقـيـة / {t_core} وهمـية
**✧ الـتـردد :** {cpu_freq}

**✧ الـمـسـاحة الإجـمـالـية :** {str(total)[:4]} GB
**✧ الـمـسـاحة الـمـسـتـهـلكـة :** {str(used)[:4]} GB
**✧ الـمـسـاحة الـفـارغـة :** {str(free)[:4]} GB

**✧ إصـدار الـبـايـثـون :** {pyver.split()[0]}
**✧ إصـدار بـايـروجـرام :** {pyrover}
**✧ إصـدار الـكـولات :** {pytgver}

**✧ الـمـجـمـوعـات :** {served_chats}
**✧ الـمـسـتـخـدمـيـن :** {served_users}
**✧ الـسـودو :** {len(await get_sudoers())}
**✧ قـاعدة الـبـيـانـات :** {str(datasize)[:6]} KB
"""
    med = InputMediaPhoto(media=config.STATS_IMG_URL, caption=text)
    try:
        await CallbackQuery.edit_message_media(media=med, reply_markup=upl)
    except MessageIdInvalid:
        await CallbackQuery.message.reply_photo(photo=config.STATS_IMG_URL, caption=text, reply_markup=upl)

# ➻ sᴏᴜʀᴄᴇ : بُودَا | ʙᴏᴅᴀ
