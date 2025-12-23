import random
import requests
import time

from pyrogram import filters
from pyrogram.enums import PollType, ChatAction
from BrandrdXMusic import app


last_command_time = {}


@app.on_message(filters.command(["quiz", "مسابقة"]))
async def quiz(client, message):
    user_id = message.from_user.id
    current_time = time.time()

    # منع التكرار قبل مرور 5 ثواني
    if user_id in last_command_time and current_time - last_command_time[user_id] < 5:
        await message.reply_text(
            "⏳ يرجى الانتظار 5 ثوانٍ قبل استخدام هذا الأمر مرة أخرى."
        )
        return

    last_command_time[user_id] = current_time

    # تصنيفات الأسئلة (عامة، علوم، حاسوب، إلخ)
    categories = [9, 17, 18, 20, 21, 27]
    await app.send_chat_action(message.chat.id, ChatAction.TYPING)

    try:
        url = f"https://opentdb.com/api.php?amount=1&category={random.choice(categories)}&type=multiple"
        response = requests.get(url).json()

        question_data = response["results"][0]
        question = question_data["question"]
        correct_answer = question_data["correct_answer"]
        incorrect_answers = question_data["incorrect_answers"]

        # دمج الإجابات وترتيبها عشوائياً
        all_answers = incorrect_answers + [correct_answer]
        random.shuffle(all_answers)

        # تحديد مكان الإجابة الصحيحة
        cid = all_answers.index(correct_answer)
        
        await app.send_poll(
            chat_id=message.chat.id,
            question=f"❓ سؤال المسابقة:\n\n{question}",
            options=all_answers,
            is_anonymous=False,
            type=PollType.QUIZ,
            correct_option_id=cid,
            explanation="إجابة صحيحة! أحسنت 🌟"
        )
    except Exception as e:
        await message.reply_text("❌ عذراً، حدث خطأ أثناء جلب السؤال. حاول مرة أخرى لاحقاً.")
