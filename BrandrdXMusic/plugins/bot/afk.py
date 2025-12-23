import time, re
from pyrogram.enums import MessageEntityType
from pyrogram import filters
from pyrogram.types import Message
from BrandrdXMusic import app
from BrandrdXMusic.mongo.readable_time import get_readable_time
from BrandrdXMusic.mongo.afkdb import add_afk, is_afk, remove_afk

# بصمة السورس المزخرفة
BODA_SOURCE = "ּبـٰﯡدَا ׀ 𝗦𝗢𝗨𝗥𝗖𝗘 𝗕𝗢𝗗𝗔 👣"

@app.on_message(filters.command(["afk", "brb"], prefixes=["/", "!"]))
async def active_afk(_, message: Message):
    if message.sender_chat:
        return
    user_id = message.from_user.id
    verifier, reasondb = await is_afk(user_id)
    if verifier:
        await remove_afk(user_id)
        try:
            afktype = reasondb["type"]
            timeafk = reasondb["time"]
            data = reasondb["data"]
            reasonafk = reasondb["reason"]
            seenago = get_readable_time((int(time.time() - timeafk)))
            if afktype == "text":
                send = await message.reply_text(
                    f"**{message.from_user.first_name}** رجع أونلاين بعد ما كان مشغول لمدة {seenago}\n\n{BODA_SOURCE}",
                    disable_web_page_preview=True,
                )
            if afktype == "text_reason":
                send = await message.reply_text(
                    f"**{message.from_user.first_name}** رجع أونلاين بعد ما كان مشغول لمدة {seenago}\n\n**السبب:** `{reasonafk}`\n\n{BODA_SOURCE}",
                    disable_web_page_preview=True,
                )
            if afktype == "animation":
                if str(reasonafk) == "None":
                    send = await message.reply_animation(
                        data,
                        caption=f"**{message.from_user.first_name}** رجع أونلاين بعد ما كان مشغول لمدة {seenago}\n\n{BODA_SOURCE}",
                    )
                else:
                    send = await message.reply_animation(
                        data,
                        caption=f"**{message.from_user.first_name}** رجع أونلاين بعد ما كان مشغول لمدة {seenago}\n\n**السبب:** `{reasonafk}`\n\n{BODA_SOURCE}",
                    )
            if afktype == "photo":
                if str(reasonafk) == "None":
                    send = await message.reply_photo(
                        photo=f"downloads/{user_id}.jpg",
                        caption=f"**{message.from_user.first_name}** رجع أونلاين بعد ما كان مشغول لمدة {seenago}\n\n{BODA_SOURCE}",
                    )
                else:
                    send = await message.reply_photo(
                        photo=f"downloads/{user_id}.jpg",
                        caption=f"**{message.from_user.first_name}** رجع أونلاين بعد ما كان مشغول لمدة {seenago}\n\n**السبب:** `{reasonafk}`\n\n{BODA_SOURCE}",
                    )
        except Exception:
            send = await message.reply_text(
                f"**{message.from_user.first_name}** نورت الشات من جديد!\n\n{BODA_SOURCE}",
                disable_web_page_preview=True,
            )

    if len(message.command) == 1 and not message.reply_to_message:
        details = {"type": "text", "time": time.time(), "data": None, "reason": None}
    elif len(message.command) > 1 and not message.reply_to_message:
        _reason = (message.text.split(None, 1)[1].strip())[:100]
        details = {"type": "text_reason", "time": time.time(), "data": None, "reason": _reason}
    elif len(message.command) == 1 and message.reply_to_message.animation:
        _data = message.reply_to_message.animation.file_id
        details = {"type": "animation", "time": time.time(), "data": _data, "reason": None}
    elif len(message.command) > 1 and message.reply_to_message.animation:
        _data = message.reply_to_message.animation.file_id
        _reason = (message.text.split(None, 1)[1].strip())[:100]
        details = {"type": "animation", "time": time.time(), "data": _data, "reason": _reason}
    elif len(message.command) == 1 and message.reply_to_message.photo:
        await app.download_media(message.reply_to_message, file_name=f"{user_id}.jpg")
        details = {"type": "photo", "time": time.time(), "data": None, "reason": None}
    elif len(message.command) > 1 and message.reply_to_message.photo:
        await app.download_media(message.reply_to_message, file_name=f"{user_id}.jpg")
        _reason = message.text.split(None, 1)[1].strip()
        details = {"type": "photo", "time": time.time(), "data": None, "reason": _reason}
    elif len(message.command) == 1 and message.reply_to_message.sticker:
        if message.reply_to_message.sticker.is_animated:
            details = {"type": "text", "time": time.time(), "data": None, "reason": None}
        else:
            await app.download_media(message.reply_to_message, file_name=f"{user_id}.jpg")
            details = {"type": "photo", "time": time.time(), "data": None, "reason": None}
    elif len(message.command) > 1 and message.reply_to_message.sticker:
        _reason = (message.text.split(None, 1)[1].strip())[:100]
        if message.reply_to_message.sticker.is_animated:
            details = {"type": "text_reason", "time": time.time(), "data": None, "reason": _reason}
        else:
            await app.download_media(message.reply_to_message, file_name=f"{user_id}.jpg")
            details = {"type": "photo", "time": time.time(), "data": None, "reason": _reason}
    else:
        details = {"type": "text", "time": time.time(), "data": None, "reason": None}

    await add_afk(user_id, details)
    await message.reply_text(f"**{message.from_user.first_name}** في وضع المشغول دلوقتي!\n\n{BODA_SOURCE}")


