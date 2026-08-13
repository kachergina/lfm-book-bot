"""Tests for catalog keyboards."""

from bot.keyboards.catalog import (
    get_book_keyboard,
    get_category_keyboard,
    get_grade_keyboard,
    get_listings_keyboard,
    get_subject_keyboard,
)
from bot.locale import fr


def test_category_keyboard():
    """Test category keyboard has correct buttons."""
    keyboard = get_category_keyboard()
    assert len(keyboard.inline_keyboard) == 3

    # First row: textbook
    assert keyboard.inline_keyboard[0][0].text == fr.CATEGORY_TEXTBOOK
    assert keyboard.inline_keyboard[0][0].callback_data == "buy:cat:textbook"

    # Second row: literature
    assert keyboard.inline_keyboard[1][0].text == fr.CATEGORY_LITERATURE
    assert keyboard.inline_keyboard[1][0].callback_data == "buy:cat:literature"

    # Third row: back
    assert keyboard.inline_keyboard[2][0].text == fr.BTN_BACK
    assert keyboard.inline_keyboard[2][0].callback_data == "buy:back:menu"


def test_grade_keyboard():
    """Test grade keyboard has correct buttons."""
    grades = ["6ème", "5ème", "4ème"]
    keyboard = get_grade_keyboard(grades)

    # 3 grades + 1 back button
    assert len(keyboard.inline_keyboard) == 4

    for i, grade in enumerate(grades):
        assert keyboard.inline_keyboard[i][0].text == grade
        assert keyboard.inline_keyboard[i][0].callback_data == f"buy:grade:{grade}"

    # Back button
    assert keyboard.inline_keyboard[3][0].text == fr.BTN_BACK
    assert keyboard.inline_keyboard[3][0].callback_data == "buy:back:category"


def test_grade_keyboard_single():
    """Test grade keyboard with single grade."""
    keyboard = get_grade_keyboard(["Terminale"])
    assert len(keyboard.inline_keyboard) == 2
    assert keyboard.inline_keyboard[0][0].text == "Terminale"


def test_subject_keyboard():
    """Test subject keyboard has correct buttons."""
    subjects = ["Mathématiques", "Français"]
    keyboard = get_subject_keyboard(subjects)

    assert len(keyboard.inline_keyboard) == 3

    assert keyboard.inline_keyboard[0][0].text == "Mathématiques"
    assert keyboard.inline_keyboard[0][0].callback_data == "buy:subj:Mathématiques"

    assert keyboard.inline_keyboard[1][0].text == "Français"
    assert keyboard.inline_keyboard[1][0].callback_data == "buy:subj:Français"

    assert keyboard.inline_keyboard[2][0].text == fr.BTN_BACK
    assert keyboard.inline_keyboard[2][0].callback_data == "buy:back:grade"


def test_book_keyboard():
    """Test book keyboard has correct buttons."""
    books = [
        {"id": 1, "title": "Math 6eme", "author": "Author A"},
        {"id": 2, "title": "Math 6eme Exercices", "author": None},
    ]
    keyboard = get_book_keyboard(books)

    assert len(keyboard.inline_keyboard) == 3

    # First book
    assert keyboard.inline_keyboard[0][0].text == "Math 6eme - Author A"
    assert keyboard.inline_keyboard[0][0].callback_data == "buy:book:1"

    # Second book (no author)
    assert keyboard.inline_keyboard[1][0].text == "Math 6eme Exercices"
    assert keyboard.inline_keyboard[1][0].callback_data == "buy:book:2"

    # Back button
    assert keyboard.inline_keyboard[2][0].text == fr.BTN_BACK
    assert keyboard.inline_keyboard[2][0].callback_data == "buy:back:subject"


def test_book_keyboard_empty():
    """Test book keyboard with empty list."""
    keyboard = get_book_keyboard([])
    assert len(keyboard.inline_keyboard) == 1  # Only back button
    assert keyboard.inline_keyboard[0][0].callback_data == "buy:back:subject"


def test_listings_keyboard():
    """Test listings keyboard has correct buttons."""
    keyboard = get_listings_keyboard(book_id=42)

    assert len(keyboard.inline_keyboard) == 2

    assert keyboard.inline_keyboard[0][0].text == fr.BTN_BACK
    assert keyboard.inline_keyboard[0][0].callback_data == "buy:back:book_list"

    assert keyboard.inline_keyboard[1][0].text == fr.BTN_MAIN_MENU
    assert keyboard.inline_keyboard[1][0].callback_data == "buy:back:menu"
