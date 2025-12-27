import asyncio
import random
from pyrogram import filters, enums
from pyrogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton, 
    Message, CallbackQuery, InlineQuery, 
    InlineQueryResultArticle, InputTextMessageContent
)
from BrandrdXMusic import app
from BrandrdXMusic.misc import SUDOERS

# --- [ قاعدة البيانات المتصلة ] ---
db = {
    "replies": {}, "personal": {}, "inline": {}, 
    "special": {}, "multi": {}, "whispers": {}
}

# --- [ قائمة 30 زاجل حزين (اقتباسات عميقة) ] ---
SAD_QUOTES = [
    "خيبة الأمل في الشخص الذي ظنناه مخبأنا، هي أبشع شعور.", "لم نكن سيئين، لكننا وثقنا في القلوب الخطأ.",
    "السكوت ليس دائماً علامة الرضا، أحياناً يكون علامة التعب.", "أصعب فراق هو الذي لا يتبعه لقاء، ولا حتى وداع.",
    "قلوبنا ليست سوداء، لكنها أُحرقت بكلمات لا تُنسى.", "أحياناً نرحل ليس حباً بالرحيل، بل لأن المكان لم يعد يسعنا.",
    "ما أصعب أن تشرح لشخص كيف آلمك، بينما هو يرى أنه لم يفعل شيء.", "الخيبة هي أن تغفو وأنت ممتلئ بكلمات لم تجد من يسمعها.",
    "كنا نحتاج فقط لشخص يرى خلف صمتنا، لكننا بقينا وحيدين.", "أشد أنواع الوجع هو أن تنام وأنت تبكي بحرقة في قلبك.",
    "سلاماً على قلوب قرأت (يُدبّر الأمر) فتركت وجعها لله.", "الحزن لا يغير الماضي، لكنه يدمر مستقبلك.. انتبه.",
    "أسوأ وداع هو الذي تشعر فيه أنك لن تراه مجدداً أبداً.", "كانوا لقلبي حياة، واليوم هم لقلبي وجع.",
    "توقف عن لوم نفسك، فالمغادر لم يكن يستحقك أبداً.", "أصعب حزن هو الذي تخفيه خلف ابتسامة باهتة.",
    "الوحدة هي أن تعيش مع أشخاص لا يفهمون لغة صمتك.", "ليت الأيام تعود، وليتنا لم نعرفهم يوماً.",
    "الذكريات هي الشيء الوحيد الذي يبقى بعد رحيل الجميع.", "أحتاج لغيبوبة طويلة تنسيني كل ما مررت به مؤخراً.",
    "هادئون جداً، وفي قلوبنا ضجيج لو سُمع لهز الجبال.", "لا تثق كثيراً، فالجميع يرحلون عند الملل.",
    "نحن لا نكتب ليعجب الناس، نحن نكتب لنفرغ حزننا فقط.", "تعبنا من تمثيل القوة، ونحن أضعف من ريشة في مهب الريح.",
    "أحياناً الصمت هو الرد الوحيد على قسوة من تحب.", "خسرناهم لأنهم أرادوا الخسارة، لا تلوموا الظروف.",
    "كنت المأوى الوحيد، والآن أنت الغريب الأكبر.", "سحقاً لكل ذكرى جعلتنا نبتسم يوماً، واليوم تبكينا.",
    "نحن بحاجة لمن يمسك أيدينا في العتمة، لا من يصفها لنا.", "انتهت الحكاية، وبقينا نحن نلملم شتات أنفسنا."
]

# دالة ذكية للتحقق من الصلاحيات
async def is_admin(m: Message):
    if m.from_user.id in SUDOERS: return True
    member = await app.get_chat_member(m.chat.id, m.from_user.id)
    return member.status in [enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.OWNER]

# --- [ 1. قسم إدارة الردود العامة (أوامر مفصلة) ] ---

