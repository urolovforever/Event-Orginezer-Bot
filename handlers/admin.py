"""Admin handlers for statistics and management."""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from database import db
from states import DepartmentManagementStates
import keyboards as kb

router = Router()

# Filter: only respond to private messages (ignore groups)
router.message.filter(F.chat.type == "private")


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


@router.message(F.text == "🏢 Bo'limlar boshqaruvi")
async def manage_departments(message: Message):
    """Manage departments (admin only)."""
    user_id = message.from_user.id

    # Check if user is admin
    if not await db.is_admin(user_id):
        await message.answer("❌ Bu buyruqdan foydalanish uchun sizda ruxsat yo'q.")
        return

    await message.answer(
        "Bo'limlarni boshqarish:",
        reply_markup=kb.get_departments_management_keyboard()
    )


@router.callback_query(F.data == "dept_manage")
async def dept_manage_callback(callback: CallbackQuery):
    """Show departments management menu."""
    await callback.message.edit_text(
        "Bo'limlarni boshqarish:",
        reply_markup=kb.get_departments_management_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "dept_add")
async def start_add_department(callback: CallbackQuery, state: FSMContext):
    """Start adding a new department."""
    await callback.message.edit_text(
        "Yangi bo'lim nomini kiriting:",
        reply_markup=None
    )
    await state.set_state(DepartmentManagementStates.waiting_for_department_name)
    await callback.answer()


@router.message(DepartmentManagementStates.waiting_for_department_name)
async def process_new_department(message: Message, state: FSMContext):
    """Process new department name."""
    dept_name = message.text.strip()

    if len(dept_name) < 3:
        await message.answer("Bo'lim nomi juda qisqa. Kamida 3 ta belgidan iborat bo'lishi kerak:")
        return

    # Add to database
    success = await db.add_department(dept_name)

    user_id = message.from_user.id
    is_admin = await db.is_admin(user_id)

    if success:
        await message.answer(
            f"✅ '{dept_name}' bo'limi muvaffaqiyatli qo'shildi!",
            reply_markup=kb.get_main_menu_keyboard(is_admin)
        )
    else:
        await message.answer(
            "❌ Xatolik yuz berdi. Ehtimol bu bo'lim allaqachon mavjud.",
            reply_markup=kb.get_main_menu_keyboard(is_admin)
        )

    await state.clear()


@router.callback_query(F.data == "dept_list")
async def show_departments_list(callback: CallbackQuery):
    """Show list of departments for deletion."""
    departments = await db.get_all_departments_with_ids()

    if not departments:
        await callback.answer("Bo'limlar ro'yxati bo'sh", show_alert=True)
        return

    await callback.message.edit_text(
        "<b>Bo'limlar ro'yxati:</b>\n\n"
        "O'chirish uchun bo'limni tanlang:",
        reply_markup=kb.get_departments_list_keyboard(departments),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("dept_delete:"))
async def delete_department(callback: CallbackQuery):
    """Delete a department safely using its ID."""
    # Extract the department ID from callback_data
    dep_id = int(callback.data.split(":")[1])

    # Get the full department info from DB
    dep = await db.get_department_by_id(dep_id)
    if not dep:
        await callback.answer("❌ Bo'lim topilmadi", show_alert=True)
        return

    dep_name = dep["name"]

    # Delete department by ID
    success = await db.delete_department_by_id(dep_id)

    if success:
        await callback.answer(f"✅ '{dep_name}' o'chirildi", show_alert=True)

        # Refresh list
        departments = await db.get_all_departments_with_ids()
        if departments:
            await callback.message.edit_text(
                "<b>Bo'limlar ro'yxati:</b>\n\n"
                "O'chirish uchun bo'limni tanlang:",
                reply_markup=kb.get_departments_list_keyboard(departments),
                parse_mode="HTML"
            )
        else:
            await callback.message.edit_text(
                "Barcha bo'limlar o'chirildi.",
                reply_markup=kb.get_departments_management_keyboard()
            )
    else:
        await callback.answer("❌ Xatolik yuz berdi", show_alert=True)

