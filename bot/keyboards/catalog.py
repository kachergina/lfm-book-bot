"""Catalog browsing keyboards."""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from bot.locale import fr


def get_category_keyboard() -> InlineKeyboardMarkup:
    """Get category selection keyboard.

    Returns:
        Inline keyboard with category options.
    """
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=fr.CATEGORY_TEXTBOOK, callback_data="buy:cat:textbook")],
            [InlineKeyboardButton(text=fr.CATEGORY_LITERATURE, callback_data="buy:cat:literature")],
            [InlineKeyboardButton(text=fr.CATEGORY_OTHER, callback_data="buy:cat:other")],
            [InlineKeyboardButton(text=fr.BTN_BACK, callback_data="buy:back:menu")],
        ],
    )


def get_sell_category_keyboard() -> InlineKeyboardMarkup:
    """Get category selection keyboard for the sell flow."""
    return get_category_keyboard()


def get_custom_title_keyboard() -> InlineKeyboardMarkup:
    """Get keyboard for custom book title entry in the sell flow."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=fr.BTN_BACK, callback_data="buy:back:category")],
        ],
    )


_GRADE_ORDER = {"6ème": 0, "5ème": 1, "4ème": 2, "3ème": 3, "2nde": 4, "1ère": 5, "Terminale": 6}


def get_grade_keyboard(grades: list[str]) -> InlineKeyboardMarkup:
    """Get grade level selection keyboard.

    Grades are displayed in ascending class order:
    6ème, 5ème, 4ème, 3ème, 2nde, 1ère, Terminale.

    Args:
        grades: List of available grade levels.

    Returns:
        Inline keyboard with grade options.
    """
    sorted_grades = sorted(grades, key=lambda g: _GRADE_ORDER.get(g, 99))
    keyboard: list[list[InlineKeyboardButton]] = []
    for grade in sorted_grades:
        keyboard.append(
            [
                InlineKeyboardButton(
                    text=grade,
                    callback_data=f"buy:grade:{grade}",
                ),
            ]
        )
    keyboard.append([InlineKeyboardButton(text=fr.BTN_BACK, callback_data="buy:back:category")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_subject_keyboard(subjects: list[str]) -> InlineKeyboardMarkup:
    """Get subject selection keyboard.

    Args:
        subjects: List of available subjects.

    Returns:
        Inline keyboard with subject options.
    """
    keyboard: list[list[InlineKeyboardButton]] = []
    for subject in subjects:
        keyboard.append(
            [
                InlineKeyboardButton(
                    text=subject,
                    callback_data=f"buy:subj:{subject}",
                ),
            ]
        )
    keyboard.append([InlineKeyboardButton(text=fr.BTN_BACK, callback_data="buy:back:grade")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_book_keyboard(
    books: list[dict],
    back_callback: str = "buy:back:subject",
) -> InlineKeyboardMarkup:
    """Get book selection keyboard.

    Args:
        books: List of book dicts with 'id', 'title', 'author'.
        back_callback: Callback data for the back button.

    Returns:
        Inline keyboard with book options.
    """
    keyboard: list[list[InlineKeyboardButton]] = []
    for book in books:
        title = book["title"]
        author = book.get("author")
        label = f"{title}" if not author else f"{title} - {author}"
        keyboard.append(
            [
                InlineKeyboardButton(
                    text=label,
                    callback_data=f"buy:book:{book['id']}",
                ),
            ]
        )
    keyboard.append([InlineKeyboardButton(text=fr.BTN_BACK, callback_data=back_callback)])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_listings_keyboard(book_id: int) -> InlineKeyboardMarkup:  # noqa: ARG001
    """Get listings view keyboard with back button.

    Args:
        book_id: Book ID for back navigation.

    Returns:
        Inline keyboard with back option.
    """
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=fr.BTN_BACK, callback_data="buy:back:book_list")],
            [InlineKeyboardButton(text=fr.BTN_MAIN_MENU, callback_data="buy:back:menu")],
        ],
    )


def get_listing_detail_keyboard(
    listing_id: int,
    has_photos: bool,
    book_id: int,  # noqa: ARG001
) -> InlineKeyboardMarkup:
    """Get keyboard for a single listing detail message.

    Args:
        listing_id: Listing ID for photo callback.
        has_photos: Whether the listing has photos.
        book_id: Book ID for back navigation.

    Returns:
        Inline keyboard with optional photo button.
    """
    keyboard: list[list[InlineKeyboardButton]] = []

    if has_photos:
        keyboard.append(
            [
                InlineKeyboardButton(
                    text=fr.BUY_BTN_VIEW_PHOTOS,
                    callback_data=f"buy:photos:{listing_id}",
                ),
            ],
        )

    keyboard.append(
        [InlineKeyboardButton(text=fr.BTN_BACK, callback_data="buy:back:book_list")],
    )
    keyboard.append(
        [InlineKeyboardButton(text=fr.BTN_MAIN_MENU, callback_data="buy:back:menu")],
    )
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_photo_nav_keyboard(book_id: int) -> InlineKeyboardMarkup:
    """Get navigation keyboard shown after photo media group.

    Args:
        book_id: Book ID for back navigation.

    Returns:
        Inline keyboard with back and menu buttons on one row.
    """
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=fr.BTN_BACK,
                    callback_data=f"buy:photos:back:{book_id}",
                ),
                InlineKeyboardButton(
                    text=fr.BTN_MAIN_MENU,
                    callback_data="buy:photos:menu",
                ),
            ],
        ],
    )
