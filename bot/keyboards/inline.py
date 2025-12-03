from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import List
from bot.database.models import Event


def get_main_menu() -> InlineKeyboardMarkup:
    """Main menu keyboard for quick access"""
    keyboard = [
        [
            InlineKeyboardButton(text="➕ Add Event", callback_data="add_event"),
            InlineKeyboardButton(text="📅 Today's Events", callback_data="events_today")
        ],
        [
            InlineKeyboardButton(text="📆 This Week", callback_data="events_week"),
            InlineKeyboardButton(text="📋 All Events", callback_data="events_all")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_admin_menu() -> InlineKeyboardMarkup:
    """Admin menu keyboard"""
    keyboard = [
        [
            InlineKeyboardButton(text="✏️ Edit Event", callback_data="edit_event"),
            InlineKeyboardButton(text="🗑 Delete Event", callback_data="delete_event")
        ],
        [
            InlineKeyboardButton(text="🔙 Back to Main Menu", callback_data="main_menu")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_event_list_keyboard(events: List[Event], prefix: str = "select") -> InlineKeyboardMarkup:
    """
    Create keyboard with list of events.
    prefix: callback data prefix (e.g., 'select', 'edit', 'delete')
    """
    keyboard = []
    for event in events:
        button_text = f"{event.title} - {event.date} {event.time}"
        callback_data = f"{prefix}_{event.id}"
        keyboard.append([InlineKeyboardButton(text=button_text, callback_data=callback_data)])

    keyboard.append([InlineKeyboardButton(text="🔙 Cancel", callback_data="cancel")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_edit_field_keyboard() -> InlineKeyboardMarkup:
    """Keyboard for selecting which field to edit"""
    keyboard = [
        [InlineKeyboardButton(text="📝 Title", callback_data="field_title")],
        [InlineKeyboardButton(text="📅 Date", callback_data="field_date")],
        [InlineKeyboardButton(text="🕐 Time", callback_data="field_time")],
        [InlineKeyboardButton(text="📍 Location", callback_data="field_location")],
        [InlineKeyboardButton(text="📄 Description", callback_data="field_description")],
        [InlineKeyboardButton(text="🔙 Cancel", callback_data="cancel")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_confirmation_keyboard(action: str, event_id: int) -> InlineKeyboardMarkup:
    """Keyboard for confirming actions"""
    keyboard = [
        [
            InlineKeyboardButton(text="✅ Yes", callback_data=f"confirm_{action}_{event_id}"),
            InlineKeyboardButton(text="❌ No", callback_data="cancel")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_cancel_keyboard() -> InlineKeyboardMarkup:
    """Simple cancel keyboard"""
    keyboard = [[InlineKeyboardButton(text="🔙 Cancel", callback_data="cancel")]]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)