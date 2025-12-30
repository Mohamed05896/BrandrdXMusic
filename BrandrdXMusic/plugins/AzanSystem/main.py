import asyncio
from pyrogram import filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from BrandrdXMusic import app
from config import BANNED_USERS, COMMAND_PREFIXES

# استدعاء المتغيرات والدوال من الملفات السابقة
from .config import (
    MAIN_OWNER, DEVS, AZAN_GROUP, PRAYER_NAMES_AR, PRAYER_NAMES_REV, 
    local_cache, admin_state, resources_db, settings_db, 
    MORNING_DUAS, NIGHT_DUAS, CURRENT_RESOURCES, CURRENT_DUA_STICKER
)
from .utils import (
    check_rights, get_chat_doc, update_doc, start_azan_stream, 
    send_duas_batch, get_azan_times, extract_vidid, scheduler
)

# --- [ 1. أوامر المشرفين (تفعيل وقفل الاذان/الدعاء) ] ---

@app.on_message(filters.command("تفعيل الاذان", COMMAND_PREFIXES) & filters.group & ~BANNED_USERS, group=AZAN_GROUP)
async def admin_enable_azan(_, m):
    if not await check_rights(m.from_user.id, m.chat.id): return
    doc = await get_chat_doc(m.chat.id)
    if doc.get("azan_active"): return await m.reply_text("الاذان مــفــعــل بــالــفــعــل")
    
    await update_doc(m.chat.id, "azan_active", True)
    await m.reply_text("تــم تــفــعــيــل الاذان بــنــجــاح")

@app.on_message(filters.command("قفل الاذان", COMMAND_PREFIXES) & filters.group & ~BANNED_USERS, group=AZAN_GROUP)
async def admin_disable_azan(_, m):
    if not await check_rights(m.from_user.id, m.chat.id): return
    doc = await get_chat_doc(m.chat.id)
    
    if doc.get("forced_active", False):
        if m.from_user.id not in DEVS:
            developer_link = '<a href="https://t.me/S_G0C7">•Abdullah Mo.•</a>'
            return await m.reply_text(
                f"عــذرا هــذا أمــر اجــبــاري مــن الــمــالــك إذا اردت الايــقــاف تــواصــل مــع الــمــطــور {developer_link}",
                disable_web_page_preview=True
            )

    if not doc.get("azan_active"): return await m.reply_text("الاذان مــعــطــل بــالــفــعــل")
    await update_doc(m.chat.id, "azan_active", False)
    await m.reply_text("تــم قــفــل الاذان بــنــجــاح")

@app.on_message(filters.command(["تفعيل الاذكار", "تفعيل الدعاء"], COMMAND_PREFIXES) & filters.group & ~BANNED_USERS, group=AZAN_GROUP)
async def admin_enable_duas(_, m):
    if not await check_rights(m.from_user.id, m.chat.id): return
    await update_doc(m.chat.id, "dua_active", True)
    await update_doc(m.chat.id, "night_dua_active", True)
    await m.reply_text("تــم تــفــعــيــل الاذكــار بــنــجــاح")

@app.on_message(filters.command(["قفل الاذكار", "قفل الدعاء"], COMMAND_PREFIXES) & filters.group & ~BANNED_USERS, group=AZAN_GROUP)
async def admin_disable_duas(_, m):
    if not await check_rights(m.from_user.id, m.chat.id): return
    doc = await get_chat_doc(m.chat.id)

    if doc.get("forced_dua_active", False):
        if m.from_user.id not in DEVS:
            developer_link = '<a href="https://t.me/S_G0C7">•Abdullah Mo.•</a>'
            return await m.reply_text(
                f"عــذرا هــذا أمــر اجــبــاري مــن الــمــالــك إذا اردت الايــقــاف تــواصــل مــع الــمــطــور {developer_link}",
                disable_web_page_preview=True
            )

    await update_doc(m.chat.id, "dua_active", False)
    await update_doc(m.chat.id, "night_dua_active", False)
    await m.reply_text("تــم قــفــل الاذكــار بــنــجــاح")


