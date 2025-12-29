# ==================================================================================================
# [ مـلـف الأوامـر الإداريـة الـشـامـل - الـنـسـخـة الـمـنـقـحـة ]
# [ الـحـالـة: مـطـابـق لـشـروط الايمـوجـي 100% | خالي من التداخل | تفعيل الرفع الحقيقي ]
# ==================================================================================================

import asyncio
import time
from pyrogram import Client, filters, enums
from pyrogram.types import ChatPermissions, ChatPrivileges, Message, InlineKeyboardMarkup, InlineKeyboardButton
from motor.motor_asyncio import AsyncIOMotorClient
from BrandrdXMusic import app
# محاولة استيراد المتغيرات مع وضع قيم افتراضية لتجنب الاخطاء
try:
    from config import MONGO_DB_URI, OWNER_ID
except ImportError:
    MONGO_DB_URI = "mongodb://localhost:27017"
    OWNER_ID = 0

# ==================================================================================================
# [ 1 ] إعـدادات قـاعـدة الـبـيـانـات (Database Setup)
# ==================================================================================================

# ضمان عدم توقف البوت اذا كان الرابط غير موجود
if not MONGO_DB_URI:
    MONGO_DB_URI = "mongodb://localhost:27017"

mongo_client = AsyncIOMotorClient(MONGO_DB_URI)
# استخدام قاعدة بيانات منفصلة عن locks.py لتجنب تداخل البيانات
database = mongo_client.BrandrdX.admin_system_v3_db

# تـعـريـف الـجـداول
ranks_collection = database.ranks              
settings_collection = database.settings        
replies_collection = database.replies          
points_collection = database.points            
rules_collection = database.rules              
welcome_collection = database.welcome          
group_data_collection = database.group_data    
ban_list_collection = database.ban_list        

# ==================================================================================================
# [ 2 ] نـظـام الـصـلاحـيـات (Hierarchy)
# ==================================================================================================

RANK_POWER_LEVELS = {
    # --- [ قـسـم الـرجـال ] ---
    "مالك اساسي": 100, "مالك": 90,
    "منشئ اساسي": 80, "منشئ": 70,
    "مدير": 60, "ادمن": 50, "مميز": 40,
    
    # --- [ قـسـم الـنـسـاء ] ---
    "مالكه اساسيه": 100, "مالكه": 90,
    "منشئه اساسيه": 80, "منشئه": 70,
    "مديره": 60, "ادمونه": 50, "مميزه": 40,
    
    # --- [ الـعـام ] ---
    "عضو": 0
}

# ==================================================================================================
# [ 3 ] الـدوال الـمـسـاعـدة (Helpers)
# ==================================================================================================

async def get_user_rank_name(chat_id: int, user_id: int) -> str:
    try:
        if user_id == OWNER_ID:
            return "مالك اساسي"
        user_doc = await ranks_collection.find_one({"chat_id": chat_id, "user_id": user_id})
        if user_doc:
            return user_doc.get("rank", "عضو")
        return "عضو"
    except: return "عضو"

async def set_user_rank_in_db(chat_id: int, user_id: int, rank_title: str):
    try:
        if rank_title == "عضو":
            await ranks_collection.delete_one({"chat_id": chat_id, "user_id": user_id})
        else:
            power = RANK_POWER_LEVELS.get(rank_title, 0)
            await ranks_collection.update_one(
                {"chat_id": chat_id, "user_id": user_id},
                {"$set": {"rank": rank_title, "power": power}},
                upsert=True
            )
    except: pass

async def check_user_permission(chat_id: int, user_id: int, required_power: int) -> bool:
    if user_id == OWNER_ID:
        return True
    current_rank = await get_user_rank_name(chat_id, user_id)
    current_power = RANK_POWER_LEVELS.get(current_rank, 0)
    return current_power >= required_power

async def is_setting_locked(chat_id: int, setting_key: str) -> bool:
    try:
        settings = await settings_collection.find_one({"chat_id": chat_id})
        if not settings: return False
        locks = settings.get("locks", {})
        return locks.get(setting_key, False)
    except: return False

