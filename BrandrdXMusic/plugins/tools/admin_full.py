import asyncio
from pyrogram import Client, filters, enums
from pyrogram.types import (
    ChatPermissions, ChatPrivileges, Message, 
    InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
)
from motor.motor_asyncio import AsyncIOMotorClient
from BrandrdXMusic import app
from BrandrdXMusic.misc import SUDOERS

# ==================================================================================================
# [ 1 ] إعـدادات الاتـصـال وقـاعـدة الـبـيـانـات
# ==================================================================================================

try:
    from config import MONGO_DB_URI, OWNER_ID
except ImportError:
    MONGO_DB_URI = "mongodb://localhost:27017"
    OWNER_ID = 0

if not MONGO_DB_URI:
    MONGO_DB_URI = "mongodb://localhost:27017"

mongo_client = AsyncIOMotorClient(MONGO_DB_URI)
database = mongo_client.BrandrdX.admin_system_v3_db

# الجداول
ranks_collection = database.ranks              
replies_collection = database.replies          
stats_collection = database.stats  

reply_state = {}

# ==================================================================================================
# [ 2 ] العدادات (حساب الرسائل والتعديلات)
# ==================================================================================================

@app.on_message(filters.group & ~filters.service & ~filters.bot, group=1)
async def messages_counter(client, message):
    try:
        await stats_collection.update_one(
            {"chat_id": message.chat.id, "user_id": message.from_user.id},
            {"$inc": {"msgs": 1}},
            upsert=True
        )
    except: pass

@app.on_edited_message(filters.group & ~filters.service & ~filters.bot, group=1)
async def edits_counter(client, message):
    try:
        await stats_collection.update_one(
            {"chat_id": message.chat.id, "user_id": message.from_user.id},
            {"$inc": {"edits": 1}},
            upsert=True
        )
    except: pass

async def get_user_stats(chat_id, user_id):
    try:
        doc = await stats_collection.find_one({"chat_id": chat_id, "user_id": user_id})
        if doc: return doc.get("msgs", 0), doc.get("edits", 0)
        return 0, 0
    except: return 0, 0

# ==================================================================================================
# [ 3 ] نـظـام الـصـلاحـيـات والـرتـب
# ==================================================================================================

RANK_POWER_LEVELS = {
    "مالك اساسي": 100, "مالك": 90,
    "منشئ اساسي": 80, "منشئ": 70,
    "مدير": 60, "ادمن": 50, "مميز": 40,
    "مالكه اساسيه": 100, "مالكه": 90,
    "منشئه اساسيه": 80, "منشئه": 70,
    "مديره": 60, "ادمونه": 50, "مميزه": 40,
    "عضو": 0
}

async def get_user_rank_name(chat_id: int, user_id: int) -> str:
    try:
        if user_id == OWNER_ID or user_id in SUDOERS: return "مطور"
        user_doc = await ranks_collection.find_one({"chat_id": chat_id, "user_id": user_id})
        return user_doc.get("rank", "عضو") if user_doc else "عضو"
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
    if user_id == OWNER_ID or user_id in SUDOERS: return True
    current_rank = await get_user_rank_name(chat_id, user_id)
    return RANK_POWER_LEVELS.get(current_rank, 0) >= required_power

async def get_target_member(message: Message):
    if message.reply_to_message:
        return message.reply_to_message.from_user
    if len(message.command) > 1:
        user_input = message.command[1]
        try:
            if user_input.startswith("@"): return await app.get_users(user_input)
            elif user_input.isdigit(): return await app.get_users(int(user_input))
        except: return None
    return None

# ==================================================================================================
# [ 4 ] أوامـر الـرتـب والـمـسـح والـعـقـوبـات
# ==================================================================================================

RANK_COMMANDS_MAP = {
    "رفع مالك اساسي": "مالك اساسي", "تنزيل مالك اساسي": "عضو",
    "رفع مالك": "مالك", "تنزيل مالك": "عضو",
    "رفع منشئ اساسي": "منشئ اساسي", "تنزيل منشئ اساسي": "عضو",
    "رفع منشئ": "منشئ", "تنزيل منشئ": "عضو",
    "رفع مدير": "مدير", "تنزيل مدير": "عضو",
    "رفع ادمن": "ادمن", "تنزيل ادمن": "عضو",
    "رفع مميز": "مميز", "تنزيل مميز": "عضو"
}

