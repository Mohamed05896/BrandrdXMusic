import asyncio
import random
from pyrogram import filters, enums
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, CallbackQuery
from BrandrdXMusic import app
from BrandrdXMusic.misc import SUDOERS
from BrandrdXMusic.utils.database import mongodb 

# --- [ إعدادات الداتا بيز والذاكرة ] ---
db = mongodb.boda_final_complete
locks_db = mongodb.BrandrdDB.locks_v5
whispers_db = {} 
user_state = {} 

async def is_locked(chat_id, key):
    res = await locks_db.find_one({"chat_id": chat_id, "key": key})
    return res["locked"] if res else False

async def set_lock(chat_id, key, state):
    await locks_db.update_one({"chat_id": chat_id, "key": key}, {"$set": {"locked": state}}, upsert=True)

# --- [ قائمة الـ 50 عبارة حزينة (للزاجل) 🖤🥀 ] ---
SAD_QUOTES = [
    "خـيـبـة الأمـل فـي الـشـخـص الـذي ظـنـنـاه مـخـبـأنـا هـي أبـشـع شـعـوࢪ 🖤🥀", "لـم نـكـن سـيـئـيـن لـكـنـنـا وثـقـنـا فـي الـقـلـوب الـخـطـأ 🖤🥀",
    "الـسـكـوت لـيـس دائـمـاً عـلامـة الـࢪضـا أحـيـانـاً يـكـون عـلامـة الـتـعـب 🖤🥀", "أصـعـب فـࢪاق هـو الـذي لا يـتـبـعـه لـقـاء ولا حـتـى وداع 🖤🥀",
    "قـلـوبـنـا لـيـسـت سـوداء لـكـنـهـا أُحـࢪقـت بـكـلـمـات لا تُـنـسـى 🖤🥀", "أحـيـانـاً نـࢪحـل لـيـس حـبـاً بـالـࢪحـيـل بـل لأن الـمـكـان لـم يـعـد يـسـعـنـا 🖤🥀",
    "الـخـيـبـة هـي أن تـغـفـو وأنـت مـمـتـلـئ بـكـلـمـات لـم تـجـد مـن يـسـمـعـهـا 🖤🥀", "كـنـا نـحـتـاج فـقـط لـشـخـص يـࢪى خـلـف صـمـتـا 🖤🥀",
    "أشـد أنـواع الـوجـع هـو أن تـنـام وأنـت تـبـكـي بـحـࢪقـة فـي قـلـبـك 🖤🥀", "سـلامـاً عـلـى قـلـوب قـࢪأت يُـدبّـر الأمـࢪ فـتـࢪكـت وجـعـهـا لـلـه 🖤🥀",
    "الـحـزن لا يـغـيـر الـمـاضـي لـكـنـه يـدمـر مـسـتـقـبـلـك 🖤🥀", "أسـوأ وداع هـو الـذي تـشـعـر فـيـه أنـك لـن تـࢪاه مـجـدداً 🖤🥀",
    "كـانـوا لـقـلـبـي حـيـاة والـيـوم هـم لـقـلـبـي وجـع 🖤🥀", "تـوقـف عـن لـوم نـفـسـك فـالـمـغـادر لـم يـكـن يـسـتـحـقـك 🖤🥀",
    "أصـعـب حـزن هـو الـذي تـخـفـيـه خـلـف ابـتـسـامـة بـاهـتـة 🖤🥀", "الـوحـدة هـي أن تـعـيـش مـع أشـخـاص لا يـفـهـمـون صـمـتـك 🖤🥀",
    "لـيـت الأيـام تـعـود ولـيـتـنـا لـم نـعـࢪفـهـم يـومـاً 🖤🥀", "الـذكـࢪيـات هـي الـشـيء الـوحـيـد الـذي يـبـقـى بـعـد ࢪحـيـل الـج_مـيـع 🖤🥀",
    "أحـتـاج لـغـيـبـوبـة طـويـلـة تـنـسـيـنـي كـل مـا مـࢪࢪت بـه 🖤🥀", "هـادئـون جـداً وفـي قـلـوبـنـا ضـجـيـج لـو سُـمـع لـهـز الـجـبـال 🖤🥀",
    "لا تـثـق كـثـيـࢪاً فـالـجـمـيـع يـࢪحـلـون عـنـد الـم_لـل 🖤🥀", "نـحـن نـكـتـب لـنـفـࢪغ حـزنـنـا فـقـط 🖤🥀",
    "تـعـبـنـا مـن تـمـثـيـل الـقـوة ونـحـن أضـعـف مـن ࢪيـشـة 🖤🥀", "أحـيـانـاً الـصـمـت هـو الـࢪد الـوحـيـد عـلـى قـسـوة مـن تـحـب 🖤🥀",
    "خـسـࢪنـاهـم لأنـهـم أࢪادوا الـخـسـاࢪة 🖤🥀", "كـنـت الـمـأوى الـوحـيـد والآن أنـت الـغـࢪيـب 🖤🥀",
    "سـحـقـاً لـكـل ذكـࢪى جـعـلـتـنـا نـبـتـسـم والـيـوم تـبـكـيـنـا 🖤🥀", "انـتـهـت الـحـكـايـة وبـقـيـنـا نـلـمـلـم شـتـات أنـفـسـنـا 🖤🥀",
    "أعـاتـب فـيـك قـلـبـي كـل يـوم وأسـأل كـيـف طـاوعـك الـࢪحـيـل 🖤🥀", "فـيـا لـيـت مـا بـيـنـي وبـيـنـك بـاب يُـطـࢪق كـلـمـا ضـاق الـفـؤاد 🖤🥀",
    "لـيـس كـل مـن يـبـتـسـم بـخـيـر 🖤🥀", "غـصـة الـقـلـب أثـقـل مـن جـبـال الأرض جـمـيـعـاً 🖤🥀",
    "نـبـحـث عـن أنـفـسـنـا فـي وجـوه الـغـࢪبـاء 🖤🥀", "مـؤلـم أن تـشـعـر أنـك عـبء عـلـى مـن تـظـنـه سـنـدك 🖤🥀",
    "أصـبـحـت غـࢪيـبـاً فـي مـديـنـة كـنـت أظـنـهـا بـيـتـي 🖤🥀", "نـࢪحـل بـصـمـت لأن الـضـجـيـج لـم يـعـد يـنـفـعـنـا 🖤🥀",
    "لـيـتـنـي لـم أتـعـمـق بـك لـيـتـك بـقـيـت غـࢪيـبـاً 🖤🥀", "أشـد الألـم غـصـة داعـيـة لـم تـسـتـجـب بـعـد 🖤🥀",
    "كـنـا أوفـيـاء جـداً لـكـنـهـم فـضـلـوا الـࢪحـيـل 🖤🥀", "سـلامـاً عـلـى مـن أبـعـد نـفـسـه بـنـفـسـه 🖤🥀",
    "أصـعـب وداع هـو وداع مـن سـكـن الـقـلـب 🖤🥀", "الـقـلـوب الـتـي تـألـمـت كـثـيـࢪاً هـي الأكـثـر صـمـتـاً 🖤🥀",
    "أحـيـانـاً تـبـكـي لأَنـك بـقـيـت قـويـاً جـداً 🖤🥀", "لا أحـد يـشـعـر بـمـا تـمـر بـه أنـت وحـدك 🖤🥀",
    "اشـتـقـنـا لأيـام كـانـت فـيـهـا قـلـوبـنـا بـخـيـر 🖤🥀", "تـعـبـنـا مـن كـل شـيء حـتـى مـن أنـفـسـنـا 🖤🥀",
    "كـأن الـدنـيـا أجـمـعـت عـلـى أن تـكـسـࢪنـي 🖤🥀", "بـيـنـي وبـيـن الـࢪاحـة جـدار مـن الـتـع_ب 🖤🥀",
    "الـحـمـد لـلـه عـلـى كـل جـࢪح جـعـلـنـا أقـوى 🖤🥀", "انـتـهـى كـل شـيء وبـقـي الـوجـع 🖤🥀"
]

