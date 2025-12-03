"""Event management handlers."""
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from datetime import datetime, timedelta
from database import db
from states import AddEventStates, EditEventStates
import keyboards as kb
from google_sheets import sheets_manager
import re

router = Router()

# Global scheduler instance (set by bot.py at startup)
reminder_scheduler = None


# ========== ADD EVENT HANDLERS ==========

@router.message(F.text == "➕ Tadbir qo'shish")
async def start_add_event(message: Message, state: FSMContext):
    """Start adding a new event."""
    await message.answer(
        "Tadbir qo'shish jarayonini boshlaymiz.\n\n"
        "Tadbir nomini kiriting:",
        reply_markup=kb.get_cancel_keyboard()
    )
    await state.set_state(AddEventStates.waiting_for_title)


@router.message(AddEventStates.waiting_for_title, F.text == "❌ Bekor qilish")
async def cancel_add_event(message: Message, state: FSMContext):
    """Cancel adding event."""
    await state.clear()
    user_id = message.from_user.id
    is_admin = await db.is_admin(user_id)

    await message.answer(
        "Tadbir qo'shish bekor qilindi.",
        reply_markup=kb.get_main_menu_keyboard(is_admin)
    )


@router.message(AddEventStates.waiting_for_title)
async def process_event_title(message: Message, state: FSMContext):
    """Process event title."""
    title = message.text.strip()

    if len(title) < 3:
        await message.answer("Tadbir nomi juda qisqa. Iltimos, kamida 3 ta belgidan iborat nom kiriting:")
        return

    await state.update_data(title=title)
    await message.answer(
        "Ajoyib! Endi tadbir sanasini kiriting.\n\n"
        "Format: DD.MM.YYYY (masalan: 25.12.2024)",
        reply_markup=kb.get_cancel_keyboard()
    )
    await state.set_state(AddEventStates.waiting_for_date)


@router.message(AddEventStates.waiting_for_date, F.text == "❌ Bekor qilish")
async def cancel_at_date(message: Message, state: FSMContext):
    """Cancel at date step."""
    await cancel_add_event(message, state)


@router.message(AddEventStates.waiting_for_date)
async def process_event_date(message: Message, state: FSMContext):
    """Process event date."""
    date_text = message.text.strip()

    # Validate date format
    if not re.match(r'^\d{2}\.\d{2}\.\d{4}$', date_text):
        await message.answer(
            "❌ Noto'g'ri format. Iltimos, sanani DD.MM.YYYY formatida kiriting (masalan: 25.12.2024):"
        )
        return

    # Parse and validate date
    try:
        day, month, year = map(int, date_text.split('.'))
        event_date = datetime(year, month, day)

        # Check if date is not in the past
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        if event_date < today:
            await message.answer(
                "❌ Tadbir sanasi o'tmishda bo'lishi mumkin emas. Iltimos, bugungi yoki kelajakdagi sanani kiriting:"
            )
            return

    except ValueError:
        await message.answer(
            "❌ Noto'g'ri sana. Iltimos, to'g'ri sanani kiriting (masalan: 25.12.2024):"
        )
        return

    await state.update_data(date=date_text)
    await message.answer(
        "Yaxshi! Endi tadbir vaqtini kiriting.\n\n"
        "Format: HH:MM (24 soatlik, masalan: 14:30)",
        reply_markup=kb.get_cancel_keyboard()
    )
    await state.set_state(AddEventStates.waiting_for_time)


@router.message(AddEventStates.waiting_for_time, F.text == "❌ Bekor qilish")
async def cancel_at_time(message: Message, state: FSMContext):
    """Cancel at time step."""
    await cancel_add_event(message, state)


