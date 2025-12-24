import requests
from pyrogram import filters
from BrandrdXMusic import app

# ➻ sᴏᴜʀᴄᴇ : بُودَا | ʙᴏᴅَا

@app.on_message(filters.command(["ig", "instagram", "reel"]))
async def download_instagram_video(client, message):
    if len(message.command) < 2:
        await message.reply_text(
            "**يـا حـبـيـب قـلـبـي حـط رابـط الـريـل بـعـد الأمـر.. 🔗**"
        )
        return
        
    a = await message.reply_text("**جـاري تـحـمـيـل الـفـيـديـو.. صـبـرك يـا حـب.. ⏳**")
    url = message.text.split()[1]
    api_url = (
        f"https://nodejs-1xn1lcfy3-jobians.vercel.app/v2/downloader/instagram?url={url}"
    )

    try:
        response = requests.get(api_url)
        data = response.json()

        if data["status"]:
            video_url = data["data"][0]["url"]
            await a.delete()
            await client.send_video(
                message.chat.id, 
                video_url,
                caption=f"**تـم الـتـحـمـيـل بـنـجـاح يـا رايـق.. ✨**\n\n**➻ sᴏᴜʀᴄᴇ : بُودَا | ʙᴏᴅَا**"
            )
        else:
            await a.edit("**عـذراً يـا حـب.. مـقـدرتـش أنـزل الـريـل ده.. 🤷🏻‍♂️**")
    except Exception as e:
        await a.edit(f"**فـيـه مـشـكـلـة يـا بـطـل :** `{e}`")


__MODULE__ = "الـإنـسـتـا"
__HELP__ = """
**أوامـر تـحـمـيـل الـإنـسـتـجـرام الـمدلـعـة :**

- `/reel` [الـرابـط] : لـتـحـمـيـل ريـل انـسـتـا.
- `/ig` [الـرابـط] : لـتـحـمـيـل ريـل انـسـتـا.
- `/instagram` [الـرابـط] : لـتـحـمـيـل ريـل انـسـتـا.

**➻ sᴏᴜʀᴄᴇ : بُودَا | ʙᴏᴅَا**
"""

# ➻ sᴏᴜʀᴄᴇ : بُودَا | ʙᴏᴅَا
