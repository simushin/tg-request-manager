from aiogram.fsm.state import State, StatesGroup


class RequestForm(StatesGroup):
    full_name = State()
    contact = State()
    subject = State()
    message = State()