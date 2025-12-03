"""Admin handlers for statistics and management."""
from aiogram import Router, F
from aiogram.types import Message
from database import db
import keyboards as kb

router = Router()


@router.message(F.text == "📊 Statistika")
async def show_statistics(message: Message):
    """Show event statistics (admin only)."""
    user_id = message.from_user.id

    # Check if user is admin
    if not await db.is_admin(user_id):
        await message.answer("❌ Bu buyruqdan foydalanish uchun sizda ruxsat yo'q.")
        return

    # Get statistics
    total_events = await db.get_total_events_count()
    dept_stats = await db.get_event_count_by_department()

    text = "<b>📊 Tadbirlar statistikasi:</b>\n\n"
    text += f"<b>Jami tadbirlar:</b> {total_events}\n\n"
    text += "<b>Bo'limlar bo'yicha:</b>\n"

    for stat in dept_stats:
        text += f"• {stat['department']}: {stat['event_count']} ta\n"

    await message.answer(text, parse_mode="HTML")


@router.message(F.text == "👥 Barcha foydalanuvchilar")
async def show_all_users(message: Message):
    """Show all registered users (admin only)."""
    user_id = message.from_user.id

    # Check if user is admin
    if not await db.is_admin(user_id):
        await message.answer("❌ Bu buyruqdan foydalanish uchun sizda ruxsat yo'q.")
        return

    await message.answer("Bu funksiya hali ishlab chiqilmoqda.")