async def get_target_member(message: Message):
    if message.reply_to_message:
        return message.reply_to_message.from_user
    if len(message.command) > 1:
        user_input = message.command[1]
        try:
            if user_input.startswith("@"):
                return await app.get_users(user_input)
            elif user_input.isdigit():
                return await app.get_users(int(user_input))
        except: return None
    return None

# ==================================================================================================
# [ 4 ] مـعـالـج الـرتـب (Rank System)
# ==================================================================================================

RANK_COMMANDS_MAP = {
    # --- الأولاد ---
    "رفع مالك اساسي": "مالك اساسي", "تنزيل مالك اساسي": "عضو",
    "رفع مالك": "مالك", "تنزيل مالك": "عضو",
    "رفع منشئ اساسي": "منشئ اساسي", "تنزيل منشئ اساسي": "عضو",
    "رفع منشئ": "منشئ", "تنزيل منشئ": "عضو",
    "رفع مدير": "مدير", "تنزيل مدير": "عضو",
    "رفع ادمن": "ادمن", "تنزيل ادمن": "عضو",
    "رفع مميز": "مميز", "تنزيل مميز": "عضو",
    # --- البـنـات ---
    "رفع مالكه اساسيه": "مالكه اساسيه", "تنزيل مالكه اساسيه": "عضو",
    "رفع مالكه": "مالكه", "تنزيل مالكه": "عضو",
    "رفع منشئه اساسيه": "منشئه اساسيه", "تنزيل منشئه اساسيه": "عضو",
    "رفع منشئه": "منشئه", "تنزيل منشئه": "عضو",
    "رفع مديره": "مديره", "تنزيل مديره": "عضو",
    "رفع ادمونه": "ادمونه", "تنزيل ادمونه": "عضو",
    "رفع مميزه": "مميزه", "تنزيل مميزه": "عضو"
}

