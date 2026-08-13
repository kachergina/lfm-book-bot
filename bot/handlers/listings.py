"""My Listings management handlers."""

import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards.listings import (
    get_condition_keyboard,
    get_confirm_status_keyboard,
    get_contact_method_keyboard,
    get_description_action_keyboard,
    get_listing_manage_keyboard,
    get_listings_list_keyboard,
    get_my_listings_tabs_keyboard,
)
from bot.locale import fr
from bot.services.listing import (
    InvalidTransitionError,
    ListingOwnershipError,
    ListingService,
    ListingValidationError,
)
from bot.states.fsm import ManageListingFlow, SellFlow
from bot.utils.helpers import edit_message as _edit_message
from bot.utils.helpers import format_price

logger = logging.getLogger(__name__)

router = Router()


async def _get_user_id(callback: CallbackQuery, session: AsyncSession) -> int | None:
    """Get internal user ID from Telegram user.

    Args:
        callback: Telegram callback.
        session: Database session.

    Returns:
        Internal user ID or None.
    """
    from bot.database.repository import UserRepository

    if not callback.from_user:
        return None

    user_repo = UserRepository(session)
    user = await user_repo.get_by_telegram_id(callback.from_user.id)
    return user.id if user else None


async def _show_tabs(callback: CallbackQuery, session: AsyncSession) -> None:
    """Show my listings tabs.

    Args:
        callback: Telegram callback.
        session: Database session.
    """
    user_id = await _get_user_id(callback, session)
    if user_id is None:
        await callback.answer(fr.MSG_USER_NOT_FOUND, show_alert=True)
        return

    service = ListingService(session)

    active = await service.get_user_listings(user_id, "active")
    reserved = await service.get_user_listings(user_id, "reserved")
    sold = await service.get_user_listings(user_id, "sold")
    archived = await service.get_user_listings(user_id, "archived")

    total = len(active) + len(reserved) + len(sold) + len(archived)

    if total == 0:
        await _edit_message(callback, fr.MY_LISTINGS_EMPTY)
        await callback.answer()
        return

    await _edit_message(
        callback,
        fr.MY_LISTINGS_TITLE,
        reply_markup=get_my_listings_tabs_keyboard(
            active_count=len(active),
            reserved_count=len(reserved),
            sold_count=len(sold),
            archived_count=len(archived),
        ),
    )
    await callback.answer()


async def _show_listings_list(
    callback: CallbackQuery,
    session: AsyncSession,
    status: str,
) -> None:
    """Show listings list for a specific status.

    Args:
        callback: Telegram callback.
        session: Database session.
        status: Listing status filter.
    """
    user_id = await _get_user_id(callback, session)
    if user_id is None:
        await callback.answer(fr.MSG_USER_NOT_FOUND, show_alert=True)
        return

    service = ListingService(session)
    listings = await service.get_user_listings(user_id, status)

    if not listings:
        await _edit_message(
            callback,
            fr.NO_LISTINGS_IN_CATEGORY,
            reply_markup=get_my_listings_tabs_keyboard(),
        )
        await callback.answer()
        return

    listings_data = [
        {
            "id": listing.id,
            "title": listing.book.title if listing.book else "Livre inconnu",
            "price": format_price(listing.price),
        }
        for listing in listings
    ]

    status_label = fr.STATUS_LABELS.get(status, status)
    text = f"{fr.MY_LISTINGS_TITLE} — {status_label}\n\n"
    text += fr.LISTINGS_COUNT.format(total=len(listings))

    await _edit_message(
        callback,
        text,
        reply_markup=get_listings_list_keyboard(listings_data, status),
    )
    await callback.answer()


