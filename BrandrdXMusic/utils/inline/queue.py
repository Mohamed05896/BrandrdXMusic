from typing import Union
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

# ➻ sᴏᴜʀᴄᴇ : بُودَا | ʙᴏᴅᴀ

def queue_markup(
    _,
    DURATION,
    CPLAY,
    videoid,
    played: Union[bool, int] = None,
    dur: Union[bool, int] = None,
):
    not_dur = [
        [
            InlineKeyboardButton(
                text=_["QU_B_1"],
                callback_data=f"GetQueued {CPLAY}|{videoid}",
            ),
            InlineKeyboardButton(
                text=_["CLOSE_BUTTON"],
                callback_data="close",
            ),
        ]
    ]
    dur_buttons = [
        [
            InlineKeyboardButton(
                text=_["QU_B_2"].format(played, dur),
                callback_data="GetTimer",
            )
        ],
        [
            InlineKeyboardButton(
                text=_["QU_B_1"],
                callback_data=f"GetQueued {CPLAY}|{videoid}",
            ),
            InlineKeyboardButton(
                text=_["CLOSE_BUTTON"],
                callback_data="close",
            ),
        ],
    ]
    # تعديل بسيط لضمان اختيار القائمة الصح بناءً على الوقت
    upl = InlineKeyboardMarkup(not_dur if DURATION == "Unknown" or DURATION == "بث مباشر" else dur_buttons)
    return upl


def queue_back_markup(_, CPLAY):
    upl = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    text=_["BACK_BUTTON"],
                    callback_data=f"queue_back_timer {CPLAY}",
                ),
                InlineKeyboardButton(
                    text=_["CLOSE_BUTTON"],
                    callback_data="close",
                ),
            ]
        ]
    )
    return upl


def aq_markup(_, chat_id):
    buttons = [
        [
            InlineKeyboardButton(text="▷", callback_data=f"ADMIN Resume|{chat_id}"),
            InlineKeyboardButton(text="II", callback_data=f"ADMIN Pause|{chat_id}"),
            InlineKeyboardButton(text="‣‣I", callback_data=f"ADMIN Skip|{chat_id}"),
            InlineKeyboardButton(text="▢", callback_data=f"ADMIN Stop|{chat_id}"),
        ],
        [
            InlineKeyboardButton(
                text="❖ الـمـالـك ❖", url="https://t.me/S_G0C7"
            ),
            InlineKeyboardButton(
                text="❖ الـدعـم ❖", url="https://t.me/music0587"
            ),
        ],
        [
            InlineKeyboardButton(text="➻ sᴏᴜʀᴄᴇ : بُودَا | ʙᴏᴅᴀ", url="https://t.me/BRANDRD_BOT")
        ],
        [InlineKeyboardButton(text=_["CLOSE_BUTTON"], callback_data="close")],
    ]
    return buttons


def queuemarkup(_, vidid, chat_id):
    from BrandrdXMusic import app # استيراد عشان اليوزر نيم
    buttons = [
        [
            InlineKeyboardButton(
                text="๏ أضـف الـبـوت لـمـجـمـوعـتـك ๏",
                url=f"https://t.me/{app.username}?startgroup=true",
            ),
        ],
        [
            InlineKeyboardButton(
                text="إيـقـاف مـؤقـت",
                callback_data=f"ADMIN Pause|{chat_id}",
            ),
            InlineKeyboardButton(
                text="إيـقـاف",
                callback_data=f"ADMIN Stop|{chat_id}",
            ),
            InlineKeyboardButton(
                text="تـخـطـي",
                callback_data=f"ADMIN Skip|{chat_id}",
            ),
        ],
        [
            InlineKeyboardButton(
                text="اسـتـئـنـاف",
                callback_data=f"ADMIN Resume|{chat_id}",
            ),
            InlineKeyboardButton(
                text="إعـادة",
                callback_data=f"ADMIN Replay|{chat_id}",
            ),
        ],
        [
            InlineKeyboardButton(
                text="๏ قـنـاة الـسـورس ๏",
                url="https://t.me/music0587",
            ),
        ],
        [
            InlineKeyboardButton(text="➻ sᴏᴜʀᴄᴇ : بُودَا | ʙᴏᴅᴀ", url="https://t.me/SourceBoda")
        ],
    ]
    return buttons

# ➻ sᴏᴜʀᴄᴇ : بُودَا | ʙᴏᴅᴀ
