import asyncio
import time
from datetime import datetime
from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from motor.motor_asyncio import AsyncIOMotorClient
from BrandrdXMusic import app
from config import MONGO_DB_URI, OWNER_ID

# ==================================================================================================
# [ إعـدادات الـنـظـام وقـواعـد الـبـيـانـات ]
# ==================================================================================================

mongo_client = AsyncIOMotorClient(MONGO_DB_URI)
# نفس قاعدة البيانات المستخدمة في call.py و azan.py
database = mongo_client.BrandrdX.admin_system_v3_db

# الجداول (Collections)
assistant_logs = database.assistant_logs 
azan_logs = database.azan_logs 
ranks_collection = database.ranks 
settings_collection = database.settings 

ASSISTANT_ID = 8462240673
CB_PREFIX = "uniq_ast_sys_" 

# ==================================================================================================
# [ 1 ] أدوات الـتـحـقـق والـمساعـدة
# ==================================================================================================

async def get_rank(chat_id: int, user_id: int):
    """التحقق من الرتبة داخل الجروب"""
    if user_id == OWNER_ID: return "مطور"
    doc = await ranks_collection.find_one({"chat_id": chat_id, "user_id": user_id})
    return doc.get("rank") if doc else None

async def is_admins_allowed(chat_id: int) -> bool:
    """التحقق هل سمح المالك للمشرفين باستخدام الكيبورد؟"""
    doc = await settings_collection.find_one({"chat_id": chat_id})
    if doc and "allow_assist_view" in doc:
        return doc["allow_assist_view"]
    return False 

async def get_main_keyboard(chat_id: int):
    is_allowed = await is_admins_allowed(chat_id)
    toggle_text = "قفل المشرفين" if is_allowed else "فتح للمشرفين"
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("احصائيات عامة", callback_data=f"{CB_PREFIX}glob"),
            InlineKeyboardButton("احصائيات الجروب", callback_data=f"{CB_PREFIX}loc")
        ],
        [
            InlineKeyboardButton(toggle_text, callback_data=f"{CB_PREFIX}perm")
        ],
        [
            InlineKeyboardButton("اغلاق", callback_data=f"{CB_PREFIX}close")
        ]
    ])

# ==================================================================================================
# [ 2 ] الأوامـر والـتـفـاعـل (الكيبورد)
# ==================================================================================================

@app.on_message(filters.command(["كيب المساعد", "لوحة المساعد"], "") & filters.group, group=777)
async def assistant_keyboard_panel(client, message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    # التحقق من الصلاحية (مطور أو رتبة مسجلة)
    rank = await get_rank(chat_id, user_id)
    if not rank and user_id != OWNER_ID:
        # يمكن السماح للمشرفين العاديين اذا تم تفعيل الخيار، لكن هنا نتحقق مبدئيا
        if not await is_admins_allowed(chat_id):
            return await message.reply_text("🤎 ¦ هذا الأمر للمسؤولين فقط 🧚")

    keyboard = await get_main_keyboard(chat_id)
    await message.reply_text(
        "🧚 ¦ **لـوحـة تـحـكـم الـمـسـاعـد والـأذان**\n"
        "🤎 ¦ أهـلا بـك عـزيـزي الـمـطـور/الـمـشـرف\n"
        "💕 ¦ يـمـكـنـك عـرض الـسـجـلات مـن هـنـا :",
        reply_markup=keyboard
    )

@app.on_callback_query(filters.regex(f"^{CB_PREFIX}"))
async def assistant_callback_handler(client, callback: CallbackQuery):
    action = callback.data.replace(CB_PREFIX, "")
    user_id = callback.from_user.id
    chat_id = callback.message.chat.id
    is_owner = (user_id == OWNER_ID)
    
    rank = await get_rank(chat_id, user_id)
    
    # [ إغلاق ]
    if action == "close":
        if not is_owner and not rank:
            return await callback.answer("للمشرفين فقط", show_alert=True)
        await callback.message.delete()
        return

    # [ رجوع ]
    if action == "back":
        if not is_owner and not rank:
             return await callback.answer("للمشرفين فقط", show_alert=True)
        keyboard = await get_main_keyboard(chat_id)
        await callback.message.edit_text(
            "🧚 ¦ **لـوحـة تـحـكـم الـمـسـاعـد والـأذان**\n"
            "🤎 ¦ أهـلا بـك عـزيـزي الـمـطـور/الـمـشـرف\n"
            "💕 ¦ يـمـكـنـك الـتـحـكـم بـالـسـجـلات مـن هـنـا :",
            reply_markup=keyboard
        )
        return

    # [ الصلاحيات ]
    if action == "perm":
        if not is_owner:
            return await callback.answer("هذا الزر للمالك الاساسي فقط 🚫", show_alert=True)
            
        current_state = await is_admins_allowed(chat_id)
        new_state = not current_state
        
        await settings_collection.update_one(
            {"chat_id": chat_id},
            {"$set": {"allow_assist_view": new_state}},
            upsert=True
        )
        
        keyboard = await get_main_keyboard(chat_id)
        state_text = "مسموح للمشرفين" if new_state else "مغلق (للمالك)"
        
        await callback.message.edit_text(
            f"🧚 ¦ **تـم تـحـديـث الـصـلاحـيـات**\n"
            f"🤎 ¦ الـوضـع الـحـالـي : **{state_text}** 💕",
            reply_markup=keyboard
        )
        return

    # [ عام - للمطور فقط ]
    if action == "glob":
        if not is_owner:
            return await callback.answer("هذا التقرير للمطور فقط 🔒", show_alert=True)
            
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
            "🤎 ¦ **مـلـحـوظـة :** هـذه الأرقـام يتم تحديثها تلقائياً من السورس."
        )
        await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("رجوع", callback_data=f"{CB_PREFIX}back")]]))
        return

    # [ محلي - للجروب الحالي ]
    if action == "loc":
        admins_ok = await is_admins_allowed(chat_id)
        if not is_owner:
            if not admins_ok: return await callback.answer("مغلق من المالك 🔒", show_alert=True)
            if not rank and not admins_ok: return await callback.answer("للمشرفين فقط 🚫", show_alert=True)
        
        local_azan = await azan_logs.count_documents({"chat_id": chat_id})
        local_joins = await assistant_logs.count_documents({"chat_id": chat_id})
        
        # محاولة معرفة حالة المساعد الحالية
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
            f"💕 ¦ عـدد مـرات دخـول الكـول : {local_joins}\n"
        )
        await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("رجوع", callback_data=f"{CB_PREFIX}back")]]))
        return

