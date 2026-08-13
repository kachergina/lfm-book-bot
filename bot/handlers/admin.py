"""Admin panel handlers."""

import logging
from datetime import date

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards.admin import (
    get_admin_back_keyboard,
    get_admin_panel_keyboard,
    get_admin_users_keyboard,
    get_admin_years_keyboard,
    get_ban_reason_keyboard,
    get_catalog_import_keyboard,
    get_confirm_ban_keyboard,
    get_user_detail_keyboard,
    get_user_list_keyboard,
    get_year_create_confirm_keyboard,
    get_year_detail_keyboard,
    get_years_list_keyboard,
)
from bot.locale import fr
from bot.utils.helpers import edit_message as _edit_message

logger = logging.getLogger(__name__)

router = Router()


async def _require_admin(callback: CallbackQuery) -> bool:
    """Check if callback user is an admin. Show error and return False if not.

    Args:
        callback: Telegram callback.

    Returns:
        True if user is admin, False otherwise.
    """
    from bot.config import get_settings

    settings = get_settings()
    if callback.from_user and callback.from_user.id in settings.bot_admin_ids:
        return True
    await callback.answer(fr.MSG_NOT_ADMIN, show_alert=True)
    return False


class AdminYearCreateFlow(StatesGroup):
    """States for academic year creation flow."""

    entering_name = State()
    entering_start_date = State()
    entering_end_date = State()
    confirming = State()


class AdminUserSearchFlow(StatesGroup):
    """States for user search flow."""

    entering_query = State()


class AdminBanFlow(StatesGroup):
    """States for ban flow."""

    entering_reason = State()
    confirming = State()


# ===== ENTRY POINTS =====


@router.message(F.text == "/admin")
async def cmd_admin(
    message: Message,
    state: FSMContext,  # noqa: ARG001
    session: AsyncSession,  # noqa: ARG001
) -> None:
    """Handle /admin command - show admin panel.

    Args:
        message: Telegram message.
        state: FSM state.
        session: Database session.
    """
    await state.clear()

    from bot.config import get_settings

    settings = get_settings()
    if message.from_user and message.from_user.id not in settings.bot_admin_ids:
        await message.answer(fr.MSG_NOT_ADMIN)
        return

    await message.answer(
        fr.ADMIN_PANEL_TITLE,
        reply_markup=get_admin_panel_keyboard(),
    )