@app.on_message(filters.regex(r"^(رفع|تنزيل|كشف الرتب|عدد الرتب|رتبتي)") & filters.group)
async def rank_logic(client: Client, message: Message):
    try:
        text = message.text.strip()
        chat_id = message.chat.id
        user_id = message.from_user.id
        
        if text == "كشف الرتب":
            if not await check_user_permission(chat_id, user_id, 50): return 
            msg = "<b>✨ كـشـف الـرتـب فـي الـمـجـمـوعـة 🧚 :</b>\n\n"
            cursor = ranks_collection.find({"chat_id": chat_id}).sort("power", -1)
            found = False
            async for doc in cursor:
                try:
                    u = await app.get_users(doc["user_id"])
                    msg += f"💕 ¦ {doc['rank']} ↢ {u.mention}\n"
                    found = True
                except: continue
            if not found: msg += "🧚 ¦ لا يـوجـد أي رتـب مـضـافـة."
            await message.reply_text(msg)
            return

        if text in RANK_COMMANDS_MAP:
            target_rank = RANK_COMMANDS_MAP[text]
            req_power = RANK_POWER_LEVELS.get(target_rank, 0) + 10
            
            if not await check_user_permission(chat_id, user_id, req_power):
                return await message.reply_text("🧚 ¦ رتـبـتـك لا تـسـمـح بـذلـك.")
            
            target = await get_target_member(message)
            if not target: return await message.reply_text("🧚 ¦ بـالـرد او الـمـعـرف.")
            
            await set_user_rank_in_db(chat_id, target.id, target_rank)
            
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
                except: pass
            
            verb = "تـنـزيـل" if target_rank == "عضو" else "رفـع"
            d_rank = target_rank if target_rank != "عضو" else "عضو"
            await message.reply_text(f"💕 ¦ تـم {verb} {target.mention} إلـى {d_rank}.")
    except: pass

@app.on_message(filters.regex(r"^مسح (.*)") & filters.group)
async def wipe_logic(client: Client, message: Message):
    try:
        if not message.matches: return
        target = message.matches[0].group(1).strip()
        cid = message.chat.id
        if target.isdigit(): return
        
        if not await check_user_permission(cid, message.from_user.id, 80):
            return await message.reply_text("🧚 ¦ لـلـمـنـشـئـيـن الأسـاسـيـيـن.")
        
        if target == "الردود":
             await replies_collection.delete_many({"chat_id": cid})
             return await message.reply_text("🧚 ¦ تـم حـذف الـردود.")
        elif target == "المحظورين":
            c = 0
            async for m in message.chat.get_members(filter=enums.ChatMembersFilter.BANNED):
                try: await message.chat.unban_member(m.user.id); c+=1
                except: pass
            return await message.reply_text(f"💕 ¦ تـم مـسـح {c} مـن الـحـظـر.")
    except: pass

@app.on_message(filters.command(["حظر", "طرد", "الغاء حظر"], "") & filters.group)
async def actions_logic(client: Client, message: Message):
    try:
        if not await check_user_permission(message.chat.id, message.from_user.id, 50): return
        target = await get_target_member(message)
        if not target: return await message.reply_text("🧚 ¦ بـالـرد او الـمـعـرف.")
        
        cmd = message.command[0]
        try:
            if cmd == "حظر":
                await message.chat.ban_member(target.id)
                await message.reply_text(f"🧚 ¦ تـم حـظـر {target.mention}.")
            elif cmd == "الغاء حظر":
                await message.chat.unban_member(target.id)
                await message.reply_text(f"💕 ¦ تـم الـغـاء الـحـظـر.")
            elif cmd == "طرد":
                await message.chat.ban_member(target.id)
                await message.chat.unban_member(target.id)
                await message.reply_text(f"🧚 ¦ تـم طـرد {target.mention}.")
        except Exception:
            await message.reply_text("🧚 ¦ ليس لدي صلاحية على هذا العضو.")
    except: pass

# ==================================================================================================
# [ 5 ] نـظـام الـردود الـشـامـل (نص، صورة، فيديو، استيكر، صوت)
# ==================================================================================================

