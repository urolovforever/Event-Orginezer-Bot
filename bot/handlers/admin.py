from typing import Union

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from bot.states.event_states import EditEventStates, DeleteEventStates
from bot.database.db import db
from bot.config import Config
from bot.keyboards.inline import (
    get_event_list_keyboard,
    get_edit_field_keyboard,
    get_confirmation_keyboard
)

router = Router()


def is_admin(user_id: int) -> bool:
    """Check if user is admin"""
    return user_id in Config.ADMIN_IDS


# ============= EDIT EVENT FLOW =============

@router.message(Command("edit_event"))
@router.callback_query(F.data == "edit_event")
async def start_edit_event(event: Union[Message, CallbackQuery], state: FSMContext):
    """
    Start event editing flow.
    Show list of events to edit.
    """
    user_id = event.from_user.id

    if not is_admin(user_id):
        text = "❌ You don't have permission to edit events."
        if isinstance(event, Message):
            await event.answer(text)
        else:
            await event.answer(text, show_alert=True)
        return

    # Get all upcoming events
    events = await db.get_all_events()

    if not events:
        text = "📋 No events available to edit."
        if isinstance(event, Message):
            await event.answer(text)
        else:
            await event.message.edit_text(text)
            await event.answer()
        return

    text = "✏️ **Edit Event**\n\nSelect an event to edit:"
    keyboard = get_event_list_keyboard(events, prefix="edit")

    if isinstance(event, Message):
        await event.answer(text, reply_markup=keyboard)
    else:
        await event.message.edit_text(text, reply_markup=keyboard)
        await event.answer()

    await state.set_state(EditEventStates.selecting_event)


@router.callback_query(EditEventStates.selecting_event, F.data.startswith("edit_"))
async def select_event_to_edit(callback: CallbackQuery, state: FSMContext):
    """Handle event selection for editing"""
    event_id = int(callback.data.split("_")[1])

    # Get event details
    event = await db.get_event(event_id)
    if not event:
        await callback.answer("❌ Event not found.", show_alert=True)
        await state.clear()
        return

    # Store event ID
    await state.update_data(event_id=event_id)

    # Show event details and field selection
    text = (
        f"**Current Event Details:**\n\n"
        f"{event.format_message()}\n\n"
        f"Select which field you want to edit:"
    )

    await callback.message.edit_text(text, reply_markup=get_edit_field_keyboard())
    await state.set_state(EditEventStates.selecting_field)
    await callback.answer()


@router.callback_query(EditEventStates.selecting_field, F.data.startswith("field_"))
async def select_field_to_edit(callback: CallbackQuery, state: FSMContext):
    """Handle field selection for editing"""
    field = callback.data.split("_")[1]
    await state.update_data(field=field)

    field_names = {
        "title": "Title",
        "date": "Date (YYYY-MM-DD)",
        "time": "Time (HH:MM)",
        "location": "Location",
        "description": "Description"
    }

    text = f"✏️ Enter new **{field_names[field]}**:"
    await callback.message.edit_text(text)
    await state.set_state(EditEventStates.entering_new_value)
    await callback.answer()


@router.message(EditEventStates.entering_new_value)
async def process_new_value(message: Message, state: FSMContext):
    """
    Process new field value and update event.
    """
    data = await state.get_data()
    event_id = data["event_id"]
    field = data["field"]
    new_value = message.text.strip()

    # Validate input based on field type
    from datetime import datetime

    if field == "date":
        try:
            event_date = datetime.strptime(new_value, "%Y-%m-%d")
            if event_date.date() < datetime.now().date():
                await message.answer("❌ Date cannot be in the past. Please try again:")
                return
        except ValueError:
            await message.answer("❌ Invalid date format. Use YYYY-MM-DD:")
            return

    elif field == "time":
        try:
            datetime.strptime(new_value, "%H:%M")
        except ValueError:
            await message.answer("❌ Invalid time format. Use HH:MM:")
            return

    # Update event
    success = await db.update_event(event_id, field, new_value)

    if success:
        # Get updated event
        event = await db.get_event(event_id)
        await message.answer(
            f"✅ Event updated successfully!\n\n"
            f"{event.format_message()}"
        )
    else:
        await message.answer("❌ Failed to update event.")

    await state.clear()


# ============= DELETE EVENT FLOW =============

@router.message(Command("delete_event"))
@router.callback_query(F.data == "delete_event")
async def start_delete_event(event: Union[Message, CallbackQuery], state: FSMContext):
    """
    Start event deletion flow.
    Show list of events to delete.
    """
    user_id = event.from_user.id

    if not is_admin(user_id):
        text = "❌ You don't have permission to delete events."
        if isinstance(event, Message):
            await event.answer(text)
        else:
            await event.answer(text, show_alert=True)
        return

    # Get all upcoming events
    events = await db.get_all_events()

    if not events:
        text = "📋 No events available to delete."
        if isinstance(event, Message):
            await event.answer(text)
        else:
            await event.message.edit_text(text)
            await event.answer()
        return

    text = "🗑 **Delete Event**\n\nSelect an event to delete:"
    keyboard = get_event_list_keyboard(events, prefix="delete")

    if isinstance(event, Message):
        await event.answer(text, reply_markup=keyboard)
    else:
        await event.message.edit_text(text, reply_markup=keyboard)
        await event.answer()

    await state.set_state(DeleteEventStates.selecting_event)


@router.callback_query(DeleteEventStates.selecting_event, F.data.startswith("delete_"))
async def select_event_to_delete(callback: CallbackQuery, state: FSMContext):
    """Handle event selection for deletion"""
    event_id = int(callback.data.split("_")[1])

    # Get event details
    event = await db.get_event(event_id)
    if not event:
        await callback.answer("❌ Event not found.", show_alert=True)
        await state.clear()
        return

    # Show confirmation
    text = (
        f"⚠️ **Confirm Deletion**\n\n"
        f"{event.format_message()}\n\n"
        f"Are you sure you want to delete this event?"
    )

    keyboard = get_confirmation_keyboard("delete", event_id)
    await callback.message.edit_text(text, reply_markup=keyboard)
    await state.set_state(DeleteEventStates.confirming_deletion)
    await callback.answer()


@router.callback_query(DeleteEventStates.confirming_deletion, F.data.startswith("confirm_delete_"))
async def confirm_delete_event(callback: CallbackQuery, state: FSMContext):
    """Handle deletion confirmation"""
    event_id = int(callback.data.split("_")[2])

    # Delete event
    success = await db.delete_event(event_id)

    if success:
        await callback.message.edit_text("✅ Event deleted successfully!")
    else:
        await callback.message.edit_text("❌ Failed to delete event.")

    await state.clear()
    await callback.answer()