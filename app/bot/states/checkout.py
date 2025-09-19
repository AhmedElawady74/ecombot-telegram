from aiogram.fsm.state import StatesGroup, State

class CheckoutStates(StatesGroup):
    name = State()
    phone = State()
    shipping = State()
    address = State()
    confirm = State()