@router.message(AddEventStates.waiting_for_time)
async def process_event_time(message: Message, state: FSMContext):
    """Process event time."""
    time_text = message.text.strip()

    # Validate time format
    if not re.match(r'^\d{2}:\d{2}$', time_text):
        await message.answer(
            "❌ Noto'g'ri format. Iltimos, vaqtni HH:MM formatida kiriting (masalan: 14:30):"
        )
        return

    # Parse and validate time
    try:
        hour, minute = map(int, time_text.split(':'))
        if not (0 <= hour <= 23 and 0 <= minute <= 59):
            raise ValueError

    except ValueError:
        await message.answer(
            "❌ Noto'g'ri vaqt. Iltimos, to'g'ri vaqtni kiriting (masalan: 14:30):"
        )
        return

    await state.update_data(time=time_text)
    await message.answer(
        "Ajoyib! Endi tadbir o'tkaziladigan joyni kiriting:",
        reply_markup=kb.get_cancel_keyboard()
    )
    await state.set_state(AddEventStates.waiting_for_place)


@router.message(AddEventStates.waiting_for_place, F.text == "❌ Bekor qilish")
async def cancel_at_place(message: Message, state: FSMContext):
    """Cancel at place step."""
    await cancel_add_event(message, state)


@router.message(AddEventStates.waiting_for_place)
async def process_event_place(message: Message, state: FSMContext):
    """Process event place."""
    place = message.text.strip()

    if len(place) < 2:
        await message.answer("Joy nomi juda qisqa. Iltimos, to'g'ri joy nomini kiriting:")
        return

    await state.update_data(place=place)
    await message.answer(
        "Yaxshi! Agar tadbir haqida qo'shimcha izoh qo'shmoqchi bo'lsangiz, kiriting.\n\n"
        "Aks holda, 'O'tkazib yuborish' tugmasini bosing:",
        reply_markup=kb.get_skip_keyboard()
    )
    await state.set_state(AddEventStates.waiting_for_comment)


@router.message(AddEventStates.waiting_for_comment, F.text == "⏭ O'tkazib yuborish")
async def skip_comment(message: Message, state: FSMContext):
    """Skip comment and show confirmation."""
    await state.update_data(comment="Izoh yo'q")
    await show_event_confirmation(message, state)


@router.message(AddEventStates.waiting_for_comment, F.text == "❌ Bekor qilish")
async def cancel_at_comment(message: Message, state: FSMContext):
    """Cancel at comment step."""
    await cancel_add_event(message, state)


@router.message(AddEventStates.waiting_for_comment)
async def process_event_comment(message: Message, state: FSMContext):
    """Process event comment."""
    comment = message.text.strip()
    await state.update_data(comment=comment)
    await show_event_confirmation(message, state)


async def show_event_confirmation(message: Message, state: FSMContext):
    """Show event confirmation."""
    data = await state.get_data()

    confirmation_text = (
        "📋 <b>Tadbir ma'lumotlarini tasdiqlang:</b>\n\n"
        f"<b>Nomi:</b> {data['title']}\n"
        f"<b>Sana:</b> {data['date']}\n"
        f"<b>Vaqt:</b> {data['time']}\n"
        f"<b>Joy:</b> {data['place']}\n"
        f"<b>Izoh:</b> {data['comment']}\n\n"
        "Tasdiqlaysizmi?"
    )

    await message.answer(
        confirmation_text,
        reply_markup=kb.get_confirmation_keyboard(),
        parse_mode="HTML"
    )
    await state.set_state(AddEventStates.waiting_for_confirmation)


