import asyncio
from BrandrdXMusic import app
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from config import MUSIC_BOT_NAME

# ➻ sᴏᴜʀᴄᴇ : بُودَا | ʙᴏᴅَا

@app.on_message(filters.command(["alive", "شغال"]))
async def start(client: Client, message: Message):
    await message.reply_photo(
        photo="https://files.catbox.moe/ht74e3.jpg",
        caption=(
            f"❤️ **أهـلاً بـك يـا** {message.from_user.mention}\n\n"
            f"🔮 **الـبـوت :** {MUSIC_BOT_NAME}\n\n"
            f"✨ **أنـا بـوت مـيـوزك سـريـع وقـوي يـعـمـل بـكـفـاءة عـالـيـة..**\n\n"
            f"💫 **لـأي اسـتـفـسـار تـفـضـل بـزيـارة جـروب الـدعـم..**\n\n"
            f"━━━━━━━━━━━━━━━━━━❄"
        ),
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        text="👑 مـالـك الـبـوت 👑", url="https://t.me/S_G0C7"
                    ),
                ],
                [
                    InlineKeyboardButton(
                        text="✧ سـورس بُـودَا ✧", url="https://t.me/SourceBoda"
                    ),
                    InlineKeyboardButton(
                        text="✧ جـروب الـدعـم ✧", url="https://t.me/music0587"
                    ),
                ],
                [
                    InlineKeyboardButton(
                        text="✯ إغـلاق ✯", callback_data="close"
                    )
                ],
            ]
        )
    )

# ➻ sᴏᴜʀᴄᴇ : بُودَا | ʙᴏᴅَا