async def _show_listing_detail(
    callback: CallbackQuery,
    session: AsyncSession,
    listing_id: int,
) -> None:
    """Show listing detail and management options.

    Args:
        callback: Telegram callback.
        session: Database session.
        listing_id: Listing ID.
    """
    user_id = await _get_user_id(callback, session)
    if user_id is None:
        await callback.answer(fr.MSG_USER_NOT_FOUND, show_alert=True)
        return

    service = ListingService(session)

    try:
        listing = await service.get_user_listing(listing_id, user_id)
    except ListingValidationError as e:
        await callback.answer(str(e), show_alert=True)
        return
    except ListingOwnershipError:
        await callback.answer(fr.MSG_NOT_YOUR_LISTING, show_alert=True)
        return

    book_title = listing.book.title if listing.book else "Livre inconnu"
    status_label = fr.STATUS_LABELS.get(listing.status, listing.status)
    condition_label = fr.CONDITION_LABELS.get(listing.condition, listing.condition)

    parts = [
        fr.MANAGE_LISTING_TITLE,
        "",
        fr.LISTING_CARD_TITLE.format(title=book_title),
        fr.LISTING_CARD_PRICE.format(price=format_price(listing.price)),
        fr.LISTING_CARD_CONDITION.format(condition=condition_label),
        fr.LISTING_CARD_STATUS.format(status=status_label),
        fr.LISTING_CARD_PHONE.format(phone=listing.contact_phone or "Non renseigné"),
    ]

    if listing.description:
        parts.append(fr.LISTING_CARD_DESCRIPTION.format(description=listing.description))

    if listing.photos:
        parts.append(fr.LISTING_CARD_PHOTOS.format(count=len(listing.photos)))

    parts.append(fr.LISTING_CARD_VIEWS.format(views=listing.view_count))

    await _edit_message(
        callback,
        "\n".join(parts),
        reply_markup=get_listing_manage_keyboard(listing_id, listing.status),
    )
    await callback.answer()


