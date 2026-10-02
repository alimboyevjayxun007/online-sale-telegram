from aiogram.fsm.state import State, StatesGroup


class Flow(StatesGroup):
    recipient_username = State()
    stars_amount = State()
    promo = State()
    topup_amount = State()


class Adm(StatesGroup):
    user_search = State()
    balance_amount = State()
    message_text = State()
    withdraw_amount = State()
    expense_amount = State()
    expense_note = State()
    plan_value = State()
    stars_markup = State()
    setting_value = State()
    promo_code = State()
    promo_value = State()
    channel = State()
    admin_user = State()
    find_order = State()
    bc_content = State()
    bc_buttons = State()
    stats_from = State()
    stats_to = State()
    fragment_cookies = State()
