import os 
import random
from datetime import datetime 
from telegraph import upload_file
from PIL import Image , ImageDraw
from pyrogram import *
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from pyrogram.enums import *

# ➻ sᴏᴜʀᴄᴇ : بُودَا | ʙᴏᴅَا

# ملفات البوت
from BrandrdXMusic import app as app
from BrandrdXMusic.mongo.couples_db import _get_image, get_couple

POLICE = [
    [
        InlineKeyboardButton(
            text="👑 مـالـك الـبـوت 👑",
            url=f"https://t.me/S_G0C7",
        ),
    ],
    [
        InlineKeyboardButton(
            text="✨ سـورس بُـودَا ✨",
            url=f"https://t.me/SourceBoda",
        ),
    ]
]


def dt():
    now = datetime.now()
    dt_string = now.strftime("%d/%m/%Y %H:%M")
    dt_list = dt_string.split(" ")
    return dt_list
    

def dt_tom():
    a = (
        str(int(dt()[0].split("/")[0]) + 1)
        + "/"
        + dt()[0].split("/")[1]
        + "/"
        + dt()[0].split("/")[2]
    )
    return a

tomorrow = str(dt_tom())
today = str(dt()[0])

@app.on_message(filters.command(["couples", "كابلز", "عشاق"]))
async def ctest(_, message):
    cid = message.chat.id
    if message.chat.type == ChatType.PRIVATE:
        return await message.reply_text("**هـذا الأمـر يـعـمـل فـي الـمـجـمـوعـات فـقـط يـا حـب.⚠️**")
    try:
         msg = await message.reply_text("**جـاري اخـتـيـار كـابـلـز الـيـوم.. 💖**")
         
         list_of_users = []

         async for i in app.get_chat_members(message.chat.id, limit=50):
             if not i.user.is_bot:
               list_of_users.append(i.user.id)

         if len(list_of_users) < 2:
             return await msg.edit("**الـمـجـمـوعـة مـحـتـاجـة أعـضـاء أكـتـر عـشـان نـخـتـار كـابـلـز! 🤷🏻‍♂️**")

         c1_id = random.choice(list_of_users)
         c2_id = random.choice(list_of_users)
         while c1_id == c2_id:
              c1_id = random.choice(list_of_users)


         photo1 = (await app.get_chat(c1_id)).photo
         photo2 = (await app.get_chat(c2_id)).photo
 
         N1 = (await app.get_users(c1_id)).mention 
         N2 = (await app.get_users(c2_id)).mention
         
         try:
            p1 = await app.download_media(photo1.big_file_id, file_name="pfp.png")
         except Exception:
            p1 = "BrandrdXMusic/assets/upic.png"
         try:
            p2 = await app.download_media(photo2.big_file_id, file_name="pfp1.png")
         except Exception:
            p2 = "BrandrdXMusic/assets/upic.png"
            
         img1 = Image.open(f"{p1}")
         img2 = Image.open(f"{p2}")

         img = Image.open("BrandrdXMusic/assets/cppicbranded.jpg")

         img1 = img1.resize((437,437))
         img2 = img2.resize((437,437))

         mask = Image.new('L', img1.size, 0)
         draw = ImageDraw.Draw(mask) 
         draw.ellipse((0, 0) + img1.size, fill=255)

         mask1 = Image.new('L', img2.size, 0)
         draw = ImageDraw.Draw(mask1) 
         draw.ellipse((0, 0) + img2.size, fill=255)


         img1.putalpha(mask)
         img2.putalpha(mask1)

         draw = ImageDraw.Draw(img)

         img.paste(img1, (116, 160), img1)
         img.paste(img2, (789, 160), img2)

         img.save(f'test_{cid}.png')
    
         TXT = f"""
**✫ كـابـلـز الـيـوم بـالـمـجـمـوعـة :**

**{N1} + {N2} = 💚**

**سـيـتـم اخـتـيـار كـابـلـز جـديـد يـوم {tomorrow} !!**
"""
    
         await message.reply_photo(
             f"test_{cid}.png", 
             caption=TXT, 
             reply_markup=InlineKeyboardMarkup(POLICE)
         )
         await msg.delete()
         
         # تنظيف الملفات
         if os.path.exists(f"test_{cid}.png"):
             os.remove(f"test_{cid}.png")

    except Exception as e:
        print(str(e))
         

__mod__ = "الـكـابـلـز"
__help__ = """
**» /couples** - لـعـرض كـابـلـز الـيـوم فـي الـجـروب بـتـنـسـيـق رائع.
"""

# ➻ sᴏᴜʀᴄᴇ : بُودَا | ʙᴏᴅَا