# --- [ 2. لوحة التحكم والأوامر التفاعلية ] ---

@app.on_message(filters.command(["اعدادات الاذان", "انلاين الاذان", "الاذان", "أوامر الاذان", "اوامر الاذان"], COMMAND_PREFIXES) & filters.group & ~BANNED_USERS, group=AZAN_GROUP)
async def azan_commands_panel(_, m):
    text = "<b>مرحباً بك في قائمة أوامر الأذان</b>\n<b>اختر القائمة المناسبة لرتبتك من الأزرار :</b>"
    
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("أوامر المالك", callback_data="cmd_owner")],
        [InlineKeyboardButton("أوامر المشرفين", callback_data="cmd_admin")],
        [InlineKeyboardButton("اغلاق", callback_data="cmd_close")]
    ])
    await m.reply_text(text, reply_markup=kb)

@app.on_message(filters.regex("^/start azset_") & filters.private, group=AZAN_GROUP)
async def open_panel_private(_, m):
    try: target_cid = int(m.text.split("azset_")[1])
    except: return
    
    if m.from_user.id != MAIN_OWNER:
        return await m.reply("عذراً، إعدادات الأذان متاحة للمالك الأساسي فقط.")
        
    await show_panel(m, target_cid)

async def show_panel(m, chat_id):
    if chat_id in local_cache: del local_cache[chat_id]
    doc = await get_chat_doc(chat_id)
    prayers = doc.get("prayers", {})
    if not prayers: prayers = {k: True for k in CURRENT_RESOURCES.keys()}
    
    kb = []
    
    st_main = "『 مــفــعــل 』" if doc.get("azan_active", True) else "『 مــعــطــل 』"
    kb.append([InlineKeyboardButton(f"الاذان العام : {st_main}", callback_data=f"set_main_{chat_id}")])
    
    st_dua = "『 مــفــعــل 』" if doc.get("dua_active", True) else "『 مــعــطــل 』"
    kb.append([InlineKeyboardButton(f"دعاء الصباح : {st_dua}", callback_data=f"set_dua_{chat_id}")])
    
    st_ndua = "『 مــفــعــل 』" if doc.get("night_dua_active", True) else "『 مــعــطــل 』"
    kb.append([InlineKeyboardButton(f"دعاء المساء : {st_ndua}", callback_data=f"set_ndua_{chat_id}")])

    row = []
    for k, name in PRAYER_NAMES_AR.items():
        is_active = prayers.get(k, True)
        pst = "『 مــفــعــل 』" if is_active else "『 مــعــطــل 』"
        row.append(InlineKeyboardButton(f"{name} : {pst}", callback_data=f"set_p_{k}_{chat_id}"))
        if len(row) == 2: kb.append(row); row = []
    if row: kb.append(row)

    kb.append([InlineKeyboardButton("تجربة الاذان (تست)", callback_data=f"test_azan_single_{chat_id}")])
    kb.append([InlineKeyboardButton("اغلاق", callback_data="close_panel")])
    text = f"<b>لوحة تحكم الأذان ( للجروب {chat_id} ) :</b>"
    
    try:
        if isinstance(m, Message): await m.reply_text(text, reply_markup=InlineKeyboardMarkup(kb))
        else: await m.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb))
    except: pass

