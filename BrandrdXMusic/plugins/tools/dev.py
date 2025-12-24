import os
import re
import subprocess
import sys
import traceback
from inspect import getfullargspec
from io import StringIO
from time import time

from pyrogram import filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

from BrandrdXMusic import app
from config import OWNER_ID

# ➻ sᴏᴜʀᴄᴇ : بُودَا | ʙᴏᴅᴀ

async def aexec(code, client, message):
    exec(
        "async def __aexec(client, message): "
        + "".join(f"\n {a}" for a in code.split("\n"))
    )
    return await locals()["__aexec"](client, message)


async def edit_or_reply(msg: Message, **kwargs):
    func = msg.edit_text if msg.from_user.is_self else msg.reply
    spec = getfullargspec(func.__wrapped__).args
    await func(**{k: v for k, v in kwargs.items() if k in spec})


@app.on_edited_message(
    filters.command("eval")
    & filters.user(OWNER_ID)
    & ~filters.forwarded
    & ~filters.via_bot
)
@app.on_message(
    filters.command("eval")
    & filters.user(OWNER_ID)
    & ~filters.forwarded
    & ~filters.via_bot
)
async def executor(client: app, message: Message):
    if len(message.command) < 2:
        return await edit_or_reply(message, text="**اكـتـب الـكـود الـلـي عـايـز تـشـغـلـه يـا مـطـور**")
    try:
        cmd = message.text.split(" ", maxsplit=1)[1]
    except IndexError:
        return await message.delete()
    t1 = time()
    old_stderr = sys.stderr
    old_stdout = sys.stdout
    redirected_output = sys.stdout = StringIO()
    redirected_error = sys.stderr = StringIO()
    stdout, stderr, exc = None, None, None
    try:
        await aexec(cmd, client, message)
    except Exception:
        exc = traceback.format_exc()
    stdout = redirected_output.getvalue()
    stderr = redirected_error.getvalue()
    sys.stdout = old_stdout
    sys.stderr = old_stderr
    evaluation = "\n"
    if exc:
        evaluation += exc
    elif stderr:
        evaluation += stderr
    elif stdout:
        evaluation += stdout
    else:
        evaluation += "تـم الـتـنـفـيـذ بـنـجـاح"
    
    final_output = f"**الـنـتـيـجـة:**\n<pre language='python'>{evaluation}</pre>"
    
    if len(final_output) > 4096:
        filename = "output.txt"
        with open(filename, "w+", encoding="utf8") as out_file:
            out_file.write(str(evaluation))
        t2 = time()
        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        text="وقت الـتـنـفـيـذ",
                        callback_data=f"runtime {t2-t1} ثانية",
                    )
                ]
            ]
        )
        await message.reply_document(
            document=filename,
            caption=f"**الأمـر:**\n<code>{cmd[0:980]}</code>\n\n**الـنـتـيـجـة:** فـي الـمـلـف الـمـرفـق",
            quote=False,
            reply_markup=keyboard,
        )
        await message.delete()
        os.remove(filename)
    else:
        t2 = time()
        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        text=f"{round(t2-t1, 3)} ثـانـيـة",
                        callback_data=f"runtime {round(t2-t1, 3)} ثانية",
                    ),
                    InlineKeyboardButton(
                        text="إغـلاق",
                        callback_data=f"forceclose abc|{message.from_user.id}",
                    ),
                ]
            ]
        )
        await edit_or_reply(message, text=final_output, reply_markup=keyboard)


@app.on_callback_query(filters.regex(r"runtime"))
async def runtime_func_cq(_, cq):
    runtime = cq.data.split(None, 1)[1]
    await cq.answer(f"وقت الـتـنـفـيـذ: {runtime}", show_alert=True)


@app.on_callback_query(filters.regex("forceclose"))
async def forceclose_command(_, CallbackQuery):
    callback_data = CallbackQuery.data.strip()
    callback_request = callback_data.split(None, 1)[1]
    query, user_id = callback_request.split("|")
    if CallbackQuery.from_user.id != int(user_id):
        try:
            return await CallbackQuery.answer(
                "الأمـر ده يـخـص الـمـطـور فـقـط", show_alert=True
            )
        except:
            return
    await CallbackQuery.message.delete()
    try:
        await CallbackQuery.answer("تـم الـحـذف")
    except:
        return


@app.on_edited_message(
    filters.command("sh")
    & filters.user(OWNER_ID)
    & ~filters.forwarded
    & ~filters.via_bot
)
@app.on_message(
    filters.command("sh")
    & filters.user(OWNER_ID)
    & ~filters.forwarded
    & ~filters.via_bot
)
async def shellrunner(_, message: Message):
    if len(message.command) < 2:
        return await edit_or_reply(message, text="**اكـتـب الأمـر بـعـد /sh**\n\nمـثـال: `/sh git pull`")
    text = message.text.split(None, 1)[1]
    if "\n" in text:
        code = text.split("\n")
        output = ""
        for x in code:
            shell = re.split(""" (?=(?:[^'"]|'[^']*'|"[^"]*")*$)""", x)
            try:
                process = subprocess.Popen(
                    shell,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )
            except Exception as err:
                await edit_or_reply(message, text=f"**خـطـأ:**\n<pre>{err}</pre>")
            output += f"**{code}**\n"
            output += process.stdout.read()[:-1].decode("utf-8")
            output += "\n"
    else:
        shell = re.split(""" (?=(?:[^'"]|'[^']*'|"[^"]*")*$)""", text)
        for a in range(len(shell)):
            shell[a] = shell[a].replace('"', "")
        try:
            process = subprocess.Popen(
                shell,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
        except Exception as err:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            errors = traceback.format_exception(
                etype=exc_type,
                value=exc_obj,
                tb=exc_tb,
            )
            return await edit_or_reply(
                message, text=f"**خـطـأ:**\n<pre>{''.join(errors)}</pre>"
            )
        output = process.stdout.read()[:-1].decode("utf-8")
    if str(output) == "\n":
        output = None
    if output:
        if len(output) > 4096:
            with open("output.txt", "w+") as file:
                file.write(output)
            await app.send_document(
                message.chat.id,
                "output.txt",
                reply_to_message_id=message.id,
                caption="**تـم اسـتـخـراج الـنـتـيـجـة فـي مـلـف**",
            )
            return os.remove("output.txt")
        await edit_or_reply(message, text=f"**الـمـخـرج:**\n<pre>{output}</pre>")
    else:
        await edit_or_reply(message, text="**الـمـخـرج:**\n`لا يـوجـد`")
    await message.stop_propagation()

# ➻ sᴏᴜʀᴄᴇ : بُودَا | ʙᴏᴅᴀ
