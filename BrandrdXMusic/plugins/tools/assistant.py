import asyncio
import time
from datetime import datetime
from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from motor.motor_asyncio import AsyncIOMotorClient
from BrandrdXMusic import app
from config import MONGO_DB_URI, OWNER_ID

# ==================================================================================================
# [ إعـدادات الـنـظـام الـذكي ]
# الآيدي: 8462240673
# ==================================================================================================

mongo_client = AsyncIOMotorClient(MONGO_DB_URI)
database = mongo_client.BrandrdX.admin_system_v3_db

# الجداول
assistant_logs = database.assistant_logs  # سجل الدخول
azan_logs = database.azan_logs            # سجل الأذان
ranks_collection = database.ranks         # الرتب
settings_collection = database.settings   # إعدادات (مثل تفعيل/تعطيل المشرفين)

ASSISTANT_ID = 8462240673

# ==================================================================================================
# [ أدوات الـمـسـاعـدة والـتـحـقـق ]
# ==================================================================================================

async def get_rank(chat_id: int, user_id: int):
    """التحقق من الرتبة"""
    if user_id == OWNER_ID: return "مطور"
    doc = await ranks_collection.find_one({"chat_id": chat_id, "user_id": user_id})
    return doc.get("rank") if doc else None

async def is_admins_allowed(chat_id: int) -> bool:
    """التحقق هل سمح المالك للمشرفين باستخدام الكيبورد؟"""
    doc = await settings_collection.find_one({"chat_id": chat_id})
    if doc and "allow_assist_view" in doc:
        return doc["allow_assist_view"]
    return False # الافتراضي: مغلق (للمالك فقط)

async def get_main_keyboard(chat_id: int):
    """دالة لإنشاء الكيبورد الرئيسي بحالته الحالية"""
    is_allowed = await is_admins_allowed(chat_id)
    toggle_text = "قفل المشرفين" if is_allowed else "فتح للمشرفين"
    
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("احصائيات عامة", callback_data="ast_glob"),
            InlineKeyboardButton("احصائيات الجروب", callback_data="ast_loc"),
        ],
        [
            InlineKeyboardButton(toggle_text, callback_data="ast_perm"),
        ],
        [
            InlineKeyboardButton("اغلاق", callback_data="ast_close"),
        ]
    ])

async def time_ago(milliseconds: int) -> str:
    """تنسيق الوقت المنقضي"""
    seconds = int(milliseconds / 1000)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    if hours > 0: return f"{hours} س و {minutes} د"
    if minutes > 0: return f"{minutes} دقيقة"
    return "الآن"

# ==================================================================================================
# [ 1 ] الـمـراقـبـات (Loggers) - أذان ودخول
# ==================================================================================================

@app.on_message(filters.regex(r"حان الآن موعد أذان") & filters.bot & filters.group, group=89)
async def log_azan_broadcast(client, message):
    try:
        now = datetime.now()
        await azan_logs.insert_one({
            "chat_id": message.chat.id,
            "chat_title": message.chat.title, 
            "date": now.strftime("%Y-%m-%d"),
            "time": now.strftime("%I:%M %p"),
            "timestamp": time.time()
        })
    except: pass

@app.on_message(filters.video_chat_members_invited & filters.group, group=88)
async def log_assistant_invite(client, message):
    try:
        invited = message.video_chat_members_invited.users
        is_assistant = any(user.id == ASSISTANT_ID for user in invited)
        if is_assistant:
            inviter = message.from_user
            now = datetime.now()
            await assistant_logs.insert_one({
                "chat_id": message.chat.id,
                "user_id": ASSISTANT_ID,
                "inviter_name": inviter.first_name,
                "date": now.strftime("%Y-%m-%d"),
                "time": now.strftime("%I:%M %p"),
                "timestamp": time.time()
            })
    except: pass

# ==================================================================================================
# [ 2 ] نـظـام الـكـيـبـورد (كيب المساعد)
# ==================================================================================================

