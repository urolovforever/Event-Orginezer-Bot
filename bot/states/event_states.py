from aiogram.fsm.state import State, StatesGroup


class AddEventStates(StatesGroup):
    """
    States for the event creation flow.
    User goes through these states step by step.
    """
    waiting_for_title = State()
    waiting_for_date = State()
    waiting_for_time = State()
    waiting_for_location = State()
    waiting_for_description = State()


class EditEventStates(StatesGroup):
    """
    States for the event editing flow.
    Admin selects event, then field, then new value.
    """
    selecting_event = State()
    selecting_field = State()
    entering_new_value = State()


class DeleteEventStates(StatesGroup):
    """
    States for the event deletion flow.
    Admin selects event and confirms deletion.
    """
    selecting_event = State()
    confirming_deletion = State()