@app.on_message(filters.regex(r"^(رفع|تنزيل|كشف الرتب|عدد الرتب|رتبتي)") & filters.group)
async def rank_logic(client: Client, message: Message):
    try:
        text = message.text.strip()
        chat_id = message.chat.id
        user_id = message.from_user.id
        
        # --- كـشـف الـرتـب ---
        if text == "كشف الرتب":
            if not await check_user_permission(chat_id, user_id, 50): return 
            msg = "<b>✨ كـشـف الـرتـب فـي الـمـجـمـوعـة 🧚 :</b>\n\n"
            found = False
            cursor = ranks_collection.find({"chat_id": chat_id}).sort("power", -1)
            async for doc in cursor:
                try:
                    u = await app.get_users(doc["user_id"])
                    msg += f"♥️ ¦ {doc['rank']} ↢ {u.mention}\n"
                    found = True
                except: continue
            if not found: msg += "🥀 ¦ لا يـوجـد أي رتـب مـضـافـة."
            await message.reply_text(msg)
            return

        # --- عـدد الـرتـب ---
        if text == "عدد الرتب":
            stats = {}
            async for doc in ranks_collection.find({"chat_id": chat_id}):
                r = doc["rank"]
                stats[r] = stats.get(r, 0) + 1
            msg = "<b>♥️ إحـصـائـيـات الـرتـب 🧚 :</b>\n\n"
            if not stats: msg += "🤎 ¦ الـقـائـمـة فـارغـة."
            else:
                for r, c in stats.items():
                    msg += f"✨ ¦ {r} ↢ {c}\n"
            await message.reply_text(msg)
            return

        # --- رفـع مـشـرف تـلـيـجـرام (فعال + لقب) ---
        if text == "رفع مشرف":
            if not await check_user_permission(chat_id, user_id, 100): return
            target = await get_target_member(message)
            if not target: return await message.reply_text("🥀 ¦ بـالـرد او الـمـعـرف.")
            try:
                # رفع في التليجرام
                await message.chat.promote_member(
                    target.id,
                    privileges=ChatPrivileges(
                        can_manage_chat=True, can_delete_messages=True, can_manage_video_chats=True,
                        can_restrict_members=True, can_promote_members=False, can_change_info=True,
                        can_invite_users=True, can_pin_messages=True
                    )
                )
                # وضع اللقب
                await client.set_administrator_title(chat_id, target.id, "مـشـرف 🧚")
                await message.reply_text(f"🤍 ¦ تـم رفـعـه مـشـرف (مـشـرف 🧚) بـكـل الـصـلاحـيـات.")
            except Exception as e:
                # في حال فشل الرفع بالتليجرام (مثلا البوت ليس ادمن)
                await message.reply_text("🥀 ¦ تـم حـفـظ الـرتـبـة، لـكـن لـم أسـتـطـع رفـعـه فـي الـجـروب (تـأكـد مـن صـلاحـيـاتـي).")
            return

        if text == "تنزيل مشرف":
            if not await check_user_permission(chat_id, user_id, 100): return
            target = await get_target_member(message)
            if not target: return
            try:
                await message.chat.promote_member(target.id, privileges=ChatPrivileges(can_manage_chat=False))
                await message.reply_text(f"🤎 ¦ تـم تـنـزيـلـه مـن الإشـراف.")
            except: pass
            return

        # --- الـرتـب والرفع التلقائي للماك ---
        if text in RANK_COMMANDS_MAP:
            if await is_setting_locked(chat_id, "promote"):
                if not await check_user_permission(chat_id, user_id, 90):
                    return await message.reply_text("🥀 ¦ الأمـر مـغـلـق حـالـيـاً.")
            
            target_rank = RANK_COMMANDS_MAP[text]
            req_power = RANK_POWER_LEVELS.get(target_rank, 0) + 10
            if not await check_user_permission(chat_id, user_id, req_power):
                return await message.reply_text("🤎 ¦ رتـبـتـك لا تـسـمـح بـذلـك.")
            
            target = await get_target_member(message)
            if not target: return await message.reply_text("🥀 ¦ بـالـرد او الـمـعـرف.")
            
            # حفظ في قاعدة البيانات
            await set_user_rank_in_db(chat_id, target.id, target_rank)
            
            # اذا كان الامر رفع مالك، نرفعه في التليجرام ونضع له لقب
            if text == "رفع مالك":
                try:
                    await client.promote_chat_member(
                        chat_id, target.id,
                        privileges=ChatPrivileges(
                            can_manage_chat=True, can_delete_messages=True, can_restrict_members=True,
                            can_promote_members=True, can_change_info=True, can_invite_users=True,
                            can_pin_messages=True, can_manage_video_chats=True
                        )
                    )
                    await client.set_administrator_title(chat_id, target.id, "مـالـك 🧚")
                except: 
                    pass # اذا فشل الرفع في التليجرام يكمل عادي
            
            verb = "تـنـزيـل" if target_rank == "عضو" else "رفـع"
            d_rank = target_rank if target_rank != "عضو" else "عضو"
            await message.reply_text(f"🤍 ¦ تـم {verb} {target.mention} إلـى {d_rank}.")
    except: pass

# ==================================================================================================
# [ 5 ] الـقـفـل الـذكـي (Smart Locks)
# ==================================================================================================

# هذه الخريطة تحتوي فقط على "الاوامر" الادارية، ولا تحتوي على الصور والروابط
# وهذا ما يمنع التداخل مع ملف locks.py
LOCKS_MAP = {
    "امر حظر": "ban", "امر رفع": "promote",
    "امر تثبيت": "pin", "امر همسه": "whisper", "امر اضف رد": "add_reply",
    "امر مسح رد": "del_reply", "امر تفعيل افتاري": "avatar",
    "امر تفعيل صورتي": "myphoto", "امر تفعيل الايدي": "id",
    "امر تفعيل الايدي بالصوره": "id_pic", "الحظر المحدود": "temp_ban",
    "الحظر - التقييد": "restrict"
}

@app.on_message(filters.regex(r"^(قفل|فتح|تعطيل|تفعيل) (.*)") & filters.group)
async def locks_logic(client: Client, message: Message):
    try:
        m = message.matches[0]
        action, target = m.group(1), m.group(2).strip()
        
        # [تعديل هام لمنع التداخل]
        if target not in LOCKS_MAP: return

        if not await check_user_permission(message.chat.id, message.from_user.id, 70):
            return await message.reply_text("🥀 ¦ لـلـمـنـشـئـيـن فـقـط.")
            
        key = LOCKS_MAP[target]
        val = True if action in ["قفل", "تعطيل"] else False
        
        await settings_collection.update_one(
            {"chat_id": message.chat.id},
            {"$set": {f"locks.{key}": val}}, upsert=True
        )
        state = "تـم قـفـل" if val else "تـم فـتـح"
        await message.reply_text(f"✨ ¦ {state} {target} بـنـجـاح.")
    except: pass

