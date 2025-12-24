import random
from pyrogram import Client, filters
from pyrogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)
from config import LOGGER_ID as LOG_GROUP_ID
from BrandrdXMusic import app
from BrandrdXMusic.core.userbot import assistants
from BrandrdXMusic.utils.database import get_assistant

# ➻ sᴏᴜʀᴄᴇ : بُودَا | ʙᴏᴅᴀ

# الـروابـط الـجـديـدة الـلـي بـعـتـهـا يـا بـودا ⚡️
photo = [
    "https://files.catbox.moe/4st2cp.jpg",
    "https://files.catbox.moe/r1lc37.jpg",
    "https://files.catbox.moe/efzuds.jpg",
    "https://files.catbox.moe/ht74e3.jpg",
    "https://files.catbox.moe/qujhu1.jpg",
]

@app.on_message(filters.new_chat_members, group=2)
async def join_watcher(_, message):
    try:
        userbot = await get_assistant(message.chat.id)
        chat = message.chat
        for members in message.new_chat_members:
            if members.id == app.id:
                count = await app.get_chat_members_count(chat.id)
                username = (
                    f"@{message.chat.username}" if message.chat.username else "مجموعة خاصة 🔐"
                )
                
                # رسـالـة مـدلعـة بـالـعـربـي
                msg = (
                    f"**✅ تـم إضـافـة الـبـوت لـمـجـمـوعـة جـديـدة**\n\n"
                    f"**✧ اسـم الـمـجـمـوعـة :** {message.chat.title}\n"
                    f"**✧ آيـدي الـمـجـمـوعـة :** `{message.chat.id}`\n"
                    f"**✧ يـوزر الـمـجـمـوعـة :** {username}\n"
                    f"**✧ عـدد الأعـضـاء :** {count}\n"
                    f"**✧ أُضـيـف بـواسـطـة :** {message.from_user.mention}\n"
                    f"\n**➻ sᴏᴜʀᴄᴇ : بُودَا | ʙᴏᴅᴀ**"
                )
                
                await app.send_photo(
                    LOG_GROUP_ID,
                    photo=random.choice(photo),
                    caption=msg,
                    reply_markup=InlineKeyboardMarkup(
                        [
                            [
                                InlineKeyboardButton(
                                    "👤 الـمـطـور الـذي أضـافـنـي",
                                    url=f"tg://openmessage?user_id={message.from_user.id}",
                                )
                            ]
                        ]
                    ),
                )
                
                if message.chat.username:
                    await userbot.join_chat(message.chat.username)
                    
    except Exception as e:
        print(f"Error in join_watcher: {e}")

# ➻ sᴏᴜʀᴄᴇ : بُودَا | ʙᴏᴅᴀ
