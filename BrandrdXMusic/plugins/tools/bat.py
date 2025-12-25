import random
import asyncio
from pyrogram import filters
from BrandrdXMusic import app

BAT = {}

@app.on_message(filters.command("بات") & filters.group)
async def bat_game(client, message):
    chat_id = message.chat.id
    user_id = message.from_user.id

    if chat_id in BAT and BAT[chat_id]["on"]:
        return await message.reply_text("🎮 اللعبة شغالة بالفعل!")

    place = random.choice(["يمين", "شمال"])

    BAT[chat_id] = {
        "on": True,
        "place": place,
        "player": user_id
    }

    await message.reply_text(
        f"🎮 **لعبة البات (المحيبس)**\n\n"
        f"👤 اللاعب: {message.from_user.mention}\n\n"
        "💍 الخاتم فين؟\n"
        "**يمين** ولا **شمال** ؟\n\n"
        "⏳ معاك 20 ثانية"
    )

    await asyncio.sleep(20)

    if chat_id in BAT and BAT[chat_id]["on"]:
        BAT[chat_id]["on"] = False
        await message.reply_text(
            f"⏰ انتهى الوقت!\n"
            f"💍 الخاتم كان في **{BAT[chat_id]['place']}**"
        )

@app.on_message(filters.text & filters.group)
async def bat_answer(client, message):
    chat_id = message.chat.id

    if chat_id not in BAT:
        return

    game = BAT[chat_id]

    if not game["on"]:
        return

    # نفس اللي في الملف: صاحب الأمر فقط
    if message.from_user.id != game["player"]:
        return

    answer = message.text.strip()

    if answer not in ["يمين", "شمال"]:
        return

    game["on"] = False

    if answer == game["place"]:
        await message.reply_text(
            f"🎉 مبروك {message.from_user.mention}\n"
            f"💍 الخاتم كان في **{game['place']}**"
        )
    else:
        await message.reply_text(
            f"❌ غلط {message.from_user.mention}\n"
            f"💍 الخاتم كان في **{game['place']}**"
        )