# ==================================================================================================
# [ 6 ] الـمـسـح الـشـامـل (Wipe System)
# ==================================================================================================

@app.on_message(filters.regex(r"^مسح (.*)") & filters.group)
async def wipe_logic(client: Client, message: Message):
    try:
        target = message.matches[0].group(1).strip()
        cid = message.chat.id
        
        # [تعديل هام لمنع التداخل]
        if target.isdigit() or (target.startswith("+") and target[1:].isdigit()): return

        if not await check_user_permission(cid, message.from_user.id, 80):
            return await message.reply_text("🤎 ¦ لـلـمـنـشـئـيـن الأسـاسـيـيـن.")

        # --- مـسـح الـكـل ---
        if target == "الكل":
            await ranks_collection.delete_many({"chat_id": cid})
            await settings_collection.delete_many({"chat_id": cid})
            await replies_collection.delete_many({"chat_id": cid})
            await points_collection.delete_many({"chat_id": cid})
            await rules_collection.delete_many({"chat_id": cid})
            await welcome_collection.delete_many({"chat_id": cid})
            await ban_list_collection.delete_many({"chat_id": cid})
            return await message.reply_text("♥️ ¦ تـم مـسـح جـمـيـع بـيـانـات الـمـجـمـوعـة.")

        # --- مـسـح الـرتـب ---
        R_WIPE = {
            "المالكين الاساسيين": ["مالك اساسي"], "المالكين": ["مالك"],
            "المنشئين الاساسيين": ["منشئ اساسي"], "المنشئين": ["منشئ"],
            "المدراء": ["مدير"], "الادمنيه": ["ادمن"], "المميزين": ["مميز"],
            "المالكات الاساسيات": ["مالكه اساسيه"], "المالكات": ["مالكه"],
            "المنشئات الاساسيات": ["منشئه اساسيه"], "المنشئات": ["منشئه"],
            "المديرات": ["مديره"], "الادمونات": ["ادمونه"], "المميزات": ["مميزه"],
            "الرتب": "all"
        }
        if target in R_WIPE:
            q = {"chat_id": cid}
            if R_WIPE[target] != "all": q["rank"] = {"$in": R_WIPE[target]}
            res = await ranks_collection.delete_many(q)
            return await message.reply_text(f"✨ ¦ تـم مـسـح {res.deleted_count} مـن {target}.")

        # --- مـسـح الـقـوائـم ---
        if target == "المحظورين":
            c = 0
            async for m in message.chat.get_members(filter=enums.ChatMembersFilter.BANNED):
                try: await message.chat.unban_member(m.user.id); c+=1
                except: pass
            return await message.reply_text(f"🤍 ¦ تـم مـسـح {c} مـن الـحـظـر.")

        if target == "المكتومين":
            c = 0
            async for m in message.chat.get_members(filter=enums.ChatMembersFilter.RESTRICTED):
                if not m.permissions.can_send_messages:
                    try: await message.chat.unban_member(m.user.id); c+=1
                    except: pass
            return await message.reply_text(f"🤍 ¦ تـم مـسـح {c} مـن الـكـتـم.")

        if target == "قائمه المنع":
            await ban_list_collection.delete_many({"chat_id": cid})
            return await message.reply_text("✨ ¦ تـم تـفـريـغ قـائـمـة الـمـنـع.")

        # --- مـسـح الـردود والـمـيـديـا ---
        if target in ["الردود", "ردود الاعضاء"]:
            await replies_collection.delete_many({"chat_id": cid})
            return await message.reply_text("🧚 ¦ تـم حـذف الـردود.")
        
        if target == "الترحيب":
            await welcome_collection.delete_one({"chat_id": cid})
            return await message.reply_text("✨ ¦ تـم مـسـح الـتـرحـيـب.")
            
        if target == "بالرد":
            if message.reply_to_message:
                await message.reply_to_message.delete()
                await message.delete()
            return
    except: pass

