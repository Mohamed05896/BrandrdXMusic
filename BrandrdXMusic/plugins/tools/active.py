from pyrogram import filters
from pyrogram.types import Message
from unidecode import unidecode

from BrandrdXMusic import app
from config import OWNER_ID
from BrandrdXMusic.utils.database import (
    get_active_chats,
    get_active_video_chats,
    remove_active_chat,
    remove_active_video_chat,
)

# ➻ sᴏᴜʀᴄᴇ : بُودَا | ʙᴏᴅᴀ

@app.on_message(filters.command(["activevc", "المكالمات", "النشطة"]) & filters.user(OWNER_ID))
async def activevc(_, message: Message):
    mystic = await message.reply_text("**جـاري فـحـص الـمـكـالـمـات الـصـوتـيـة الـنـشـطـة.. 📡**")
    served_chats = await get_active_chats()
    text = ""
    j = 0
    for x in served_chats:
        try:
            title = (await app.get_chat(x)).title
        except:
            await remove_active_chat(x)
            continue
        try:
            title_clean = unidecode(title).upper()
            if (await app.get_chat(x)).username:
                user = (await app.get_chat(x)).username
                text += f"**{j + 1}ـ** <a href=https://t.me/{user}>{title_clean}</a>\n└ **آيـدي:** `[ {x} ]`\n\n"
            else:
                text += f"**{j + 1}ـ** {title_clean}\n└ **آيـدي:** `[ {x} ]`\n\n"
            j += 1
        except:
            continue
    if not text:
        await mystic.edit_text(f"**لا تـوجـد مـكـالـمـات نـشـطـة حـالـيـاً يـا مـطـور 🎧**")
    else:
        await mystic.edit_text(
            f"**قـائـمـة الـمـكـالـمـات الـصـوتـيـة الـجـاريـة 🎤 :**\n\n{text}**عـدد الـمـكـالـمـات:** {j}",
            disable_web_page_preview=True,
        )


@app.on_message(filters.command(["activev", "الفيديو", "نشطة_فيديو"]) & filters.user(OWNER_ID))
async def activevi_(_, message: Message):
    mystic = await message.reply_text("**جـاري بـحـث مـكـالـمـات الـفـيـديـو الـنـشـطـة.. 🎥**")
    served_chats = await get_active_video_chats()
    text = ""
    j = 0
    for x in served_chats:
        try:
            title = (await app.get_chat(x)).title
        except:
            await remove_active_video_chat(x)
            continue
        try:
            title_clean = unidecode(title).upper()
            if (await app.get_chat(x)).username:
                user = (await app.get_chat(x)).username
                text += f"**{j + 1}ـ** <a href=https://t.me/{user}>{title_clean}</a>\n└ **آيـدي:** `[ {x} ]`\n\n"
            else:
                text += f"**{j + 1}ـ** {title_clean}\n└ **آيـدي:** `[ {x} ]`\n\n"
            j += 1
        except:
            continue
    if not text:
        await mystic.edit_text(f"**لا تـوجـد مـكـالـمـات فـيـديـو جـاريـة حـالـيـاً 🎬**")
    else:
        await mystic.edit_text(
            f"**قـائـمـة مـكـالـمـات الـفـيـديـو الـنـشـطـة 🎥 :**\n\n{text}**عـدد الـمـكـالـمـات:** {j}",
            disable_web_page_preview=True,
        )

# ➻ sᴏᴜʀᴄᴇ : بُودَا | ʙᴏᴅᴀ