@router.callback_query(AddEventStates.waiting_for_confirmation, F.data == "confirm_yes")
async def confirm_add_event(callback: CallbackQuery, state: FSMContext):
    """Confirm and add event."""
    data = await state.get_data()
    user_id = callback.from_user.id

    # Add event to database
    event_id = await db.add_event(
        title=data['title'],
        date=data['date'],
        time=data['time'],
        place=data['place'],
        comment=data['comment'],
        created_by_user_id=user_id
    )

    if event_id:
        # Get full event data with user info
        event = await db.get_event(event_id)

        # Add to Google Sheets
        if sheets_manager.is_connected():
            sheets_manager.add_event(event)

        # Send notification to media group
        try:
            from scheduler import reminder_scheduler
            if reminder_scheduler:
                await reminder_scheduler.send_immediate_notification(event)
        except Exception as e:
            print(f"Error sending notification: {e}")

        is_admin = await db.is_admin(user_id)

        await callback.message.edit_text(
            "✅ Tadbir muvaffaqiyatli qo'shildi!\n\n"
            "Media guruhiga xabar yuborildi.",
            reply_markup=None
        )

        await callback.message.answer(
            "Asosiy menyu:",
            reply_markup=kb.get_main_menu_keyboard(is_admin)
        )
    else:
        await callback.message.edit_text(
            "❌ Tadbir qo'shishda xatolik yuz berdi. Iltimos, qaytadan urinib ko'ring.",
            reply_markup=None
        )

    await state.clear()
    await callback.answer()


@router.callback_query(AddEventStates.waiting_for_confirmation, F.data == "confirm_no")
async def cancel_confirmation(callback: CallbackQuery, state: FSMContext):
    """Cancel event confirmation."""
    await state.clear()
    user_id = callback.from_user.id
    is_admin = await db.is_admin(user_id)

    await callback.message.edit_text(
        "❌ Tadbir qo'shish bekor qilindi.",
        reply_markup=None
    )

    await callback.message.answer(
        "Asosiy menyu:",
        reply_markup=kb.get_main_menu_keyboard(is_admin)
    )

    await callback.answer()


# ========== VIEW EVENTS HANDLERS ==========

@router.message(F.text == "📅 Tadbirlar jadvali")
async def show_events_menu(message: Message):
    """Show events schedule menu."""
    await message.answer(
        "Qaysi jadvalini ko'rmoqchisiz?",
        reply_markup=kb.get_events_schedule_keyboard()
    )


@router.callback_query(F.data == "schedule_today")
async def show_today_events(callback: CallbackQuery):
    """Show today's events."""
    today = datetime.now().strftime('%d.%m.%Y')
    events = await db.get_events_by_date(today)

    if not events:
        await callback.answer("Bugun tadbirlar yo'q", show_alert=True)
        return

    text = "<b>📆 Bugungi tadbirlar:</b>\n\n"
    for event in events:
        text += format_event_text(event) + "\n\n"

    await callback.message.edit_text(
        text,
        reply_markup=kb.get_events_schedule_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "schedule_week")
async def show_week_events(callback: CallbackQuery):
    """Show this week's events."""
    events = await db.get_upcoming_events()

    # Filter events for next 7 days
    today = datetime.now()
    week_later = today + timedelta(days=7)

    week_events = []
    for event in events:
        try:
            day, month, year = map(int, event['date'].split('.'))
            event_date = datetime(year, month, day)
            if today <= event_date <= week_later:
                week_events.append(event)
        except:
            pass

    if not week_events:
        await callback.answer("Kelgusi haftada tadbirlar yo'q", show_alert=True)
        return

    text = "<b>📅 Haftalik jadval:</b>\n\n"
    for event in week_events:
        text += format_event_text(event) + "\n\n"

    await callback.message.edit_text(
        text,
        reply_markup=kb.get_events_schedule_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "schedule_all")
async def show_all_events(callback: CallbackQuery):
    """Show all upcoming events."""
    events = await db.get_upcoming_events(limit=20)

    if not events:
        await callback.answer("Hozircha tadbirlar yo'q", show_alert=True)
        return

    text = "<b>📋 Barcha tadbirlar:</b>\n\n"
    for event in events:
        text += format_event_text(event) + "\n\n"

    if len(events) == 20:
        text += "\n<i>... va boshqalar</i>"

    await callback.message.edit_text(
        text,
        reply_markup=kb.get_events_schedule_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "back_to_menu")
