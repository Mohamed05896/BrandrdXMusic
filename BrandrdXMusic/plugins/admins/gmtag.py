from BrandrdXMusic import app 
import asyncio
import random
from pyrogram import Client, filters
from pyrogram.enums import ChatType, ChatMemberStatus
from pyrogram.errors import UserNotParticipant
from pyrogram.types import ChatPermissions

spam_chats = []

EMOJI = [ "🦋🦋🦋🦋🦋",
          "🧚🌸🧋🍬🫖",
          "🥀🌷🌹🌺💐",
          "🌸🌿💮🌱🌵",
          "❤️💚💙💜🖤",
          "💓💕💞💗💖",
          "🌸💐🌺🌹🦋",
          "🍔🦪🍛🍲🥗",
          "🍎🍓🍒🍑🌶️",
          "🧋🥤🧋🥛🍷",
          "🍬🍭🧁🎂🍡",
          "🍨🧉🍺☕🍻",
          "🥪🥧🍦🍥🍚",
          "🫖☕🍹🍷🥛",
          "☕🧃🍩🍦🍙",
          "🍁🌾💮🍂🌿",
          "🌨️🌥️⛈️🌩️🌧️",
          "🌷🏵️🌸🌺💐",
          "💮🌼🌻🍀🍁",
          "🧟🦸🦹🧙👸",
          "🧅🍠🥕🌽🥦",
          "🐷🐹🐭🐨🐻‍❄️",
          "🦋🐇🐀🐈🐈‍⬛",
          "🌼🌳🌲🌴🌵",
          "🥩🍋🍐🍈🍇",
          "🍴🍽️🔪🍶🥃",
          "🕌🏰🏩⛩️🏩",
          "🎉🎊🎈🎂🎀",
          "🪴🌵🌴🌳🌲",
          "🎄🎋🎍🎑🎎",
          "🦅🦜🕊️🦤🦢",
          "🦤🦩🦚🦃🦆",
          "🐬🦭🦈🐋🐳",
          "🐔🐟🐠🐡🦐",
          "🦩🦀🦑🐙🦪",
          "🐦🦂🕷️🕸️🐚",
          "🥪🍰🥧🍨🍨",
          " 🥬🍉🧁🧇",
        ]

TAGMES = [ " **➠ تصبح على خير يا جميل 🌚** ",
           " **➠ ششش.. نام بقى كفاية رغي 🙊** ",
           " **➠ سيب الموبايل ونام يا بطل، العفريت هيطلعلك..👻** ",
           " **➠ يا بيبي كملوا حب الصبح، نام دلوقتي بقا..؟؟ 🥲** ",
           " **➠ يا طنط تعالي شوفي ابنك، قاعد يكلم صاحبته تحت اللحاف ومش عايز ينام 😜** ",
           " **➠ يا حاج الحق ابنك، طول الليل ماسك الموبايل ومش مريحه 🤭** ",
           " **➠ يا روحي، ما تيجي نضبط سهرة الليلة..؟؟ 🌠** ",
           " **➠ تصبح على خير يا نجم.. 🙂** ",
           " **➠ أحلام سعيدة ونوم الهنا يا رب..؟؟ ✨** ",
           " **➠ الوقت اتأخر أوي، نام بقى عشان تركز..؟؟ 🌌** ",
           " **➠ يا ماما الحقي الساعة داخلة على 11 وهو لسة صاحي بيلعب في الموبايل 🕦** ",
           " **➠ إنت موراكش مصلحة الصبح؟ نام بقى وبطل سهر 🏫** ",
           " **➠ يا بيبي، نوم العوافي وأحلام وردية..؟؟ 😊** ",
           " **➠ الدنيا برد أوي النهاردة، أنا هنام بقى وأتغطى كويس 🌼** ",
           " **➠ يا عسل، تصبح على خير 🌷** ",
           " **➠ أنا رايحة أنام بقى، أحلام سعيدة ليكم 🏵️** ",
           " **➠ مساء الفل عليكم، تصبحوا على خير 🍃** ",
           " **➠ إيه يا بيبي، لسة منمتش ولا إيه؟ ☃️** ",
           " **➠ طابت ليلتكم، الوقت سرقنا.. ⛄** ",
           " **➠ أنا ماشية أعيط.. قصدي أنام، تصبحوا على خير 😁** ",
           " **➠ يا سمكة يا فلة، نامي واصحي زي الفل، تصبحي على خير 🌄** ",
           " **➠ ليلة سعيدة ومنورة بيكم 🤭** ",
           " **➠ الليل جه والنهار مشي، والقمر نور بدل الشمس.. نوم الهنا 😊** ",
           " **➠ يا رب كل أحلامك تتحقق ❤️** ",
           " **➠ تصبح على خير، أحلام كلها سكر 💚** ",
           " **➠ أنا خلاص فصلت وعايز أنام 🥱** ",
           " **➠ يا صاحبي تصبح على ألف خير 💤** ",
           " **➠ ما تيجي نسهر سهرة حلوة النهاردة 🥰** ",
           " **➠ بتعمل إيه صاحي لدلوقتي؟ مش هتموت وتنام؟ 😜** ",
           " **➠ غمض عينك ونام في دفا، والملايكة هتحرسك الليلة.. 💫** ",
           ]