@app.on_callback_query(filters.regex(r"^(set_|help_|close_|devset_|dev_cancel|test_azan|test_global|cmd_)"), group=AZAN_GROUP)
async def cb_handler(_, q):
    data = q.data
    uid = q.from_user.id
    chat_id = q.message.chat.id
    
    if data == "cmd_close" or data == "close_panel":
        if not await check_rights(uid, chat_id):
            return await q.answer("• عـذرا هـذا الـزر لـلـمـشـرف فـقـط 🤍", show_alert=True)
        return await q.message.delete()
        
    if data == "cmd_owner":
        if uid != MAIN_OWNER:
            return await q.answer("• عـذرا هـذا الـزر لـلـمـالـك فـقـط 🤍", show_alert=True)
        
        text = (
            "<b>أوامــر الــمــالــك (الــســورس) :</b>\n"
            "• <code>تفعيل الاذان الاجباري</code> / <code>قفل الاذان الاجباري</code>\n"
            "• <code>تفعيل الدعاء الاجباري</code> / <code>قفل الدعاء الاجباري</code>\n"
            "• <code>ايقاف الاذان @يوزر</code>\n"
            "• <code>تست دعاء صباح</code> / <code>تست دعاء مساء</code>\n"
            "• <code>فحص الاذان</code>\n"
            "• <code>تغيير رابط الاذان [الصلاة]</code>\n\n"
            "<b>لعمل تست عام للجروبات اضغط بالاسفل :</b>"
        )
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("تست الاذان (في هذا الجروب)", callback_data=f"test_azan_single_{chat_id}")],
            [InlineKeyboardButton("تست اذان عام (داخل البوت فقط)", url=f"https://t.me/{(await app.get_me()).username}?start=test_global")],
            [InlineKeyboardButton("تغيير استيكر الاذان", callback_data="devset_sticker_Fajr")],
            [InlineKeyboardButton("رجوع", callback_data="cmd_back_main")]
        ])
        return await q.edit_message_text(text, reply_markup=kb)

    if data == "cmd_admin":
        if not await check_rights(uid, chat_id):
            return await q.answer("• عـذرا هـذا الـزر لـلـمـشـرف فـقـط 🤍", show_alert=True)
            
        bot_username = (await app.get_me()).username
        settings_link = f"https://t.me/{bot_username}?start=azset_{chat_id}"
        
        text = (
            "<b>أوامــر الــمــشــرفــيــن :</b>\n"
            "• <code>تفعيل الاذان</code> / <code>قفل الاذان</code>\n"
            "• <code>تفعيل الدعاء</code> / <code>قفل الدعاء</code>\n"
            "• <code>تست الاذان</code> (تجربة داخل الجروب)\n\n"
            "<b>للاعدادات المتقدمة (تشغيل صلوات محددة) اضغط الزر:</b>"
        )
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("الاعدادات المتقدمة (للمالك)", url=settings_link)],
            [InlineKeyboardButton("رجوع", callback_data="cmd_back_main")]
        ])
        return await q.edit_message_text(text, reply_markup=kb)

    if data == "cmd_back_main":
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("أوامر المالك", callback_data="cmd_owner")],
            [InlineKeyboardButton("أوامر المشرفين", callback_data="cmd_admin")],
            [InlineKeyboardButton("اغلاق", callback_data="cmd_close")]
        ])
        return await q.edit_message_text("<b>مرحباً بك في قائمة أوامر الأذان</b>\n<b>اختر القائمة المناسبة لرتبتك من الأزرار :</b>", reply_markup=kb)

    if data.startswith("test_azan_single_"):
        chat_id = int(data.split("_")[3])
        if uid != MAIN_OWNER and uid not in DEVS:
             return await q.answer("للـمـالـك فـقـط", show_alert=True)
        await q.answer("جاري الارسال...", show_alert=False)
        await start_azan_stream(chat_id, "Fajr", force_test=True)
        return

    if data.startswith("set_"):
        parts = data.split("_")
        if uid != MAIN_OWNER:
             return await q.answer("للمالك الأساسي فقط", show_alert=True)

        if "_p_" in data:
            try:
                pkey = parts[2]
                chat_id = int(parts[3])
            except: return await q.answer("خطأ", show_alert=True)
            doc = await get_chat_doc(chat_id)
            prayers = doc.get("prayers", {})
            new_status = not prayers.get(pkey, True)
            await update_doc(chat_id, new_status, new_status, sub_key=pkey)
            await show_panel(q, chat_id)
            return

        chat_id = int(parts[-1])
        doc = await get_chat_doc(chat_id)

        if "main" in data: await update_doc(chat_id, "azan_active", not doc.get("azan_active", True))
        elif "_dua_" in data: await update_doc(chat_id, "dua_active", not doc.get("dua_active", True))
        elif "ndua" in data: await update_doc(chat_id, "night_dua_active", not doc.get("night_dua_active", True))
        
        await show_panel(q, chat_id)
    
    elif data == "dev_cancel":
        if uid in admin_state: del admin_state[uid]
        return await q.message.delete()
    
    elif data.startswith("devset_"):
        if uid not in DEVS: return await q.answer("للمطورين فقط", show_alert=True)
        parts = data.split("_")
        atype, pkey = parts[1], parts[2]
        admin_state[uid] = {"action": f"wait_azan_{atype}", "key": pkey}
        req = "استيكر" if atype == "sticker" else "رابط"
        await q.message.edit_text(f"<b>ارسل الان {req} صلاة {PRAYER_NAMES_AR[pkey]} :</b>")


