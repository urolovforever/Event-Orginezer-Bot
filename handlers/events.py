"""Event management handlers."""
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from datetime import datetime, timedelta
from database import db
from states import AddEventStates, EditEventStates
import keyboards as kb
from google_sheets import sheets_manager
import config
import re

router = Router()

# Filter: only respond to private messages (ignore groups)
router.message.filter(F.chat.type == "private")

# Global scheduler instance (set by bot.py at startup)
reminder_scheduler = None


# ========== ADD EVENT HANDLERS ==========

@router.message(F.text == "➕ Tadbir qo'shish")
async def start_add_event(message: Message, state: FSMContext):
    """Start adding a new event."""
    # Check if user is registered
    user_id = message.from_user.id
    if not await db.is_user_registered(user_id):
        await message.answer(
            "❌ Tadbir qo'shish uchun avval ro'yxatdan o'tishingiz kerak.\n"
            "Iltimos, /start buyrug'ini yuboring.",
            reply_markup=kb.get_main_menu_keyboard(False)
        )
        return

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

    # Check if all required data exists
    required_fields = ['title', 'date', 'time', 'place', 'comment']
    missing_fields = [f for f in required_fields if f not in data]
    if missing_fields:
        print(f"❌ Missing FSM data fields: {missing_fields}")
        await callback.message.edit_text(
            "❌ Ma'lumotlar topilmadi. Iltimos, qaytadan boshlang.",
            reply_markup=None
        )
        await state.clear()
        await callback.answer()
        return

    # Add event to database
    try:
        event_id = await db.add_event(
            title=data['title'],
            date=data['date'],
            time=data['time'],
            place=data['place'],
            comment=data['comment'],
            created_by_user_id=user_id
        )
    except Exception as e:
        print(f"❌ Exception in add_event: {e}")
        import traceback
        traceback.print_exc()
        event_id = None

    if event_id:
        # Get full event data with user info
        event = await db.get_event(event_id)

        if event:
            # Add to Google Sheets
            if sheets_manager.is_connected():
                try:
                    sheets_manager.add_event(event)
                except Exception as e:
                    print(f"❌ Error adding to Google Sheets: {e}")

            # Send notification to media group
            if reminder_scheduler:
                try:
                    await reminder_scheduler.send_immediate_notification(event)
                except Exception as e:
                    print(f"❌ Error sending notification: {e}")

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
        print(f"❌ Failed to add event for user_id={user_id}, data={data}")
        is_admin = await db.is_admin(user_id)
        await callback.message.edit_text(
            "❌ Tadbir qo'shishda xatolik yuz berdi. Iltimos, qaytadan urinib ko'ring.",
            reply_markup=None
        )
        await callback.message.answer(
            "Asosiy menyu:",
            reply_markup=kb.get_main_menu_keyboard(is_admin)
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
        reply_markup=kb.get_events_schedule_reply_keyboard()
    )


@router.message(F.text == "📆 Bugungi tadbirlar")
async def show_today_events(message: Message):
    """
    Show today's events only.

    Filter: event date == today's date (bugun 00:00 - 23:59)
    """
    today = datetime.now().strftime('%d.%m.%Y')
    events = await db.get_events_by_date(today)

    if not events:
        await message.answer("Bugun tadbirlar yo'q")
        return

    text = "<b>📆 Bugungi tadbirlar:</b>\n\n"
    for event in events:
        text += format_event_text(event) + "\n\n"

    await message.answer(text, parse_mode="HTML")


@router.message(F.text == "📅 Haftalik jadval")
async def show_week_events(message: Message):
    """
    Show events from today until the end of this week (Sunday).

    Filter: event_date in [today ... end of week (Sunday)]
    """
    today = datetime.now()

    # Calculate days until Sunday (0=Monday, 6=Sunday)
    days_until_sunday = 6 - today.weekday()
    end_of_week = today + timedelta(days=days_until_sunday)

    # Format dates for date range query
    start_date = today.strftime('%d.%m.%Y')
    end_date = end_of_week.strftime('%d.%m.%Y')

    # Get events from today until end of week
    events = await db.get_events_by_date_range(start_date, end_date)

    if not events:
        await message.answer("Ushbu haftada tadbirlar yo'q")
        return

    text = "<b>📅 Haftalik jadval (bugundan yakshanba oxirigacha):</b>\n\n"
    for event in events:
        text += format_event_text(event) + "\n\n"

    await message.answer(text, parse_mode="HTML")


