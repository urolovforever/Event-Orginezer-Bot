"""Registration and start handlers."""
from aiogram import Router, F
from aiogram.filters import CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardRemove

from config import ALLOWED_USER_IDS
from database import db
from states import RegistrationStates
import keyboards as kb

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    """Handle /start command with allowed users check."""
    user_id = message.from_user.id

    # Check if user is allowed
    if user_id not in ALLOWED_USER_IDS:
        await message.answer("❌ Sizda botni ishlatish uchun ruxsat yo'q!")
        return

    # Check if user is already registered
    if await db.is_user_registered(user_id):
        user = await db.get_user(user_id)
        is_admin = await db.is_admin(user_id)

        await message.answer(
            f"Xush kelibsiz, {user['full_name']}! 👋\n\n"
            f"Quyidagi menyudan kerakli bo'limni tanlang:",
            reply_markup=kb.get_main_menu_keyboard(is_admin)
        )
    else:
        # Start registration process
        await message.answer(
            "Assalomu alaykum! 👋\n\n"
            "Men Tadbirlar boshqaruvi botiman. Sizni ro'yxatdan o'tkazish uchun "
            "quyidagi ma'lumotlarni taqdim eting.\n\n"
            "Iltimos, ismingiz va familiyangizni kiriting:",
            reply_markup=ReplyKeyboardRemove()
        )
        await state.set_state(RegistrationStates.waiting_for_full_name)


@router.message(RegistrationStates.waiting_for_full_name)
async def process_full_name(message: Message, state: FSMContext):
    """Process user's full name."""
    full_name = message.text.strip()

    if len(full_name) < 3:
        await message.answer("Iltimos, to'liq ism va familiyangizni kiriting:")
        return

    # Save full name to state
    await state.update_data(full_name=full_name)

    # Get departments from database
    departments = await db.get_all_departments()

    # Ask for department
    await message.answer(
        "Ajoyib! Endi ishlaydigan bo'limingizni tanlang:",
        reply_markup=kb.get_departments_keyboard(departments)
    )
    await state.set_state(RegistrationStates.waiting_for_department)


@router.message(RegistrationStates.waiting_for_department)
async def process_department(message: Message, state: FSMContext):
    """Process user's department."""
    department = message.text.strip()

    # Save department to state
    await state.update_data(department=department)

    # Ask for phone number
    await message.answer(
        "Yaxshi! Endi telefon raqamingizni yuboring.\n\n"
        "Siz quyidagi tugma orqali telefon raqamingizni yuborishingiz yoki "
        "uni matn ko'rinishida kiritishingiz mumkin:",
        reply_markup=kb.get_phone_keyboard()
    )
    await state.set_state(RegistrationStates.waiting_for_phone)


@router.message(RegistrationStates.waiting_for_phone, F.contact)
async def process_phone_contact(message: Message, state: FSMContext):
    """Process phone number from contact sharing."""
    phone = message.contact.phone_number

    # Complete registration
    await complete_registration(message, state, phone)


@router.message(RegistrationStates.waiting_for_phone)
async def process_phone_text(message: Message, state: FSMContext):
    """Process phone number from text input."""
    phone = message.text.strip()

    # Basic phone validation
    if len(phone) < 9:
        await message.answer(
            "Telefon raqami juda qisqa. Iltimos, to'g'ri telefon raqamini kiriting:"
        )
        return

    # Complete registration
    await complete_registration(message, state, phone)


async def complete_registration(message: Message, state: FSMContext, phone: str):
    """Complete the registration process."""
    # Get data from state
    data = await state.get_data()
    full_name = data['full_name']
    department = data['department']

    # Save to database
    user_id = message.from_user.id
    success = await db.add_user(user_id, full_name, department, phone)

    if success:
        is_admin = await db.is_admin(user_id)

        await message.answer(
            "✅ Ro'yxatdan o'tish muvaffaqiyatli yakunlandi!\n\n"
            f"Ism: {full_name}\n"
            f"Bo'lim: {department}\n"
            f"Telefon: {phone}\n\n"
            "Endi quyidagi menyudan kerakli bo'limni tanlashingiz mumkin:",
            reply_markup=kb.get_main_menu_keyboard(is_admin)
        )
    else:
        await message.answer(
            "❌ Ro'yxatdan o'tishda xatolik yuz berdi. Iltimos, qaytadan urinib ko'ring.",
            reply_markup=ReplyKeyboardRemove()
        )

    # Clear state
    await state.clear()


@router.message(F.text == "🔙 Asosiy menyu")
async def back_to_main_menu(message: Message, state: FSMContext):
    """Return to main menu."""
    await state.clear()

    user_id = message.from_user.id
    is_admin = await db.is_admin(user_id)

    await message.answer(
        "Asosiy menyu:",
        reply_markup=kb.get_main_menu_keyboard(is_admin)
    )
