"""Tests for buying flow handlers."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import CallbackQuery, Message, User

from bot.database.models import Listing
from bot.handlers.catalog import (
    _format_condition,
    _format_price,
    cmd_buy,
    handle_book_selection,
    handle_category_selection,
    handle_grade_selection,
    handle_subject_selection,
)
from bot.states.fsm import BuyFlow


def _create_mock_message(text: str = "test") -> Message:
    """Create a mock Telegram message."""
    message = MagicMock(spec=Message)
    message.text = text
    message.from_user = MagicMock(spec=User)
    message.from_user.id = 123456789
    message.answer = AsyncMock()
    message.edit_text = AsyncMock()
    return message


def _create_mock_callback(data: str) -> CallbackQuery:
    """Create a mock Telegram callback query."""
    callback = MagicMock(spec=CallbackQuery)
    callback.data = data
    callback.message = MagicMock(spec=Message)
    callback.message.edit_text = AsyncMock()
    callback.message.answer = AsyncMock()
    callback.message.chat = MagicMock()
    callback.message.chat.id = 123456789
    callback.message.from_user = MagicMock(spec=User)
    callback.message.from_user.id = 123456789
    callback.message.from_user.username = "test_user"
    callback.message.from_user.first_name = "Test"
    callback.message.from_user.last_name = "User"
    callback.message.from_user.language_code = "fr"
    callback.answer = AsyncMock()
    callback.from_user = MagicMock(spec=User)
    callback.from_user.id = 123456789
    return callback


def _create_mock_state() -> FSMContext:
    """Create a mock FSM context."""
    storage = MemoryStorage()
    return FSMContext(storage=storage, key=MagicMock())


def test_format_condition():
    """Test condition formatting."""
    assert _format_condition("new") == "Neuf"
    assert _format_condition("like_new") == "Comme neuf"
    assert _format_condition("good") == "Bon"
    assert _format_condition("fair") == "Correct"
    assert _format_condition("poor") == "Usagé"
    assert _format_condition("unknown") == "unknown"


def test_format_price():
    """Test price formatting."""
    from decimal import Decimal

    assert _format_price(Decimal("15.00")) == "15"
    assert _format_price(Decimal("10.5")) == "10"
    assert _format_price(Decimal("0")) == "0"


@pytest.mark.asyncio
async def test_cmd_buy_no_academic_year(db_session):
    """Test buy button when no academic year exists."""
    message = _create_mock_message()
    state = _create_mock_state()

    await cmd_buy(message, state, db_session)

    message.answer.assert_called_once()
    call_args = message.answer.call_args
    assert "année scolaire" in call_args[0][0].lower() or "configurée" in call_args[0][0]


@pytest.mark.asyncio
async def test_cmd_buy_with_academic_year(db_session, academic_year):  # noqa: ARG001
    """Test buy button with academic year."""
    message = _create_mock_message()
    state = _create_mock_state()

    await cmd_buy(message, state, db_session)

    message.answer.assert_called_once()
    call_args = message.answer.call_args
    assert "catégorie" in call_args[0][0].lower()

    # Check state was set
    state_data = await state.get_state()
    assert state_data == BuyFlow.selecting_category


@pytest.mark.asyncio
async def test_handle_category_selection(db_session, academic_year):
    """Test category selection."""
    callback = _create_mock_callback("buy:cat:textbook")
    state = _create_mock_state()
    await state.set_state(BuyFlow.selecting_category)
    await state.update_data(academic_year_id=academic_year.id)

    # Create a book to ensure grades are returned
    from bot.database.repository import BookRepository

    repo = BookRepository(db_session)
    await repo.create(
        category="textbook",
        title="Math 6eme",
        catalog_year_id=academic_year.id,
        grade_level="6ème",
    )
    await db_session.commit()

    await handle_category_selection(callback, state, db_session)

    callback.message.edit_text.assert_called_once()
    state_data = await state.get_state()
    assert state_data == BuyFlow.selecting_grade


@pytest.mark.asyncio
async def test_handle_category_selection_no_grades(db_session, academic_year):
    """Test category selection when no grades exist."""
    callback = _create_mock_callback("buy:cat:textbook")
    state = _create_mock_state()
    await state.set_state(BuyFlow.selecting_category)
    await state.update_data(academic_year_id=academic_year.id)

    await handle_category_selection(callback, state, db_session)

    # Should go back to category selection
    state_data = await state.get_state()
    assert state_data == BuyFlow.selecting_category


@pytest.mark.asyncio
async def test_handle_grade_selection(db_session, academic_year):
    """Test grade selection."""
    callback = _create_mock_callback("buy:grade:6ème")
    state = _create_mock_state()
    await state.set_state(BuyFlow.selecting_grade)
    await state.update_data(academic_year_id=academic_year.id, category="textbook")

    # Create a book to ensure subjects are returned
    from bot.database.repository import BookRepository

    repo = BookRepository(db_session)
    await repo.create(
        category="textbook",
        title="Math 6eme",
        catalog_year_id=academic_year.id,
        grade_level="6ème",
        subject="Mathématiques",
    )
    await db_session.commit()

    await handle_grade_selection(callback, state, db_session)

    callback.message.edit_text.assert_called_once()
    state_data = await state.get_state()
    assert state_data == BuyFlow.selecting_subject


@pytest.mark.asyncio
async def test_handle_subject_selection(db_session, academic_year):
    """Test subject selection."""
    callback = _create_mock_callback("buy:subj:Mathématiques")
    state = _create_mock_state()
    await state.set_state(BuyFlow.selecting_subject)
    await state.update_data(
        academic_year_id=academic_year.id,
        category="textbook",
        grade="6ème",
    )

    # Create a book to ensure books are returned
    from bot.database.repository import BookRepository

    repo = BookRepository(db_session)
    await repo.create(
        category="textbook",
        title="Math 6eme",
        catalog_year_id=academic_year.id,
        grade_level="6ème",
        subject="Mathématiques",
    )
    await db_session.commit()

    await handle_subject_selection(callback, state, db_session)

    callback.message.edit_text.assert_called_once()
    state_data = await state.get_state()
    assert state_data == BuyFlow.selecting_book


@pytest.mark.asyncio
async def test_handle_book_selection_no_listings(db_session, academic_year, user):  # noqa: ARG001
    """Test book selection when no listings exist."""
    from bot.database.repository import BookRepository

    repo = BookRepository(db_session)
    book = await repo.create(
        category="textbook",
        title="Math 6eme",
        catalog_year_id=academic_year.id,
    )
    await db_session.commit()

    callback = _create_mock_callback(f"buy:book:{book.id}")
    state = _create_mock_state()
    await state.set_state(BuyFlow.selecting_book)
    await state.update_data(academic_year_id=academic_year.id)

    await handle_book_selection(callback, state, db_session)

    # No listings → answer with "no listings" message
    assert callback.message.answer.call_count == 1
    call_args = callback.message.answer.call_args
    assert "aucune annonce" in call_args[0][0].lower()


@pytest.mark.asyncio
async def test_handle_book_selection_with_listings(db_session, academic_year, user):
    """Test book selection with active listings."""
    from bot.database.repository import BookRepository

    repo = BookRepository(db_session)
    book = await repo.create(
        category="textbook",
        title="Math 6eme",
        catalog_year_id=academic_year.id,
    )
    await db_session.commit()

    listing = Listing(
        book_id=book.id,
        seller_id=user.id,
        academic_year_id=academic_year.id,
        price=15.00,
        condition="good",
        status="active",
        contact_phone="0612345678",
    )
    db_session.add(listing)
    await db_session.commit()

    callback = _create_mock_callback(f"buy:book:{book.id}")
    state = _create_mock_state()
    await state.set_state(BuyFlow.selecting_book)
    await state.update_data(academic_year_id=academic_year.id)

    await handle_book_selection(callback, state, db_session)

    # Header + listing message = 2 answer calls
    assert callback.message.answer.call_count == 2
    calls = callback.message.answer.call_args_list
    header_text = calls[0].args[0]
    listing_text = calls[1].args[0]
    assert "Math 6eme" in header_text
    assert "0612345678" in listing_text
    assert "15" in listing_text


@pytest.mark.asyncio
async def test_handle_book_selection_multiple_listings(
    db_session,
    academic_year,
):
    """Test book selection with multiple active listings."""
    from bot.database.repository import BookRepository, UserRepository

    book_repo = BookRepository(db_session)
    user_repo = UserRepository(db_session)

    book = await book_repo.create(
        category="textbook",
        title="Math 6eme",
        catalog_year_id=academic_year.id,
    )

    user1 = await user_repo.create(telegram_id=111111111, username="seller1")
    user2 = await user_repo.create(telegram_id=222222222, username="seller2")
    await db_session.commit()

    listing1 = Listing(
        book_id=book.id,
        seller_id=user1.id,
        academic_year_id=academic_year.id,
        price=15.00,
        condition="good",
        status="active",
        contact_phone="0612345678",
    )
    listing2 = Listing(
        book_id=book.id,
        seller_id=user2.id,
        academic_year_id=academic_year.id,
        price=18.00,
        condition="like_new",
        status="active",
        contact_phone="0698765432",
    )
    db_session.add_all([listing1, listing2])
    await db_session.commit()

    callback = _create_mock_callback(f"buy:book:{book.id}")
    state = _create_mock_state()
    await state.set_state(BuyFlow.selecting_book)
    await state.update_data(academic_year_id=academic_year.id)

    await handle_book_selection(callback, state, db_session)

    # Header + 2 listing messages = 3 answer calls
    assert callback.message.answer.call_count == 3
    calls = callback.message.answer.call_args_list
    all_text = " ".join(c.args[0] for c in calls)
    assert "0612345678" in all_text
    assert "0698765432" in all_text


@pytest.mark.asyncio
async def test_handle_book_selection_sold_listing_hidden(
    db_session,
    academic_year,
    user,
):
    """Test that sold listings are not shown."""
    from bot.database.repository import BookRepository

    repo = BookRepository(db_session)
    book = await repo.create(
        category="textbook",
        title="Math 6eme",
        catalog_year_id=academic_year.id,
    )
    await db_session.commit()

    # Active listing
    active_listing = Listing(
        book_id=book.id,
        seller_id=user.id,
        academic_year_id=academic_year.id,
        price=15.00,
        condition="good",
        status="active",
        contact_phone="0612345678",
    )
    # Sold listing
    sold_listing = Listing(
        book_id=book.id,
        seller_id=user.id,
        academic_year_id=academic_year.id,
        price=20.00,
        condition="new",
        status="sold",
        contact_phone="0698765432",
    )
    db_session.add_all([active_listing, sold_listing])
    await db_session.commit()

    callback = _create_mock_callback(f"buy:book:{book.id}")
    state = _create_mock_state()
    await state.set_state(BuyFlow.selecting_book)
    await state.update_data(academic_year_id=academic_year.id)

    await handle_book_selection(callback, state, db_session)

    # Header + 1 active listing message = 2 answer calls
    assert callback.message.answer.call_count == 2
    calls = callback.message.answer.call_args_list
    listing_text = calls[1].args[0]
    assert "0612345678" in listing_text
    assert "0698765432" not in listing_text


@pytest.mark.asyncio
async def test_handle_book_selection_listing_with_photos_has_button(
    db_session,
    academic_year,
    user,
):
    """Test that a listing with photos shows a photo button."""
    from bot.database.repository import BookRepository

    repo = BookRepository(db_session)
    book = await repo.create(
        category="textbook",
        title="Math 6eme",
        catalog_year_id=academic_year.id,
    )
    await db_session.commit()

    listing = Listing(
        book_id=book.id,
        seller_id=user.id,
        academic_year_id=academic_year.id,
        price=15.00,
        condition="good",
        status="active",
        contact_phone="0612345678",
        photos=["file_id_1", "file_id_2"],
    )
    db_session.add(listing)
    await db_session.commit()

    callback = _create_mock_callback(f"buy:book:{book.id}")
    state = _create_mock_state()
    await state.set_state(BuyFlow.selecting_book)
    await state.update_data(academic_year_id=academic_year.id)

    await handle_book_selection(callback, state, db_session)

    # Header + listing message = 2 answer calls
    assert callback.message.answer.call_count == 2
    call_kwargs = callback.message.answer.call_args_list[1]
    reply_markup = call_kwargs[1].get("reply_markup") or call_kwargs[0][1]
    button_texts = [btn.text for row in reply_markup.inline_keyboard for btn in row]
    assert "📸 Voir les photos" in button_texts


@pytest.mark.asyncio
async def test_handle_book_selection_listing_without_photos_no_button(
    db_session,
    academic_year,
    user,
):
    """Test that a listing without photos has no photo button."""
    from bot.database.repository import BookRepository

    repo = BookRepository(db_session)
    book = await repo.create(
        category="textbook",
        title="Math 6eme",
        catalog_year_id=academic_year.id,
    )
    await db_session.commit()

    listing = Listing(
        book_id=book.id,
        seller_id=user.id,
        academic_year_id=academic_year.id,
        price=15.00,
        condition="good",
        status="active",
        contact_phone="0612345678",
        photos=None,
    )
    db_session.add(listing)
    await db_session.commit()

    callback = _create_mock_callback(f"buy:book:{book.id}")
    state = _create_mock_state()
    await state.set_state(BuyFlow.selecting_book)
    await state.update_data(academic_year_id=academic_year.id)

    await handle_book_selection(callback, state, db_session)

    # Header + listing message = 2 answer calls
    assert callback.message.answer.call_count == 2
    call_kwargs = callback.message.answer.call_args_list[1]
    reply_markup = call_kwargs[1].get("reply_markup") or call_kwargs[0][1]
    button_texts = [btn.text for row in reply_markup.inline_keyboard for btn in row]
    assert "📸 Voir les photos" not in button_texts


@pytest.mark.asyncio
async def test_handle_view_listing_photos_sends_media_group(
    db_session,
    academic_year,
    user,
):
    """Test that viewing listing photos sends a media group and navigation message."""
    from unittest.mock import MagicMock

    from bot.database.repository import BookRepository
    from bot.handlers.catalog import handle_view_listing_photos

    repo = BookRepository(db_session)
    book = await repo.create(
        category="textbook",
        title="Math 6eme",
        catalog_year_id=academic_year.id,
    )
    await db_session.commit()

    listing = Listing(
        book_id=book.id,
        seller_id=user.id,
        academic_year_id=academic_year.id,
        price=15.00,
        condition="good",
        status="active",
        contact_phone="0612345678",
        photos=["file_id_1", "file_id_2"],
    )
    db_session.add(listing)
    await db_session.commit()

    callback = _create_mock_callback(f"buy:photos:{listing.id}")
    mock_bot = MagicMock()
    mock_bot.send_media_group = AsyncMock()
    callback.message.bot = mock_bot

    await handle_view_listing_photos(callback, db_session)

    mock_bot.send_media_group.assert_called_once()
    call_kwargs = mock_bot.send_media_group.call_args
    assert call_kwargs[1]["chat_id"] == callback.message.chat.id
    media = call_kwargs[1]["media"]
    assert len(media) == 2

    # Navigation message sent after photos
    assert callback.message.answer.call_count == 1
    nav_args = callback.message.answer.call_args
    nav_reply_markup = nav_args[1].get("reply_markup") or nav_args[0][1]
    nav_button_texts = [btn.text for row in nav_reply_markup.inline_keyboard for btn in row]
    assert "⬅️ Retour" in nav_button_texts
    assert "🏠 Menu principal" in nav_button_texts


@pytest.mark.asyncio
async def test_handle_view_listing_photos_no_photos_shows_alert(
    db_session,
    academic_year,
    user,
):
    """Test that viewing photos for a listing with no photos shows an alert."""
    from bot.database.repository import BookRepository
    from bot.handlers.catalog import handle_view_listing_photos

    repo = BookRepository(db_session)
    book = await repo.create(
        category="textbook",
        title="Math 6eme",
        catalog_year_id=academic_year.id,
    )
    await db_session.commit()

    listing = Listing(
        book_id=book.id,
        seller_id=user.id,
        academic_year_id=academic_year.id,
        price=15.00,
        condition="good",
        status="active",
        contact_phone="0612345678",
        photos=None,
    )
    db_session.add(listing)
    await db_session.commit()

    callback = _create_mock_callback(f"buy:photos:{listing.id}")

    await handle_view_listing_photos(callback, db_session)

    callback.answer.assert_called_once()
    assert callback.answer.call_args[1].get("show_alert") is True


@pytest.mark.asyncio
async def test_photo_back_returns_to_book_listings(
    db_session,
    academic_year,
    user,
):
    """Test that clicking Retour after viewing photos returns to book listings."""
    from bot.database.repository import BookRepository
    from bot.handlers.catalog import handle_photo_back

    repo = BookRepository(db_session)
    book = await repo.create(
        category="textbook",
        title="Math 6eme",
        catalog_year_id=academic_year.id,
    )
    await db_session.commit()

    listing = Listing(
        book_id=book.id,
        seller_id=user.id,
        academic_year_id=academic_year.id,
        price=15.00,
        condition="good",
        status="active",
        contact_phone="0612345678",
    )
    db_session.add(listing)
    await db_session.commit()

    callback = _create_mock_callback(f"buy:photos:back:{book.id}")
    state = _create_mock_state()
    await state.set_state(BuyFlow.viewing_listings)
    await state.update_data(academic_year_id=academic_year.id, book_id=book.id)

    await handle_photo_back(callback, state, db_session)

    # State should remain viewing_listings
    state_data = await state.get_state()
    assert state_data == BuyFlow.viewing_listings

    # Should send header + listing message
    assert callback.message.answer.call_count == 2
    calls = callback.message.answer.call_args_list
    header_text = calls[0].args[0]
    listing_text = calls[1].args[0]
    assert "Math 6eme" in header_text
    assert "0612345678" in listing_text


@pytest.mark.asyncio
async def test_photo_menu_sends_main_menu(
    db_session,  # noqa: ARG001
    academic_year,  # noqa: ARG001
    user,  # noqa: ARG001
):
    """Test that clicking Menu principal after photos sends main menu like /start."""
    from bot.handlers.catalog import handle_photo_menu

    callback = _create_mock_callback("buy:photos:menu")
    state = _create_mock_state()
    await state.set_state(BuyFlow.viewing_listings)

    await handle_photo_menu(callback, state, db_session)

    # State should be cleared
    state_data = await state.get_state()
    assert state_data is None

    # Should send welcome message with main menu keyboard
    assert callback.message.answer.call_count == 1
    call_args = callback.message.answer.call_args
    welcome_text = call_args[0][0]
    reply_markup = call_args[1].get("reply_markup") or call_args[0][1]

    assert "Bienvenue" in welcome_text
    assert "Menu principal" in welcome_text

    button_texts = [btn.text for row in reply_markup.keyboard for btn in row]
    assert "🔍 Acheter un livre" in button_texts
    assert "📝 Mettre en vente" in button_texts


@pytest.mark.asyncio
async def test_photo_nav_callback_data_format(
    db_session,
    academic_year,
    user,
):
    """Test that photo navigation callbacks use correct format with book_id."""
    from bot.database.repository import BookRepository
    from bot.handlers.catalog import handle_view_listing_photos

    repo = BookRepository(db_session)
    book = await repo.create(
        category="textbook",
        title="Math 6eme",
        catalog_year_id=academic_year.id,
    )
    await db_session.commit()

    listing = Listing(
        book_id=book.id,
        seller_id=user.id,
        academic_year_id=academic_year.id,
        price=15.00,
        condition="good",
        status="active",
        contact_phone="0612345678",
        photos=["file_id_1"],
    )
    db_session.add(listing)
    await db_session.commit()

    callback = _create_mock_callback(f"buy:photos:{listing.id}")
    mock_bot = MagicMock()
    mock_bot.send_media_group = AsyncMock()
    callback.message.bot = mock_bot

    await handle_view_listing_photos(callback, db_session)

    # Navigation keyboard should contain correct callback_data with book_id
    nav_args = callback.message.answer.call_args
    nav_markup = nav_args[1].get("reply_markup") or nav_args[0][1]
    callback_data_list = [btn.callback_data for row in nav_markup.inline_keyboard for btn in row]
    assert f"buy:photos:back:{book.id}" in callback_data_list
    assert "buy:photos:menu" in callback_data_list


def test_listing_detail_keyboard_back_button():
    """Test that listing detail keyboard 'Retour' triggers buy:back:book_list."""
    from bot.keyboards.catalog import get_listing_detail_keyboard

    kb = get_listing_detail_keyboard(listing_id=1, has_photos=False, book_id=42)
    callback_data_list = [btn.callback_data for row in kb.inline_keyboard for btn in row]
    assert "buy:back:book_list" in callback_data_list
    assert "buy:book:42" not in callback_data_list


@pytest.mark.asyncio
async def test_handle_back_to_books_from_viewing_listings(
    db_session,
    academic_year,  # noqa: ARG001
):
    """Test that buy:back:book_list works from viewing_listings state."""
    from bot.database.repository import BookRepository
    from bot.handlers.catalog import handle_back_to_books

    repo = BookRepository(db_session)
    await repo.create(
        category="textbook",
        title="Math 6eme",
        catalog_year_id=academic_year.id,
    )
    await db_session.commit()

    callback = _create_mock_callback("buy:back:book_list")
    state = _create_mock_state()
    await state.set_state(BuyFlow.viewing_listings)
    await state.update_data(
        academic_year_id=academic_year.id,
        category="textbook",
        grade="6ème",
        subject="Mathématiques",
    )

    await handle_back_to_books(callback, state, db_session)

    callback.message.edit_text.assert_called_once()
    call_args = callback.message.edit_text.call_args
    assert "Choisissez un livre" in call_args[0][0]

    state_data = await state.get_state()
    assert state_data == BuyFlow.selecting_book
