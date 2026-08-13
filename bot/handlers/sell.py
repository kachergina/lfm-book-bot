"""Sell flow handlers for creating listings."""

import logging
from decimal import Decimal

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.repository import BookRepository
from bot.keyboards.catalog import (
    get_book_keyboard,
    get_grade_keyboard,
    get_sell_category_keyboard,
    get_subject_keyboard,
)
from bot.keyboards.listings import (
    get_condition_keyboard,
    get_contact_method_keyboard,
    get_description_action_keyboard,
    get_photos_initial_keyboard,
    get_photos_received_keyboard,
    get_sell_confirm_keyboard,
)
from bot.locale import fr
from bot.services.browsing import BrowsingService
from bot.services.listing import (
    ListingService,
    ListingValidationError,
)
from bot.states.fsm import SellFlow
from bot.utils.helpers import edit_message as _edit_message
from bot.utils.helpers import format_price

logger = logging.getLogger(__name__)

router = Router()


@router.message(F.text == fr.BTN_SELL_BOOK)
async def cmd_sell(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Handle sell button - start the selling flow.

    Args:
        message: Telegram message.
        state: FSM state.
        session: Database session.
    """
    await state.clear()
    await _start_sell_flow(message, state, session)


async def _start_sell_flow(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Start the sell flow - show category selection.

    Args:
        message: Telegram message.
        state: FSM state.
        session: Database session.
    """
    service = BrowsingService(session)
    academic_year = await service.get_current_academic_year()

    if academic_year is None:
        await message.answer(fr.MSG_NO_ACADEMIC_YEAR)
        return

    await state.update_data(academic_year_id=academic_year.id)
    await state.set_state(SellFlow.selecting_category)

    await message.answer(
        fr.SELL_SELECT_CATEGORY,
        reply_markup=get_sell_category_keyboard(),
    )


# Category selection
@router.callback_query(SellFlow.selecting_category, F.data.startswith("buy:cat:"))
async def handle_sell_category(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Handle category selection in sell flow.

    Args:
        callback: Telegram callback.
        state: FSM state.
        session: Database session.
    """
    if not callback.data:
        return

    category = callback.data.split(":")[2]
    await state.update_data(category=category)
    await state.set_state(SellFlow.selecting_grade)

    data = await state.get_data()
    academic_year_id = data["academic_year_id"]

    service = BrowsingService(session)
    grades = await service.get_grade_levels(academic_year_id, category)

    if not grades:
        books = await service.get_books_by_category(academic_year_id, category)
        if books:
            await state.set_state(SellFlow.selecting_book)
            books_data = [{"id": b.id, "title": b.title, "author": b.author} for b in books]
            await _edit_message(
                callback,
                fr.SELL_SELECT_BOOK,
                reply_markup=get_book_keyboard(books_data),
            )
            await callback.answer()
            return

        await _edit_message(
            callback,
            fr.SELL_NO_BOOKS,
            reply_markup=get_sell_category_keyboard(),
        )
        await state.set_state(SellFlow.selecting_category)
        await callback.answer()
        return

    await _edit_message(
        callback,
        fr.SELL_SELECT_GRADE,
        reply_markup=get_grade_keyboard(grades),
    )
    await callback.answer()


# Back to category from grade
@router.callback_query(SellFlow.selecting_grade, F.data == "buy:back:category")
async def handle_sell_back_to_category(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    """Handle back to category selection.

    Args:
        callback: Telegram callback.
        state: FSM state.
    """
    await state.set_state(SellFlow.selecting_category)
    await _edit_message(
        callback,
        fr.SELL_SELECT_CATEGORY,
        reply_markup=get_sell_category_keyboard(),
    )
    await callback.answer()


# Grade selection
@router.callback_query(SellFlow.selecting_grade, F.data.startswith("buy:grade:"))
async def handle_sell_grade(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Handle grade selection in sell flow.

    Args:
        callback: Telegram callback.
        state: FSM state.
        session: Database session.
    """
    if not callback.data:
        return

    grade = callback.data.split(":")[2]
    await state.update_data(grade=grade)
    await state.set_state(SellFlow.selecting_subject)

    data = await state.get_data()
    academic_year_id = data["academic_year_id"]
    category = data["category"]

    service = BrowsingService(session)
    subjects = await service.get_subjects(academic_year_id, category, grade)

    if not subjects:
        grades = await service.get_grade_levels(academic_year_id, category)
        await _edit_message(
            callback,
            fr.SELL_NO_BOOKS,
            reply_markup=get_grade_keyboard(grades),
        )
        await state.set_state(SellFlow.selecting_grade)
        await callback.answer()
        return

    await _edit_message(
        callback,
        fr.SELL_SELECT_SUBJECT,
        reply_markup=get_subject_keyboard(subjects),
    )
    await callback.answer()


# Back to grade from subject
@router.callback_query(SellFlow.selecting_subject, F.data == "buy:back:grade")
async def handle_sell_back_to_grade(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Handle back to grade selection.

    Args:
        callback: Telegram callback.
        state: FSM state.
        session: Database session.
    """
    data = await state.get_data()
    academic_year_id = data["academic_year_id"]
    category = data["category"]

    service = BrowsingService(session)
    grades = await service.get_grade_levels(academic_year_id, category)

    await state.set_state(SellFlow.selecting_grade)
    await _edit_message(
        callback,
        fr.SELL_SELECT_GRADE,
        reply_markup=get_grade_keyboard(grades),
    )
    await callback.answer()


# Subject selection
@router.callback_query(SellFlow.selecting_subject, F.data.startswith("buy:subj:"))
async def handle_sell_subject(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Handle subject selection in sell flow.

    Args:
        callback: Telegram callback.
        state: FSM state.
        session: Database session.
    """
    if not callback.data:
        return

    subject = callback.data.split(":")[2]
    await state.update_data(subject=subject)
    await state.set_state(SellFlow.selecting_book)

    data = await state.get_data()
    academic_year_id = data["academic_year_id"]
    category = data["category"]
    grade = data["grade"]

    service = BrowsingService(session)
    books = await service.get_books(academic_year_id, category, grade, subject)

    if not books:
        subjects = await service.get_subjects(academic_year_id, category, grade)
        await _edit_message(
            callback,
            fr.SELL_NO_BOOKS,
            reply_markup=get_subject_keyboard(subjects),
        )
        await state.set_state(SellFlow.selecting_subject)
        await callback.answer()
        return

    books_data = [{"id": b.id, "title": b.title, "author": b.author} for b in books]

    await _edit_message(
        callback,
        fr.SELL_SELECT_BOOK,
        reply_markup=get_book_keyboard(books_data),
    )
    await callback.answer()


# Back to subject from book
@router.callback_query(SellFlow.selecting_book, F.data == "buy:back:subject")
async def handle_sell_back_to_subject(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Handle back to subject selection.

    Args:
        callback: Telegram callback.
        state: FSM state.
        session: Database session.
    """
    data = await state.get_data()
    academic_year_id = data["academic_year_id"]
    category = data["category"]
    grade = data["grade"]

    service = BrowsingService(session)
    subjects = await service.get_subjects(academic_year_id, category, grade)

    await state.set_state(SellFlow.selecting_subject)
    await _edit_message(
        callback,
        fr.SELL_SELECT_SUBJECT,
        reply_markup=get_subject_keyboard(subjects),
    )
    await callback.answer()


# Book selection → price entry
@router.callback_query(SellFlow.selecting_book, F.data.startswith("buy:book:"))
async def handle_sell_book(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Handle book selection - move to price entry.

    Args:
        callback: Telegram callback.
        state: FSM state.
        session: Database session.
    """
    if not callback.data:
        return

    book_id = int(callback.data.split(":")[2])

    book_repo = BookRepository(session)
    book = await book_repo.get_by_id(book_id)
    book_title = book.title if book else "Livre inconnu"

    await state.update_data(book_id=book_id, book_title=book_title)
    await state.set_state(SellFlow.entering_price)

    await _edit_message(callback, fr.SELL_ENTER_PRICE)
    await callback.answer()


# Price entry
@router.message(SellFlow.entering_price)
async def handle_price_input(
    message: Message,
    state: FSMContext,
) -> None:
    """Handle price input.

    Args:
        message: Telegram message.
        state: FSM state.
    """
    if not message.text:
        await message.answer(fr.SELL_PRICE_INVALID)
        return

    try:
        price = ListingService.validate_price(message.text)
    except ListingValidationError as e:
        await message.answer(str(e))
        return

    await state.update_data(price=str(price))
    await state.set_state(SellFlow.entering_condition)

    await message.answer(
        fr.SELL_SELECT_CONDITION,
        reply_markup=get_condition_keyboard(),
    )


# Back to price from condition (via inline button)
@router.callback_query(SellFlow.entering_condition, F.data == "sell:back:price")
async def handle_back_to_price(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    """Handle back to price entry.

    Args:
        callback: Telegram callback.
        state: FSM state.
    """
    await state.set_state(SellFlow.entering_price)
    await _edit_message(callback, fr.SELL_ENTER_PRICE)
    await callback.answer()


# Condition selection
@router.callback_query(SellFlow.entering_condition, F.data.startswith("sell:cond:"))
async def handle_condition_selection(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    """Handle condition selection.

    Args:
        callback: Telegram callback.
        state: FSM state.
    """
    if not callback.data:
        return

    condition = callback.data.split(":")[2]

    try:
        ListingService.validate_condition(condition)
    except ListingValidationError as e:
        await callback.answer(str(e), show_alert=True)
        return

    await state.update_data(condition=condition)
    await state.set_state(SellFlow.selecting_contact_method)

    await _edit_message(
        callback,
        fr.SELL_SELECT_CONTACT_METHOD,
        reply_markup=get_contact_method_keyboard(),
    )
    await callback.answer()


# Contact method selection
@router.callback_query(SellFlow.selecting_contact_method, F.data.startswith("sell:contact:"))
async def handle_contact_method_selection(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    """Handle contact method selection.

    Args:
        callback: Telegram callback.
        state: FSM state.
    """
    if not callback.data:
        return

    method = callback.data.split(":")[2]

    if method == "phone":
        await state.update_data(contact_method="phone")
        await state.set_state(SellFlow.entering_phone)
        await _edit_message(callback, fr.SELL_ENTER_PHONE)
    elif method == "telegram":
        await state.update_data(contact_method="telegram")
        await state.set_state(SellFlow.entering_telegram)
        await _edit_message(callback, fr.SELL_ENTER_TELEGRAM)
    else:
        await callback.answer(fr.MSG_INVALID_ACTION, show_alert=True)
        return

    await callback.answer()


# Back to condition from contact method
@router.callback_query(SellFlow.selecting_contact_method, F.data == "sell:back:condition")
async def handle_back_to_condition_from_contact(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    """Handle back to condition from contact method selection.

    Args:
        callback: Telegram callback.
        state: FSM state.
    """
    await state.set_state(SellFlow.entering_condition)
    await _edit_message(
        callback,
        fr.SELL_SELECT_CONDITION,
        reply_markup=get_condition_keyboard(),
    )
    await callback.answer()


# Phone entry
@router.message(SellFlow.entering_phone)
async def handle_phone_input(
    message: Message,
    state: FSMContext,
) -> None:
    """Handle phone number input.

    Args:
        message: Telegram message.
        state: FSM state.
    """
    if not message.text:
        await message.answer(fr.SELL_PHONE_INVALID)
        return

    try:
        phone = ListingService.validate_phone(message.text)
    except ListingValidationError as e:
        await message.answer(str(e))
        return

    await state.update_data(phone=phone)
    await state.set_state(SellFlow.uploading_photos)

    await message.answer(
        fr.SELL_UPLOAD_PHOTOS,
        reply_markup=get_photos_initial_keyboard(),
    )


# Telegram username entry
@router.message(SellFlow.entering_telegram)
async def handle_telegram_input(
    message: Message,
    state: FSMContext,
) -> None:
    """Handle Telegram username input.

    Args:
        message: Telegram message.
        state: FSM state.
    """
    if not message.text:
        await message.answer(fr.SELL_TELEGRAM_INVALID)
        return

    try:
        username = ListingService.validate_telegram_username(message.text)
    except ListingValidationError as e:
        await message.answer(str(e))
        return

    await state.update_data(phone=username)
    await state.set_state(SellFlow.uploading_photos)

    await message.answer(
        fr.SELL_UPLOAD_PHOTOS,
        reply_markup=get_photos_initial_keyboard(),
    )


# Photo upload - receive photo
@router.message(SellFlow.uploading_photos, F.photo)
async def handle_photo_upload(
    message: Message,
    state: FSMContext,
) -> None:
    """Handle photo upload.

    Args:
        message: Telegram message.
        state: FSM state.
    """
    if not message.photo:
        return

    data = await state.get_data()
    photos = data.get("photos", [])

    if len(photos) >= 5:
        await message.answer(fr.SELL_PHOTOS_MAX_REACHED.format(max=5))
        return

    # Get the largest photo file_id
    photo = message.photo[-1]
    photos.append(photo.file_id)
    await state.update_data(photos=photos)

    await message.answer(
        fr.SELL_PHOTOS_RECEIVED.format(count=len(photos), max=5),
        reply_markup=get_photos_received_keyboard(),
    )


# Photos - done
@router.callback_query(SellFlow.uploading_photos, F.data == "sell:photos:done")
async def handle_photos_done(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    """Handle photos upload done.

    Args:
        callback: Telegram callback.
        state: FSM state.
    """
    data = await state.get_data()
    photos = data.get("photos", [])

    if not photos:
        await callback.answer(fr.SELL_PHOTOS_NONE, show_alert=True)
        return

    await state.update_data(photos=photos)
    await state.set_state(SellFlow.entering_description)

    await _edit_message(
        callback,
        fr.SELL_ENTER_DESCRIPTION,
        reply_markup=get_description_action_keyboard(),
    )
    await callback.answer()


# Photos - skip
@router.callback_query(SellFlow.uploading_photos, F.data == "sell:photos:skip")
async def handle_photos_skip(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    """Handle skip photos.

    Args:
        callback: Telegram callback.
        state: FSM state.
    """
    await state.update_data(photos=None)
    await state.set_state(SellFlow.entering_description)

    await _edit_message(
        callback,
        fr.SELL_ENTER_DESCRIPTION,
        reply_markup=get_description_action_keyboard(),
    )
    await callback.answer()


# Description - text input
@router.message(SellFlow.entering_description)
async def handle_description_input(
    message: Message,
    state: FSMContext,
) -> None:
    """Handle description text input.

    Args:
        message: Telegram message.
        state: FSM state.
    """
    if not message.text:
        await message.answer(fr.SELL_DESCRIPTION_TOO_LONG)
        return

    try:
        description = ListingService.validate_description(message.text)
    except ListingValidationError as e:
        await message.answer(str(e))
        return

    await state.update_data(description=description)
    await _show_confirmation(message, state)


# Description - skip
@router.callback_query(SellFlow.entering_description, F.data == "sell:desc:skip")
async def handle_description_skip(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    """Handle skip description.

    Args:
        callback: Telegram callback.
        state: FSM state.
    """
    await state.update_data(description=None)
    await state.set_state(SellFlow.confirming)

    data = await state.get_data()
    confirm_text = _build_confirm_text(data)

    await _edit_message(
        callback,
        confirm_text,
        reply_markup=get_sell_confirm_keyboard(),
    )
    await callback.answer()


async def _show_confirmation(
    message: Message,
    state: FSMContext,
) -> None:
    """Show confirmation screen.

    Args:
        message: Telegram message.
        state: FSM state.
    """
    await state.set_state(SellFlow.confirming)

    data = await state.get_data()
    confirm_text = _build_confirm_text(data)

    await message.answer(
        confirm_text,
        reply_markup=get_sell_confirm_keyboard(),
    )


def _build_confirm_text(data: dict) -> str:
    """Build confirmation text from state data.

    Args:
        data: FSM state data.

    Returns:
        Formatted confirmation text.
    """
    from bot.locale import fr

    parts = [fr.SELL_CONFIRM_TITLE, ""]

    # Book info from state
    book_title = data.get("book_title", "Livre inconnu")
    parts.append(fr.SELL_CONFIRM_BOOK.format(title=book_title))

    price = Decimal(data.get("price", "0"))
    parts.append(fr.SELL_CONFIRM_PRICE.format(price=format_price(price)))

    condition = data.get("condition", "")
    condition_label = fr.CONDITION_LABELS.get(condition, condition)
    parts.append(fr.SELL_CONFIRM_CONDITION.format(condition=condition_label))

    phone = data.get("phone", "")
    parts.append(fr.SELL_CONFIRM_PHONE.format(phone=phone))

    description = data.get("description")
    if description:
        parts.append(fr.SELL_CONFIRM_DESCRIPTION.format(description=description))

    photos = data.get("photos")
    if photos:
        parts.append(fr.SELL_CONFIRM_PHOTOS.format(count=len(photos)))

    parts.append("")
    parts.append(fr.SELL_CONFIRM_ACTIONS)

    return "\n".join(parts)


# Confirmation - publish
@router.callback_query(SellFlow.confirming, F.data == "sell:confirm:publish")
async def handle_confirm_publish(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Handle confirm and publish listing.

    Args:
        callback: Telegram callback.
        state: FSM state.
        session: Database session.
    """
    from bot.database.repository import UserRepository

    data = await state.get_data()

    if not callback.from_user:
        await callback.answer(fr.MSG_INVALID_ACTION, show_alert=True)
        return

    user_repo = UserRepository(session)
    user = await user_repo.get_by_telegram_id(callback.from_user.id)
    if user is None:
        await callback.answer(fr.MSG_USER_NOT_FOUND, show_alert=True)
        return

    service = ListingService(session)

    try:
        listing = await service.create_listing(
            book_id=data["book_id"],
            seller_id=user.id,
            price=Decimal(data["price"]),
            condition=data["condition"],
            phone=data["phone"],
            contact_method=data.get("contact_method", "phone"),
            description=data.get("description"),
            photos=data.get("photos"),
        )
    except ListingValidationError as e:
        await callback.answer(str(e), show_alert=True)
        return

    await state.clear()
    await _edit_message(callback, fr.SELL_PUBLISH_SUCCESS)
    await callback.answer()

    # Notify admins about new listing (best-effort)
    bot = data.get("bot")
    if bot is not None:
        try:
            from bot.services.notification import NotificationService

            notification_service = NotificationService(bot, session)
            await notification_service.notify_admin_listing_created(
                listing=listing,
                seller=user,
            )
        except Exception:
            logger.exception(
                "Failed to send admin listing notification",
                extra={"listing_id": listing.id},
            )


# Confirmation - cancel
@router.callback_query(SellFlow.confirming, F.data == "sell:confirm:cancel")
async def handle_confirm_cancel(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    """Handle cancel listing creation.

    Args:
        callback: Telegram callback.
        state: FSM state.
    """
    await state.clear()
    await _edit_message(callback, fr.SELL_PUBLISH_CANCELLED)
    await callback.answer()


# Edit actions from confirmation screen
@router.callback_query(SellFlow.confirming, F.data == "sell:edit:price")
async def handle_edit_price_from_confirm(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    """Handle edit price from confirmation screen.

    Args:
        callback: Telegram callback.
        state: FSM state.
    """
    await state.set_state(SellFlow.entering_price)
    await _edit_message(callback, fr.SELL_ENTER_PRICE)
    await callback.answer()


@router.callback_query(SellFlow.confirming, F.data == "sell:edit:condition")
async def handle_edit_condition_from_confirm(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    """Handle edit condition from confirmation screen.

    Args:
        callback: Telegram callback.
        state: FSM state.
    """
    await state.set_state(SellFlow.entering_condition)
    await _edit_message(
        callback,
        fr.SELL_SELECT_CONDITION,
        reply_markup=get_condition_keyboard(),
    )
    await callback.answer()


@router.callback_query(SellFlow.confirming, F.data == "sell:edit:phone")
async def handle_edit_phone_from_confirm(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    """Handle edit contact from confirmation screen.

    Args:
        callback: Telegram callback.
        state: FSM state.
    """
    await state.set_state(SellFlow.selecting_contact_method)
    await _edit_message(
        callback,
        fr.SELL_SELECT_CONTACT_METHOD,
        reply_markup=get_contact_method_keyboard(),
    )
    await callback.answer()


@router.callback_query(SellFlow.confirming, F.data == "sell:edit:description")
async def handle_edit_description_from_confirm(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    """Handle edit description from confirmation screen.

    Args:
        callback: Telegram callback.
        state: FSM state.
    """
    await state.set_state(SellFlow.entering_description)
    await _edit_message(
        callback,
        fr.SELL_ENTER_DESCRIPTION,
        reply_markup=get_description_action_keyboard(),
    )
    await callback.answer()


@router.callback_query(SellFlow.confirming, F.data == "sell:edit:photos")
async def handle_edit_photos_from_confirm(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    """Handle edit photos from confirmation screen.

    Args:
        callback: Telegram callback.
        state: FSM state.
    """
    await state.set_state(SellFlow.uploading_photos)
    await _edit_message(
        callback,
        fr.SELL_UPLOAD_PHOTOS,
        reply_markup=get_photos_initial_keyboard(),
    )
    await callback.answer()