@app.on_message(filters.command("اضف رد", "") & filters.group)
async def start_add_reply(client: Client, message: Message):
    try:
        chat_id = message.chat.id
        user_id = message.from_user.id

        if not await check_user_permission(chat_id, user_id, 50):
            return await message.reply_text("🧚 ¦ هـذا الأمـر لـلادارة فـقـط.")

        if user_id == OWNER_ID or user_id in SUDOERS:
            kb = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("• عـام (مـوحـد) •", callback_data=f"reply_scope_global"),
                    InlineKeyboardButton("• فـي الـجـروب فـقـط •", callback_data=f"reply_scope_local")
                ],
                [
                    InlineKeyboardButton("• اغـلاق •", callback_data="reply_close")
                ]
            ])
            await message.reply_text(
                "**اخـتـر نـوع الـرد الـذي تـريـد إضـافـتـه :**\n• عـام : يـظـهـر فـي جـمـيـع الـجـروبـات\n• خـاص : يـظـهـر هـنـا فـقـط",
                reply_markup=kb
            )
        else:
            reply_state[user_id] = {
                "step": "wait_keyword",
                "chat_id": chat_id, 
                "origin_chat": chat_id
            }
            await message.reply_text("**✨ ¦ حـلـو ، الـحـين ارسـل الـكلـمـة اللي تريـدهـا**")
    except Exception as e: print(e)

@app.on_callback_query(filters.regex(r"^reply_(scope_global|scope_local|close)"))
async def reply_scope_callback(client: Client, cb: CallbackQuery):
    try:
        user_id = cb.from_user.id
        chat_id = cb.message.chat.id
        data = cb.data

        if user_id != OWNER_ID and user_id not in SUDOERS:
            return await cb.answer("هذا الأمر للمالك فقط", show_alert=True)

        if data == "reply_close":
            await cb.message.delete()
            return

        save_chat_id = 0
        scope_text = "( عـام لـكـل الـجـروبـات )"
        if data == "reply_scope_local":
            save_chat_id = chat_id
            scope_text = "( لـهـذا الـجـروب فـقـط )"

        reply_state[user_id] = {
            "step": "wait_keyword",
            "chat_id": save_chat_id,
            "origin_chat": chat_id
        }
        await cb.message.edit_text(f"**✨ ¦ حـلـو ، الـحـين ارسـل الـكلـمـة اللي تريـدهـا**\n**{scope_text}**")
    except: pass

@app.on_message((filters.text | filters.media) & filters.group, group=50)
async def unified_reply_processor(client: Client, message: Message):
    try:
        user_id = message.from_user.id
        chat_id = message.chat.id
        
        if user_id not in reply_state: return
        state = reply_state[user_id]
        if state["origin_chat"] != chat_id: return

        if state["step"] == "wait_keyword":
            if not message.text: return await message.reply_text("🧚 ¦ يـجـب أن تـكـون الـكـلـمـة نـصـاً.")
            keyword = message.text.strip()
            reply_state[user_id]["step"] = "wait_response"
            reply_state[user_id]["keyword"] = keyword
            
            text_menu = (
                f"**✨ ¦ حـلـو , الـحـيـن ارسـل جـواب الـرد**\n"
                f"**• ( نص,صوره,فيديو,متحركه,بصمه,اغنيه,ملف )**\n"
                f"**ٴ⋆┄─┄─┄─┄┄─┄─┄─┄─┄┄⋆**\n"
                f"**{{اليوزر}} ↬ يوزر المستخدم**\n"
                f"**{{الرسائل}} ↬ عدد الرسائل**\n"
                f"**{{الاسم}} ↬ اسم المستخدم**\n"
                f"**{{الايدي}} ↬ ايدي المستخدم**\n"
                f"**{{الرتبه}} ↬ رتبة المستخدم**\n"
                f"**{{التعديل}} ↬ عدد التعديلات**"
            )
            await message.reply_text(text_menu)
            return

        elif state["step"] == "wait_response":
            keyword = state["keyword"]
            save_chat_id = state["chat_id"]
            reply_type = "text"
            file_id = None
            text_content = message.text or message.caption or ""
            
            # التعرف على نوع الميديا
            if message.photo: reply_type = "photo"; file_id = message.photo.file_id
            elif message.sticker: reply_type = "sticker"; file_id = message.sticker.file_id
            elif message.video: reply_type = "video"; file_id = message.video.file_id
            elif message.animation: reply_type = "animation"; file_id = message.animation.file_id
            elif message.audio: reply_type = "audio"; file_id = message.audio.file_id
            elif message.voice: reply_type = "voice"; file_id = message.voice.file_id
            elif message.document: reply_type = "document"; file_id = message.document.file_id

            await replies_collection.update_one(
                {"chat_id": save_chat_id, "keyword": keyword},
                {"$set": {"type": reply_type, "file_id": file_id, "text": text_content, "by": user_id}},
                upsert=True
            )
            del reply_state[user_id]
            scope_text = "عـام" if save_chat_id == 0 else "للمجمـوعـة"
            await message.reply_text(f"**🧚 ¦ تـم إضـافـة الـرد ({scope_text}) بـنـجـاح : {keyword}**")
    except: pass

