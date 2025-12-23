from pyrogram import Client, filters
import requests
import random
from BrandrdXMusic import app

# تـوقـيـع الـسـورس
BODA_SIGNATURE = "➻ sᴏᴜʀᴄᴇ : بُودَا | ʙᴏᴅᴀ"

# روابط الألـعـاب
truth_api_url = "https://api.truthordarebot.xyz/v1/truth"
dare_api_url = "https://api.truthordarebot.xyz/v1/dare"

@app.on_message(filters.command("truth"))
def get_truth(client, message):
    try:
        # طلـب سـؤال صـراحـة
        response = requests.get(truth_api_url)
        if response.status_code == 200:
            truth_question = response.json()["question"]
            message.reply_text(
                f"🧐 **سـؤال صـراحـة جـديـد :**\n\n`{truth_question}`\n\n{BODA_SIGNATURE}"
            )
        else:
            message.reply_text("⚠️ **عـذراً، فـشـل جـلـب الـسـؤال.. حـاول مـرة ثـانـيـة.**")
    except Exception as e:
        message.reply_text("❌ **حـصـل خـطأ أثـنـاء جـلـب سـؤال الـصـراحـة.**")

@app.on_message(filters.command("dare"))
def get_dare(client, message):
    try:
        # طلـب سـؤال جـرأة
        response = requests.get(dare_api_url)
        if response.status_code == 200:
            dare_question = response.json()["question"]
            message.reply_text(
                f"🔥 **تـحـدي جـرأة جـديـد :**\n\n`{dare_question}`\n\n{BODA_SIGNATURE}"
            )
        else:
            message.reply_text("⚠️ **عـذراً، فـشـل جـلـب الـتـحـدي.. حـاول مـرة ثـانـيـة.**")
    except Exception as e:
        message.reply_text("❌ **حـصـل خـطأ أثـنـاء جـلـب سـؤال الـجـرأة.**")