# --- [ قائمة الـ 50 عبارة حب ودلع (لاهمسلي) 💗🧚 ] ---
SWEET_QUOTES = [
    "أنـتِ جـمـيـلـة كـطـوق وردٍ نـضِـر كـقـصـيـدةٍ عـذبـةٍ 💗🧚", "فـي عـيـنـيـكِ أࢪى وطـنـاً وفـي قـلـبـكِ أجـدُ الـسـلام 💗🧚",
    "وجـودك بـجـانـبـي يـغـنـيـنـي عـن كـل الـعـالـم 💗🧚", "كـأنـكِ خُـلـقـتِ مـن خـيـوطِ الـشـمـس 💗🧚",
    "أحـبـبـتـكِ بـقـلـبٍ لا يـࢪى فـي الـعـالـمِ سـواكِ 💗🧚", "أنـتِ الـصـدفـةُ الـتـي غـي_ࢪت حـيـاتـي لـلأجـمـل 💗🧚",
    "سـأبـقـى أحـبـكِ حـتـى تـتـوقـفُ الـنـب_ضـات 💗🧚", "أنـتِ الـنـعـمـةُ الـتـي أشـكـرُ الـلـه عـلـيـهـا 💗🧚",
    "بـجـانـبـكِ فـقـط أشـعـرُ أن الـحـيـاةَ بـخـيـر 💗🧚", "يـا حـظ قـلـبـي فـيـك ويـا بـخـت عـيـنـي 💗🧚",
    "ضـحـكـتـكِ هـي الـمـوسـيـقـى الـتـي تـهـدئ قـلـبـي 💗🧚", "أنـتِ الـفـكـࢪةُ الـجـمـيـلـة الـتـي أبـتـدئُ بـهـا يـومـي 💗🧚",
    "عـسـى ࢪبـي يـحـفـظـك لـي يـا أجـمـل أقـداࢪي 💗🧚", "وجـهـكِ يـبـددُ كـل أحـزانـي 💗🧚",
    "أحـبـكِ فـوق حـب الـم_حـبـيـن حـبـاً 💗🧚", "أنـتِ عـالـمـي الـصـغـيـر الـتـي أهـࢪبُ إلـيـه 💗🧚",
    "لـيـتـنـي أسـتـطـيـعُ حـمـايـتـكِ مـن كـل حـزن 💗🧚", "أنـتِ أجـمـلُ سـرٍ خـبـأتـه فـي قـلـبـي 💗🧚",
    "عـطـࢪك يـمـلأُ الـمـكـان كـأنـه ࢪسـالـة حـب 💗🧚", "كـل ثـانـيـة مـعـك هـي عـمـر كـامـل 💗🧚",
    "أنـتِ الـنـبـض الـذى أعـيـش بـه 💗🧚", "لا أࢪيـد شـيـئـاً سـوى أن تـبـقـي بـجـانـبـي 💗🧚",
    "عـيـنـيـكِ قـصـة لا يـمـلُّ قـلـبـي مـن قـࢪاءتـهـا 💗🧚", "أنـتِ الـمـعـنـى الـحـقـيـقـي لـلـجـمـال 💗🧚",
    "أحـبـكِ بـكـل تـفـاصـيـلـك 💗🧚", "قـࢪبـك هـو جـنـتـي وبـعـدك هـو ضـيـاعـي 💗🧚",
    "أنـتِ مـلاكـي الـذي نـزل لـيـحـمـي قـلـبـي 💗🧚", "فـي كـل يـوم أحـبـكِ أكـثـر مـن الأمـس 💗🧚",
    "أنـتِ لـي وهـذا يـكـفـيـنـي 💗🧚", "خُـلـقـتِ لـتـك_ونـي مـلـكـةً ع_لـى قـلـبـي 💗🧚",
    "صـوتـكِ هـو الـدواء لـكـل تـعـبـي 💗🧚", "أنـتِ الـشـࢪوق الـذي يـمـحـو عـتـمـتـي 💗🧚",
    "يـا بـسـمـة قـلـبـي ويـا ࢪوح الـࢪوح 💗🧚", "أنـتِ الاسـتـثـنـاء الـوحـيـد لـكـل قـواعـدي 💗🧚",
    "أحـبـبـتـكِ وكـأنـكِ آخـر امـࢪأة عـلـى الأرض 💗🧚", "جـمـالـكِ لا يـوصـف بـالـكـلـمـات 💗🧚",
    "أنـتِ عـيـدي كـل يـوم وفـࢪحـي الـدائـم 💗🧚", "بـكـل لـغـات الـعـالـم أحـبـكِ 💗🧚",
    "وجـودك هـو الأمـان الـذي أبـحـث عـنـه 💗🧚", "يـا وࢪدة قـلـبـي ويـا شـمـعـة دࢪبـي 💗🧚",
    "أنـتِ أجـمـل مـا حـدث لـي فـي حـيـاتـي 💗🧚", "أحـبـكِ حـبـاً يـتـجـاوز الـخـيـال 💗🧚",
    "سـأظـل أحـمـيـكِ بـقـلـبـي حـتـى آخـر نـفـس 💗🧚", "يـا كـلـي ويـا كـل مـا أمـلـك 💗🧚",
    "أنـتِ الـضـيـاء فـي عـيـنـي 💗🧚", "أحـبـكِ وكـفـى بـهـذا الـحـب فـخـࢪاً 💗🧚",
    "أنـتِ الـحـيـاة وأنـا عـلـى قـيـد حـبـكِ 💗🧚", "سـلامـاً عـلـى وجـهـكِ الـم_بـتـسـم 💗🧚",
    "أعـشـقـكِ حـتـى يـنـتـهـي الـعـشـق 💗🧚", "كـل عـام وأنـتِ مـلـكـة قـلـبـي 💗🧚"
]