# --- [ 3. أوامر المالك الخاصة والمدخلات ] ---

@app.on_message((filters.text | filters.sticker) & filters.user(DEVS), group=AZAN_GROUP)
async def dev_input_wait(_, m):
    uid = m.from_user.id
    if uid not in admin_state: return
    state = admin_state[uid]
    action = state["action"]

    if action == "wait_dua_sticker":
        if not m.sticker: return await m.reply("استيكر فقط")
        global CURRENT_DUA_STICKER
        CURRENT_DUA_STICKER = m.sticker.file_id
        await resources_db.update_one({"type": "dua_sticker"}, {"$set": {"sticker_id": CURRENT_DUA_STICKER}}, upsert=True)
        await m.reply("تــم الــحــفــظ")
        del admin_state[uid]

    elif action.startswith("wait_azan_"): 
        pkey = state["key"]
        if "sticker" in action:
            if not m.sticker: return await m.reply("استيكر فقط")
            CURRENT_RESOURCES[pkey]["sticker"] = m.sticker.file_id
            await resources_db.update_one({"type": "azan_data"}, {"$set": {f"data.{pkey}.sticker": m.sticker.file_id}}, upsert=True)
            await m.reply(f"تــم الــتــغــيــيــر")
        elif "link" in action:
            if not m.text: return
            vid = extract_vidid(m.text)
            if not vid: return await m.reply("رابط خطأ")
            CURRENT_RESOURCES[pkey]["link"] = m.text
            CURRENT_RESOURCES[pkey]["vidid"] = vid
            await resources_db.update_one({"type": "azan_data"}, {"$set": {f"data.{pkey}.link": m.text, f"data.{pkey}.vidid": vid}}, upsert=True)
            await m.reply(f"تــم الــتــغــيــيــر")
        del admin_state[uid]

@app.on_message(filters.command(["تغيير رابط الاذان", "تغير رابط الاذان"], COMMAND_PREFIXES) & filters.user(DEVS), group=AZAN_GROUP)
async def change_azan_link_cmd(client, message):
    if message.from_user.id != MAIN_OWNER: return
    
    args = message.text.split()
    if len(args) < 4:
        return await message.reply("الرجاء تحديد الصلاة، مثال: `تغيير رابط الاذان الفجر`")
    
    prayer_name = args[-1]
    prayer_key = PRAYER_NAMES_REV.get(prayer_name)
    
    if not prayer_key:
        return await message.reply(f"اسم الصلاة غير صحيح. الأسماء المتاحة: {', '.join(PRAYER_NAMES_AR.values())}")
        
    admin_state[message.from_user.id] = {"action": "wait_azan_link", "key": prayer_key}
    await message.reply(f"<b>الان رسـل لـي رابـط الاذان لـصـلاة {prayer_name} :</b>")

@app.on_message(filters.regex("^/start test_global") & filters.private, group=AZAN_GROUP)
async def test_global_start_trigger(_, m):
    if m.from_user.id != MAIN_OWNER: return
    await m.reply("<b>جاري بدء البث في جميع الجروبات...</b>")
    count = 0
    async for doc in settings_db.find({"azan_active": True}):
        cid = doc.get("chat_id")
        if cid:
            asyncio.create_task(start_azan_stream(cid, "Fajr", force_test=True))
            count += 1
            await asyncio.sleep(0.5)
    await m.reply(f"<b>تــم إرســال أمــر الــتــســت لــجــمــيــع الــجــروبــات ({count})</b>")


