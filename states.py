"""FSM States for the Event Organizer Bot."""
from aiogram.fsm.state import State, StatesGroup


class RegistrationStates(StatesGroup):
    """States for user registration process."""
    waiting_for_full_name = State()
    waiting_for_department = State()
    waiting_for_phone = State()


class AddEventStates(StatesGroup):
    """States for adding a new event."""
    waiting_for_title = State()
    waiting_for_date = State()
    waiting_for_time = State()
    waiting_for_place = State()
    waiting_for_comment = State()
    waiting_for_confirmation = State()


class EditEventStates(StatesGroup):
    """States for editing an event."""
    selecting_event = State()
    selecting_field = State()
    waiting_for_new_value = State()
    waiting_for_confirmation = State()