# --- [ 1. نظام القفل والفتح المتطور ] ---
@app.on_message(filters.command(["قفل", "فتح"], "") & filters.group, group=1)
async def lock_manager(client, m: Message):
    user_id = m.from_user.id
    if user_id not in SUDOERS:
        try:
            member = await client.get_chat_member(m.chat.id, user_id)
            if member.status not in [enums.ChatMemberStatus.OWNER, enums.ChatMemberStatus.ADMINISTRATOR]: return
        except: return

    if len(m.command) < 2: return
    cmd = m.command[0]
    target = m.command[1]
    state = (cmd == "قفل")

    keys = {
        "همسه": ("whisper", "الـهـمـسـه"),
        "زاجل": ("zajel", "الـزاجـل"),
        "الزاجل": ("zajel", "الـزاجـل"),
        "اهمسلي": ("whisper_me", "اهمسلي")
    }

    if target in keys:
        db_key, name = keys[target]
        await set_lock(m.chat.id, db_key, state)
        act = "قـفـل" if state else "فـتـح"
        await m.reply_text(f"• تـم {act} {name} بـنـجـاح 🧚")

# --- [ 2. أمر همسه (نظام الـ Start والخاص) ] ---
@app.on_message(filters.command("همسه", "") & filters.group, group=2)
async def whisper_group(client, m: Message):
    if await is_locked(m.chat.id, "whisper"): return await m.reply_text("• الـهـمـسـه مـقـفـولـه يـا عـمـࢪي 🥀")
    if not m.reply_to_message: return await m.reply_text("• بـالـࢪد عـلـى الـشـخـص لـتـهـمـس لـه 🧚")
    
    bot = await client.get_me()
    user_state[m.from_user.id] = {
        "chat_id": m.chat.id,
        "to_id": m.reply_to_message.from_user.id,
        "to_name": m.reply_to_message.from_user.first_name
    }
    
    await m.reply_text(
        f"• عـمـࢪي {m.from_user.mention}\n• اضـغـط عـلـى الـزࢪ لـكـتـابـة هـمـسـتـك لـ {m.reply_to_message.from_user.mention}",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("اكـتـب الـهـمـسـه ✍️", url=f"t.me/{bot.username}?start=w_{m.from_user.id}")]])
    )