VC_TAG = [ "**➠ صباح الفل، عامل إيه يا وحش 🐱**",
         "**➠ صباح الخير، الشمس طلعت وإنت لسة نايم 🌤️**",
         "**➠ يا بيبي صباح الورد، اشرب الشاي يلا ☕**",
         "**➠ اصحى بسرعة، موراكش شغل ولا إيه 🏫**",
         "**➠ صباحو، قوم فز من السرير وإلا هكب عليك مية ساقعة 🧊**",
         "**➠ اصحى يا روحي وفوق كدة، الفطار جاهز يا بطل 🫕**",
         "**➠ مفيش شغل النهاردة ولا إيه؟ الساعة بقت كام وإنت لسة نايم 🏣**",
         "**➠ صباح القشطة يا صاحبي، تشرب شاي ولا قهوة ☕🍵**",
         "**➠ يا بيبي الساعة داخلة على 8 وإنت في سابع نومة 🕖**",
         "**➠ اصحى يا حنكش، النوم مش هيطير.. ☃️**",
         "**➠ صباح الفل، يومك يبقى عسل زيك... 🌄**",
         "**➠ صباح الجمال، يومك كله رزق وبركة... 🪴**",
         "**➠ يا بيبي صباح الخير، عامل إيه النهاردة 😇**",
         "**➠ يا طنط شوفي ابنك النايم ده، مش عايز يقوم ليه... 😵‍💫**",
         "**➠ طول الليل حب وكلام ودلوقتي نايم ومش عايز تصحى.. قوم بقا 😏**",
         "**➠ يا بيبي صباح القشطة، اصحى وصبح على الصحاب في الجروب... 🌟**",
         "**➠ يا بابا إلحق ابنك، مصلحته هتضيع وهو لسة في السرير... 🥲**",
         "**➠ صباح الورد يا روح قلبي، بتعمل إيه... 😅**",
         "**➠ صباح الفل يا زميلي، فطرت ولا لسة... 🍳**",
        ]