# Entry point: "Mes annonces" button
@router.message(F.text == fr.BTN_MY_LISTINGS)
async def cmd_my_listings(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Handle my listings button.

    Args:
        message: Telegram message.
        state: FSM state.
        session: Database session.
    """
    await state.clear()
    await state.set_state(ManageListingFlow.selecting_listing)

    from bot.database.repository import UserRepository

    user_repo = UserRepository(session)
    if not message.from_user:
        return

    user = await user_repo.get_by_telegram_id(message.from_user.id)
    if user is None:
        await message.answer(fr.MSG_USER_NOT_FOUND)
        return

    service = ListingService(session)

    active = await service.get_user_listings(user.id, "active")
    reserved = await service.get_user_listings(user.id, "reserved")
    sold = await service.get_user_listings(user.id, "sold")
    archived = await service.get_user_listings(user.id, "archived")

    total = len(active) + len(reserved) + len(sold) + len(archived)

    if total == 0:
        await message.answer(fr.MY_LISTINGS_EMPTY)
        return

    await message.answer(
        fr.MY_LISTINGS_TITLE,
        reply_markup=get_my_listings_tabs_keyboard(
            active_count=len(active),
            reserved_count=len(reserved),
            sold_count=len(sold),
            archived_count=len(archived),
        ),
    )


# Tab selection
@router.callback_query(ManageListingFlow.selecting_listing, F.data.startswith("mylistings:tab:"))
async def handle_tab_selection(
    callback: CallbackQuery,
    state: FSMContext,  # noqa: ARG001
    session: AsyncSession,
) -> None:
    """Handle tab selection.

    Args:
        callback: Telegram callback.
        state: FSM state.
        session: Database session.
    """
    if not callback.data:
        return

    status = callback.data.split(":")[2]
    await _show_listings_list(callback, session, status)
    await callback.answer()


# Back to tabs
@router.callback_query(ManageListingFlow.selecting_listing, F.data == "mylistings:back:tabs")
async def handle_back_to_tabs(
    callback: CallbackQuery,
    state: FSMContext,  # noqa: ARG001
    session: AsyncSession,
) -> None:
    """Handle back to tabs.

    Args:
        callback: Telegram callback.
        state: FSM state.
        session: Database session.
    """
    await _show_tabs(callback, session)


# View listing
@router.callback_query(ManageListingFlow.selecting_listing, F.data.startswith("mylistings:view:"))
async def handle_view_listing(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Handle view listing detail.

    Args:
        callback: Telegram callback.
        state: FSM state.
        session: Database session.
    """
    if not callback.data:
        return

    try:
        listing_id = int(callback.data.split(":")[2])
    except (ValueError, IndexError):
        await callback.answer(fr.MSG_INVALID_ACTION, show_alert=True)
        return

    await state.set_state(ManageListingFlow.managing)
    await state.update_data(listing_id=listing_id)

    await _show_listing_detail(callback, session, listing_id)


# New listing (from my listings)
@router.callback_query(ManageListingFlow.selecting_listing, F.data == "mylistings:new")
async def handle_new_listing(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Handle new listing from my listings.

    Args:
        callback: Telegram callback.
        state: FSM state.
        session: Database session.
    """
    if not callback.message or not callback.from_user:
        return

    # Clear current state
    await state.clear()

    # Start sell flow by sending a new message
    from bot.keyboards.catalog import get_sell_category_keyboard
    from bot.services.browsing import BrowsingService

    service_browsing = BrowsingService(session)
    academic_year = await service_browsing.get_current_academic_year()

    if academic_year is None:
        await callback.message.answer(fr.MSG_NO_ACADEMIC_YEAR)
        await callback.answer()
        return

    await state.update_data(academic_year_id=academic_year.id)
    await state.set_state(SellFlow.selecting_category)

    await callback.message.answer(
        fr.SELL_SELECT_CATEGORY,
        reply_markup=get_sell_category_keyboard(),
    )
    await callback.answer()


# Back to main menu
@router.callback_query(ManageListingFlow.selecting_listing, F.data == "mylistings:menu")
async def handle_back_to_menu(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    """Handle back to main menu.

    Args:
        callback: Telegram callback.
        state: FSM state.
    """
    await state.clear()

    if callback.message and hasattr(callback.message, "edit_text"):
        await callback.message.edit_text(fr.MAIN_MENU_TITLE)
    await callback.answer()


# ===== LISTING MANAGEMENT ACTIONS =====


# Edit price
@router.callback_query(ManageListingFlow.managing, F.data.endswith(":edit_price"))
async def handle_edit_price(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    """Handle edit price action.

    Args:
        callback: Telegram callback.
        state: FSM state.
    """
    if not callback.data:
        return

    try:
        listing_id = int(callback.data.split(":")[1])
    except (ValueError, IndexError):
        await callback.answer(fr.MSG_INVALID_ACTION, show_alert=True)
        return

    await state.update_data(listing_id=listing_id)
    await state.set_state(ManageListingFlow.editing_price)

    await _edit_message(callback, fr.SELL_ENTER_PRICE)
    await callback.answer()


@router.message(ManageListingFlow.editing_price)
async def handle_price_input(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Handle price input for editing.

    Args:
        message: Telegram message.
        state: FSM state.
        session: Database session.
    """
    from bot.database.repository import UserRepository

    if not message.text or not message.from_user:
        return

    try:
        price = ListingService.validate_price(message.text)
    except ListingValidationError as e:
        await message.answer(str(e))
        return

    data = await state.get_data()
    listing_id = data.get("listing_id")
    if listing_id is None:
        return

    user_repo = UserRepository(session)
    user = await user_repo.get_by_telegram_id(message.from_user.id)
    if user is None:
        return

    service = ListingService(session)
    try:
        await service.update_field(listing_id, user.id, "price", float(price))
    except (ListingValidationError, ListingOwnershipError) as e:
        await message.answer(str(e))
        return

    await state.set_state(ManageListingFlow.managing)
    await message.answer(fr.LISTING_EDITED_PRICE.format(price=format_price(price)))

    # Show management keyboard again
    from bot.keyboards.listings import get_listing_manage_keyboard

    listing = await service.get_user_listing(listing_id, user.id)
    await message.answer(
        fr.MANAGE_LISTING_TITLE,
        reply_markup=get_listing_manage_keyboard(listing_id, listing.status),
    )


# Edit condition
@router.callback_query(ManageListingFlow.managing, F.data.endswith(":edit_condition"))
async def handle_edit_condition(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    """Handle edit condition action.

    Args:
        callback: Telegram callback.
        state: FSM state.
    """
    if not callback.data:
        return

    try:
        listing_id = int(callback.data.split(":")[1])
    except (ValueError, IndexError):
        await callback.answer(fr.MSG_INVALID_ACTION, show_alert=True)
        return

    await state.update_data(listing_id=listing_id)
    await state.set_state(ManageListingFlow.editing_condition)

    await _edit_message(
        callback,
        fr.SELL_SELECT_CONDITION,
        reply_markup=get_condition_keyboard(),
    )
    await callback.answer()


@router.callback_query(ManageListingFlow.editing_condition, F.data.startswith("sell:cond:"))
async def handle_condition_input(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Handle condition selection for editing.

    Args:
        callback: Telegram callback.
        state: FSM state.
        session: Database session.
    """
    from bot.database.repository import UserRepository

    if not callback.data or not callback.from_user:
        return

    condition = callback.data.split(":")[2]

    try:
        ListingService.validate_condition(condition)
    except ListingValidationError as e:
        await callback.answer(str(e), show_alert=True)
        return

    data = await state.get_data()
    listing_id = data.get("listing_id")
    if listing_id is None:
        return

    user_repo = UserRepository(session)
    user = await user_repo.get_by_telegram_id(callback.from_user.id)
    if user is None:
        return

    service = ListingService(session)
    try:
        await service.update_field(listing_id, user.id, "condition", condition)
    except (ListingValidationError, ListingOwnershipError) as e:
        await callback.answer(str(e), show_alert=True)
        return

    await state.set_state(ManageListingFlow.managing)
    condition_label = fr.CONDITION_LABELS.get(condition, condition)
    await _edit_message(callback, fr.LISTING_EDITED_CONDITION.format(condition=condition_label))

    listing = await service.get_user_listing(listing_id, user.id)
    from bot.keyboards.listings import get_listing_manage_keyboard

    if callback.message and hasattr(callback.message, "answer"):
        await callback.message.answer(
            fr.MANAGE_LISTING_TITLE,
            reply_markup=get_listing_manage_keyboard(listing_id, listing.status),
        )
    await callback.answer()


# Edit phone/telegram contact
@router.callback_query(ManageListingFlow.managing, F.data.endswith(":edit_phone"))
async def handle_edit_phone(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    """Handle edit contact action.

    Args:
        callback: Telegram callback.
        state: FSM state.
    """
    if not callback.data:
        return

    try:
        listing_id = int(callback.data.split(":")[1])
    except (ValueError, IndexError):
        await callback.answer(fr.MSG_INVALID_ACTION, show_alert=True)
        return

    await state.update_data(listing_id=listing_id)
    await state.set_state(ManageListingFlow.editing_phone)

    await _edit_message(
        callback,
        fr.SELL_SELECT_CONTACT_METHOD,
        reply_markup=get_contact_method_keyboard(),
    )
    await callback.answer()


@router.callback_query(ManageListingFlow.editing_phone, F.data.startswith("sell:contact:"))
async def handle_edit_contact_method_selection(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    """Handle contact method selection during edit.

    Args:
        callback: Telegram callback.
        state: FSM state.
    """
    if not callback.data:
        return

    method = callback.data.split(":")[2]

    if method == "phone":
        await state.update_data(edit_contact_method="phone")
        await _edit_message(callback, fr.SELL_ENTER_PHONE)
    elif method == "telegram":
        await state.update_data(edit_contact_method="telegram")
        await _edit_message(callback, fr.SELL_ENTER_TELEGRAM)
    else:
        await callback.answer(fr.MSG_INVALID_ACTION, show_alert=True)
        return

    await callback.answer()


@router.message(ManageListingFlow.editing_phone)
async def handle_phone_input(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Handle phone/telegram input for editing.

    Args:
        message: Telegram message.
        state: FSM state.
        session: Database session.
    """
    from bot.database.repository import UserRepository

    if not message.text or not message.from_user:
        return

    data = await state.get_data()
    listing_id = data.get("listing_id")
    edit_method = data.get("edit_contact_method", "phone")

    if edit_method == "telegram":
        try:
            contact_value = ListingService.validate_telegram_username(message.text)
        except ListingValidationError as e:
            await message.answer(str(e))
            return
    else:
        try:
            contact_value = ListingService.validate_phone(message.text)
        except ListingValidationError as e:
            await message.answer(str(e))
            return

    if listing_id is None:
        return

    user_repo = UserRepository(session)
    user = await user_repo.get_by_telegram_id(message.from_user.id)
    if user is None:
        return

    service = ListingService(session)
    try:
        await service.update_field(listing_id, user.id, "contact_phone", contact_value)
        await service.update_field(listing_id, user.id, "contact_method", edit_method)
    except (ListingValidationError, ListingOwnershipError) as e:
        await message.answer(str(e))
        return

    await state.set_state(ManageListingFlow.managing)
    await message.answer(fr.LISTING_EDITED_PHONE.format(phone=contact_value))

    listing = await service.get_user_listing(listing_id, user.id)
    from bot.keyboards.listings import get_listing_manage_keyboard

    await message.answer(
        fr.MANAGE_LISTING_TITLE,
        reply_markup=get_listing_manage_keyboard(listing_id, listing.status),
    )


# Edit description
@router.callback_query(ManageListingFlow.managing, F.data.endswith(":edit_desc"))
async def handle_edit_description(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    """Handle edit description action.

    Args:
        callback: Telegram callback.
        state: FSM state.
    """
    if not callback.data:
        return

    try:
        listing_id = int(callback.data.split(":")[1])
    except (ValueError, IndexError):
        await callback.answer(fr.MSG_INVALID_ACTION, show_alert=True)
        return

    await state.update_data(listing_id=listing_id)
    await state.set_state(ManageListingFlow.editing_description)

    await _edit_message(
        callback,
        fr.SELL_ENTER_DESCRIPTION,
        reply_markup=get_description_action_keyboard(),
    )
    await callback.answer()


@router.message(ManageListingFlow.editing_description)
async def handle_description_input(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Handle description input for editing.

    Args:
        message: Telegram message.
        state: FSM state.
        session: Database session.
    """
    from bot.database.repository import UserRepository

    if not message.text or not message.from_user:
        return

    try:
        description = ListingService.validate_description(message.text)
    except ListingValidationError as e:
        await message.answer(str(e))
        return

    data = await state.get_data()
    listing_id = data.get("listing_id")
    if listing_id is None:
        return

    user_repo = UserRepository(session)
    user = await user_repo.get_by_telegram_id(message.from_user.id)
    if user is None:
        return

    service = ListingService(session)
    try:
        await service.update_field(listing_id, user.id, "description", description)
    except (ListingValidationError, ListingOwnershipError) as e:
        await message.answer(str(e))
        return

    await state.set_state(ManageListingFlow.managing)
    await message.answer(fr.LISTING_EDITED_DESCRIPTION)

    listing = await service.get_user_listing(listing_id, user.id)
    from bot.keyboards.listings import get_listing_manage_keyboard

    await message.answer(
        fr.MANAGE_LISTING_TITLE,
        reply_markup=get_listing_manage_keyboard(listing_id, listing.status),
    )


# ===== STATUS CHANGES =====


# Mark as reserved
@router.callback_query(ManageListingFlow.managing, F.data.endswith(":reserve"))
async def handle_reserve(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    """Handle mark as reserved.

    Args:
        callback: Telegram callback.
        state: FSM state.
    """
    if not callback.data:
        return

    try:
        listing_id = int(callback.data.split(":")[1])
    except (ValueError, IndexError):
        await callback.answer(fr.MSG_INVALID_ACTION, show_alert=True)
        return

    await state.update_data(listing_id=listing_id, pending_action="reserve")

    await _edit_message(
        callback,
        fr.CONFIRM_MARK_RESERVED,
        reply_markup=get_confirm_status_keyboard(listing_id, "reserve"),
    )
    await callback.answer()


# Mark as sold
@router.callback_query(ManageListingFlow.managing, F.data.endswith(":sell"))
async def handle_sell(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    """Handle mark as sold.

    Args:
        callback: Telegram callback.
        state: FSM state.
    """
    if not callback.data:
        return

    try:
        listing_id = int(callback.data.split(":")[1])
    except (ValueError, IndexError):
        await callback.answer(fr.MSG_INVALID_ACTION, show_alert=True)
        return

    await state.update_data(listing_id=listing_id, pending_action="sell")

    await _edit_message(
        callback,
        fr.CONFIRM_MARK_SOLD,
        reply_markup=get_confirm_status_keyboard(listing_id, "sell"),
    )
    await callback.answer()


# Mark as active (from reserved)
@router.callback_query(ManageListingFlow.managing, F.data.endswith(":activate"))
async def handle_activate(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    """Handle mark as active.

    Args:
        callback: Telegram callback.
        state: FSM state.
    """
    if not callback.data:
        return

    try:
        listing_id = int(callback.data.split(":")[1])
    except (ValueError, IndexError):
        await callback.answer(fr.MSG_INVALID_ACTION, show_alert=True)
        return

    await state.update_data(listing_id=listing_id, pending_action="activate")

    await _edit_message(
        callback,
        fr.CONFIRM_MARK_ACTIVE,
        reply_markup=get_confirm_status_keyboard(listing_id, "activate"),
    )
    await callback.answer()


# Archive
@router.callback_query(ManageListingFlow.managing, F.data.endswith(":archive"))
async def handle_archive(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    """Handle archive/delete.

    Args:
        callback: Telegram callback.
        state: FSM state.
    """
    if not callback.data:
        return

    try:
        listing_id = int(callback.data.split(":")[1])
    except (ValueError, IndexError):
        await callback.answer(fr.MSG_INVALID_ACTION, show_alert=True)
        return

    await state.update_data(listing_id=listing_id, pending_action="archive")

    await _edit_message(
        callback,
        fr.CONFIRM_ARCHIVE,
        reply_markup=get_confirm_status_keyboard(listing_id, "archive"),
    )
    await callback.answer()


# Confirm status change
@router.callback_query(ManageListingFlow.managing, F.data.endswith(":confirm:reserve"))
@router.callback_query(ManageListingFlow.managing, F.data.endswith(":confirm:sell"))
@router.callback_query(ManageListingFlow.managing, F.data.endswith(":confirm:activate"))
@router.callback_query(ManageListingFlow.managing, F.data.endswith(":confirm:archive"))
async def handle_confirm_status(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Handle confirm status change.

    Args:
        callback: Telegram callback.
        state: FSM state.
        session: Database session.
    """
    from bot.database.repository import UserRepository

    # Validate inputs
    error_msg = await _validate_confirm_status_inputs(callback, state, session)
    if error_msg is not None:
        await callback.answer(error_msg, show_alert=True)
        return

    assert callback.data is not None
    assert callback.from_user is not None

    parts = callback.data.split(":")
    action = parts[3]

    data = await state.get_data()
    listing_id: int = data["listing_id"]

    user_repo = UserRepository(session)
    user = await user_repo.get_by_telegram_id(callback.from_user.id)
    assert user is not None

    # Map action to status
    status_map = {
        "reserve": "reserved",
        "sell": "sold",
        "activate": "active",
        "archive": "archived",
    }

    new_status = status_map[action]

    service = ListingService(session)

    # Get listing before status change (for notification context)
    try:
        listing = await service.get_user_listing(listing_id, user.id)
    except ListingValidationError:
        await callback.answer(fr.MSG_LISTING_NOT_FOUND, show_alert=True)
        return
    except ListingOwnershipError:
        await callback.answer(fr.MSG_NOT_YOUR_LISTING, show_alert=True)
        return

    old_status = listing.status

    try:
        await service.update_status(listing_id, user.id, new_status)
    except InvalidTransitionError:
        await callback.answer(fr.MSG_STATUS_TRANSITION_INVALID, show_alert=True)
        return
    except (ListingValidationError, ListingOwnershipError) as e:
        await callback.answer(str(e), show_alert=True)
        return

    status_label = fr.STATUS_LABELS.get(new_status, new_status)
    await _edit_message(callback, fr.STATUS_CHANGED.format(status=status_label))
    await callback.answer()

    # Send notification to seller (best-effort, after DB commit)
    bot = data.get("bot")
    if bot is not None:
        try:
            from bot.services.notification import NotificationService

            notification_service = NotificationService(bot, session)
            await notification_service.notify_seller_status_change(
                listing=listing,
                old_status=old_status,
                new_status=new_status,
            )
        except Exception:
            logger.exception(
                "Failed to send status change notification",
                extra={"listing_id": listing_id, "new_status": new_status},
            )


async def _validate_confirm_status_inputs(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,  # noqa: ARG001
) -> str | None:
    """Validate confirm status inputs.

    Args:
        callback: Telegram callback.
        state: FSM state.
        session: Database session.

    Returns:
        Error message string if validation fails, None if valid.
    """
    from bot.database.repository import UserRepository

    if not callback.data or not callback.from_user:
        return fr.MSG_INVALID_ACTION

    # Parse action from callback data: ml:{id}:confirm:{action}
    parts = callback.data.split(":")
    if len(parts) < 4:
        return fr.MSG_INVALID_CALLBACK

    action = parts[3]

    data = await state.get_data()
    listing_id = data.get("listing_id")
    if listing_id is None:
        return fr.MSG_DATA_ERROR

    user_repo = UserRepository(session)
    user = await user_repo.get_by_telegram_id(callback.from_user.id)
    if user is None:
        return fr.MSG_USER_NOT_FOUND

    # Map action to status
    status_map = {
        "reserve": "reserved",
        "sell": "sold",
        "activate": "active",
        "archive": "archived",
    }

    if action not in status_map:
        return fr.MSG_INVALID_ACTION

    return None


# Cancel status change
@router.callback_query(ManageListingFlow.managing, F.data.endswith(":cancel"))
async def handle_cancel_status(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Handle cancel status change.

    Args:
        callback: Telegram callback.
        state: FSM state.
        session: Database session.
    """
    data = await state.get_data()
    listing_id = data.get("listing_id")
    if listing_id is None:
        await callback.answer()
        return

    # Go back to listing management
    await _show_listing_detail(callback, session, listing_id)


# Back to listings from management
@router.callback_query(ManageListingFlow.managing, F.data.startswith("mylistings:tab:"))
async def handle_back_to_listings_from_manage(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Handle back to listings list from management view.

    Args:
        callback: Telegram callback.
        state: FSM state.
        session: Database session.
    """
    if not callback.data:
        return

    status = callback.data.split(":")[2]
    await state.set_state(ManageListingFlow.selecting_listing)
    await _show_listings_list(callback, session, status)
