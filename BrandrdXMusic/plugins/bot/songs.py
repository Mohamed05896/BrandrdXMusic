import os
import re
import yt_dlp
from pyrogram import Client, filters
from pyrogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InputMediaAudio,
    InputMediaVideo,
    Message,
)

from config import (
    BANNED_USERS,
    SONG_DOWNLOAD_DURATION,
    SONG_DOWNLOAD_DURATION_LIMIT,
)
from BrandrdXMusic import YouTube, app
from BrandrdXMusic.utils.decorators.language import language, languageCB
from BrandrdXMusic.utils.formatters import convert_bytes
from BrandrdXMusic.utils.inline.song import song_markup

# تـوقـيـع الـسـورس
BODA_SIGNATURE = "➻ sᴏᴜʀᴄᴇ : بُودَا | ʙᴏᴅᴀ"

# وحـدة تـحـمـيـل الأغـانـي 🎵

@app.on_message(filters.command(["song"]))
@language
async def song_commad_private(client, message: Message, _):
    await message.delete()
    url = await YouTube.url(message)
    if url:
        if not await YouTube.exists(url):
            return await message.reply_text("❌ الـلـيـنـك غـيـر صـالـح أو غـيـر مـوجـود.")
        mystic = await message.reply_text("🔍 جـاري جـلـب تـفـاصـيـل الـفـيـديـو..")
        (
            title,
            duration_min,
            duration_sec,
            thumbnail,
            vidid,
        ) = await YouTube.details(url)
        if str(duration_min) == "None":
            return await mystic.edit_text("📺 عـفـواً، لا يـمـكـن تـحـمـيـل الـبـث الـمـبـاشـر.")
        if int(duration_sec) > SONG_DOWNLOAD_DURATION_LIMIT:
            return await mystic.edit_text(
                f"⏳ الـفـيـديـو طـويـل جـداً، الـحـد الـمـسـمـوح هـو {SONG_DOWNLOAD_DURATION} دقـيـقـة."
            )
        buttons = song_markup(_, vidid)
        await mystic.delete()
        await message.reply_photo(
            thumbnail,
            caption=f"**🎬 الـعـنـوان:** `{title}`\n\n{BODA_SIGNATURE}",
            reply_markup=InlineKeyboardMarkup(buttons),
        )
    else:
        if len(message.command) < 2:
            return await message.reply_text("💡 يـرجـى كـتـابـة اسـم الأغـنـيـة أو الـرابـط بـعـد الأمـر.\nمـثـال: `/song عـمـرو ديـاب`")
    
    mystic = await message.reply_text("✨ جـاري الـبـحـث.. يـرجـى الانـتـظـار.")
    query = message.text.split(None, 1)[1]
    try:
        (
            title,
            duration_min,
            duration_sec,
            thumbnail,
            vidid,
        ) = await YouTube.details(query)
    except:
        return await mystic.edit_text("😔 لـم يـتـم الـعـثـور عـلـى نـتـائـج، حـاول مـرة أخـرى.")
        
    if str(duration_min) == "None":
        return await mystic.edit_text("📺 لا يـمـكـن تـحـمـيـل فـيـديـو الـبـث الـمـبـاشـر.")
    if int(duration_sec) > SONG_DOWNLOAD_DURATION_LIMIT:
        return await mystic.edit_text(
            f"⏳ الأغـنـيـة طـويـلـة جـداً، الـحـد الـمـسـمـوح هـو {SONG_DOWNLOAD_DURATION} دقـيـقـة."
        )
    buttons = song_markup(_, vidid)
    await mystic.delete()
    await message.reply_photo(
        thumbnail,
        caption=f"**🎶 تـم الـعـثـور عـلـى:** `{title}`\n\n{BODA_SIGNATURE}",
        reply_markup=InlineKeyboardMarkup(buttons),
    )

@app.on_callback_query(filters.regex(pattern=r"song_back") & ~BANNED_USERS)
@languageCB
async def songs_back_helper(client, callback_query: CallbackQuery, _):
    callback_data = callback_query.data.strip()
    callback_request = callback_data.split(None, 1)[1]
    stype, vidid = callback_request.split("|")
    buttons = song_markup(_, vidid)
    await callback_query.edit_message_reply_markup(
        reply_markup=InlineKeyboardMarkup(buttons)
    )

