import asyncio
import importlib
from sys import argv
from pyrogram import idle
from pytgcalls.exceptions import NoActiveGroupCall

import config
from BrandrdXMusic import LOGGER, app, userbot
from BrandrdXMusic.core.call import Hotty
from BrandrdXMusic.misc import sudo
from BrandrdXMusic.plugins import ALL_MODULES
from BrandrdXMusic.utils.database import get_banned_users, get_gbanned
from config import BANNED_USERS


async def init():
    if (
        not config.STRING1
        and not config.STRING2
        and not config.STRING3
        and not config.STRING4
        and not config.STRING5
    ):
        LOGGER(__name__).error("⚠️ عذراً، لم يتم العثور على جلسات المساعد (String Session).")
        exit()
    await sudo()
    try:
        users = await get_gbanned()
        for user_id in users:
            BANNED_USERS.add(user_id)
        users = await get_banned_users()
        for user_id in users:
            BANNED_USERS.add(user_id)
    except:
        pass
    await app.start()
    for all_module in ALL_MODULES:
        importlib.import_module("BrandrdXMusic.plugins" + all_module)
    LOGGER("BrandrdXMusic.plugins").info("✅ تم تحميل جميع الإضافات والموديولات بنجاح.")
    await userbot.start()
    await Hotty.start()
    try:
        await Hotty.stream_call("https://graph.org/file/e999c40cb700e7c684b75.mp4")
    except NoActiveGroupCall:
        LOGGER("BrandrdXMusic").error(
            "❌ يرجى تفعيل المحادثة المرئية في مجموعة السجل أولاً.. يتم الإغلاق."
        )
        exit()
    except:
        pass
    await Hotty.decorators()
    LOGGER("BrandrdXMusic").info(
        "\n\n✨ تم تشغيل سورس بُودَا بنجاح ✨\n\n➻ sᴏᴜʀᴄᴇ : بُودَا | ʙᴏᴅᴀ\n"
    )
    await idle()
    await app.stop()
    await userbot.stop()
    LOGGER("BrandrdXMusic").info("🛑 يتم الآن إيقاف تشغيل البوت.. نراكم لاحقاً.\n\n➻ sᴏᴜʀᴄᴇ : بُودَا | ʙᴏᴅᴀ")


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(init())

# ➻ sᴏᴜʀᴄᴇ : بُودَا | ʙᴏᴅᴀ