@app.on_message(filters.command("كيب المساعد", "") & filters.group)
async def assistant_keyboard_panel(client, message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    # 1. التحقق من الصلاحية
    rank = await get_rank(chat_id, user_id)
    if not rank and user_id != OWNER_ID:
        return await message.reply_text("🤎 ¦ هذا الأمر للمسؤولين فقط 🧚")

    # 2. جلب الكيبورد وعرضه
    keyboard = await get_main_keyboard(chat_id)
    
    await message.reply_text(
        "🧚 ¦ **لـوحـة تـحـكـم الـمـسـاعـد والـأذان**\n"
        "🤎 ¦ أهـلا بـك عـزيـزي الـمـطـور/الـمـشـرف\n"
        "💕 ¦ يـمـكـنـك الـتـحـكـم بـالـسـجـلات مـن هـنـا :",
        reply_markup=keyboard
    )

@app.on_callback_query(filters.regex(r"^ast_"))
async def assistant_callback_handler(client, callback: CallbackQuery):
    data = callback.data
    user_id = callback.from_user.id
    chat_id = callback.message.chat.id
    is_owner = (user_id == OWNER_ID)
    
    # [ زر الإغلاق ]
    if data == "ast_close":
        await callback.message.delete()
        return

    # [ زر الرجوع للقائمة الرئيسية ]
    if data == "ast_back":
        keyboard = await get_main_keyboard(chat_id)
        await callback.message.edit_text(
            "🧚 ¦ **لـوحـة تـحـكـم الـمـسـاعـد والـأذان**\n"
            "🤎 ¦ أهـلا بـك عـزيـزي الـمـطـور/الـمـشـرف\n"
            "💕 ¦ يـمـكـنـك الـتـحـكـم بـالـسـجـلات مـن هـنـا :",
            reply_markup=keyboard
        )
        return

    # [ زر التحكم بالصلاحية ](تحديث فوري ومتصل)
    if data == "ast_perm":
        if not is_owner:
            return await callback.answer("هذا الزر للمالك الاساسي فقط", show_alert=True)
            
        current_state = await is_admins_allowed(chat_id)
        new_state = not current_state
        
        # حفظ الإعداد الجديد
        await settings_collection.update_one(
            {"chat_id": chat_id},
            {"$set": {"allow_assist_view": new_state}},
            upsert=True
        )
        
        # إعادة تحميل الكيبورد بالحالة الجديدة
        keyboard = await get_main_keyboard(chat_id)
        state_text = "مسموح" if new_state else "مغلق"
        
        # تعديل الرسالة لتبدو متصلة
        await callback.message.edit_text(
            f"🧚 ¦ **تـم تـحـديـث الـصـلاحـيـات بـنـجـاح**\n"
            f"🤎 ¦ حـالـة عـرض الـسـجـلات للمـشـرفـيـن الآن : **{state_text}** 💕\n"
            f"👇 ¦ يـمـكـنـك الـمـتـابـعـة مـن الأسـفـل :",
            reply_markup=keyboard
        )
        return

    # [ زر الإحصائيات العامة ]
    if data == "ast_glob":
        if not is_owner:
            return await callback.answer("هذا التقرير للمطور فقط", show_alert=True)
            
        groups_azan = len(await azan_logs.distinct("chat_id"))
        groups_join = len(await assistant_logs.distinct("chat_id"))
        total_azan = await azan_logs.count_documents({})
        total_join = await assistant_logs.count_documents({})
        
        text = (
            "🤎 ¦ **الـتـقـريـر الـعـام (لـلـمـطـور)**\n"
            "ـــــــــــــــــــــــــــــــــــــــــــــــــــــ\n\n"
            f"🕌 ¦ عـدد جـروبـات الـأذان : {groups_azan}\n"
            f"🤍 ¦ إجـمـالـي مـرات الـأذان : {total_azan}\n"
            f"🧚 ¦ عـدد جـروبـات الـمـسـاعـد : {groups_join}\n"
            f"💕 ¦ إجـمـالـي مـرات الـدخـول : {total_join}\n\n"
            "🤎 ¦ **مـلـحـوظـة :** هـذه الأرقـام إجـمـالـيـة لـكـل الـمـجـمـوعـات."
        )
        await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("رجوع", callback_data="ast_back")]]))
        return

    # [ زر إحصائيات الجروب ]
    if data == "ast_loc":
        admins_ok = await is_admins_allowed(chat_id)
        if not is_owner and not admins_ok:
            return await callback.answer("هذا التقرير محصور للمالك حالياً", show_alert=True)
        
        local_azan = await azan_logs.count_documents({"chat_id": chat_id})
        local_joins = await assistant_logs.count_documents({"chat_id": chat_id})
        
        state = "غير موجود"
        try:
            mem = await app.get_chat_member(chat_id, ASSISTANT_ID)
            if mem.status == enums.ChatMemberStatus.ADMINISTRATOR: state = "مشرف"
            elif mem.status == enums.ChatMemberStatus.MEMBER: state = "عضو"
        except: pass
        
        text = (
            "🕌 ¦ **تـقـريـر الـمـجـمـوعـة الـحـالـيـة**\n"
            "ـــــــــــــــــــــــــــــــــــــــــــــــــــــ\n\n"
            f"🧚 ¦ حـالـة الـمـسـاعـد : {state}\n"
            f"🤎 ¦ عـدد مـرات الـأذان : {local_azan}\n"
            f"💕 ¦ عـدد مـرات الـدخـول : {local_joins}\n"
        )
        await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("رجوع", callback_data="ast_back")]]))
        return

# ==================================================================================================
# [ 3 ] الأوامـر الـنـصـيـة (للسرعة أو كبديل)
# ==================================================================================================

@app.on_message(filters.command("سجل الاذان", "") & filters.group)
async def text_azan_report(client, message):
    try:
        if not await get_rank(message.chat.id, message.from_user.id):
             return await message.reply_text("للادارة فقط 🤎")
        
        count = await azan_logs.count_documents({"chat_id": message.chat.id})
        if count == 0: return await message.reply_text("لم يعمل الأذان هنا من قبل 🤍")
        
        msg = f"🧚 ¦ **سـجـل إقـامـة الـصـلاة**\nــــــــــــــــــــــــــــــــــــــــ\n"
        cursor = azan_logs.find({"chat_id": message.chat.id}).sort("timestamp", -1).limit(5)
        async for doc in cursor:
            msg += f"🕌 ¦ {doc['date']} ({doc['time']})\n"
        msg += f"\n🤎 ¦ الإجمالي : {count}"
        await message.reply_text(msg)
    except: pass

@app.on_message(filters.command("مسح سجل المساعد", "") & filters.group)
async def text_clear_logs(client, message):
    try:
        rank = await get_rank(message.chat.id, message.from_user.id)
        if rank not in ["مالك اساسي", "مالك", "منشئ اساسي", "منشئ", "مطور"]:
             return await message.reply_text("هذا الأمر لكبار المسؤولين فقط 🧚")

        r1 = await assistant_logs.delete_many({"chat_id": message.chat.id})
        r2 = await azan_logs.delete_many({"chat_id": message.chat.id})
        await message.reply_text(f"💕 ¦ تـم تـنـظـيـف {r1.deleted_count + r2.deleted_count} سـجـل.")
    except: pass
