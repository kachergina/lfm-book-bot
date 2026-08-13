"""FSM states for multi-step flows."""

from aiogram.fsm.state import State, StatesGroup


class BuyFlow(StatesGroup):
    """States for the buying/browsing flow."""

    selecting_category = State()
    selecting_grade = State()
    selecting_subject = State()
    selecting_book = State()
    viewing_listings = State()


class SellFlow(StatesGroup):
    """States for the selling/listing creation flow."""

    selecting_category = State()
    selecting_grade = State()
    selecting_subject = State()
    selecting_book = State()
    entering_price = State()
    entering_condition = State()
    selecting_contact_method = State()
    entering_phone = State()
    entering_telegram = State()
    uploading_photos = State()
    entering_description = State()
    confirming = State()


class ManageListingFlow(StatesGroup):
    """States for listing management flow."""

    selecting_listing = State()
    managing = State()
    editing_price = State()
    editing_condition = State()
    editing_phone = State()
    editing_telegram = State()
    editing_description = State()
    confirming_status_change = State()