@router.message(F.text == "📊 Bir oylik jadval")
async def show_monthly_events(message: Message):
    """
    Show events from today until the end of the current month.

    Filter: event_date in [today ... end of current month]
    """
    today = datetime.now()

    # Calculate last day of current month
    if today.month == 12:
        # December - end is Dec 31
        end_of_month = datetime(today.year, 12, 31)
    else:
        # Get first day of next month, then subtract 1 day
        first_of_next_month = datetime(today.year, today.month + 1, 1)
        end_of_month = first_of_next_month - timedelta(days=1)

    # Format dates for date range query
    start_date = today.strftime('%d.%m.%Y')
    end_date = end_of_month.strftime('%d.%m.%Y')

    # Get events from today until end of month
    events = await db.get_events_by_date_range(start_date, end_date)

    if not events:
        await message.answer("Ushbu oyda tadbirlar yo'q")
        return

    text = "<b>📊 Oylik jadval (bugundan oy oxirigacha):</b>\n\n"
    for event in events:
        text += format_event_text(event) + "\n\n"

    # Show count if many events
    if len(events) > 20:
        text += f"\n<i>Jami: {len(events)} ta tadbir</i>"

    await message.answer(text, parse_mode="HTML")


@router.message(F.text == "🔙 Asosiy menyu")
async def back_to_main_menu_from_schedule(message: Message):
    """Back to main menu from schedule."""
    user_id = message.from_user.id
    is_admin = await db.is_admin(user_id)

    await message.answer(
        "Asosiy menyu:",
        reply_markup=kb.get_main_menu_keyboard(is_admin)
    )


# ========== MY EVENTS HANDLERS ==========

@router.message(F.text == "📝 Mening tadbirlarim")
async def show_my_events(message: Message):
    """
    Show user's upcoming events only.

    Filter:
    - Only non-cancelled events
    - Only events with datetime > now (upcoming events)
    """
    user_id = message.from_user.id
    events = await db.get_events_by_user(user_id)  # upcoming_only=True by default

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

        # Send cancellation notification to media group
        if reminder_scheduler and config.MEDIA_GROUP_CHAT_ID:
            try:
                cancellation_msg = (
                    f"❌ <b>Tadbir bekor qilindi!</b>\n\n"
                    f"<b>{event['title']}</b>\n\n"
                    f"📅 Sana: {event['date']}\n"
                    f"🕐 Vaqt: {event['time']}\n"
                    f"📍 Joy: {event['place']}\n"
                    f"💬 Izoh: {event.get('comment', 'Izoh yoʼq')}\n\n"
                    f"👤 Mas'ul: {event['creator_name']}\n"
                    f"🏢 Bo'lim: {event['creator_department']}\n"
                    f"📱 Telefon: {event['creator_phone']}"
                )

                await reminder_scheduler.bot.send_message(
                    chat_id=config.MEDIA_GROUP_CHAT_ID,
                    text=cancellation_msg,
                    parse_mode="HTML"
                )
            except Exception as e:
                print(f"❌ Error sending cancellation notification: {e}")

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
        # Get updated event
        event = await db.get_event(event_id)

        # Update in Google Sheets
        if event and sheets_manager.is_connected():
            sheets_manager.update_event(event_id, event)

        # Send notification to media group
        if event and reminder_scheduler and config.MEDIA_GROUP_CHAT_ID:
            try:
                field_names_uz = {
                    "title": "Tadbir nomi",
                    "date": "Sana",
                    "time": "Vaqt",
                    "place": "Joy",
                    "comment": "Izoh"
                }

                notification_msg = (
                    f"✏️ <b>Tadbir tahrirlandi!</b>\n\n"
                    f"<b>{event['title']}</b>\n\n"
                    f"O'zgargan maydon: {field_names_uz.get(field, field)}\n"
                    f"Yangi qiymat: {new_value}\n\n"
                    f"📅 Sana: {event['date']}\n"
                    f"🕐 Vaqt: {event['time']}\n"
                    f"📍 Joy: {event['place']}\n"
                    f"💬 Izoh: {event.get('comment', '')}\n\n"
                    f"👤 Mas'ul: {event['creator_name']}\n"
                    f"🏢 Bo'lim: {event['creator_department']}\n"
                    f"📱 Telefon: {event['creator_phone']}"
                )

                await reminder_scheduler.bot.send_message(
                    chat_id=config.MEDIA_GROUP_CHAT_ID,
                    text=notification_msg,
                    parse_mode="HTML"
                )
            except Exception as e:
                print(f"❌ Error sending edit notification: {e}")

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
        f"💬 Izoh: {event.get('comment', 'Izoh yo‘q')}"
    )

    if detailed:
        text += (
            f"\n\n👤 Mas'ul: {event['creator_name']}\n"
            f"🏢 Bo'lim: {event['creator_department']}\n"
            f"📱 Telefon: {event['creator_phone']}"
        )

    return text

