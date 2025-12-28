import asyncio
from pyrogram import Client, filters, enums
from pyrogram.types import ChatPrivileges, Message
from BrandrdXMusic import app
from BrandrdXMusic.misc import SUDOERS
from motor.motor_asyncio import AsyncIOMotorClient
from config import MONGO_DB_URI 

# --- إعداد MongoDB ---
mongodb = AsyncIOMotorClient(MONGO_DB_URI)
db = mongodb.BrandrdDB 
ranks_col = db.ranks   

MALE_RANKS = ["مالك اساسي", "مالك", "منشئ اساسي", "منشئ", "مدير", "ادمن", "مميز"]
FEMALE_RANKS = ["مالكه اساسيه", "مالكه", "منشئه اساسيه", "منشئه", "مديره", "ادمونه", "مميزه"]
ALL_RANKS = MALE_RANKS + FEMALE_RANKS

# --- دوال قاعدة البيانات ---
async def get_rank(chat_id, user_id):
    res = await ranks_col.find_one({"chat_id": chat_id, "user_id": user_id})
    return res["rank"] if res else None

async def set_rank(chat_id, user_id, rank_name):
    await ranks_col.update_one(
        {"chat_id": chat_id, "user_id": user_id},
        {"$set": {"rank": rank_name}},
        upsert=True
    )

async def del_rank(chat_id, user_id):
    await ranks_col.delete_one({"chat_id": chat_id, "user_id": user_id})

async def is_admin(client, message):
    if message.from_user.id in SUDOERS: return True
    try:
        m = await client.get_chat_member(message.chat.id, message.from_user.id)
        return m.status in [enums.ChatMemberStatus.OWNER, enums.ChatMemberStatus.ADMINISTRATOR]
    except: return False

# --- منطق الرفع والتبديل ---
@app.on_message(filters.regex(r"^(رفع|تنزيل) (.*)") & filters.group)
async def rank_switch_logic(client, message):
    if not await is_admin(client, message): return
    
    parts = message.text.split()
    action = parts[0]
    rank_name = " ".join(parts[1:])
    
    if rank_name not in ALL_RANKS: return 
    if not message.reply_to_message: return await message.reply_text("بـالـرد عـلـى الـعـضـو 🥀")

    user = message.reply_to_message.from_user
    chat_id = message.chat.id
    current_rank = await get_rank(chat_id, user.id)

    if action == "رفع":
        # إذا كانت الرتبة الجديدة هي نفسها الحالية
        if current_rank == rank_name:
            return await message.reply_text(f"الـعـضـو {user.mention} ↢ مـرفـوع {rank_name} بـالـفـعـل 🧚")
        
        # إذا كانت رتبة مختلفة، سيتم التبديل تلقائياً بفضل upsert=True في دالة set_rank
        await set_rank(chat_id, user.id, rank_name)
        await message.reply_text(f"تـم رفـع الـعـضـو ↢ {rank_name} ✨")

    elif action == "تنزيل":
        if current_rank != rank_name:
            return await message.reply_text(f"الـعـضـو {user.mention} ↢ لـيـس {rank_name} بـالـفـعـل 🥀")
        
        await del_rank(chat_id, user.id)
        await message.reply_text(f"تـم تـنـزيـل الـعـضـو مـن ↢ {rank_name} 💫")
