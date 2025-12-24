import io
from gtts import gTTS
from pyrogram import filters
from BrandrdXMusic import app

# ➻ sᴏᴜʀᴄᴇ : بُودَا | ʙᴏᴅᴀ

@app.on_message(filters.command("tts"))
async def text_to_speech(client, message):
    if len(message.command) < 2:
        return await message.reply_text(
            "**يا ريت تكتب النص اللي عايز تحوله لصوت بعد الأمر.. مثال:**\n`/tts يا هلا بيك في سورس بودا`"
        )

    text = message.text.split(None, 1)[1]
    # تم تغيير اللغة إلى العربية (lang="ar")
    tts = gTTS(text, lang="ar")
    audio_data = io.BytesIO()
    tts.write_to_fp(audio_data)
    audio_data.seek(0)

    audio_file = io.BytesIO(audio_data.read())
    audio_file.name = "Boda_Audio.mp3"
    
    await message.reply_audio(
        audio_file, 
        caption=f"**تم تحويل النص إلى صوت بنجاح ✅**\n\n**النص:** {text[:50]}..."
    )


__HELP__ = """
**✨ أمـر تـحـويـل الـنـص إلـى صـوت (TTS)**

اسـتـخـدم الأمـر `/tts` لـتـحـويـل أي نـص تـكـتـبـه لـمـقـطع صـوتـي بـالـلـغة الـعـربـيـة.

- `/tts <الـنـص>`: بـيـحـول الـكـلام اللـي كـتـبـتـه لـصـوت.

**مثال:**
- `/tts منور يا بودا`

**ملاحظة:**
لازم تـكـتـب كـلام بـعـد الأمـر عـشـان الـبـوت يـعـرف يـحـولـه.
"""

__MODULE__ = "تحويل صوتي"

# ➻ sᴏᴜʀᴄᴇ : بُودَا | ʙᴏᴅᴀ