async def back_to_menu_callback(callback: CallbackQuery):
    """Back to main menu."""
    user_id = callback.from_user.id
    is_admin = await db.is_admin(user_id)

    await callback.message.delete()
    await callback.message.answer(
        "Asosiy menyu:",
        reply_markup=kb.get_main_menu_keyboard(is_admin)
    )
    await callback.answer()


# ========== MY EVENTS HANDLERS ==========

@router.message(F.text == "📝 Mening tadbirlarim")
async def show_my_events(message: Message):
    """Show user's events."""
    user_id = message.from_user.id
    events = await db.get_events_by_user(user_id)

    if not events:
        await message.answer("Sizda hali tadbirlar yo'q.")
        return

    await message.answer(
        "Sizning tadbirlaringiz:",
        reply_markup=kb.get_my_events_keyboard(events)
    )


@router.callback_query(F.data.startswith("view_event_"))
async def view_event_detail(callback: CallbackQuery):
    """View event details."""
    event_id = int(callback.data.split("_")[2])
    event = await db.get_event(event_id)

    if not event:
        await callback.answer("Tadbir topilmadi", show_alert=True)
        return

    user_id = callback.from_user.id
    is_creator = event['created_by_user_id'] == user_id

    text = format_event_text(event, detailed=True)

    await callback.message.edit_text(
        text,
        reply_markup=kb.get_event_actions_keyboard(event_id, is_creator),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "back_to_events")
async def back_to_my_events(callback: CallbackQuery):
    """Back to my events list."""
    user_id = callback.from_user.id
    events = await db.get_events_by_user(user_id)

    await callback.message.edit_text(
        "Sizning tadbirlaringiz:",
        reply_markup=kb.get_my_events_keyboard(events)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("cancel_event_"))
async def cancel_event(callback: CallbackQuery):
    """Cancel an event."""
    event_id = int(callback.data.split("_")[2])
    event = await db.get_event(event_id)

    if not event:
        await callback.answer("Tadbir topilmadi", show_alert=True)
        return

    # Check if user is the creator
    if event['created_by_user_id'] != callback.from_user.id:
        await callback.answer("Siz bu tadbirni bekor qila olmaysiz", show_alert=True)
        return

    # Cancel event
    success = await db.cancel_event(event_id)

    if success:
        # Update Google Sheets
        if sheets_manager.is_connected():
            sheets_manager.mark_event_cancelled(event_id)

        await callback.answer("Tadbir bekor qilindi", show_alert=True)
        await back_to_my_events(callback)
    else:
        await callback.answer("Xatolik yuz berdi", show_alert=True)


# ========== EDIT EVENT HANDLERS ==========

@router.callback_query(F.data.startswith("edit_event_"))
async def start_edit_event(callback: CallbackQuery, state: FSMContext):
    """Start editing an event."""
    event_id = int(callback.data.split("_")[2])
    event = await db.get_event(event_id)

    if not event:
        await callback.answer("Tadbir topilmadi", show_alert=True)
        return

    # Check if user is the creator
    if event['created_by_user_id'] != callback.from_user.id:
        await callback.answer("Siz bu tadbirni tahrirlash huquqiga ega emassiz", show_alert=True)
        return

    # Save event ID to state
    await state.update_data(editing_event_id=event_id)

    # Show fields to edit
    await callback.message.edit_text(
        f"<b>Tadbir:</b> {event['title']}\n\n"
        "Qaysi maydonni tahrirlashni xohlaysiz?",
        reply_markup=kb.get_edit_event_fields_keyboard(),
        parse_mode="HTML"
    )
    await state.set_state(EditEventStates.selecting_field)
    await callback.answer()


@router.callback_query(EditEventStates.selecting_field, F.data.startswith("edit_field_"))
async def select_field_to_edit(callback: CallbackQuery, state: FSMContext):
    """Select which field to edit."""
    field = callback.data.split("_")[2]
    await state.update_data(editing_field=field)

    field_names = {
        "title": "tadbir nomi",
        "date": "sana (DD.MM.YYYY)",
        "time": "vaqt (HH:MM)",
        "place": "joy",
        "comment": "izoh"
    }

    await callback.message.edit_text(
        f"Yangi {field_names[field]}ni kiriting:",
        reply_markup=None
    )
    await state.set_state(EditEventStates.waiting_for_new_value)
    await callback.answer()


