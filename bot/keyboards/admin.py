"""Admin panel keyboards."""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from bot.locale import fr


def get_admin_panel_keyboard() -> InlineKeyboardMarkup:
    """Get admin panel main keyboard.

    Returns:
        Inline keyboard with admin options.
    """
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=fr.ADMIN_PANEL_CATALOG, callback_data="admin:catalog")],
            [InlineKeyboardButton(text=fr.ADMIN_PANEL_YEARS, callback_data="admin:years")],
            [InlineKeyboardButton(text=fr.ADMIN_PANEL_USERS, callback_data="admin:users")],
            [InlineKeyboardButton(text=fr.ADMIN_PANEL_STATS, callback_data="admin:stats")],
        ]
    )


def get_admin_years_keyboard() -> InlineKeyboardMarkup:
    """Get academic years management keyboard.

    Returns:
        Inline keyboard with year management options.
    """
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=fr.ADMIN_TRANSITION_TITLE,
                    callback_data="admin:years:transition",
                ),
            ],
            [
                InlineKeyboardButton(
                    text=fr.ADMIN_YEARS_CREATE,
                    callback_data="admin:years:create",
                ),
            ],
            [
                InlineKeyboardButton(
                    text=fr.ADMIN_BTN_BACK_PANEL,
                    callback_data="admin:back:panel",
                ),
            ],
        ]
    )


def get_years_list_keyboard(years: list[dict]) -> InlineKeyboardMarkup:
    """Get keyboard listing all academic years.

    Args:
        years: List of year dicts with 'id', 'name', 'is_current'.

    Returns:
        Inline keyboard with year buttons.
    """
    keyboard: list[list[InlineKeyboardButton]] = []
    for year in years:
        badge = "📌 " if year["is_current"] else ""
        keyboard.append(
            [
                InlineKeyboardButton(
                    text=f"{badge}{year['name']}",
                    callback_data=f"admin:year:{year['id']}",
                ),
            ]
        )
    keyboard.append(
        [
            InlineKeyboardButton(
                text=fr.ADMIN_BTN_BACK_PANEL,
                callback_data="admin:back:panel",
            ),
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_year_detail_keyboard(year_id: int, is_current: bool) -> InlineKeyboardMarkup:
    """Get keyboard for a specific year detail.

    Args:
        year_id: Academic year ID.
        is_current: Whether this year is current.

    Returns:
        Inline keyboard with year actions.
    """
    buttons: list[list[InlineKeyboardButton]] = []
    if not is_current:
        buttons.append(
            [
                InlineKeyboardButton(
                    text=fr.ADMIN_YEARS_SET_CURRENT,
                    callback_data=f"admin:year:set_current:{year_id}",
                ),
            ]
        )
    buttons.append(
        [
            InlineKeyboardButton(
                text=fr.ADMIN_BTN_BACK_YEARS,
                callback_data="admin:years:list",
            ),
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_transition_confirm_keyboard(
    old_year_id: int,
    new_year_id: int,
) -> InlineKeyboardMarkup:
    """Get transition confirmation keyboard.

    Args:
        old_year_id: Current year ID.
        new_year_id: Target year ID.

    Returns:
        Inline keyboard with confirm/cancel.
    """
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Confirmer",
                    callback_data=f"admin:transition:confirm:{old_year_id}:{new_year_id}",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="❌ Annuler",
                    callback_data="admin:years:list",
                ),
            ],
        ]
    )


def get_admin_users_keyboard() -> InlineKeyboardMarkup:
    """Get user management keyboard.

    Returns:
        Inline keyboard with user management options.
    """
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=fr.ADMIN_USERS_LIST,
                    callback_data="admin:users:list",
                ),
            ],
            [
                InlineKeyboardButton(
                    text=fr.ADMIN_USERS_SEARCH,
                    callback_data="admin:users:search",
                ),
            ],
            [
                InlineKeyboardButton(
                    text=fr.ADMIN_BTN_BACK_PANEL,
                    callback_data="admin:back:panel",
                ),
            ],
        ]
    )


def get_user_list_keyboard(users: list[dict]) -> InlineKeyboardMarkup:
    """Get keyboard listing users.

    Args:
        users: List of user dicts.

    Returns:
        Inline keyboard with user buttons.
    """
    keyboard: list[list[InlineKeyboardButton]] = []
    for u in users:
        name = u.get("username") or u.get("first_name") or str(u["telegram_id"])
        ban_badge = "🚫 " if u.get("is_banned") else ""
        keyboard.append(
            [
                InlineKeyboardButton(
                    text=f"{ban_badge}{name}",
                    callback_data=f"admin:user:{u['id']}",
                ),
            ]
        )
    keyboard.append(
        [
            InlineKeyboardButton(
                text=fr.ADMIN_BTN_BACK_USERS,
                callback_data="admin:users",
            ),
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_user_detail_keyboard(user_id: int, is_banned: bool) -> InlineKeyboardMarkup:
    """Get keyboard for a specific user detail.

    Args:
        user_id: Internal user ID.
        is_banned: Whether the user is banned.

    Returns:
        Inline keyboard with user actions.
    """
    buttons: list[list[InlineKeyboardButton]] = []
    if is_banned:
        buttons.append(
            [
                InlineKeyboardButton(
                    text=fr.ADMIN_USER_UNBAN,
                    callback_data=f"admin:user:unban:{user_id}",
                ),
            ]
        )
    else:
        buttons.append(
            [
                InlineKeyboardButton(
                    text=fr.ADMIN_USER_BAN,
                    callback_data=f"admin:user:ban:{user_id}",
                ),
            ]
        )
    buttons.append(
        [
            InlineKeyboardButton(
                text=fr.ADMIN_BTN_BACK_USERS,
                callback_data="admin:users:list",
            ),
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_ban_reason_keyboard(user_id: int) -> InlineKeyboardMarkup:
    """Get ban reason skip keyboard.

    Args:
        user_id: User ID to ban.

    Returns:
        Inline keyboard with skip option.
    """
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⏭️ Sans raison",
                    callback_data=f"admin:user:ban_confirm:{user_id}:skip",
                ),
            ],
        ]
    )


def get_confirm_ban_keyboard(
    user_id: int,
    reason: str,
) -> InlineKeyboardMarkup:
    """Get ban confirmation keyboard.

    Args:
        user_id: User ID to ban.
        reason: Ban reason (or "skip").

    Returns:
        Inline keyboard with confirm/cancel.
    """
    reason_param = reason if reason else "skip"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Confirmer le bannissement",
                    callback_data=f"admin:user:ban_confirm:{user_id}:{reason_param}",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="❌ Annuler",
                    callback_data=f"admin:user:{user_id}",
                ),
            ],
        ]
    )


def get_year_create_confirm_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Oui", callback_data="admin:year:create:confirm")],
            [InlineKeyboardButton(text="✏️ Modifier", callback_data="admin:year:create:modify")],
        ]
    )


def get_catalog_import_keyboard() -> InlineKeyboardMarkup:
    """Get catalog import keyboard.

    Returns:
        Inline keyboard for catalog import.
    """
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=fr.ADMIN_BTN_BACK_PANEL,
                    callback_data="admin:back:panel",
                ),
            ],
        ]
    )


def get_admin_back_keyboard() -> InlineKeyboardMarkup:
    """Get simple back to admin panel keyboard.

    Returns:
        Inline keyboard with back button.
    """
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=fr.ADMIN_BTN_BACK_PANEL,
                    callback_data="admin:back:panel",
                ),
            ],
        ]
    )
