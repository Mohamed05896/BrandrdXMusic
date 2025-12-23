from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from config import SUPPORT_CHAT


def botplaylist_markup(_):
    buttons = [
        [
            InlineKeyboardButton(text="🥀 دعـم الـبـوت 🥀", url=SUPPORT_CHAT),
            InlineKeyboardButton(text="إغـلاق", callback_data="close"),
        ],
    ]
    return buttons


def close_markup(_):
    upl = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    text="🥀 دعـم الـبـوت 🥀",
                    url="https://t.me/music0587"
                ),
                InlineKeyboardButton(
                    text="إغـلاق",
                    callback_data="close",
                ),
            ]
        ]
    )
    return upl


def supp_markup(_):
    upl = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    text="🥀 دعـم الـبـوت 🥀",
                    url=SUPPORT_CHAT,
                ),
            ]
        ]
    )
    return upl