@app.on_message(filters.private & ~filters.bot)
async def whisper_private(client, m: Message):
    uid = m.from_user.id
    if m.text and m.text.startswith("/start w_"):
        if uid in user_state: return await m.reply_text("• الآن أࢪسـل هـمـسـتـك هـنـا.. وسـأرسـلـهـا لـه فـي الـجـࢪوب فـوࢪاً ✨")
        else: return await m.reply_text("• انـتـهـت صـلاحـيـة الـطـلـب.. ابـدأ مـن الـجـࢪوب مـرة أخـࢪى 🥀")

    if uid in user_state:
        data = user_state.pop(uid)
        w_id = f"sec_{m.id}"
        whispers_db[w_id] = {"from": uid, "to": data["to_id"], "msg": m.text}
        await client.send_message(data["chat_id"], f"• لـديـك هـمـسـه جـديـدة يـا {data['to_name']} ✨\n• مـن: {m.from_user.mention}",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("فـتـح الـهـمـسـه 🔐", callback_data=f"wh_{w_id}")]]))
        await m.reply_text("• تـم إࢪسـال هـمـسـتـك فـي الـجـࢪوب ✅")

# --- [ 3. الزاجل واهمسلي ] ---
@app.on_message(filters.command("زاجل", "") & filters.group, group=3)
async def zajel_cmd(client, m: Message):
    if await is_locked(m.chat.id, "zajel"): return await m.reply_text("• الـزاجـل مـقـفـول يـا عـمـࢪي 🥀")
    mems = [mem.user async for mem in client.get_chat_members(m.chat.id, limit=100) if not mem.user.is_bot]
    if not mems: return
    target = random.choice(mems)
    w_id = f"z_{m.id}"
    whispers_db[w_id] = {"from": m.from_user.id, "to": target.id, "msg": random.choice(SAD_QUOTES)}
    await m.reply_text(f"• عـمـࢪي {m.from_user.mention}\n• عـمـࢪي {target.mention}\n• هـمـسـه زاجـل مـشـتـࢪكـه لـكـمـا 🥀",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("ࢪؤيـة الـزاجـل 💌", callback_data=f"wh_{w_id}")]]))

