from aiogram.fsm.state import StatesGroup, State

class NewProduct(StatesGroup):
    name = State()
    price = State()
    category = State()
    description = State()
    image = State()
    confirm = State()

class SetPhoto(StatesGroup):
    waiting_photo = State()
    product_id = State()

class EditProduct(StatesGroup):
    waiting_value = State()  # we store product_id + field in state data