# ==================================================================================================
# [ 3 ] الأوامـر الـنـصـيـة الإضـافـيـة
# ==================================================================================================

@app.on_message(filters.command("سجل الاذان", "") & filters.group, group=778)
async def text_azan_report(client, message):
    try:
        rank = await get_rank(message.chat.id, message.from_user.id)
        if not rank and message.from_user.id != OWNER_ID: return

        count = await azan_logs.count_documents({"chat_id": message.chat.id})
        if count == 0: return await message.reply_text("لم يعمل الأذان هنا من قبل 🤍")
        
        msg = f"🧚 ¦ **آخـر 5 مـرات لـلأذان**\nــــــــــــــــــــــــــــــــــــــــ\n"
        cursor = azan_logs.find({"chat_id": message.chat.id}).sort("timestamp", -1).limit(5)
        async for doc in cursor:
            msg += f"🕌 ¦ {doc['date']} ({doc['time']})\n"
        msg += f"\n🤎 ¦ الإجمالي : {count}"
        await message.reply_text(msg)
    except: pass

@app.on_message(filters.command("سجل المساعد", "") & filters.group, group=779)
async def text_assistant_report(client, message):
    try:
        rank = await get_rank(message.chat.id, message.from_user.id)
        if not rank and message.from_user.id != OWNER_ID: return

        count = await assistant_logs.count_documents({"chat_id": message.chat.id})
        if count == 0: return await message.reply_text("لم يدخل المساعد الكول هنا من قبل (أو لم يتم التسجيل) 🤍")
        
        msg = f"🧚 ¦ **آخـر 5 مـرات لـدخـول الـكـول**\nــــــــــــــــــــــــــــــــــــــــ\n"
        cursor = assistant_logs.find({"chat_id": message.chat.id}).sort("timestamp", -1).limit(5)
        async for doc in cursor:
            msg += f"👤 ¦ {doc['date']} ({doc['time']})\n"
        msg += f"\n🤎 ¦ الإجمالي : {count}"
        await message.reply_text(msg)
    except: pass

@app.on_message(filters.command("مسح سجل المساعد", "") & filters.group, group=780)
async def text_clear_logs(client, message):
    try:
        # الأمر حساس، نسمح به فقط للمالك أو المنشئ الأساسي
        if message.from_user.id != OWNER_ID:
             rank = await get_rank(message.chat.id, message.from_user.id)
             if rank not in ["مالك اساسي", "منشئ اساسي"]:
                 return await message.reply_text("هذا الأمر للمالك والمنشئ الأساسي فقط 🧚")
                 
        r1 = await assistant_logs.delete_many({"chat_id": message.chat.id})
        r2 = await azan_logs.delete_many({"chat_id": message.chat.id})
        await message.reply_text(f"💕 ¦ تـم تـنـظـيـف {r1.deleted_count + r2.deleted_count} سـجـل.")
    except: pass
