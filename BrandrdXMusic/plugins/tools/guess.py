import random
from pyrogram import filters
from pyrogram.types import Message
from BrandrdXMusic import app

# تخزين حالة اللعبة لكل جروب
GUESS_GAMES = {}

# تشغيل اللعبة
@app.on_message(filters.group & filters.text & ~filters.bot)
async def start_guess_game(client, message: Message):
    text = message.text.strip()

    # أمر بدء اللعبة
    if text == "التخمين":
        chat_id = message.chat.id

        if chat_id in GUESS_GAMES:
            await message.reply_text("❌ **لعبة التخمين شغالة بالفعل!**\nاستنوا النتيجة 🎯")
            return

        number = random.randint(1, 20)
        GUESS_GAMES[chat_id] = number

        await message.reply_text(
            "🎮 **لعبة التخمين بدأت!**\n\n"
            "🔢 خمنت رقم من **1 إلى 20**\n"
            "✍️ اكتب الرقم اللي تتوقعه في الشات\n\n"
            "🏆 أول واحد يجاوب صح يكسب!"
        )
        return

    # التحقق من التخمين
    chat_id = message.chat.id
    if chat_id not in GUESS_GAMES:
        return

    if not text.isdigit():
        return

    guess = int(text)
    correct_number = GUESS_GAMES[chat_id]

    if guess == correct_number:
        del GUESS_GAMES[chat_id]
        await message.reply_text(
            f"🎉 **مبروك!**\n\n"
            f"🏆 الفائز: {message.from_user.mention}\n"
            f"✅ الرقم الصحيح: **{correct_number}**\n\n"
            "➻ sᴏᴜʀᴄᴇ : BrandrdXMusic"
        )