@app.on_message(filters.command(["تست الاذان"], COMMAND_PREFIXES) & filters.group, group=AZAN_GROUP)
async def tst_group_admin(client, message):
    if not await check_rights(message.from_user.id, message.chat.id):
        return await message.reply("هذا الأمر للمشرفين فقط")
    chat_id = message.chat.id
    msg = await message.reply(f"<b>جــاري تــشــغــيــل الأذان الــتــجــريــبــي . . .</b>")
    try:
        await start_azan_stream(chat_id, "Fajr", force_test=True)
    except Exception as e:
        await msg.edit_text(f"<b>حــدث خــطــأ :</b>\n`{e}`")

@app.on_message(filters.command(["تست دعاء صباح"], COMMAND_PREFIXES) & filters.user(DEVS), group=AZAN_GROUP)
async def tst_morning(client, message):
    if message.from_user.id != MAIN_OWNER:
        return await message.reply("عــذرا هــذا الأمــر خــاص بــالــمــالــك الاســاســي فــقــط")
    await message.reply("<b>جــاري تــجــربــة أذكــار الــصــبــاح . . .</b>")
    await send_duas_batch(MORNING_DUAS, None, "أذكار الصباح", target_chat_id=message.chat.id)

@app.on_message(filters.command(["تست دعاء مساء"], COMMAND_PREFIXES) & filters.user(DEVS), group=AZAN_GROUP)
async def tst_evening(client, message):
    if message.from_user.id != MAIN_OWNER:
        return await message.reply("عــذرا هــذا الأمــر خــاص بــالــمــالــك الاســاســي فــقــط")
    await message.reply("<b>جــاري تــجــربــة أذكــار الــمــســاء . . .</b>")
    await send_duas_batch(NIGHT_DUAS, None, "أذكار المساء", target_chat_id=message.chat.id)

@app.on_message(filters.command(["فحص الاذان"], COMMAND_PREFIXES) & filters.group, group=AZAN_GROUP)
async def activate_and_debug(client, message):
    if not await check_rights(message.from_user.id, message.chat.id):
        return 
    log = "<b>جــاري تــفــعــيــل الــمــلــف واخــتــبــار الــنــظــام . . .</b>\n\n"
    msg = await message.reply_text(log)
    
    try:
        await settings_db.find_one({})
        log += "• قـاعـدة الـبـيـانـات :  تــعــمــل بــنــجــاح\n"
    except Exception as e:
        log += f"• قـاعـدة الـبـيـانـات :  خــطــأ ({e})\n"
    
    try:
        times = await get_azan_times()
        if times: log += "• اتـصـال الـمـواقـيـت :  مــتــصــل بــنــجــاح\n"
        else: log += "• اتـصـال الـمـواقـيـت :  لا يــوجــد رد\n"
    except Exception as e:
        log += f"• اتـصـال الـمـواقـيـت :  خــطــأ ({e})\n"

    if scheduler.running: log += "• الـمـجـدول الـزمنـي :  يــعــمــل بــنــجــاح\n"
    else: log += "• الـمـجـدول الـزمنـي :  مــتــوقــف\n"
    await msg.edit_text(log + "\n<b>تــم اكــتــمــال الــفــحــص .</b>")

@app.on_message(filters.command("تفعيل الاذان الاجباري", COMMAND_PREFIXES) & filters.user(DEVS), group=AZAN_GROUP)
async def force_enable(_, m):
    if m.from_user.id != MAIN_OWNER:
        return await m.reply("هذا الأمر للمالك الأساسي فقط")
    msg = await m.reply("<b>جــاري الــتــفــعــيــل الإجــبــاري . . .</b>")
    c = 0
    text_to_send = "• تـم تـفـعـيـل الاذان من قـبـل الـمـالـك الاسـاسـي"
    
    async for doc in settings_db.find({}):
        chat_id = doc.get("chat_id")
        await settings_db.update_one(
            {"_id": doc["_id"]}, 
            {"$set": {"azan_active": True, "forced_active": True}}
        )
        try: 
            await app.send_message(chat_id, text_to_send)
            c += 1
        except: pass
    local_cache.clear()
    await msg.edit_text(f"• تــم الــتــفــعــيــل لـعدد {c} مــجــمــوعــه")

