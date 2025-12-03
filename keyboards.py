"""Keyboard layouts for the Event Organizer Bot."""
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from typing import List, Optional
import config


def get_phone_keyboard() -> ReplyKeyboardMarkup:
    """Get keyboard with phone number sharing button."""
    keyboard = ReplyKeyboardBuilder()
    keyboard.button(text="📱 Telefon raqamini yuborish", request_contact=True)
    return keyboard.as_markup(resize_keyboard=True, one_time_keyboard=True)


def get_departments_keyboard() -> ReplyKeyboardMarkup:
    """Get keyboard with department buttons."""
    keyboard = ReplyKeyboardBuilder()
    for department in config.DEPARTMENTS:
        keyboard.button(text=department)
    keyboard.adjust(2)  # 2 buttons per row
    return keyboard.as_markup(resize_keyboard=True, one_time_keyboard=True)


def get_main_menu_keyboard(is_admin: bool = False) -> ReplyKeyboardMarkup:
    """Get main menu keyboard."""
    keyboard = ReplyKeyboardBuilder()
    keyboard.button(text="➕ Tadbir qo'shish")
    keyboard.button(text="📅 Tadbirlar jadvali")
    keyboard.button(text="📝 Mening tadbirlarim")

    if is_admin:
        keyboard.button(text="📊 Statistika")
        keyboard.button(text="👥 Barcha foydalanuvchilar")

    keyboard.adjust(2)
    return keyboard.as_markup(resize_keyboard=True)


def get_events_schedule_keyboard() -> InlineKeyboardMarkup:
    """Get keyboard for events schedule options."""
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="📆 Bugungi tadbirlar", callback_data="schedule_today")
    keyboard.button(text="📅 Haftalik jadval", callback_data="schedule_week")
    keyboard.button(text="📋 Barcha tadbirlar", callback_data="schedule_all")
    keyboard.button(text="🔙 Orqaga", callback_data="back_to_menu")
    keyboard.adjust(1)
    return keyboard.as_markup()


def get_confirmation_keyboard() -> InlineKeyboardMarkup:
    """Get confirmation keyboard."""
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="✅ Tasdiqlash", callback_data="confirm_yes")
    keyboard.button(text="❌ Bekor qilish", callback_data="confirm_no")
    keyboard.adjust(2)
    return keyboard.as_markup()


def get_event_actions_keyboard(event_id: int, is_creator: bool = True) -> InlineKeyboardMarkup:
    """Get keyboard with event actions."""
    keyboard = InlineKeyboardBuilder()

    if is_creator:
        keyboard.button(text="✏️ Tahrirlash", callback_data=f"edit_event_{event_id}")
        keyboard.button(text="❌ Bekor qilish", callback_data=f"cancel_event_{event_id}")

    keyboard.button(text="🔙 Orqaga", callback_data="back_to_events")
    keyboard.adjust(2 if is_creator else 1)
    return keyboard.as_markup()


def get_edit_event_fields_keyboard() -> InlineKeyboardMarkup:
    """Get keyboard for selecting field to edit."""
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="📝 Tadbir nomi", callback_data="edit_field_title")
    keyboard.button(text="📅 Sana", callback_data="edit_field_date")
    keyboard.button(text="🕐 Vaqt", callback_data="edit_field_time")
    keyboard.button(text="📍 Joy", callback_data="edit_field_place")
    keyboard.button(text="💬 Izoh", callback_data="edit_field_comment")
    keyboard.button(text="🔙 Orqaga", callback_data="back_to_event")
    keyboard.adjust(1)
    return keyboard.as_markup()


def get_my_events_keyboard(events: List[dict]) -> InlineKeyboardMarkup:
    """Get keyboard with user's events."""
    keyboard = InlineKeyboardBuilder()

    for event in events:
        button_text = f"{event['date']} - {event['title'][:30]}"
        keyboard.button(text=button_text, callback_data=f"view_event_{event['id']}")

    keyboard.button(text="🔙 Orqaga", callback_data="back_to_menu")
    keyboard.adjust(1)
    return keyboard.as_markup()


def get_cancel_keyboard() -> ReplyKeyboardMarkup:
    """Get keyboard with cancel button."""
    keyboard = ReplyKeyboardBuilder()
    keyboard.button(text="❌ Bekor qilish")
    return keyboard.as_markup(resize_keyboard=True)


def get_skip_keyboard() -> ReplyKeyboardMarkup:
    """Get keyboard with skip button for optional fields."""
    keyboard = ReplyKeyboardBuilder()
    keyboard.button(text="⏭ O'tkazib yuborish")
    keyboard.button(text="❌ Bekor qilish")
    keyboard.adjust(2)
    return keyboard.as_markup(resize_keyboard=True)


def remove_keyboard() -> ReplyKeyboardMarkup:
    """Remove keyboard."""
    from aiogram.types import ReplyKeyboardRemove
    return ReplyKeyboardRemove()