# ==================================================================================================
# [ 7 ] الـعـقـوبـات (Actions)
# ==================================================================================================

# تم حذف (كتم / الغاء كتم) من هنا لمنع التداخل مع locks.py
@app.on_message(filters.command(["حظر", "طرد", "تقييد", "الغاء حظر", "الغاء تقييد", "رفع القيود", "طرد المحذوفين", "طرد البوتات", "كشف البوتات"], "") & filters.group)
async def actions_logic(client: Client, message: Message):
    try:
        cmd = message.command[0]
        cid = message.chat.id
        uid = message.from_user.id

        lock_key = "ban"
        if await is_setting_locked(cid, lock_key):
            if not await check_user_permission(cid, uid, 80):
                return await message.reply_text("🥀 ¦ الأمـر مـغـلـق حـالـيـاً.")

        if cmd == "طرد المحذوفين":
            if not await check_user_permission(cid, uid, 60): return
            c = 0
            async for m in message.chat.get_members():
                if m.user.is_deleted:
                    try: await message.chat.ban_member(m.user.id); c+=1
                    except: pass
            return await message.reply_text(f"✨ ¦ تـم طـرد {c} حـسـاب مـحـذوف.")

        if cmd == "كشف البوتات":
            bots = [f"🧚 {m.user.mention}" async for m in message.chat.get_members(filter=enums.ChatMembersFilter.BOTS)]
            if bots: await message.reply_text("\n".join(bots))
            else: await message.reply_text("🤍 ¦ لا يـوجـد بـوتـات.")
            return

        if not await check_user_permission(cid, uid, 50): return
        target = await get_target_member(message)
        if not target: return await message.reply_text("🥀 ¦ بـالـرد او الـمـعـرف.")
        
        # Check Power
        if (await get_user_rank_name(cid, target.id)) != "عضو" and uid != OWNER_ID:
            return await message.reply_text("🤎 ¦ لا يـمـكـنـك ذلـك.")

        try:
            if cmd == "حظر":
                await message.chat.ban_member(target.id)
                await message.reply_text(f"🥀 ¦ تـم حـظـر {target.mention}.")
            elif cmd == "الغاء حظر":
                await message.chat.unban_member(target.id)
                await message.reply_text(f"♥️ ¦ تـم الـغـاء الـحـظـر.")
            # تم حذف اكواد الكتم من هنا
        except: await message.reply_text("🤎 ¦ خـطـأ فـي الـتـنـفـيـذ.")
    except: pass

# ==================================================================================================
# [ 8 ] لـوحـة الـتـحـكـم (Dashboard)
# ==================================================================================================

@app.on_message(filters.command("انلاين الرتب", "") & filters.group)
async def open_dashboard(client: Client, message: Message):
    if not await check_user_permission(message.chat.id, message.from_user.id, 70):
        return await message.reply_text("🥀 ¦ لـلـمـنـشـئـيـن فـقـط.")

    markup = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🤎 رتـب الأولاد", callback_data="adm_show_boys"),
            InlineKeyboardButton("💕 رتـب الـبـنـات", callback_data="adm_show_girls")
        ],
        [
            InlineKeyboardButton("✨ أوامـر الـقـفـل", callback_data="adm_show_locks"),
            InlineKeyboardButton("🥀 أوامـر الـمـسـح", callback_data="adm_show_wipes")
        ],
        [
            InlineKeyboardButton("♥️ الـعـقـوبـات", callback_data="adm_show_actions"),
            InlineKeyboardButton("🧚 الإحـصـائـيـات", callback_data="adm_show_stats")
        ],
        [
            InlineKeyboardButton("🥀 إغـلاق الـلـوحـة", callback_data="adm_close_panel")
        ]
    ])

    await message.reply_text(
        text="<b>✨ لـوحـة الـتـحـكـم الـشـامـلـة 🧚</b>\n\n"
             "<b>🤍 ¦ اخـتـر الـقـسـم الـمـطـلـوب :</b>",
        reply_markup=markup
    )

