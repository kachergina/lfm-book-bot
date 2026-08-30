"""Listing management keyboards."""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from bot.locale import fr


def get_condition_keyboard() -> InlineKeyboardMarkup:
    """Get condition selection keyboard.

    Returns:
        Inline keyboard with condition options.
    """
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=label,
                    callback_data=f"sell:cond:{key}",
                )
            ]
            for key, label in fr.CONDITION_CALLBACK_LABELS.items()
        ]
        + [[InlineKeyboardButton(text=fr.BTN_BACK, callback_data="sell:back:price")]]
    )


def get_contact_method_keyboard() -> InlineKeyboardMarkup:
    """Get contact method selection keyboard for the sell flow.

    Returns:
        Inline keyboard with phone and telegram options.
    """
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=fr.SELL_CONTACT_METHOD_PHONE,
                    callback_data="sell:contact:phone",
                ),
            ],
            [
                InlineKeyboardButton(
                    text=fr.SELL_CONTACT_METHOD_TELEGRAM,
                    callback_data="sell:contact:telegram",
                ),
            ],
            [InlineKeyboardButton(text=fr.BTN_BACK, callback_data="sell:back:condition")],
        ]
    )


def get_manage_contact_method_keyboard(listing_id: int) -> InlineKeyboardMarkup:
    """Get contact method selection keyboard for listing management."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=fr.SELL_CONTACT_METHOD_PHONE,
                    callback_data="sell:contact:phone",
                ),
            ],
            [
                InlineKeyboardButton(
                    text=fr.SELL_CONTACT_METHOD_TELEGRAM,
                    callback_data="sell:contact:telegram",
                ),
            ],
            [
                InlineKeyboardButton(
                    text=fr.BTN_BACK_TO_MANAGE,
                    callback_data=f"ml:{listing_id}:back:manage",
                ),
            ],
        ]
    )


def get_sell_confirm_keyboard() -> InlineKeyboardMarkup:
    """Get sell flow confirmation keyboard.

    Returns:
        Inline keyboard with confirm/edit/cancel options.
    """
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Publier", callback_data="sell:confirm:publish")],
            [
                InlineKeyboardButton(text=fr.SELL_EDIT_PRICE, callback_data="sell:edit:price"),
            ],
            [
                InlineKeyboardButton(
                    text=fr.SELL_EDIT_CONDITION, callback_data="sell:edit:condition"
                ),
            ],
            [
                InlineKeyboardButton(text=fr.SELL_EDIT_PHONE, callback_data="sell:edit:phone"),
            ],
            [
                InlineKeyboardButton(
                    text=fr.SELL_EDIT_DESCRIPTION,
                    callback_data="sell:edit:description",
                ),
            ],
            [
                InlineKeyboardButton(text=fr.SELL_EDIT_PHOTOS, callback_data="sell:edit:photos"),
            ],
            [InlineKeyboardButton(text="❌ Annuler", callback_data="sell:confirm:cancel")],
        ]
    )


def get_photos_initial_keyboard() -> InlineKeyboardMarkup:
    """Get photos upload initial keyboard (no photos yet).

    Returns:
        Inline keyboard with only skip option.
    """
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⏭️ Ignorer", callback_data="sell:photos:skip")],
        ]
    )


def get_photos_received_keyboard() -> InlineKeyboardMarkup:
    """Get photos upload keyboard shown after receiving a photo.

    Returns:
        Inline keyboard with only done option.
    """
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Terminé", callback_data="sell:photos:done")],
        ]
    )


def get_description_action_keyboard() -> InlineKeyboardMarkup:
    """Get description input action keyboard.

    Returns:
        Inline keyboard with skip option.
    """
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⏭️ Ignorer", callback_data="sell:desc:skip")],
        ]
    )


def get_my_listings_tabs_keyboard(
    active_count: int = 0,
    reserved_count: int = 0,
    sold_count: int = 0,
    archived_count: int = 0,
) -> InlineKeyboardMarkup:
    """Get my listings tab keyboard.

    Args:
        active_count: Number of active listings.
        reserved_count: Number of reserved listings.
        sold_count: Number of sold listings.
        archived_count: Number of archived listings.

    Returns:
        Inline keyboard with tab buttons.
    """
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=fr.MY_LISTINGS_TAB_ACTIVE.format(count=active_count),
                    callback_data="mylistings:tab:active",
                ),
            ],
            [
                InlineKeyboardButton(
                    text=fr.MY_LISTINGS_TAB_RESERVED.format(count=reserved_count),
                    callback_data="mylistings:tab:reserved",
                ),
            ],
            [
                InlineKeyboardButton(
                    text=fr.MY_LISTINGS_TAB_SOLD.format(count=sold_count),
                    callback_data="mylistings:tab:sold",
                ),
            ],
            [
                InlineKeyboardButton(
                    text=fr.MY_LISTINGS_TAB_ARCHIVED.format(count=archived_count),
                    callback_data="mylistings:tab:archived",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="➕ Nouvelle annonce",
                    callback_data="mylistings:new",
                ),
            ],
            [
                InlineKeyboardButton(
                    text=fr.BTN_MAIN_MENU,
                    callback_data="mylistings:menu",
                ),
            ],
        ]
    )


def get_listings_list_keyboard(
    listings: list[dict],
    status: str,  # noqa: ARG001
) -> InlineKeyboardMarkup:
    """Get listings list keyboard for a specific status.

    Args:
        listings: List of listing dicts with 'id', 'title', 'price'.
        status: Current status filter.

    Returns:
        Inline keyboard with listing buttons.
    """
    keyboard: list[list[InlineKeyboardButton]] = []
    for listing in listings:
        label = f"{listing['title']} - {listing['price']} ₽"
        keyboard.append(
            [
                InlineKeyboardButton(
                    text=label,
                    callback_data=f"mylistings:view:{listing['id']}",
                ),
            ]
        )

    keyboard.append(
        [
            InlineKeyboardButton(
                text=fr.BTN_BACK,
                callback_data="mylistings:back:tabs",
            ),
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_listing_manage_keyboard(listing_id: int, status: str) -> InlineKeyboardMarkup:
    """Get listing management action keyboard.

    Args:
        listing_id: Listing ID.
        status: Current listing status.

    Returns:
        Inline keyboard with management actions.
    """
    buttons: list[list[InlineKeyboardButton]] = []

    # Always allow editing
    buttons.append(
        [
            InlineKeyboardButton(
                text=fr.BTN_EDIT_PRICE,
                callback_data=f"ml:{listing_id}:edit_price",
            )
        ]
    )
    buttons.append(
        [
            InlineKeyboardButton(
                text=fr.BTN_EDIT_CONDITION,
                callback_data=f"ml:{listing_id}:edit_condition",
            )
        ]
    )
    buttons.append(
        [
            InlineKeyboardButton(
                text=fr.BTN_EDIT_PHONE,
                callback_data=f"ml:{listing_id}:edit_phone",
            )
        ]
    )
    buttons.append(
        [
            InlineKeyboardButton(
                text=fr.BTN_EDIT_DESCRIPTION,
                callback_data=f"ml:{listing_id}:edit_desc",
            )
        ]
    )
    buttons.append(
        [
            InlineKeyboardButton(
                text=fr.BTN_EDIT_PHOTOS,
                callback_data=f"ml:{listing_id}:edit_photos",
            )
        ]
    )

    # Status-specific actions
    if status == "active":
        buttons.append(
            [
                InlineKeyboardButton(
                    text=fr.BTN_MARK_RESERVED,
                    callback_data=f"ml:{listing_id}:reserve",
                )
            ]
        )
        buttons.append(
            [
                InlineKeyboardButton(
                    text=fr.BTN_MARK_SOLD,
                    callback_data=f"ml:{listing_id}:sell",
                )
            ]
        )
        buttons.append(
            [
                InlineKeyboardButton(
                    text=fr.BTN_ARCHIVE,
                    callback_data=f"ml:{listing_id}:archive",
                )
            ]
        )
    elif status == "reserved":
        buttons.append(
            [
                InlineKeyboardButton(
                    text=fr.BTN_MARK_ACTIVE,
                    callback_data=f"ml:{listing_id}:activate",
                )
            ]
        )
        buttons.append(
            [
                InlineKeyboardButton(
                    text=fr.BTN_MARK_SOLD,
                    callback_data=f"ml:{listing_id}:sell",
                )
            ]
        )
        buttons.append(
            [
                InlineKeyboardButton(
                    text=fr.BTN_ARCHIVE,
                    callback_data=f"ml:{listing_id}:archive",
                )
            ]
        )

    buttons.append(
        [
            InlineKeyboardButton(
                text=fr.BTN_BACK_TO_LISTINGS,
                callback_data=f"mylistings:tab:{status}",
            )
        ]
    )

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_confirm_status_keyboard(
    listing_id: int,
    action: str,
) -> InlineKeyboardMarkup:
    """Get confirmation keyboard for status change.

    Args:
        listing_id: Listing ID.
        action: Action being confirmed.

    Returns:
        Inline keyboard with confirm/cancel.
    """
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Confirmer",
                    callback_data=f"ml:{listing_id}:confirm:{action}",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="❌ Annuler",
                    callback_data=f"ml:{listing_id}:cancel",
                ),
            ],
        ]
    )


def get_edit_photos_menu_keyboard(listing_id: int) -> InlineKeyboardMarkup:
    """Get photo editing submenu for listing management."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=fr.BTN_ADD_PHOTOS,
                    callback_data=f"ml:{listing_id}:photos:add",
                ),
            ],
            [
                InlineKeyboardButton(
                    text=fr.BTN_DELETE_PHOTOS,
                    callback_data=f"ml:{listing_id}:photos:delete",
                ),
            ],
            [
                InlineKeyboardButton(
                    text=fr.BTN_BACK_TO_MANAGE,
                    callback_data=f"ml:{listing_id}:back:manage",
                ),
            ],
        ]
    )


def get_manage_photos_add_keyboard(listing_id: int) -> InlineKeyboardMarkup:
    """Get keyboard while adding photos to an existing listing."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Terminé",
                    callback_data=f"ml:{listing_id}:photos:done_add",
                ),
            ],
            [
                InlineKeyboardButton(
                    text=fr.BTN_BACK,
                    callback_data=f"ml:{listing_id}:back:photos_menu",
                ),
            ],
        ]
    )


def get_manage_photos_delete_keyboard(
    listing_id: int,
    photos: list[str],
) -> InlineKeyboardMarkup:
    """Get keyboard for selecting a specific photo to delete."""
    keyboard: list[list[InlineKeyboardButton]] = []
    for index, _photo in enumerate(photos, start=1):
        keyboard.append(
            [
                InlineKeyboardButton(
                    text=fr.MANAGE_PHOTO_DELETE_LABEL.format(number=index),
                    callback_data=f"ml:{listing_id}:photos:del:{index - 1}",
                ),
            ]
        )
    keyboard.append(
        [
            InlineKeyboardButton(
                text=fr.BTN_BACK,
                callback_data=f"ml:{listing_id}:back:photos_menu",
            ),
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=keyboard)