@app.on_callback_query(filters.regex(pattern=r"song_helper") & ~BANNED_USERS)
@languageCB
async def song_helper_cb(client, callback_query: CallbackQuery, _):
    callback_data = callback_query.data.strip()
    callback_request = callback_data.split(None, 1)[1]
    stype, vidid = callback_request.split("|")
    try:
        await callback_query.answer("📥 جـاري تـجـهـيـز الـجـودات..", show_alert=False)
    except:
        pass
    if stype == "audio":
        try:
            formats_available, link = await YouTube.formats(vidid, True)
        except:
            return await callback_query.edit_message_text("❌ فـشـل جـلـب جـودات الـصـوت.")
        keyboard = InlineKeyboardMarkup(inline_keyboard=[])
        done = []
        for x in formats_available:
            check = x["format"]
            if "audio" in check:
                if x["filesize"] is None:
                    continue
                form = x["format_note"].title()
                if form not in done:
                    done.append(form)
                else:
                    continue
                sz = convert_bytes(x["filesize"])
                fom = x["format_id"]
                keyboard.inline_keyboard.append(
                    [
                        InlineKeyboardButton(
                            text=f"🎵 جـودة {form} ➻ {sz}",
                            callback_data=f"song_download {stype}|{fom}|{vidid}",
                        ),
                    ]
                )
        keyboard.inline_keyboard.append(
            [
                InlineKeyboardButton(text="⬅️ رجـوع", callback_data=f"song_back {stype}|{vidid}"),
                InlineKeyboardButton(text="❌ إغـلاق", callback_data=f"close"),
            ]
        )
        await callback_query.edit_message_reply_markup(reply_markup=keyboard)
    else:
        try:
            formats_available, link = await YouTube.formats(vidid, True)
        except Exception as e:
            return await callback_query.edit_message_text("❌ حـصـل خـطأ فـي جـلـب الـجـودات.")
        keyboard = InlineKeyboardMarkup(inline_keyboard=[])
        done = [160, 133, 134, 135, 136, 137, 298, 299, 264, 304, 266]
        for x in formats_available:
            check = x["format"]
            if x["filesize"] is None:
                continue
            if int(x["format_id"]) not in done:
                continue
            sz = convert_bytes(x["filesize"])
            ap = check.split("-")[1]
            to = f"🎬 جـودة {ap} ➻ {sz}"
            keyboard.inline_keyboard.append(
                [
                    InlineKeyboardButton(
                        text=to,
                        callback_data=f"song_download {stype}|{x['format_id']}|{vidid}",
                    ),
                ]
            )
        keyboard.inline_keyboard.append(
            [
                InlineKeyboardButton(text="⬅️ رجـوع", callback_data=f"song_back {stype}|{vidid}"),
                InlineKeyboardButton(text="❌ إغـلاق", callback_data=f"close"),
            ]
        )
        await callback_query.edit_message_reply_markup(reply_markup=keyboard)

@app.on_callback_query(filters.regex(pattern=r"song_download") & ~BANNED_USERS)
@languageCB
async def song_download_cb(client, callback_query: CallbackQuery, _) :
    try:
        await callback_query.answer("⚡ جـاري الـتـحـمـيـل..")
    except:
        pass
    callback_data = callback_query.data.strip()
    callback_request = callback_data.split(None, 1)[1]
    stype, format_id, vidid = callback_request.split("|")
    mystic = await callback_query.edit_message_text("🛠 جـاري مـعـالـجـة الـتـحـمـيـل..")
    yturl = f"https://www.youtube.com/watch?v={vidid}"
    with yt_dlp.YoutubeDL({"quiet": True}) as ytdl:
        x = ytdl.extract_info(yturl, download=False)
    title = (x["title"]).title()
    title = re.sub("\W+", " ", title)
    thumb_image_path = await callback_query.message.download()
    duration = x["duration"]
    
    if stype == "video":
        width = callback_query.message.photo.width
        height = callback_query.message.photo.height
        try:
            file_path = await YouTube.download(
                yturl, mystic, songvideo=True, format_id=format_id, title=title
            )
        except Exception as e:
            return await mystic.edit_text(f"❌ فـشـل الـتـحـمـيـل: `{e}`")
        med = InputMediaVideo(
            media=file_path,
            duration=duration,
            width=width,
            height=height,
            thumb=thumb_image_path,
            caption=f"✅ **تـم الـتـحـمـيـل بـنـجـاح!**\n\n🎬 **الـعـنـوان:** {title}\n\n{BODA_SIGNATURE}",
            supports_streaming=True,
        )
        await mystic.edit_text("✅ جـاري رفـع الـفـيـديـو الآن..")
        await app.send_chat_action(callback_query.message.chat.id, "upload_video")
        try:
            await callback_query.edit_message_media(media=med)
        except:
            return await mystic.edit_text("❌ حـصـل خـطأ أثـنـاء الـرفـع.")
        os.remove(file_path)
    elif stype == "audio":
        try:
            filename = await YouTube.download(
                yturl, mystic, songaudio=True, format_id=format_id, title=title
            )
        except Exception as e:
            return await mystic.edit_text(f"❌ فـشـل الـتـحـمـيـل: `{e}`")
        med = InputMediaAudio(
            media=filename,
            caption=f"✅ **تـم الـتـحـمـيـل بـنـجـاح!**\n\n🎧 **الـعـنـوان:** {title}\n\n{BODA_SIGNATURE}",
            thumb=thumb_image_path,
            title=title,
            performer=x["uploader"],
        )
        await mystic.edit_text("✅ جـاري رفـع مـلـف الـصـوت الآن..")
        await app.send_chat_action(callback_query.message.chat.id, "upload_audio")
        try:
            await callback_query.edit_message_media(media=med)
        except:
            return await mystic.edit_text("❌ حـصـل خـطأ أثـنـاء الـرفـع.")
        os.remove(filename)
