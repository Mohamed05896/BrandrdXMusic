from io import BytesIO

from httpx import AsyncClient, Timeout
from pyrogram import filters
from pyrogram.types import Message

from BrandrdXMusic import app

# ➻ sᴏᴜʀᴄᴇ : بُودَا | ʙᴏᴅᴀ

fetch = AsyncClient(
    http2=True,
    verify=False,
    headers={
        "Accept-Language": "id-ID",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36 Edge/107.0.1418.42",
    },
    timeout=Timeout(20),
)


class QuotlyException(Exception):
    pass


async def get_message_sender_id(ctx: Message):
    if ctx.forward_date:
        if ctx.forward_sender_name:
            return 1
        elif ctx.forward_from:
            return ctx.forward_from.id
        elif ctx.forward_from_chat:
            return ctx.forward_from_chat.id
        else:
            return 1
    elif ctx.from_user:
        return ctx.from_user.id
    elif ctx.sender_chat:
        return ctx.sender_chat.id
    else:
        return 1


async def get_message_sender_name(ctx: Message):
    if ctx.forward_date:
        if ctx.forward_sender_name:
            return ctx.forward_sender_name
        elif ctx.forward_from:
            return (
                f"{ctx.forward_from.first_name} {ctx.forward_from.last_name}"
                if ctx.forward_from.last_name
                else ctx.forward_from.first_name
            )

        elif ctx.forward_from_chat:
            return ctx.forward_from_chat.title
        else:
            return ""
    elif ctx.from_user:
        if ctx.from_user.last_name:
            return f"{ctx.from_user.first_name} {ctx.from_user.last_name}"
        else:
            return ctx.from_user.first_name
    elif ctx.sender_chat:
        return ctx.sender_chat.title
    else:
        return ""


async def get_custom_emoji(ctx: Message):
    if ctx.forward_date:
        return (
            ""
            if ctx.forward_sender_name
            or not ctx.forward_from
            and ctx.forward_from_chat
            or not ctx.forward_from
            else ctx.forward_from.emoji_status.custom_emoji_id
        )

    return ctx.from_user.emoji_status.custom_emoji_id if ctx.from_user else ""


async def get_message_sender_username(ctx: Message):
    if ctx.forward_date:
        if (
            not ctx.forward_sender_name
            and not ctx.forward_from
            and ctx.forward_from_chat
            and ctx.forward_from_chat.username
        ):
            return ctx.forward_from_chat.username
        elif (
            not ctx.forward_sender_name
            and not ctx.forward_from
            and ctx.forward_from_chat
            or ctx.forward_sender_name
            or not ctx.forward_from
        ):
            return ""
        else:
            return ctx.forward_from.username or ""
    elif ctx.from_user and ctx.from_user.username:
        return ctx.from_user.username
    elif (
        ctx.from_user
        or ctx.sender_chat
        and not ctx.sender_chat.username
        or not ctx.sender_chat
    ):
        return ""
    else:
        return ctx.sender_chat.username


async def get_message_sender_photo(ctx: Message):
    if ctx.forward_date:
        if (
            not ctx.forward_sender_name
            and not ctx.forward_from
            and ctx.forward_from_chat
            and ctx.forward_from_chat.photo
        ):
            return {
                "small_file_id": ctx.forward_from_chat.photo.small_file_id,
                "small_photo_unique_id": ctx.forward_from_chat.photo.small_photo_unique_id,
                "big_file_id": ctx.forward_from_chat.photo.big_file_id,
                "big_photo_unique_id": ctx.forward_from_chat.photo.big_photo_unique_id,
            }
        elif (
            not ctx.forward_sender_name
            and not ctx.forward_from
            and ctx.forward_from_chat
            or ctx.forward_sender_name
            or not ctx.forward_from
        ):
            return ""
        else:
            return (
                {
                    "small_file_id": ctx.forward_from.photo.small_file_id,
                    "small_photo_unique_id": ctx.forward_from.photo.small_photo_unique_id,
                    "big_file_id": ctx.forward_from.photo.big_file_id,
                    "big_photo_unique_id": ctx.forward_from.photo.big_photo_unique_id,
                }
                if ctx.forward_from.photo
                else ""
            )

    elif ctx.from_user and ctx.from_user.photo:
        return {
            "small_file_id": ctx.from_user.photo.small_file_id,
            "small_photo_unique_id": ctx.from_user.photo.small_photo_unique_id,
            "big_file_id": ctx.from_user.photo.big_file_id,
            "big_photo_unique_id": ctx.from_user.photo.big_photo_unique_id,
        }
    elif (
        ctx.from_user
        or ctx.sender_chat
        and not ctx.sender_chat.photo
        or not ctx.sender_chat
    ):
        return ""
    else:
        return {
            "small_file_id": ctx.sender_chat.photo.small_file_id,
            "small_photo_unique_id": ctx.sender_chat.photo.small_photo_unique_id,
            "big_file_id": ctx.sender_chat.photo.big_file_id,
            "big_photo_unique_id": ctx.sender_chat.photo.big_photo_unique_id,
        }


async def get_text_or_caption(ctx: Message):
    if ctx.text:
        return ctx.text
    elif ctx.caption:
        return ctx.caption
    else:
        return ""