@app.on_message(filters.command("قفل الاذان الاجباري", COMMAND_PREFIXES) & filters.user(DEVS), group=AZAN_GROUP)
async def force_disable(_, m):
    if m.from_user.id != MAIN_OWNER:
        return await m.reply("هذا الأمر للمالك الأساسي فقط")
    msg = await m.reply("<b>جــاري الإيــقــاف الإجــبــاري . . .</b>")
    c = 0
    text_to_send = "• تـم ايـقـاف الاذان من قـبـل الـمـالـك الاسـاسـي إذا اردت الـتـفـعـيـل فـي هذه الـمـجـمـوعـه فقط اكتب {تفعيل الاذان}"
    
    async for doc in settings_db.find({}):
        chat_id = doc.get("chat_id")
        await settings_db.update_one(
            {"_id": doc["_id"]}, 
            {"$set": {"azan_active": False, "forced_active": False}}
        )
        try: 
            await app.send_message(chat_id, text_to_send)
            c += 1
        except: pass
    local_cache.clear()
    await msg.edit_text(f"• تــم الايــقــاف لـعدد {c} مــجــمــوعــه")

@app.on_message(filters.command("تفعيل الدعاء الاجباري", COMMAND_PREFIXES) & filters.user(DEVS), group=AZAN_GROUP)
async def force_enable_duas(_, m):
    if m.from_user.id != MAIN_OWNER:
        return await m.reply("هذا الأمر للمالك الأساسي فقط")
    msg = await m.reply("<b>جــاري الــتــفــعــيــل الإجــبــاري لــلــدعــاء . . .</b>")
    c = 0
    text_to_send = "• تـم تـفـعـيـل الــدعــاء من قـبـل الـمـالـك الاسـاسـي"
    async for doc in settings_db.find({}):
        chat_id = doc.get("chat_id")
        await settings_db.update_one(
            {"_id": doc["_id"]}, 
            {"$set": {"dua_active": True, "night_dua_active": True, "forced_dua_active": True}}
        )
        try: 
            await app.send_message(chat_id, text_to_send)
            c += 1
        except: pass
    local_cache.clear()
    await msg.edit_text(f"• تــم الــتــفــعــيــل لـعدد {c} مــجــمــوعــه")

@app.on_message(filters.command("قفل الدعاء الاجباري", COMMAND_PREFIXES) & filters.user(DEVS), group=AZAN_GROUP)
async def force_disable_duas(_, m):
    if m.from_user.id != MAIN_OWNER:
        return await m.reply("هذا الأمر للمالك الأساسي فقط")
    msg = await m.reply("<b>جــاري الإيــقــاف الإجــبــاري لــلــدعــاء . . .</b>")
    c = 0
    text_to_send = "• تـم ايـقـاف الــدعــاء من قـبـل الـمـالـك الاسـاسـي إذا اردت الـتـفـعـيـل فـي هذه الـمـجـمـوعـه فقط اكتب {تفعيل الدعاء}"
    async for doc in settings_db.find({}):
        chat_id = doc.get("chat_id")
        await settings_db.update_one(
            {"_id": doc["_id"]}, 
            {"$set": {"dua_active": False, "night_dua_active": False, "forced_dua_active": False}}
        )
        try: 
            await app.send_message(chat_id, text_to_send)
            c += 1
        except: pass
    local_cache.clear()
    await msg.edit_text(f"• تــم الايــقــاف لـعدد {c} مــجــمــوعــه")

@app.on_message(filters.command("ايقاف الاذان", COMMAND_PREFIXES) & filters.user(DEVS), group=AZAN_GROUP)
async def stop_specific_azan(_, m):
    if m.from_user.id != MAIN_OWNER: return
    if len(m.command) < 2:
        return await m