chat_watcher_group = 1

@app.on_message(~filters.me & ~filters.bot & ~filters.via_bot, group=chat_watcher_group)
async def chat_watcher_func(_, message):
    if message.sender_chat:
        return
    userid = message.from_user.id
    user_name = message.from_user.first_name
    if message.entities:
        possible = ["/afk", f"/afk@{app.username}"]
        message_text = message.text or message.caption
        for entity in message.entities:
            if entity.type == MessageEntityType.BOT_COMMAND:
                if (message_text[0 : 0 + entity.length]).lower() in possible:
                    return

    msg = ""
    replied_user_id = 0

    verifier, reasondb = await is_afk(userid)
    if verifier:
        await remove_afk(userid)
        try:
            afktype = reasondb["type"]
            timeafk = reasondb["time"]
            seenago = get_readable_time((int(time.time() - timeafk)))
            msg += f"**{user_name[:25]}** رجع أونلاين بعد ما كان مشغول لمدة {seenago}\n\n"
        except:
            msg += f"**{user_name[:25]}** رجع أونلاين\n\n"

    if message.reply_to_message:
        try:
            replied_first_name = message.reply_to_message.from_user.first_name
            replied_user_id = message.reply_to_message.from_user.id
            verifier, reasondb = await is_afk(replied_user_id)
            if verifier:
                try:
                    timeafk = reasondb["time"]
                    reasonafk = reasondb["reason"]
                    seenago = get_readable_time((int(time.time() - timeafk)))
                    if not reasonafk:
                        msg += f"**{replied_first_name[:25]}** مشغول بقاله {seenago}\n\n"
                    else:
                        msg += f"**{replied_first_name[:25]}** مشغول بقاله {seenago}\n**السبب:** `{reasonafk}`\n\n"
                except Exception:
                    msg += f"**{replied_first_name}** مشغول حالياً..\n\n"
        except:
            pass

    if message.entities:
        entity = message.entities
        j = 0
        for x in range(len(entity)):
            if (entity[j].type) == MessageEntityType.MENTION:
                found = re.findall("@([_0-9a-zA-Z]+)", message.text)
                try:
                    get_user = found[j]
                    user = await app.get_users(get_user)
                    if user.id == replied_user_id:
                        j += 1
                        continue
                except:
                    j += 1
                    continue
                verifier, reasondb = await is_afk(user.id)
                if verifier:
                    try:
                        timeafk = reasondb["time"]
                        reasonafk = reasondb["reason"]
                        seenago = get_readable_time((int(time.time() - timeafk)))
                        if not reasonafk:
                            msg += f"**{user.first_name[:25]}** مشغول بقاله {seenago}\n\n"
                        else:
                            msg += f"**{user.first_name[:25]}** مشغول بقاله {seenago}\n**السبب:** `{reasonafk}`\n\n"
                    except:
                        msg += f"**{user.first_name[:25]}** في وضع المشغول\n\n"
            j += 1

    if msg != "":
        try:
            await message.reply_text(f"{msg}{BODA_SOURCE}", disable_web_page_preview=True)
        except:
            return
