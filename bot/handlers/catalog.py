"""Catalog browsing and buying flow handlers."""

import logging

from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards.catalog import (
    get_book_keyboard,
    get_category_keyboard,
    get_grade_keyboard,
    get_listing_detail_keyboard,
    get_listings_keyboard,
    get_photo_nav_keyboard,
    get_subject_keyboard,
)
from bot.keyboards.common import get_main_menu_keyboard
from bot.locale import fr
from bot.services.browsing import BrowsingService
from bot.states.fsm import BuyFlow
from bot.utils.helpers import edit_message as _edit_message
from bot.utils.helpers import format_price as _format_price

logger = logging.getLogger(__name__)

router = Router()


def _format_condition(condition: str) -> str:
    """Format condition string to French label.

    Args:
        condition: Internal condition string.

    Returns:
        French condition label.
    """
    return fr.CONDITION_LABELS.get(condition, condition)


async def _show_listings_for_book(
    message: Message,
    book_id: int,
    academic_year_id: int,
    session: AsyncSession,
) -> None:
    """Display listing cards for a book as separate messages.

    Args:
        message: Telegram message to answer from.
        book_id: Book ID.
        academic_year_id: Academic year ID.
        session: Database session.
    """
    service = BrowsingService(session)
    listings = await service.get_active_listings(book_id, academic_year_id)

    book_repo = service.book_repo
    book = await book_repo.get_by_id(book_id)
    book_title = book.title if book else "Livre inconnu"

    if not listings:
        await message.answer(
            fr.BUY_NO_LISTINGS,
            reply_markup=get_listings_keyboard(book_id),
        )
        return

    await message.answer(fr.BUY_LISTINGS_TITLE.format(book_title=book_title))

    for listing in listings:
        condition = _format_condition(listing.condition)
        price = _format_price(listing.price)

        if listing.contact_method == "telegram" and listing.contact_phone:
            text = fr.BUY_LISTING_ITEM_TELEGRAM.format(
                price=price,
                condition=condition,
                contact=listing.contact_phone,
            )
        else:
            contact = listing.contact_phone or "Non renseigné"
            text = fr.BUY_LISTING_ITEM.format(
                price=price,
                condition=condition,
                contact=contact,
            )

        if listing.description:
            text += f"\n{fr.BUY_LISTING_DESCRIPTION.format(description=listing.description)}"

        has_photos = bool(listing.photos)
        reply_markup = get_listing_detail_keyboard(
            listing_id=listing.id,
            has_photos=has_photos,
            book_id=book_id,
        )
        await message.answer(text, reply_markup=reply_markup)


async def _send_main_menu(message: Message, session: AsyncSession) -> None:
    """Send the main menu welcome message and keyboard.

    Replicates the /start flow: looks up user, academic year, and sends
    the full welcome message with main menu keyboard.

    Args:
        message: Telegram message to answer from.
        session: Database session.
    """
    from bot.database.repository import AcademicYearRepository, UserRepository

    user_repo = UserRepository(session)

    if not message.from_user:
        return

    user = await user_repo.get_by_telegram_id(message.from_user.id)

    if user is None:
        user = await user_repo.create(
            telegram_id=message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
            last_name=message.from_user.last_name,
            language_code=message.from_user.language_code or "fr",
        )
        logger.info(
            "New user registered",
            extra={"user_id": user.id, "telegram_id": user.telegram_id},
        )

    academic_year_repo = AcademicYearRepository(session)
    academic_year = await academic_year_repo.get_current()

    if academic_year:
        year_text = fr.MAIN_MENU_ACADEMIC_YEAR.format(year=academic_year.name)
    else:
        year_text = "Année scolaire non configurée"

    welcome_text = f"{fr.WELCOME_MESSAGE}\n\n{fr.MAIN_MENU_TITLE}\n{year_text}"

    await message.answer(
        welcome_text,
        reply_markup=get_main_menu_keyboard(),
    )


@router.message(F.text == fr.BTN_BUY_BOOK)
async def cmd_buy(message: Message, state: FSMContext, session: AsyncSession) -> None:
    """Handle buy button - start the buying flow.

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

    # Store academic year in state
    await state.update_data(academic_year_id=academic_year.id)
    await state.set_state(BuyFlow.selecting_category)

    await message.answer(
        fr.BUY_SELECT_CATEGORY,
        reply_markup=get_category_keyboard(),
    )


@router.callback_query(F.data == "buy:back:menu")
async def cmd_back_to_menu(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Handle back to main menu.

    Sends a new message replicating the /start welcome experience.

    Args:
        callback: Telegram callback.
        state: FSM state.
        session: Database session.
    """
    await state.clear()
    if callback.message and hasattr(callback.message, "answer"):
        await _send_main_menu(callback.message, session)  # type: ignore[arg-type]
    await callback.answer()