@app.on_message(filters.command(["اضف رد", "اضف رد مميز", "اضف رد متعدد", "اضف رد انلاين"], "") & filters.group)
async def adds_manager(_, m: Message):
    if not await is_admin(m): return
    cat = "replies" if m.command[0] == "اضف رد" else "special" if "مميز" in m.text else "multi" if "متعدد" in m.text else "inline"
    w = (await app.listen(m.chat.id, m.from_user.id, text="**ارسل الكلمة الآن.. ✨**")).text
    r = (await app.listen(m.chat.id, m.from_user.id, text=f"**ارسل الرد على ({w}) الآن.. ✨**")).text
    if cat == "multi":
        if w not in db["multi"]: db["multi"][w] = []
        db["multi"][w].append(r)
    else: db[cat][w] = r
    await m.reply_text(f"**✅ تم الحفظ في قائمة {m.command[0]}.**")

@app.on_message(filters.command(["مسح رد", "مسح رد مميز", "حذف رد متعدد", "مسح رد انلاين", "مسح الردود", "مسح الردود المميزه", "مسح الردود المتعدده", "مسح الردود الانلاين"], "") & filters.group)
async def dels_manager(_, m: Message):
    if not await is_admin(m): return
    cmd = m.command[0]
    if "الردود" in cmd:
        cat = "replies" if cmd == "مسح الردود" else "special" if "المميزه" in cmd else "multi" if "المتعدده" in cmd else "inline"
        db[cat].clear(); return await m.reply_text(f"**🗑️ تم تصفير {cmd}.**")
    if len(m.command) < 2: return
    w = m.command[1]; cat = "replies" if "رد" in cmd else "special" if "مميز" in cmd else "multi" if "متعدد" in cmd else "inline"
    if w in db[cat]: del db[cat][w]; await m.reply_text(f"**✅ تم حذف ({w}).**")

# --- [ 2. قسم الردود الشخصية وردود الأعضاء (بالملي) ] ---

@app.on_message(filters.command("اضف ردي", "") & filters.group)
async def add_me(_, m: Message):
    u = m.from_user.id
    w = (await app.listen(m.chat.id, u, text="**ارسل كلمة ردك الخاص.. ✨**")).text
    r = (await app.listen(m.chat.id, u, text="**ارسل إجابة الرد.. ✨**")).text
    if u not in db["personal"]: db["personal"][u] = {}
    db["personal"][u][w] = r
    await m.reply_text("**✅ تم تسجيل ردك الشخصي.**")

@app.on_message(filters.command(["مسح ردي", "ردي", "ردود الاعضاء", "مسح ردود الاعضاء"], "") & filters.group)
async def me_manager(_, m: Message):
    u = m.from_user.id
    if "مسح ردود الاعضاء" in m.text:
        if await is_admin(m): db["personal"].clear(); await m.reply_text("**🗑️ تم مسح كل ردود الأعضاء.**")
    elif "ردود الاعضاء" in m.text:
        res = "\n".join([f"• <a href='tg://user?id={uid}'>{uid}</a>" for uid in db["personal"]]) or "لا يوجد."
        await m.reply_text(f"**👥 الأعضاء المسجلين:\n{res}**")
    elif "مسح ردي" in m.text:
        if u in db["personal"]: del db["personal"][u]; await m.reply_text("**✅ تم مسح ردودك.**")
    elif "ردي" in m.text:
        res = "\n".join([f"• {k}" for k in db["personal"].get(u, {}).keys()]) or "لا يوجد."
        await m.reply_text(f"**📋 ردودك الخاصة:\n{res}**")

@app.on_message(filters.command(["رده", "حذف رده"], "") & filters.group)
async def his_manager(_, m: Message):
    if not await is_admin(m) and "حذف" in m.text: return
    u_id = m.reply_to_message.from_user.id if m.reply_to_message else (await app.get_users(m.command[1])).id if len(m.command) > 1 else None
    if not u_id: return
    if "حذف" in m.text:
        if u_id in db["personal"]: del db["personal"][u_id]; await m.reply_text("**✅ تم الحذف.**")
    else:
        res = "\n".join([f"• {k}" for k in db["personal"].get(u_id, {}).keys()]) or "لا يوجد."
        await m.reply_text(f"**📋 ردود الشخص:\n{res}**")

