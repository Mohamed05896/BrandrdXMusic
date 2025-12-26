from strings import get_string
from BrandrdXMusic.misc import SUDOERS
from BrandrdXMusic.utils.database import get_lang, is_maintenance
from config import SUPPORT_CHAT
from BrandrdXMusic import app


def language(mystic):
    async def wrapper(_, message, **kwargs):
        if await is_maintenance() is False:
            if message.from_user.id not in SUDOERS:
                return await message.reply_text(
                    text=(
                        f"{app.mention} ⚠️ الـبـوت تـحـت الـصـيـانـة\n\n"
                        f"🔧 يـرجـى الـدخـول إلـى <a href={SUPPORT_CHAT}>دعـم الـبـوت</a>\n"
                        f"📌 لـمـعـرفـة الـسـبـب والـتـفـاصـيـل."
                    ),
                    disable_web_page_preview=True,
                )
        try:
            await message.delete()
        except:
            pass

        try:
            language = await get_lang(message.chat.id)
            language = get_string(language)
        except:
            language = get_string("ar")
        return await mystic(_, message, language)

    return wrapper


def languageCB(mystic):
    async def wrapper(_, CallbackQuery, **kwargs):
        if await is_maintenance() is False:
            if CallbackQuery.from_user.id not in SUDOERS:
                return await CallbackQuery.answer(
                    text=(
                        f"{app.mention} ⚠️ الـبـوت تـحـت الـصـيـانـة\n\n"
                        f"🔧 يـرجـى الـتـوجـه إلـى دعـم الـبـوت\n"
                        f"📌 لـمـعـرفـة الـسـبـب والـتـفـاصـيـل."
                    ),
                    show_alert=True,
                )
        try:
            language = await get_lang(CallbackQuery.message.chat.id)
            language = get_string(language)
        except:
            language = get_string("ar")
        return await mystic(_, CallbackQuery, language)

    return wrapper


def LanguageStart(mystic):
    async def wrapper(_, message, **kwargs):
        try:
            language = await get_lang(message.chat.id)
            language = get_string(language)
        except:
            language = get_string("ar")
        return await mystic(_, message, language)

    return wrapper
