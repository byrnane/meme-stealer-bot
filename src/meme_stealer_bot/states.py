from aiogram.fsm.state import State, StatesGroup


class SettingsState(StatesGroup):
    waiting_for_channel = State()
    waiting_for_signature = State()