# --- [ 3. نظام الهمسات والزاجل المبتكر ] ---

@app.on_message(filters.command("زاجل", "") & filters.group)
async def zajel_pro(_, m: Message):
    mems = [mem.user async for mem in app.get_chat_members(m.chat.id, limit=50) if not mem.user.is_bot and mem.user.id != m.from_user.id]
    if not mems: return
    u1, u2 = m.from_user, random.choice(mems)
    wid = f"z_{m.id}"
    db["whispers"][wid] = {"f": u1.id, "t": u2.id, "m": random.choice(SAD_QUOTES)}
    
    await m.reply_text(
        f"• عمࢪي 「 {u1.mention} 」\n• عمࢪي 「 {u2.mention} 」\n\n"
        f"• لديكما همسة زاجل مشتركه 🕊\n• لا احد غيركما يستطيع رؤيتها 📬",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("رؤية الرسالة 🔐", callback_data=f"open_{wid}")]])
    )

@app.on_message(filters.command(["همسه", "همسه ميديا"], "") & filters.reply & filters.group)
async def whisper_pro(_, m: Message):
    u_to, u_fr = m.reply_to_message.from_user, m.from_user
    is_m = "ميديا" in m.text
    ask = await m.reply_text(f"**ارسل محتوى الهمسة لـ {u_to.mention}.. 🤫**")
    con = await app.listen(m.chat.id, u_fr.id)
    wid = f"w_{m.id}"
    db["whispers"][wid] = {"f": u_fr.id, "t": u_to.id, "m": con.text if not is_m else "ميديا 🖼️", "media": con.id if is_m else None}
    await con.delete(); await ask.delete()
    await m.reply_text(f"🤫 همسة لـ {u_to.mention}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("فتح الهمسة 🔐", callback_data=f"open_{wid}")]]))

@app.on_callback_query(filters.regex(r"^open_"))
async def open_pro(_, q: CallbackQuery):
    d = db["whispers"].get(q.data.replace("open_", ""))
    if not d or q.from_user.id not in [d["f"], d["t"]]: return await q.answer("مش ليك ❌", show_alert=True)
    if d.get("media"): await app.send_cached_media(q.from_user.id, d["media"]); await q.answer("شيك على الخاص 🔐")
    else: await q.answer(f"🤫: {d['m']}", show_alert=True)

# --- [ 4. الانلاين والخدمات الذكية ] ---

@app.on_inline_query()
async def inline_pro(_, iq: InlineQuery):
    q = iq.query; res = []
    if "@" in q and len(q.split("@")) > 1: # همسه انلاين
        try:
            target = await app.get_users(q.split("@")[-1].strip())
            res.append(InlineQueryResultArticle(title=f"همسة لـ {target.first_name}", input_message_content=InputTextMessageContent(f"🤫 همسة سرية لـ @{target.username}"), reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("فتح 🔐", callback_data="none")]])))
        except: pass
    for w, r in db["inline"].items():
        if w in q: res.append(InlineQueryResultArticle(title=w, input_message_content=InputTextMessageContent(r)))
    await iq.answer(res, cache_time=1)

@app.on_message(filters.command("اهمسلي", "") & filters.group)
async def whisper_me(_, m: Message):
    await app.send_message(m.from_user.id, "🤫: لست وحدك، أنا هنا دائماً.")
    await m.reply_text("**شوف الخاص.. 💌**")

# --- [ 5. محرك الاستجابة الذكي (الذكاء التفاعلي) ] ---

@app.on_message(filters.group & ~filters.me, group=1)
async def watcher_pro(_, m: Message):
    if not m.text: return
    t, u = m.text, m.from_user.id
    # أولوية الرد: الشخصي > المميز > المتعدد > العام
    if u in db["personal"] and t in db["personal"][u]: await m.reply_text(db["personal"][u][t])
    elif t in db["special"]: await m.reply_text(f"**✨ {db['special'][t]}**")
    elif t in db["multi"]: await m.reply_text(random.choice(db["multi"][t]))
    elif t in db["replies"]: await m.reply_text(db["replies"][t])