@router.callback_query(BuyFlow.selecting_category, F.data.startswith("buy:cat:"))
async def handle_category_selection(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Handle category selection.

    Args:
        callback: Telegram callback.
        state: FSM state.
        session: Database session.
    """
    if not callback.data:
        return

    category = callback.data.split(":")[2]
    await state.update_data(category=category)
    await state.set_state(BuyFlow.selecting_grade)

    data = await state.get_data()
    academic_year_id = data["academic_year_id"]

    service = BrowsingService(session)
    grades = await service.get_grade_levels(academic_year_id, category)

    if not grades:
        if category == "other":
            books = await service.get_books_with_active_listings_by_category(
                academic_year_id,
                category,
            )
        else:
            books = await service.get_books_by_category(academic_year_id, category)

        if not books:
            await _edit_message(
                callback,
                fr.MSG_NO_BOOKS_IN_CATEGORY,
                reply_markup=get_category_keyboard(),
            )
            await state.set_state(BuyFlow.selecting_category)
            await callback.answer()
            return

        await state.set_state(BuyFlow.selecting_book)
        books_data = [{"id": b.id, "title": b.title, "author": b.author} for b in books]
        await _edit_message(
            callback,
            fr.BUY_SELECT_BOOK,
            reply_markup=get_book_keyboard(books_data, back_callback="buy:back:category"),
        )
        await callback.answer()
        return

    await _edit_message(
        callback,
        fr.BUY_SELECT_GRADE,
        reply_markup=get_grade_keyboard(grades),
    )
    await callback.answer()


@router.callback_query(BuyFlow.selecting_grade, F.data == "buy:back:category")
async def handle_back_to_category(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    """Handle back to category selection.

    Args:
        callback: Telegram callback.
        state: FSM state.
    """
    await state.set_state(BuyFlow.selecting_category)
    await _edit_message(
        callback,
        fr.BUY_SELECT_CATEGORY,
        reply_markup=get_category_keyboard(),
    )
    await callback.answer()


@router.callback_query(BuyFlow.selecting_grade, F.data.startswith("buy:grade:"))
async def handle_grade_selection(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Handle grade level selection.

    Args:
        callback: Telegram callback.
        state: FSM state.
        session: Database session.
    """
    if not callback.data:
        return

    grade = callback.data.split(":")[2]
    await state.update_data(grade=grade)
    await state.set_state(BuyFlow.selecting_subject)

    data = await state.get_data()
    academic_year_id = data["academic_year_id"]
    category = data["category"]

    service = BrowsingService(session)
    subjects = await service.get_subjects(academic_year_id, category, grade)

    if not subjects:
        await _edit_message(
            callback,
            fr.MSG_NO_BOOKS_IN_CATEGORY,
            reply_markup=get_grade_keyboard(
                await service.get_grade_levels(academic_year_id, category),
            ),
        )
        await state.set_state(BuyFlow.selecting_grade)
        await callback.answer()
        return

    await _edit_message(
        callback,
        fr.BUY_SELECT_SUBJECT,
        reply_markup=get_subject_keyboard(subjects),
    )
    await callback.answer()


@router.callback_query(BuyFlow.selecting_subject, F.data == "buy:back:grade")
async def handle_back_to_grade(
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

    await state.set_state(BuyFlow.selecting_grade)
    await _edit_message(
        callback,
        fr.BUY_SELECT_GRADE,
        reply_markup=get_grade_keyboard(grades),
    )
    await callback.answer()


@router.callback_query(BuyFlow.selecting_subject, F.data.startswith("buy:subj:"))
async def handle_subject_selection(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Handle subject selection.

    Args:
        callback: Telegram callback.
        state: FSM state.
        session: Database session.
    """
    if not callback.data:
        return

    subject = callback.data.split(":")[2]
    await state.update_data(subject=subject)
    await state.set_state(BuyFlow.selecting_book)

    data = await state.get_data()
    academic_year_id = data["academic_year_id"]
    category = data["category"]
    grade = data["grade"]

    service = BrowsingService(session)
    books = await service.get_books(academic_year_id, category, grade, subject)

    if not books:
        await _edit_message(
            callback,
            fr.MSG_NO_BOOKS_IN_CATEGORY,
            reply_markup=get_subject_keyboard(
                await service.get_subjects(academic_year_id, category, grade),
            ),
        )
        await state.set_state(BuyFlow.selecting_subject)
        await callback.answer()
        return

    books_data = [{"id": b.id, "title": b.title, "author": b.author} for b in books]

    await _edit_message(
        callback,
        fr.BUY_SELECT_BOOK,
        reply_markup=get_book_keyboard(books_data),
    )
    await callback.answer()


@router.callback_query(BuyFlow.selecting_book, F.data == "buy:back:category")
async def handle_back_to_category_from_book(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    """Handle back to category selection from book list without grade/subject."""
    await state.set_state(BuyFlow.selecting_category)
    await _edit_message(
        callback,
        fr.BUY_SELECT_CATEGORY,
        reply_markup=get_category_keyboard(),
    )
    await callback.answer()


@router.callback_query(BuyFlow.selecting_book, F.data == "buy:back:subject")
async def handle_back_to_subject(
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

    await state.set_state(BuyFlow.selecting_subject)
    await _edit_message(
        callback,
        fr.BUY_SELECT_SUBJECT,
        reply_markup=get_subject_keyboard(subjects),
    )
    await callback.answer()


@router.callback_query(BuyFlow.selecting_book, F.data.startswith("buy:book:"))
async def handle_book_selection(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Handle book selection - show active listings.

    Each listing is sent as a separate message with an optional photo button.

    Args:
        callback: Telegram callback.
        state: FSM state.
        session: Database session.
    """
    if not callback.data:
        return

    book_id = int(callback.data.split(":")[2])
    await state.update_data(book_id=book_id)
    await state.set_state(BuyFlow.viewing_listings)

    data = await state.get_data()
    academic_year_id = data["academic_year_id"]

    if isinstance(callback.message, Message):
        await _show_listings_for_book(
            callback.message,
            book_id,
            academic_year_id,
            session,
        )

    await callback.answer()


@router.callback_query(F.data.regexp(r"^buy:photos:\d+$"))
async def handle_view_listing_photos(
    callback: CallbackQuery,
    session: AsyncSession,
) -> None:
    """Handle photo view request - send listing photos as media group.

    After sending photos, sends a navigation message with Retour/Menu buttons.

    Args:
        callback: Telegram callback.
        session: Database session.
    """
    if not callback.data:
        return

    listing_id = int(callback.data.split(":")[2])

    from bot.database.repository import ListingRepository

    repo = ListingRepository(session)
    listing = await repo.get_by_id(listing_id)

    if not listing or not listing.photos:
        await callback.answer(fr.MSG_LISTING_NOT_FOUND, show_alert=True)
        return

    from aiogram.types import InputMediaPhoto

    media = [InputMediaPhoto(media=file_id) for file_id in listing.photos]

    if callback.message and hasattr(callback.message, "answer"):
        bot = callback.message.bot
        if bot:
            await bot.send_media_group(
                chat_id=callback.message.chat.id,
                media=media,  # type: ignore[arg-type]
            )
            await callback.message.answer(
                fr.BUY_PHOTOS_NAV,
                reply_markup=get_photo_nav_keyboard(listing.book_id),
            )

    await callback.answer()


@router.callback_query(F.data.startswith("buy:photos:back:"))
async def handle_photo_back(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Handle back from photo view - return to book listings.

    Re-displays the listing cards for the book.

    Args:
        callback: Telegram callback.
        state: FSM state.
        session: Database session.
    """
    if not callback.data:
        return

    book_id = int(callback.data.split(":")[3])

    data = await state.get_data()
    academic_year_id = data.get("academic_year_id")
    if academic_year_id is None:
        await callback.answer(fr.MSG_DATA_ERROR, show_alert=True)
        return

    await state.set_state(BuyFlow.viewing_listings)
    await state.update_data(book_id=book_id)

    if isinstance(callback.message, Message):
        await _show_listings_for_book(
            callback.message,
            book_id,
            academic_year_id,
            session,
        )

    await callback.answer()


@router.callback_query(F.data == "buy:photos:menu")
async def handle_photo_menu(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Handle menu from photo view - send main menu like /start.

    Args:
        callback: Telegram callback.
        state: FSM state.
        session: Database session.
    """
    await state.clear()
    if callback.message and hasattr(callback.message, "answer"):
        await _send_main_menu(callback.message, session)  # type: ignore[arg-type]
    await callback.answer()


@router.callback_query(BuyFlow.viewing_listings, F.data == "buy:back:book_list")
async def handle_back_to_books(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Handle back to book list.

    Args:
        callback: Telegram callback.
        state: FSM state.
        session: Database session.
    """
    data = await state.get_data()
    academic_year_id = data["academic_year_id"]
    category = data["category"]
    grade = data["grade"]
    subject = data["subject"]

    service = BrowsingService(session)
    books = await service.get_books(academic_year_id, category, grade, subject)

    books_data = [{"id": b.id, "title": b.title, "author": b.author} for b in books]

    await state.set_state(BuyFlow.selecting_book)
    await _edit_message(
        callback,
        fr.BUY_SELECT_BOOK,
        reply_markup=get_book_keyboard(books_data),
    )
    await callback.answer()


@router.message(CommandStart())
async def cmd_start_buy_flow(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Handle /start command - reset state and show main menu.

    Args:
        message: Telegram message.
        state: FSM state.
        session: Database session.
    """
    await state.clear()
    await _send_main_menu(message, session)