@app.on_message(filters.command(["gntag", "tagmember" ], prefixes=["/", "@", "#"]))
async def mentionall(client, message):
    chat_id = message.chat.id
    if message.chat.type == ChatType.PRIVATE:
        return await message.reply("๏ الأمر ده للمجموعات بس يا نجم.")

    is_admin = False
    try:
        participant = await client.get_chat_member(chat_id, message.from_user.id)
    except UserNotParticipant:
        is_admin = False
    else:
        if participant.status in (
            ChatMemberStatus.ADMINISTRATOR,
            ChatMemberStatus.OWNER
        ):
            is_admin = True
    if not is_admin:
        return await message.reply("๏ إنت مش أدمن يا جميل، المنشن للمشرفين بس. ")

    if message.reply_to_message and message.text:
        return await message.reply("اكتب الأمر كدة: /tagall + الكلمة، أو رد على أي رسالة.")
    elif message.text:
        mode = "text_on_cmd"
        msg = message.text
    elif message.reply_to_message:
        mode = "text_on_reply"
        msg = message.reply_to_message
        if not msg:
            return await message.reply("رد على أي رسالة عشان أبدأ منشن...")
    else:
        return await message.reply("اكتب الأمر كدة: /tagall + الكلمة، أو رد على أي رسالة.")
    if chat_id in spam_chats:
        return await message.reply("๏ وقف المنشن اللي شغال الأول يا غالي...")
    spam_chats.append(chat_id)
    usrnum = 0
    usrtxt = ""
    async for usr in client.get_chat_members(chat_id):
        if not chat_id in spam_chats:
            break
        if usr.user.is_bot:
            continue
        usrnum += 1
        usrtxt += "<a href='tg://user?id={}'>{}</a>".format(usr.user.id, usr.user.first_name)

        if usrnum == 1:
            if mode == "text_on_cmd":
                txt = f"{usrtxt} {random.choice(TAGMES)}"
                await client.send_message(chat_id, txt)
            elif mode == "text_on_reply":
                await msg.reply(f"[{random.choice(EMOJI)}](tg://user?id={usr.user.id})")
            await asyncio.sleep(4)
            usrnum = 0
            usrtxt = ""
    try:
        spam_chats.remove(chat_id)
    except:
        pass


@app.on_message(filters.command(["gmtag"], prefixes=["/", "@", "#"]))
async def mention_allvc(client, message):
    chat_id = message.chat.id
    if message.chat.type == ChatType.PRIVATE:
        return await message.reply("๏ الأمر ده للمجموعات بس يا نجم.")

    is_admin = False
    try:
        participant = await client.get_chat_member(chat_id, message.from_user.id)
    except UserNotParticipant:
        is_admin = False
    else:
        if participant.status in (
            ChatMemberStatus.ADMINISTRATOR,
            ChatMemberStatus.OWNER
        ):
            is_admin = True
    if not is_admin:
        return await message.reply("๏ إنت مش أدمن يا جميل، المنشن للمشرفين بس. ")
    if chat_id in spam_chats:
        return await message.reply("๏ وقف المنشن اللي شغال الأول يا غالي...")
    spam_chats.append(chat_id)
    usrnum = 0
    usrtxt = ""
    async for usr in client.get_chat_members(chat_id):
        if not chat_id in spam_chats:
            break
        if usr.user.is_bot:
            continue
        usrnum += 1
        usrtxt += "<a href='tg://user?id={}'>{}</a>".format(usr.user.id, usr.user.first_name)

        if usrnum == 1:
            txt = f"{usrtxt} {random.choice(VC_TAG)}"
            await client.send_message(chat_id, txt)
            await asyncio.sleep(4)
            usrnum = 0
            usrtxt = ""
    try:
        spam_chats.remove(chat_id)
    except:
        pass



@app.on_message(filters.command(["gmstop", "gnstop", "cancle"]))
async def cancel_spam(client, message):
    if not message.chat.id in spam_chats:
        return await message.reply("๏ مفيش منشن شغال دلوقتي أصلاً يا بيبي.")
    is_admin = False
    try:
        participant = await client.get_chat_member(message.chat.id, message.from_user.id)
    except UserNotParticipant:
        is_admin = False
    else:
        if participant.status in (
            ChatMemberStatus.ADMINISTRATOR,
            ChatMemberStatus.OWNER
        ):
            is_admin = True
    if not is_admin:
        return await message.reply("๏ الأمر ده للأدمن بس، إنت ملكش دعوة.")
    else:
        try:
            spam_chats.remove(message.chat.id)
        except:
            pass
        return await message.reply("๏ خلاص وقفت المنشن أهو ๏")
