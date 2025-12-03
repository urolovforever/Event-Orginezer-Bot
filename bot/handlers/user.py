from typing import Union

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from datetime import datetime

from bot.states.event_states import AddEventStates
from bot.database.db import db
from bot.database.models import Event
from bot.keyboards.inline import get_cancel_keyboard

router = Router()


# ============= ADD EVENT FLOW =============

@router.message(Command("add_event"))
@router.callback_query(F.data == "add_event")
async def start_add_event(event: Union[Message, CallbackQuery], state: FSMContext):
    """
    Start the event creation flow.
    First step: ask for title.
    """
    text = (
        "➕ **Adding New Event**\n\n"
        "Let's create a new event step by step.\n\n"
        "**Step 1/5:** Please enter the event title:"
    )

    if isinstance(event, Message):
        await event.answer(text, reply_markup=get_cancel_keyboard())
    else:
        await event.message.edit_text(text, reply_markup=get_cancel_keyboard())
        await event.answer()

    await state.set_state(AddEventStates.waiting_for_title)


@router.message(AddEventStates.waiting_for_title)
async def process_title(message: Message, state: FSMContext):
    """Process event title and ask for date"""
    await state.update_data(title=message.text)

    await message.answer(
        "**Step 2/5:** Please enter the event date.\n\n"
        "Format: YYYY-MM-DD (e.g., 2025-12-15)",
        reply_markup=get_cancel_keyboard()
    )
    await state.set_state(AddEventStates.waiting_for_date)


@router.message(AddEventStates.waiting_for_date)
async def process_date(message: Message, state: FSMContext):
    """Process event date with validation"""
    date_str = message.text.strip()

    # Validate date format
    try:
        event_date = datetime.strptime(date_str, "%Y-%m-%d")
        # Check if date is not in the past
        if event_date.date() < datetime.now().date():
            await message.answer(
                "❌ The date cannot be in the past. Please enter a valid future date:",
                reply_markup=get_cancel_keyboard()
            )
            return
    except ValueError:
        await message.answer(
            "❌ Invalid date format. Please use YYYY-MM-DD format (e.g., 2025-12-15):",
            reply_markup=get_cancel_keyboard()
        )
        return

    await state.update_data(date=date_str)

    await message.answer(
        "**Step 3/5:** Please enter the event time.\n\n"
        "Format: HH:MM (e.g., 14:30 or 09:00)",
        reply_markup=get_cancel_keyboard()
    )
    await state.set_state(AddEventStates.waiting_for_time)


@router.message(AddEventStates.waiting_for_time)
async def process_time(message: Message, state: FSMContext):
    """Process event time with validation"""
    time_str = message.text.strip()

    # Validate time format
    try:
        datetime.strptime(time_str, "%H:%M")
    except ValueError:
        await message.answer(
            "❌ Invalid time format. Please use HH:MM format (e.g., 14:30):",
            reply_markup=get_cancel_keyboard()
        )
        return

    await state.update_data(time=time_str)

    await message.answer(
        "**Step 4/5:** Please enter the event location.\n\n"
        "Example: Building A, Room 301",
        reply_markup=get_cancel_keyboard()
    )
    await state.set_state(AddEventStates.waiting_for_location)


@router.message(AddEventStates.waiting_for_location)
async def process_location(message: Message, state: FSMContext):
    """Process event location and ask for description"""
    await state.update_data(location=message.text)

    await message.answer(
        "**Step 5/5:** Please enter a description for the event.\n\n"
        "Or type 'skip' if you don't want to add a description.",
        reply_markup=get_cancel_keyboard()
    )
    await state.set_state(AddEventStates.waiting_for_description)


@router.message(AddEventStates.waiting_for_description)
async def process_description(message: Message, state: FSMContext):
    """
    Process description and save event to database.
    Final step of event creation.
    """
    description = "" if message.text.lower() == "skip" else message.text
    await state.update_data(description=description)

    # Get all collected data
    data = await state.get_data()

    # Create event object
    event = Event(
        title=data["title"],
        date=data["date"],
        time=data["time"],
        location=data["location"],
        description=description,
        created_by=message.from_user.id
    )

    # Save to database
    event_id = await db.add_event(event)
    event.id = event_id

    # Send confirmation
    confirmation_text = (
        "✅ **Event Created Successfully!**\n\n"
        f"{event.format_message()}\n\n"
        f"Event ID: {event_id}"
    )
    await message.answer(confirmation_text)

    # Clear state
    await state.clear()


# ============= VIEW EVENTS =============

@router.message(Command("events_today"))
@router.callback_query(F.data == "events_today")
async def show_events_today(event: Union[Message, CallbackQuery]):
    """Show all events happening today"""
    events = await db.get_events_today()

    if not events:
        text = "📅 No events scheduled for today."
    else:
        text = f"📅 **Today's Events** ({len(events)}):\n\n"
        for evt in events:
            text += f"• {evt.title} at {evt.time}\n  📍 {evt.location}\n\n"

    if isinstance(event, Message):
        await event.answer(text)
    else:
        await event.message.edit_text(text)
        await event.answer()


@router.message(Command("events_week"))
@router.callback_query(F.data == "events_week")
async def show_events_week(event: Union[Message, CallbackQuery]):
    """Show all events happening this week"""
    events = await db.get_events_week()

    if not events:
        text = "📆 No events scheduled for this week."
    else:
        text = f"📆 **This Week's Events** ({len(events)}):\n\n"
        for evt in events:
            text += f"• {evt.title}\n"
            text += f"  📅 {evt.date} at {evt.time}\n"
            text += f"  📍 {evt.location}\n\n"

    if isinstance(event, Message):
        await event.answer(text)
    else:
        await event.message.edit_text(text)
        await event.answer()


@router.message(Command("events_all"))
@router.callback_query(F.data == "events_all")
async def show_all_events(event: Union[Message, CallbackQuery]):
    """Show all upcoming events"""
    events = await db.get_all_events()

    if not events:
        text = "📋 No upcoming events scheduled."
    else:
        text = f"📋 **All Upcoming Events** ({len(events)}):\n\n"
        for evt in events:
            text += f"• **{evt.title}**\n"
            text += f"  📅 {evt.date} at {evt.time}\n"
            text += f"  📍 {evt.location}\n\n"

    if isinstance(event, Message):
        await event.answer(text)
    else:
        await event.message.edit_text(text)
        await event.answer()