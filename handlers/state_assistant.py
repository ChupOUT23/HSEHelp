from aiogram.dispatcher.filters.state import State, StatesGroup


class NewAssistant(StatesGroup):
    tg_username = State()
    full_name = State()
    phone_number = State()
    university = State()
    faculty = State()
    specialization = State()
    graduation_year = State()
    priority_subjects = State()
    cover_letter = State()
