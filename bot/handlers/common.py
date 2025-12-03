from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from bot.keyboards.inline import get_main_menu, get_admin_menu
from bot.config import Config

router = Router()


@router.message(Command("start"))
async def cmd_start(message: Message):
    """
    Handle /start command.
    Welcome message with main menu.
    """
    user_name = message.from_user.first_name
    welcome_text = (
        f"👋 Hello, {user_name}!\n\n"
        f"Welcome to the University Event Management Bot.\n\n"
        f"Use the buttons below to get started or type /help for more information."
    )
    await message.answer(welcome_text, reply_markup=get_main_menu())


@router.message(Command("help"))
async def cmd_help(message: Message):
    """
    Handle /help command.
    Show available commands based on user role.
    """
    user_id = message.from_user.id
    is_admin = user_id in Config.ADMIN_IDS

    help_text = (
        "📚 **Available Commands:**\n\n"
        "**For Everyone:**\n"
        "/start - Show main menu\n"
        "/add_event - Add a new event\n"
        "/events_today - View today's events\n"
        "/events_week - View this week's events\n"
        "/events_all - View all upcoming events\n"
        "/help - Show this help message\n"
    )

    if is_admin:
        help_text += (
            "\n**Admin Commands:**\n"
            "/edit_event - Edit an existing event\n"
            "/delete_event - Delete an event\n"
            "/admin_help - Show admin menu\n"
        )

    await message.answer(help_text)


@router.message(Command("admin_help"))
async def cmd_admin_help(message: Message):
    """
    Handle /admin_help command.
    Show admin menu if user is admin.
    """
    user_id = message.from_user.id

    if user_id not in Config.ADMIN_IDS:
        await message.answer("❌ You don't have admin privileges.")
        return

    admin_text = (
        "🔐 **Admin Panel**\n\n"
        "Use the buttons below to manage events:"
    )
    await message.answer(admin_text, reply_markup=get_admin_menu())


@router.callback_query(F.data == "main_menu")
async def callback_main_menu(callback: CallbackQuery, state: FSMContext):
    """Handle return to main menu"""
    await state.clear()
    await callback.message.edit_text(
        "📋 Main Menu:",
        reply_markup=get_main_menu()
    )
    await callback.answer()


@router.callback_query(F.data == "cancel")
async def callback_cancel(callback: CallbackQuery, state: FSMContext):
    """Handle cancellation of any operation"""
    await state.clear()
    await callback.message.edit_text("❌ Operation cancelled.")
    await callback.answer()