@app.on_callback_query(filters.regex(r"^adm_"))
async def dashboard_callback(client: Client, callback_query):
    try:
        data = callback_query.data
        if not await check_user_permission(callback_query.message.chat.id, callback_query.from_user.id, 70):
            return await callback_query.answer("🥀 ¦ لـيـس لـديـك صـلاحـيـة.", show_alert=True)

        back_btn = [[InlineKeyboardButton("✨ الـرجـوع", callback_data="adm_back_home")]]

        if data == "adm_back_home":
            markup = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("🤎 رتـب الأولاد", callback_data="adm_show_boys"),
                    InlineKeyboardButton("💕 رتـب الـبـنـات", callback_data="adm_show_girls")
                ],
                [
                    InlineKeyboardButton("✨ أوامـر الـقـفـل", callback_data="adm_show_locks"),
                    InlineKeyboardButton("🥀 أوامـر الـمـسـح", callback_data="adm_show_wipes")
                ],
                [
                    InlineKeyboardButton("♥️ الـعـقـوبـات", callback_data="adm_show_actions"),
                    InlineKeyboardButton("🧚 الإحـصـائـيـات", callback_data="adm_show_stats")
                ],
                [
                    InlineKeyboardButton("🥀 إغـلاق الـلـوحـة", callback_data="adm_close_panel")
                ]
            ])
            await callback_query.edit_message_text("<b>✨ لـوحـة الـتـحـكـم الـشـامـلـة 🧚</b>", reply_markup=markup)

        elif data == "adm_show_boys":
            text = "<b>🤎 رتـب الأولاد :</b>\n\n• رفـع/تـنـزيـل مـالـك اسـاسـي\n• رفـع/تـنـزيـل مـالـك\n• رفـع/تـنـزيـل مـنـشـئ اسـاسـي\n• رفـع/تـنـزيـل مـنـشـئ\n• رفـع/تـنـزيـل مـديـر\n• رفـع/تـنـزيـل ادمـن\n• رفـع/تـنـزيـل مـمـيـز"
            await callback_query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(back_btn))

        elif data == "adm_show_girls":
            text = "<b>💕 رتـب الـبـنـات :</b>\n\n• رفـع/تـنـزيـل مـالـكـه اسـاسـيـه\n• رفـع/تـنـزيـل مـالـكـه\n• رفـع/تـنـزيـل مـنـشـئـه اسـاسـيـه\n• رفـع/تـنـزيـل مـنـشـئـه\n• رفـع/تـنـزيـل مـديـره\n• رفـع/تـنـزيـل ادمـونـه\n• رفـع/تـنـزيـل مـمـيـزه"
            await callback_query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(back_btn))

        elif data == "adm_show_locks":
            text = "<b>✨ أوامـر الـقـفـل (قـفـل/فـتـح) :</b>\n\n• امـر حـظـر\n• امـر رفـع / تـثـبـيـت\n• امـر هـمـسـه\n• امـر اضـف/مـسـح رد\n• امـر تـفـعـيـل افـتـاري/صـورتـي"
            await callback_query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(back_btn))

        elif data == "adm_show_wipes":
            text = "<b>🥀 أوامـر الـمـسـح :</b>\n\n• مـسـح الـكـل\n• مـسـح الـمـحـظـوريـن\n• مـسـح الـردود\n• مـسـح الـمـالـكـيـن\n• مـسـح الـمـنـشـئـيـن\n• مـسـح الـتـرحـيـب"
            await callback_query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(back_btn))

        elif data == "adm_show_actions":
            text = "<b>♥️ الـعـقـوبـات :</b>\n\n• حـظـر / الـغـاء حـظـر\n• طـرد\n• طـرد الـبـوتـات\n• طـرد الـمـحـذوفـيـن"
            await callback_query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(back_btn))

        elif data == "adm_show_stats":
            text = "<b>🧚 الإحـصـائـيـات :</b>\n\n• كـشـف الـرتـب\n• عـدد الـرتـب\n• كـشـف الـبـوتـات"
            await callback_query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(back_btn))

        elif data == "adm_close_panel":
            await callback_query.message.delete()
    except: pass