@app.on_message(filters.command("اهمسلي", "") & filters.group, group=4)
async def whisper_me_cmd(_, m: Message):
    if await is_locked(m.chat.id, "whisper_me"): return await m.reply_text("• أمـࢪ اهمسلي مـقـف_ول يـا عـمـࢪي 🥀")
    w_id = f"me_{m.id}"
    whispers_db[w_id] = {"from": m.from_user.id, "to": m.from_user.id, "msg": random.choice(SWEET_QUOTES)}
    await m.reply_text(f"• عـمـࢪي {m.from_user.mention}\n• هـمـسـه لـقـلـبـك ✨",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("ࢪؤيـة الـهـمـسـه 💗", callback_data=f"wh_{w_id}")]]))

# --- [ 4. فتح الهمسات والردود ] ---
@app.on_callback_query(filters.regex("^wh_"))
async def open_whisper(client, q: CallbackQuery):
    data = whispers_db.get(q.data.split("_", 1)[1])
    if not data: return await q.answer("الـهـمـسـه قـديـمـه 🥀", show_alert=True)
    if q.from_user.id not in [data["from"], data["to"]]: 
        return await q.answer("مـش لـك يـا عـمـࢪي.. دي خـاصـه 🤨", show_alert=True)
    await q.answer(data["msg"], show_alert=True)

@app.on_
