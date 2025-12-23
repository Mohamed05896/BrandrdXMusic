import asyncio, os, time, aiohttp
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from asyncio import sleep
from BrandrdXMusic import app
from pyrogram import filters, Client, enums
from pyrogram.enums import ParseMode
from pyrogram.types import *
from typing import Union, Optional
import random

# تـوقـيـع الـسـورس
BODA_SIGNATURE = "➻ sᴏᴜʀᴄᴇ : بُودَا | ʙᴏᴅᴀ"

random_photo = [
    "https://i.ibb.co/C3Tn6qgt/pexels-dsnsyj-1139541.jpg",
    "https://i.ibb.co/MDCHLs5p/premium-photo-1669748157617-a3a83cc8ea23.jpg",
    "https://i.ibb.co/8QkPT67/bg2.jpg",
    "https://i.ibb.co/Pv3x0zDC/pexels-trupert-1032650.jpg",
    "https://telegra.ph/file/2973150dd62fd27a3a6ba.jpg",
]

# --------------------------------------------------------------------------------- #

get_font = lambda font_size, font_path: ImageFont.truetype(font_path, font_size)
resize_text = (
    lambda text_size, text: (text[:text_size] + "...").upper()
    if len(text) > text_size
    else text.upper()
)

# --------------------------------------------------------------------------------- #

async def get_userinfo_img(
    bg_path: str,
    font_path: str,
    user_id: Union[int, str],    
    profile_path: Optional[str] = None
):
    bg = Image.open(bg_path)

    if profile_path:
        img = Image.open(profile_path)
        mask = Image.new("L", img.size, 0)
        draw = ImageDraw.Draw(mask)
        draw.pieslice([(0, 0), img.size], 0, 360, fill=255)

        circular_img = Image.new("RGBA", img.size, (0, 0, 0, 0))
        circular_img.paste(img, (0, 0), mask)
        resized = circular_img.resize((400, 400))
        bg.paste(resized, (440, 160), resized)

    img_draw = ImageDraw.Draw(bg)

    img_draw.text(
        (529, 627),
        text=str(user_id).upper(),
        font=get_font(46, font_path),
        fill=(255, 255, 255),
    )

    path = f"./userinfo_img_{user_id}.png"
    bg.save(path)
    return path
   
# --------------------------------------------------------------------------------- #

bg_path = "BrandrdXMusic/assets/userinfo.png"
font_path = "BrandrdXMusic/assets/hiroko.ttf"

# --------------------------------------------------------------------------------- #

INFO_TEXT = """**
💎 ───※ الـمـعـلـومـات ※─── 💎

⭐ الـآيـدي ‣ **`{}`
**⭐ الـأسـم ‣ **{}
**⭐ الـلـقـب ‣ **{}
**⭐ الـيـوزر ‣ **`@{}`
**⭐ الـحـسـاب ‣ **{}
**⭐ الـتـواجد ‣ **{}
**⭐ الـديـسـي ‣ **{}
**⭐ الـبـايـو ‣ **`{}`

**➻ sᴏᴜʀᴄᴇ : بُودَا | ʙᴏᴅᴀ**
"""

# --------------------------------------------------------------------------------- #

async def userstatus(user_id):
   try:
      user = await app.get_users(user_id)
      x = user.status
      if x == enums.UserStatus.RECENTLY:
         return "مـتـواجـد مـؤخـراً"
      elif x == enums.UserStatus.LAST_WEEK:
          return "أخـر تـواجـد مـنـذ أسـبـوع"
      elif x == enums.UserStatus.LONG_AGO:
          return "مـنـذ فـتـرة طـويـلـة"
      elif x == enums.UserStatus.OFFLINE:
          return "غـيـر مـتـصـل"
      elif x == enums.UserStatus.ONLINE:
         return "مـتـصـل الـآن"
   except:
        return "تـعذر جـلـب الـحـالـة"
    
# --------------------------------------------------------------------------------- #

@app.on_message(filters.command(["info", "userinfo"], prefixes=["/", "!", "%", ",", "", ".", "@", "#"]))
async def userinfo(_, message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    # مـحـرك الـجـلـب الـمـوحد
    async def process_user(u_id):
        user_info = await app.get_chat(u_id)
        user = await app.get_users(u_id)
        status = await userstatus(user.id)
        
        id = user_info.id
        dc_id = user.dc_id if user.dc_id else "1"
        first_name = user_info.first_name 
        last_name = user_info.last_name if user_info.last_name else "لا يـوجـد"
        username = user_info.username if user_info.username else "لا يـوجـد"
        mention = user.mention
        bio = user_info.bio if user_info.bio else "لا يـوجـد نـبـذة شـخـصـيـة"
        
        if user.photo:
            photo = await app.download_media(user.photo.big_file_id)
            welcome_photo = await get_userinfo_img(
                bg_path=bg_path,
                font_path=font_path,
                user_id=user.id,
                profile_path=photo,
            )
        else:
            welcome_photo = random.choice(random_photo)
            
        await app.send_photo(
            chat_id, 
            photo=welcome_photo, 
            caption=INFO_TEXT.format(id, first_name, last_name, username, mention, status, dc_id, bio), 
            reply_to_message_id=message.id
        )

    try:
        if not message.reply_to_message and len(message.command) == 2:
            target_id = message.text.split(None, 1)[1]
            await process_user(target_id)
        elif not message.reply_to_message:
            await process_user(user_id)
        elif message.reply_to_message:
            await process_user(message.reply_to_message.from_user.id)
    except Exception as e:
        await message.reply_text(f"❌ **حـصـل خـطأ:** `{e}`")