@app.on_message(filters.command("مسح رد", "") & filters.group)
async def delete_reply_handler(client: Client, message: Message):
    try:
        user_id = message.from_user.id
        chat_id = message.chat.id
        if not await check_user_permission(chat_id, user_id, 50): return await message.reply_text("🧚 ¦ لـلادارة فـقـط.")
        if len(message.command) < 2: return await message.reply_text("🧚 ¦ اكـتـب الـكـلـمـة.")
        keyword = message.text.split(None, 1)[1].strip()

        del_count = 0
        res1 = await replies_collection.delete_one({"chat_id": chat_id, "keyword": keyword})
        del_count += res1.deleted_count
        if user_id == OWNER_ID or user_id in SUDOERS:
            res2 = await replies_collection.delete_one({"chat_id": 0, "keyword": keyword})
            del_count += res2.deleted_count

        if del_count > 0: await message.reply_text(f"🗑 ¦ تـم مـسـح الـرد : {keyword}")
        else: await message.reply_text("🧚 ¦ الـرد غـيـر مـوجـود.")
    except: pass

# ==================================================================================================
# [ 6 ] مـحـرك الـردود (Reply Engine)
# ==================================================================================================

@app.on_message(filters.text & filters.group, group=100)
async def reply_engine(client: Client, message: Message):
    try:
        if message.from_user.is_bot or message.text.startswith(("/", "!", ".", "#")): return
        
        chat_id = message.chat.id
        text = message.text.strip()
        user = message.from_user
        
        reply_data = await replies_collection.find_one({"chat_id": chat_id, "keyword": text})
        if not reply_data:
            reply_data = await replies_collection.find_one({"chat_id": 0, "keyword": text})
            
        if reply_data:
            r_type = reply_data.get("type")
            r_file = reply_data.get("file_id")
            raw_text = reply_data.get("text", "")
            
            final_text = raw_text
            if final_text:
                rank_name = await get_user_rank_name(chat_id, user.id)
                msgs, edits = await get_user_stats(chat_id, user.id)
                
                final_text = final_text.replace("{اليوزر}", f"@{user.username}" if user.username else "لا يوجد")
                final_text = final_text.replace("{الاسم}", user.first_name or "")
                final_text = final_text.replace("{الايدي}", str(user.id))
                final_text = final_text.replace("{الرتبه}", rank_name)
                final_text = final_text.replace("{الرسائل}", str(msgs)) 
                final_text = final_text.replace("{التعديل}", str(edits)) 

            # الإرسال بناءً على النوع
            if r_type == "text": await message.reply_text(final_text)
            elif r_type == "photo": await message.reply_photo(r_file, caption=final_text)
            elif r_type == "sticker": await message.reply_sticker(r_file)
            elif r_type == "video": await message.reply_video(r_file, caption=final_text)
            elif r_type == "animation": await message.reply_animation(r_file, caption=final_text)
            elif r_type == "audio": await message.reply_audio(r_file, caption=final_text)
            elif r_type == "voice": await message.reply_voice(r_file, caption=final_text)
            elif r_type == "document": await message.reply_document(r_file, caption=final_text)
            
    except: pass