@router.callback_query(F.data == "admin:back:panel")
async def handle_back_to_panel(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    """Handle back to admin panel.

    Args:
        callback: Telegram callback.
        state: FSM state.
    """
    if not await _require_admin(callback):
        return
    await state.clear()
    await _edit_message(callback, fr.ADMIN_PANEL_TITLE, get_admin_panel_keyboard())
    await callback.answer()


@router.callback_query(F.data == "admin:stats")
async def handle_stats(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    if not await _require_admin(callback):
        return
    await state.clear()
    from bot.database.repository import ListingRepository, UserRepository

    user_repo = UserRepository(session)
    listing_repo = ListingRepository(session)
    total_users = await user_repo.count_all()
    total_listings = await listing_repo.count_all()
    total_sold = await listing_repo.count_sold()
    text = (
        f"{fr.ADMIN_STATS_TITLE}\n\n"
        f"{fr.ADMIN_STATS_USERS.format(count=total_users)}\n"
        f"{fr.ADMIN_STATS_LISTINGS.format(count=total_listings)}\n"
        f"{fr.ADMIN_STATS_SOLD.format(count=total_sold)}"
    )
    await _edit_message(callback, text, get_admin_back_keyboard())
    await callback.answer()


# ===== ACADEMIC YEAR MANAGEMENT =====


@router.callback_query(F.data == "admin:years")
async def handle_years_menu(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Handle years management menu.

    Args:
        callback: Telegram callback.
        state: FSM state.
        session: Database session.
    """
    if not await _require_admin(callback):
        return
    await state.clear()

    from bot.services.academic_year import AcademicYearService

    service = AcademicYearService(session)
    current = await service.get_current_year()

    if current is not None:
        text = fr.ADMIN_YEARS_TITLE + "\n\n" + fr.ADMIN_YEARS_CURRENT.format(name=current.name)
    else:
        text = fr.ADMIN_YEARS_TITLE + "\n\n" + fr.ADMIN_YEARS_NO_CURRENT

    await _edit_message(callback, text, get_admin_years_keyboard())
    await callback.answer()


@router.callback_query(F.data == "admin:years:list")
async def handle_years_list(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Handle years list.

    Args:
        callback: Telegram callback.
        state: FSM state.
        session: Database session.
    """
    if not await _require_admin(callback):
        return
    await state.clear()

    from bot.services.academic_year import AcademicYearService

    service = AcademicYearService(session)
    years = await service.list_years()

    if not years:
        await _edit_message(
            callback,
            fr.ADMIN_YEARS_TITLE + "\n\nAucune année scolaire configurée.",
            get_admin_years_keyboard(),
        )
        await callback.answer()
        return

    years_data = [{"id": y.id, "name": y.name, "is_current": y.is_current} for y in years]
    await _edit_message(
        callback,
        fr.ADMIN_YEARS_TITLE,
        get_years_list_keyboard(years_data),
    )
    await callback.answer()


def _is_year_detail_callback(data: str | None) -> bool:
    """Check if callback is a year-detail action (not a year-create action)."""
    if data is None:
        return False
    if not data.startswith("admin:year:"):
        return False
    return not data.startswith("admin:year:create")


@router.callback_query(F.data.func(_is_year_detail_callback))
async def handle_year_detail(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Handle year detail view.

    Args:
        callback: Telegram callback.
        state: FSM state.
        session: Database session.
    """
    if not await _require_admin(callback) or not callback.data:
        return

    parts = callback.data.split(":")
    action = parts[2] if len(parts) >= 3 else None

    if action == "set_current":
        await _handle_set_current(callback, state, session, int(parts[3]))
        return

    try:
        year_id = int(action)  # type: ignore[arg-type]
    except (ValueError, IndexError, TypeError):
        await callback.answer(fr.MSG_INVALID_ACTION, show_alert=True)
        return

    from bot.services.academic_year import AcademicYearService

    service = AcademicYearService(session)
    try:
        year = await service.get_year_by_id(year_id)
    except Exception:
        await callback.answer(fr.MSG_SOMETHING_WENT_WRONG, show_alert=True)
        return

    current_badge = " (📌 Courante)" if year.is_current else ""
    text = fr.ADMIN_YEARS_YEAR_INFO.format(
        name=year.name,
        start=year.start_date.strftime("%d/%m/%Y"),
        end=year.end_date.strftime("%d/%m/%Y"),
        current_badge=current_badge,
    )

    await _edit_message(
        callback,
        text,
        get_year_detail_keyboard(year.id, year.is_current),
    )
    await callback.answer()


async def _handle_set_current(
    callback: CallbackQuery,
    state: FSMContext,  # noqa: ARG001
    session: AsyncSession,
    year_id: int,
) -> None:
    """Handle setting a year as current.

    Args:
        callback: Telegram callback.
        state: FSM state.
        session: Database session.
        year_id: Year ID to set as current.
    """
    from bot.services.academic_year import AcademicYearService

    service = AcademicYearService(session)
    try:
        await service.set_current_year(year_id)
        year = await service.get_year_by_id(year_id)
        await _edit_message(
            callback,
            f"✅ L'année scolaire « {year.name} » est maintenant l'année courante.",
            get_admin_years_keyboard(),
        )
    except Exception as e:
        await callback.answer(str(e), show_alert=True)
        return
    await callback.answer()


@router.callback_query(F.data == "admin:years:create")
async def handle_year_create_start(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    """Handle start year creation.

    Args:
        callback: Telegram callback.
        state: FSM state.
    """
    if not await _require_admin(callback):
        return
    await state.set_state(AdminYearCreateFlow.entering_name)
    await _edit_message(callback, fr.ADMIN_YEAR_CREATE_PROMPT)
    await callback.answer()


@router.message(AdminYearCreateFlow.entering_name)
async def handle_year_name_input(
    message: Message,
    state: FSMContext,
) -> None:
    """Handle year name input.

    Args:
        message: Telegram message.
        state: FSM state.
    """
    if not message.text:
        await message.answer(fr.ADMIN_YEAR_NAME_INVALID)
        return

    name = message.text.strip()

    # Validate name format (YYYY-YYYY)
    if len(name) < 4 or "-" not in name:
        await message.answer(fr.ADMIN_YEAR_NAME_INVALID)
        return

    await state.update_data(year_name=name)
    await state.set_state(AdminYearCreateFlow.entering_start_date)
    await message.answer(fr.ADMIN_YEAR_CREATE_START)


@router.message(AdminYearCreateFlow.entering_start_date)
async def handle_year_start_date_input(
    message: Message,
    state: FSMContext,
) -> None:
    """Handle start date input.

    Args:
        message: Telegram message.
        state: FSM state.
    """
    if not message.text:
        await message.answer(fr.ADMIN_YEAR_DATE_INVALID)
        return

    parsed_date = _parse_date(message.text.strip())
    if parsed_date is None:
        await message.answer(fr.ADMIN_YEAR_DATE_INVALID)
        return

    await state.update_data(year_start=parsed_date.isoformat())
    await state.set_state(AdminYearCreateFlow.entering_end_date)
    await message.answer(fr.ADMIN_YEAR_CREATE_END)


@router.message(AdminYearCreateFlow.entering_end_date)
async def handle_year_end_date_input(
    message: Message,
    state: FSMContext,
) -> None:
    """Handle end date input.

    Args:
        message: Telegram message.
        state: FSM state.
    """
    if not message.text:
        await message.answer(fr.ADMIN_YEAR_DATE_INVALID)
        return

    parsed_date = _parse_date(message.text.strip())
    if parsed_date is None:
        await message.answer(fr.ADMIN_YEAR_DATE_INVALID)
        return

    data = await state.get_data()
    start_date = date.fromisoformat(data["year_start"])

    if parsed_date <= start_date:
        await message.answer(fr.ADMIN_YEAR_DATE_ORDER)
        return

    await state.update_data(year_end=parsed_date.isoformat())

    name = data["year_name"]
    confirm_text = fr.ADMIN_YEAR_CREATE_CONFIRM.format(
        name=name,
        start=start_date.strftime("%d/%m/%Y"),
        end=parsed_date.strftime("%d/%m/%Y"),
    )

    await state.set_state(AdminYearCreateFlow.confirming)
    await message.answer(confirm_text, reply_markup=get_year_create_confirm_keyboard())


@router.callback_query(AdminYearCreateFlow.confirming, F.data == "admin:year:create:confirm")
async def handle_year_create_confirm(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Handle year creation confirmation.

    Args:
        callback: Telegram callback.
        state: FSM state.
        session: Database session.
    """
    if not await _require_admin(callback):
        return
    data = await state.get_data()
    name = data["year_name"]
    start_date = date.fromisoformat(data["year_start"])
    end_date = date.fromisoformat(data["year_end"])

    from bot.services.academic_year import AcademicYearError, AcademicYearService

    service = AcademicYearService(session)
    try:
        year = await service.create_year(name, start_date, end_date)
    except AcademicYearError as e:
        await callback.answer(str(e), show_alert=True)
        return

    await state.clear()
    await _edit_message(
        callback,
        fr.ADMIN_YEAR_CREATED.format(name=year.name),
        get_admin_years_keyboard(),
    )
    await callback.answer()


@router.callback_query(AdminYearCreateFlow.confirming, F.data == "admin:year:create:modify")
async def handle_year_create_modify(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    if not await _require_admin(callback):
        return
    await state.set_state(AdminYearCreateFlow.entering_name)
    await _edit_message(callback, fr.ADMIN_YEAR_CREATE_PROMPT)
    await callback.answer()


# ===== YEAR TRANSITION =====


@router.callback_query(F.data == "admin:years:transition")
async def handle_transition_start(
    callback: CallbackQuery,
    state: FSMContext,  # noqa: ARG001
    session: AsyncSession,
) -> None:
    """Handle transition start - show year selection.

    Args:
        callback: Telegram callback.
        state: FSM state.
        session: Database session.
    """
    if not await _require_admin(callback):
        return
    from bot.services.academic_year import AcademicYearService

    service = AcademicYearService(session)
    current = await service.get_current_year()
    years = await service.list_years()

    if not years:
        await callback.answer(fr.ADMIN_YEARS_NO_CURRENT, show_alert=True)
        return

    # Filter out the current year from options
    available = [y for y in years if not y.is_current]

    if not available:
        await callback.answer(
            "Aucune autre année scolaire disponible pour la transition.",
            show_alert=True,
        )
        return

    current_name = current.name if current else "Aucune"

    text = (
        f"{fr.ADMIN_TRANSITION_TITLE}\n\n"
        f"{fr.ADMIN_TRANSITION_CURRENT.format(name=current_name)}\n\n"
        "Sélectionnez la nouvelle année scolaire :"
    )

    keyboard = get_years_list_keyboard(
        [{"id": y.id, "name": y.name, "is_current": y.is_current} for y in available]
    )
    await _edit_message(callback, text, keyboard)
    await callback.answer()


@router.callback_query(F.data.startswith("admin:transition:confirm:"))
async def handle_transition_confirm(
    callback: CallbackQuery,
    state: FSMContext,  # noqa: ARG001
    session: AsyncSession,
) -> None:
    """Handle transition confirmation.

    Args:
        callback: Telegram callback.
        state: FSM state.
        session: Database session.
    """
    if not await _require_admin(callback):
        return
    if not callback.data:
        return

    parts = callback.data.split(":")
    if len(parts) < 5:
        await callback.answer(fr.MSG_INVALID_ACTION, show_alert=True)
        return

    try:
        new_year_id = int(parts[4])
    except (ValueError, IndexError):
        await callback.answer(fr.MSG_INVALID_ACTION, show_alert=True)
        return

    from bot.services.academic_year import AcademicYearError, AcademicYearService

    service = AcademicYearService(session)
    try:
        result = await service.transition_to_year(new_year_id)
    except AcademicYearError as e:
        await callback.answer(str(e), show_alert=True)
        return

    new_year = result["new_year"]
    archived_count = result["archived_count"]

    assert hasattr(new_year, "name")

    await _edit_message(
        callback,
        fr.ADMIN_TRANSITION_SUCCESS.format(
            name=new_year.name,
            archived_count=archived_count,
        ),
        get_admin_years_keyboard(),
    )
    await callback.answer()


# ===== CATALOG IMPORT =====


@router.callback_query(F.data == "admin:catalog")
async def handle_catalog_import(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Handle catalog import entry.

    Args:
        callback: Telegram callback.
        state: FSM state.
        session: Database session.
    """
    if not await _require_admin(callback):
        return
    await state.clear()

    from bot.services.academic_year import AcademicYearService

    service = AcademicYearService(session)
    current = await service.get_current_year()

    if current is None:
        await _edit_message(
            callback,
            fr.ADMIN_IMPORT_NO_CURRENT_YEAR,
            get_admin_back_keyboard(),
        )
        await callback.answer()
        return

    await _edit_message(
        callback,
        fr.ADMIN_IMPORT_SEND_FILE,
        get_catalog_import_keyboard(),
    )
    await callback.answer()


@router.message(F.document)
async def handle_document_upload(
    message: Message,
    state: FSMContext,  # noqa: ARG001
    session: AsyncSession,
) -> None:
    """Handle document upload for catalog import.

    Only processes documents from admins.

    Args:
        message: Telegram message.
        state: FSM state.
        session: Database session.
    """
    from bot.config import get_settings

    settings = get_settings()
    if message.from_user is None or message.from_user.id not in settings.bot_admin_ids:
        return

    if not message.document or not message.document.file_name:
        return

    filename = message.document.file_name.lower()
    if not filename.endswith((".xlsx", ".csv")):
        await message.answer(fr.ADMIN_IMPORT_INVALID_FILE)
        return

    await message.answer(fr.ADMIN_IMPORT_PROCESSING)

    # Download file
    try:
        from pathlib import Path

        assert message.bot is not None
        file = await message.bot.get_file(message.document.file_id)
        assert file.file_path is not None
        import tempfile

        suffix = ".xlsx" if filename.endswith(".xlsx") else ".csv"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            await message.bot.download_file(file.file_path, tmp.name)
            tmp_path = tmp.name

        from bot.services.academic_year import AcademicYearService
        from bot.services.catalog.importer import CatalogImportService

        # Get current year
        year_service = AcademicYearService(session)
        current = await year_service.get_current_year()
        if current is None:
            await message.answer(fr.ADMIN_IMPORT_NO_CURRENT_YEAR)
            Path(tmp_path).unlink()
            return

        # Import
        import_service = CatalogImportService(session)
        result = await import_service.import_from_file(tmp_path, current.id)

        Path(tmp_path).unlink()

        if result.errors:
            errors_text = "\n".join(f"• {e}" for e in result.errors)
            await message.answer(
                fr.ADMIN_IMPORT_ERRORS.format(errors=errors_text),
                reply_markup=get_admin_back_keyboard(),
            )
        else:
            await message.answer(
                fr.ADMIN_IMPORT_SUCCESS.format(
                    parsed=result.total_parsed,
                    created=result.total_created,
                    existing=result.total_existing,
                ),
                reply_markup=get_admin_back_keyboard(),
            )
    except Exception:
        logger.exception("Catalog import failed")
        await message.answer(
            fr.MSG_SOMETHING_WENT_WRONG,
            reply_markup=get_admin_back_keyboard(),
        )


# ===== USER MANAGEMENT =====


@router.callback_query(F.data == "admin:users")
async def handle_users_menu(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    """Handle users management menu.

    Args:
        callback: Telegram callback.
        state: FSM state.
    """
    if not await _require_admin(callback):
        return
    await state.clear()
    await _edit_message(
        callback,
        fr.ADMIN_USERS_TITLE,
        get_admin_users_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data == "admin:users:list")
async def handle_users_list(
    callback: CallbackQuery,
    state: FSMContext,  # noqa: ARG001
    session: AsyncSession,
) -> None:
    """Handle users list.

    Args:
        callback: Telegram callback.
        state: FSM state.
        session: Database session.
    """
    if not await _require_admin(callback):
        return
    from bot.services.admin import AdminService

    service = AdminService(session)
    users = await service.list_users()

    if not users:
        await _edit_message(
            callback,
            fr.ADMIN_USERS_TITLE + "\n\nAucun utilisateur.",
            get_admin_users_keyboard(),
        )
        await callback.answer()
        return

    await _edit_message(
        callback,
        fr.ADMIN_USERS_TITLE,
        get_user_list_keyboard(users),
    )
    await callback.answer()


@router.callback_query(F.data == "admin:users:search")
async def handle_users_search_start(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    """Handle start user search.

    Args:
        callback: Telegram callback.
        state: FSM state.
    """
    if not await _require_admin(callback):
        return
    await state.set_state(AdminUserSearchFlow.entering_query)
    await _edit_message(callback, fr.ADMIN_USERS_SEARCH_PROMPT)
    await callback.answer()


@router.message(AdminUserSearchFlow.entering_query)
async def handle_users_search_input(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Handle user search input.

    Args:
        message: Telegram message.
        state: FSM state.
        session: Database session.
    """
    if not message.text:
        return

    query = message.text.strip()
    if not query:
        return

    from bot.services.admin import AdminService

    service = AdminService(session)
    users = await service.search_users(query)

    await state.clear()

    if not users:
        await message.answer(
            "Aucun utilisateur trouvé.",
            reply_markup=get_admin_back_keyboard(),
        )
        return

    await message.answer(
        f"Résultats pour « {query} » :",
        reply_markup=get_user_list_keyboard(users),
    )


@router.callback_query(F.data.startswith("admin:user:"))
async def handle_user_detail(  # noqa: PLR0911
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Handle user detail view.

    Args:
        callback: Telegram callback.
        state: FSM state.
        session: Database session.
    """
    if not await _require_admin(callback):
        return
    if not callback.data:
        return

    parts = callback.data.split(":")
    if len(parts) < 4:
        await callback.answer(fr.MSG_INVALID_ACTION, show_alert=True)
        return

    action = parts[2]

    # Handle ban/unban actions
    if action == "ban":
        await _handle_ban_start(callback, state, session, int(parts[3]))
        return
    if action == "unban":
        await _handle_unban(callback, state, session, int(parts[3]))
        return
    if action == "ban_confirm":
        reason = parts[4] if len(parts) > 4 else "skip"
        await _handle_ban_confirm(callback, state, session, parts[3], reason)
        return

    try:
        user_id = int(parts[2])
    except (ValueError, IndexError):
        await callback.answer(fr.MSG_INVALID_ACTION, show_alert=True)
        return

    from bot.services.admin import AdminService

    service = AdminService(session)
    users = await service.list_users()
    target_user = None
    for u in users:
        if u["id"] == user_id:
            target_user = u
            break

    if target_user is None:
        await callback.answer(fr.MSG_USER_NOT_FOUND, show_alert=True)
        return

    name = (
        target_user.get("username")
        or target_user.get("first_name")
        or str(target_user["telegram_id"])
    )
    ban_status = "🚫 Banni" if target_user["is_banned"] else "✅ Actif"
    role_label = "Administrateur" if target_user["role"] == "admin" else "Utilisateur"

    text = (
        f"👤 {name}\n"
        f"🆔 ID : {target_user['telegram_id']}\n"
        f"📛 Rôle : {role_label}\n"
        f"📊 Statut : {ban_status}"
    )
    if target_user["is_banned"] and target_user.get("ban_reason"):
        text += f"\n📝 Raison : {target_user['ban_reason']}"

    await _edit_message(
        callback,
        text,
        get_user_detail_keyboard(user_id, target_user["is_banned"]),
    )
    await callback.answer()


async def _handle_ban_start(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,  # noqa: ARG001
    user_id: int,
) -> None:
    """Handle ban start - ask for reason.

    Args:
        callback: Telegram callback.
        state: FSM state.
        session: Database session.
        user_id: User ID to ban.
    """
    await state.update_data(ban_user_id=user_id)
    await state.set_state(AdminBanFlow.entering_reason)
    await _edit_message(
        callback,
        fr.ADMIN_USER_BAN_REASON_PROMPT,
        get_ban_reason_keyboard(user_id),
    )
    await callback.answer()


@router.callback_query(AdminBanFlow.entering_reason, F.data.startswith("admin:user:ban_confirm:"))
async def handle_ban_skip_reason(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Handle skip ban reason.

    Args:
        callback: Telegram callback.
        state: FSM state.
        session: Database session.
    """
    if not await _require_admin(callback):
        return
    if not callback.data:
        return

    parts = callback.data.split(":")
    user_id = int(parts[3])
    await _handle_ban_confirm(callback, state, session, str(user_id), "skip")


@router.message(AdminBanFlow.entering_reason)
async def handle_ban_reason_input(
    message: Message,
    state: FSMContext,
) -> None:
    """Handle ban reason input.

    Args:
        message: Telegram message.
        state: FSM state.
    """
    if not message.text:
        return

    reason = message.text.strip()
    if reason == "-":
        reason = ""

    data = await state.get_data()
    user_id = data["ban_user_id"]

    await state.set_state(AdminBanFlow.confirming)
    confirm_text = f"Confirmer le bannissement de l'utilisateur #{user_id}" + (
        f"\nRaison : {reason}" if reason else ""
    )
    await message.answer(
        confirm_text,
        reply_markup=get_confirm_ban_keyboard(user_id, reason or "skip"),
    )


async def _handle_ban_confirm(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
    user_id_str: str,
    reason: str,
) -> None:
    """Handle ban confirmation.

    Args:
        callback: Telegram callback.
        state: FSM state.
        session: Database session.
        user_id_str: User ID as string.
        reason: Ban reason or "skip".
    """
    try:
        user_id = int(user_id_str)
    except ValueError:
        await callback.answer(fr.MSG_INVALID_ACTION, show_alert=True)
        return

    ban_reason = None if reason == "skip" else reason

    from bot.services.admin import AdminError, AdminService

    service = AdminService(session)
    try:
        result = await service.ban_user(
            admin_telegram_id=callback.from_user.id if callback.from_user else 0,
            target_user_id=user_id,
            reason=ban_reason,
        )
    except AdminError as e:
        await callback.answer(str(e), show_alert=True)
        return

    await state.clear()
    username = result.get("username") or str(result["telegram_id"])
    await _edit_message(
        callback,
        fr.ADMIN_USER_BANNED_SUCCESS.format(username=username),
        get_admin_users_keyboard(),
    )
    await callback.answer()


async def _handle_unban(
    callback: CallbackQuery,
    state: FSMContext,  # noqa: ARG001
    session: AsyncSession,
    user_id: int,
) -> None:
    """Handle unban user.

    Args:
        callback: Telegram callback.
        state: FSM state.
        session: Database session.
        user_id: User ID to unban.
    """
    from bot.services.admin import AdminError, AdminService

    service = AdminService(session)
    try:
        result = await service.unban_user(user_id)
    except AdminError as e:
        await callback.answer(str(e), show_alert=True)
        return

    username = result.get("username") or str(result["telegram_id"])
    await _edit_message(
        callback,
        fr.ADMIN_USER_UNBANNED_SUCCESS.format(username=username),
        get_admin_users_keyboard(),
    )
    await callback.answer()


# ===== HELPERS =====


def _parse_date(text: str) -> date | None:
    """Parse a date from DD/MM/YYYY format.

    Args:
        text: Date string.

    Returns:
        Parsed date or None if invalid.
    """
    try:
        parts = text.split("/")
        if len(parts) != 3:
            return None
        day, month, year = int(parts[0]), int(parts[1]), int(parts[2])
        return date(year, month, day)
    except (ValueError, IndexError):
        return None