@router.callback_query(EditEventStates.selecting_field, F.data == "back_to_event")
async def back_to_event_from_edit(callback: CallbackQuery, state: FSMContext):
    """Cancel editing and go back to event."""
    data = await state.get_data()
    event_id = data.get('editing_event_id')
    await state.clear()

    if event_id:
        event = await db.get_event(event_id)
        if event:
            text = format_event_text(event, detailed=True)
            user_id = callback.from_user.id
            is_creator = event['created_by_user_id'] == user_id

            await callback.message.edit_text(
                text,
                reply_markup=kb.get_event_actions_keyboard(event_id, is_creator),
                parse_mode="HTML"
            )
    await callback.answer()


@router.message(EditEventStates.waiting_for_new_value)
async def process_new_field_value(message: Message, state: FSMContext):
    """Process the new value for the field."""
    data = await state.get_data()
    field = data.get('editing_field')
    event_id = data.get('editing_event_id')
    new_value = message.text.strip()

    # Validate based on field type
    if field == "date":
        if not re.match(r'^\d{2}\.\d{2}\.\d{4}$', new_value):
            await message.answer(
                "❌ Noto'g'ri format. Iltimos, sanani DD.MM.YYYY formatida kiriting:"
            )
            return

        try:
            day, month, year = map(int, new_value.split('.'))
            event_date = datetime(year, month, day)
            today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            if event_date < today:
                await message.answer("❌ Tadbir sanasi o'tmishda bo'lishi mumkin emas:")
                return
        except ValueError:
            await message.answer("❌ Noto'g'ri sana. Iltimos, to'g'ri sanani kiriting:")
            return

    elif field == "time":
        if not re.match(r'^\d{2}:\d{2}$', new_value):
            await message.answer(
                "❌ Noto'g'ri format. Iltimos, vaqtni HH:MM formatida kiriting:"
            )
            return

        try:
            hour, minute = map(int, new_value.split(':'))
            if not (0 <= hour <= 23 and 0 <= minute <= 59):
                raise ValueError
        except ValueError:
            await message.answer("❌ Noto'g'ri vaqt. Iltimos, to'g'ri vaqtni kiriting:")
            return

    elif field == "title" and len(new_value) < 3:
        await message.answer("Tadbir nomi juda qisqa. Kamida 3 ta belgidan iborat bo'lishi kerak:")
        return

    elif field == "place" and len(new_value) < 2:
        await message.answer("Joy nomi juda qisqa:")
        return

    # Update in database
    success = await db.update_event(event_id, **{field: new_value})

    if success:
        # Update in Google Sheets
        event = await db.get_event(event_id)
        if event and sheets_manager.is_connected():
            sheets_manager.update_event(event_id, event)

        user_id = message.from_user.id
        is_admin = await db.is_admin(user_id)

        await message.answer(
            "✅ Tadbir muvaffaqiyatli yangilandi!",
            reply_markup=kb.get_main_menu_keyboard(is_admin)
        )
    else:
        await message.answer("❌ Xatolik yuz berdi. Qaytadan urinib ko'ring.")

    await state.clear()


def format_event_text(event: dict, detailed: bool = False) -> str:
    """Format event information as text."""
    text = (
        f"<b>{event['title']}</b>\n"
        f"📅 {event['date']} – {event['time']}\n"
        f"📍 {event['place']}\n"
        f"💬 Izoh: {event.get('comment', 'Izoh yo\\'q')}"
    )

    if detailed:
        text += (
            f"\n\n👤 Mas'ul: {event['creator_name']}\n"
            f"🏢 Bo'lim: {event['creator_department']}\n"
            f"📱 Telefon: {event['creator_phone']}"
        )

    return text
