from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def speed_markup(_, chat_id):
    upl = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    text="🕒 بــطــيء 0.5x",
                    callback_data=f"SpeedUP {chat_id}|0.5",
                ),
                InlineKeyboardButton(
                    text="🕓 هــادئ 0.75x",
                    callback_data=f"SpeedUP {chat_id}|0.75",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="⚡ سـرعـة طـبـيـعـيـة 1.0x",
                    callback_data=f"SpeedUP {chat_id}|1.0",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🕤 سـريـع 1.5x",
                    callback_data=f"SpeedUP {chat_id}|1.5",
                ),
                InlineKeyboardButton(
                    text="🕛 سـريـع جـداً 2.0x",
                    callback_data=f"SpeedUP {chat_id}|2.0",
                ),
            ],
            [
                InlineKeyboardButton(
                    text=_["CLOSE_BUTTON"],
                    callback_data="close",
                ),
            ],
        ]
    )
    return upl