async def pyrogram_to_quotly(messages, is_reply):
    if not isinstance(messages, list):
        messages = [messages]
    payload = {
        "type": "quote",
        "format": "png",
        "backgroundColor": "#1b1429",
        "messages": [],
    }

    for message in messages:
        the_message_dict_to_append = {}
        if message.entities:
            the_message_dict_to_append["entities"] = [
                {
                    "type": entity.type.name.lower(),
                    "offset": entity.offset,
                    "length": entity.length,
                }
                for entity in message.entities
            ]
        elif message.caption_entities:
            the_message_dict_to_append["entities"] = [
                {
                    "type": entity.type.name.lower(),
                    "offset": entity.offset,
                    "length": entity.length,
                }
                for entity in message.caption_entities
            ]
        else:
            the_message_dict_to_append["entities"] = []
        the_message_dict_to_append["chatId"] = await get_message_sender_id(message)
        the_message_dict_to_append["text"] = await get_text_or_caption(message)
        the_message_dict_to_append["avatar"] = True
        the_message_dict_to_append["from"] = {}
        the_message_dict_to_append["from"]["id"] = await get_message_sender_id(message)
        the_message_dict_to_append["from"]["name"] = await get_message_sender_name(
            message
        )
        the_message_dict_to_append["from"]["username"] = (
            await get_message_sender_username(message)
        )
        the_message_dict_to_append["from"]["type"] = message.chat.type.name.lower()
        the_message_dict_to_append["from"]["photo"] = await get_message_sender_photo(
            message
        )
        if message.reply_to_message and is_reply:
            the_message_dict_to_append["replyMessage"] = {
                "name": await get_message_sender_name(message.reply_to_message),
                "text": await get_text_or_caption(message.reply_to_message),
                "chatId": await get_message_sender_id(message.reply_to_message),
            }
        else:
            the_message_dict_to_append["replyMessage"] = {}
        payload["messages"].append(the_message_dict_to_append)
    r = await fetch.post("https://bot.lyo.su/quote/generate.png", json=payload)
    if not r.is_error:
        return r.read()
    else:
        raise QuotlyException(r.json())


def isArgInt(txt) -> list:
    count = txt
    try:
        count = int(count)
        return [True, count]
    except ValueError:
        return [False, 0]


@app.on_message(filters.command(["q", "r"]) & filters.reply)
async def msg_quotly_cmd(self: app, ctx: Message):
    ww = await ctx.reply_text("**صـبـرك ثـوانـي جـاري تـنـفـيـذ طـلـبـك...**")
    is_reply = False
    if ctx.command[0].endswith("r"):
        is_reply = True
    if len(ctx.text.split()) > 1:
        check_arg = isArgInt(ctx.command[1])
        if check_arg[0]:
            if check_arg[1] < 2 or check_arg[1] > 10:
                await ww.delete()
                return await ctx.reply_text("**الـنـطـاق غـيـر صـالـح يـا مـطـور ⚠️**")
            try:
                messages = [
                    i
                    for i in await self.get_messages(
                        chat_id=ctx.chat.id,
                        message_ids=range(
                            ctx.reply_to_message.id,
                            ctx.reply_to_message.id + (check_arg[1] + 5),
                        ),
                        replies=-1,
                    )
                    if not i.empty and not i.media
                ]
            except Exception:
                return await ctx.reply_text("**مـش عـارف جـلـب الـرسـايـل لـيـه! 🤷🏻‍♂️**")
            try:
                make_quotly = await pyrogram_to_quotly(messages, is_reply=is_reply)
                bio_sticker = BytesIO(make_quotly)
                bio_sticker.name = "boda_quote.webp"
                await ww.delete()
                return await ctx.reply_sticker(bio_sticker)
            except Exception:
                await ww.delete()
                return await ctx.reply_text("**فـشـل فـي عـمـل الـمـلـصـق 🤷🏻‍♂️**")
    try:
        messages_one = await self.get_messages(
            chat_id=ctx.chat.id, message_ids=ctx.reply_to_message.id, replies=-1
        )
        messages = [messages_one]
    except Exception:
        await ww.delete()
        return await ctx.reply_text("**مـش عـارف أجـيـب الـرسـالـة دي! 🤷🏻‍♂️**")
    try:
        make_quotly = await pyrogram_to_quotly(messages, is_reply=is_reply)
        bio_sticker = BytesIO(make_quotly)
        bio_sticker.name = "boda_quote.webp"
        await ww.delete()
        return await ctx.reply_sticker(bio_sticker)
    except Exception as e:
        await ww.delete()
        return await ctx.reply_text(f"**حـصـل خـطـأ يـا مـطـور :** `{e}`")


__HELP__ = """
**أوامـر صـنـع الـاقتـبـاسـات الـمـدلعـة**

اسـتـخـدم الأوامـر دي عـلـى أي رسـالـة (ريـبـلاي):

- `/q`: لـعـمـل مـلـصـق لـرسـالـة واحـدة.
- `/r`: لـعـمـل مـلـصـق لـلـرسـالـة مـع الـرد الـخـاص بـهـا.

**أمـثـلـة:**
- `/q 5`: لـعـمـل مـلـصـق يـجـمـع 5 رسـايـل مـتـتـالـيـة.

**مـلاحـظـة:**
لازم تـرد (ريـبـلاي) عـلـى الـرسـالـة الـلـي عـايـز تـحـولـهـا لـمـلـصـق.
"""

__MODULE__ = "الـاقتـبـاسـات"

# ➻ sᴏᴜʀᴄᴇ : بُودَا | ʙᴏᴅᴀ
