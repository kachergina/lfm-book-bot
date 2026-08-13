"""Tests for browsing repository methods."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.models import AcademicYear, Listing, User
from bot.database.repository import BookRepository, ListingRepository


@pytest.mark.asyncio
async def test_get_categories(
    db_session: AsyncSession,
    academic_year: AcademicYear,
):
    """Test getting categories for an academic year."""
    repo = BookRepository(db_session)

    # Create books with different categories
    await repo.create(
        category="textbook",
        title="Math Book",
        catalog_year_id=academic_year.id,
    )
    await repo.create(
        category="literature",
        title="Novel",
        catalog_year_id=academic_year.id,
    )
    await db_session.commit()

    categories = await repo.get_categories(academic_year.id)
    assert sorted(categories) == ["literature", "textbook"]


@pytest.mark.asyncio
async def test_get_categories_empty(
    db_session: AsyncSession,
    academic_year: AcademicYear,
):
    """Test getting categories when none exist."""
    repo = BookRepository(db_session)
    categories = await repo.get_categories(academic_year.id)
    assert categories == []


@pytest.mark.asyncio
async def test_get_grade_levels(
    db_session: AsyncSession,
    academic_year: AcademicYear,
):
    """Test getting grade levels for a category."""
    repo = BookRepository(db_session)

    await repo.create(
        category="textbook",
        title="Math 6eme",
        catalog_year_id=academic_year.id,
        grade_level="6ème",
    )
    await repo.create(
        category="textbook",
        title="Math 5eme",
        catalog_year_id=academic_year.id,
        grade_level="5ème",
    )
    await repo.create(
        category="literature",
        title="Novel",
        catalog_year_id=academic_year.id,
        grade_level=None,
    )
    await db_session.commit()

    grades = await repo.get_grade_levels(academic_year.id, "textbook")
    assert sorted(grades) == ["5ème", "6ème"]


@pytest.mark.asyncio
async def test_get_grade_levels_filters_category(
    db_session: AsyncSession,
    academic_year: AcademicYear,
):
    """Test that grade levels are filtered by category."""
    repo = BookRepository(db_session)

    await repo.create(
        category="textbook",
        title="Math 6eme",
        catalog_year_id=academic_year.id,
        grade_level="6ème",
    )
    await repo.create(
        category="literature",
        title="Novel 6eme",
        catalog_year_id=academic_year.id,
        grade_level="6ème",
    )
    await db_session.commit()

    grades_textbook = await repo.get_grade_levels(academic_year.id, "textbook")
    grades_literature = await repo.get_grade_levels(academic_year.id, "literature")

    assert grades_textbook == ["6ème"]
    assert grades_literature == ["6ème"]


@pytest.mark.asyncio
async def test_get_subjects(
    db_session: AsyncSession,
    academic_year: AcademicYear,
):
    """Test getting subjects for a category and grade level."""
    repo = BookRepository(db_session)

    await repo.create(
        category="textbook",
        title="Math 6eme",
        catalog_year_id=academic_year.id,
        grade_level="6ème",
        subject="Mathématiques",
    )
    await repo.create(
        category="textbook",
        title="Francais 6eme",
        catalog_year_id=academic_year.id,
        grade_level="6ème",
        subject="Français",
    )
    await repo.create(
        category="textbook",
        title="Math 5eme",
        catalog_year_id=academic_year.id,
        grade_level="5ème",
        subject="Mathématiques",
    )
    await db_session.commit()

    subjects = await repo.get_subjects(academic_year.id, "textbook", "6ème")
    assert sorted(subjects) == ["Français", "Mathématiques"]


@pytest.mark.asyncio
async def test_get_subjects_filters_correctly(
    db_session: AsyncSession,
    academic_year: AcademicYear,
):
    """Test that subjects are filtered by both category and grade."""
    repo = BookRepository(db_session)

    await repo.create(
        category="textbook",
        title="Math 6eme",
        catalog_year_id=academic_year.id,
        grade_level="6ème",
        subject="Mathématiques",
    )
    await repo.create(
        category="literature",
        title="Novel 6eme",
        catalog_year_id=academic_year.id,
        grade_level="6ème",
        subject="Littérature",
    )
    await db_session.commit()

    subjects_textbook = await repo.get_subjects(academic_year.id, "textbook", "6ème")
    subjects_literature = await repo.get_subjects(academic_year.id, "literature", "6ème")

    assert subjects_textbook == ["Mathématiques"]
    assert subjects_literature == ["Littérature"]


@pytest.mark.asyncio
async def test_get_books_for_browsing(
    db_session: AsyncSession,
    academic_year: AcademicYear,
):
    """Test getting books for browsing."""
    repo = BookRepository(db_session)

    book1 = await repo.create(
        category="textbook",
        title="Math 6eme",
        catalog_year_id=academic_year.id,
        grade_level="6ème",
        subject="Mathématiques",
    )
    book2 = await repo.create(
        category="textbook",
        title="Math 6eme - Exercices",
        catalog_year_id=academic_year.id,
        grade_level="6ème",
        subject="Mathématiques",
    )
    await repo.create(
        category="textbook",
        title="Francais 6eme",
        catalog_year_id=academic_year.id,
        grade_level="6ème",
        subject="Français",
    )
    await db_session.commit()

    books = await repo.get_books_for_browsing(
        academic_year.id,
        "textbook",
        "6ème",
        "Mathématiques",
    )
    book_ids = [b.id for b in books]
    assert book1.id in book_ids
    assert book2.id in book_ids
    assert len(books) == 2


@pytest.mark.asyncio
async def test_get_books_for_browsing_empty(
    db_session: AsyncSession,
    academic_year: AcademicYear,
):
    """Test getting books when none match."""
    repo = BookRepository(db_session)
    books = await repo.get_books_for_browsing(
        academic_year.id,
        "textbook",
        "6ème",
        "Mathématiques",
    )
    assert books == []


@pytest.mark.asyncio
async def test_get_active_for_book(
    db_session: AsyncSession,
    academic_year: AcademicYear,
    user: User,
):
    """Test getting active listings for a book."""
    book_repo = BookRepository(db_session)
    listing_repo = ListingRepository(db_session)

    book = await book_repo.create(
        category="textbook",
        title="Math 6eme",
        catalog_year_id=academic_year.id,
    )
    await db_session.commit()

    # Create active listing
    listing1 = Listing(
        book_id=book.id,
        seller_id=user.id,
        academic_year_id=academic_year.id,
        price=15.00,
        condition="good",
        status="active",
        contact_phone="0612345678",
    )
    db_session.add(listing1)

    # Create sold listing (should not appear)
    listing2 = Listing(
        book_id=book.id,
        seller_id=user.id,
        academic_year_id=academic_year.id,
        price=20.00,
        condition="new",
        status="sold",
        contact_phone="0612345679",
    )
    db_session.add(listing2)
    await db_session.commit()

    active_listings = await listing_repo.get_active_for_book(book.id, academic_year.id)
    assert len(active_listings) == 1
    assert active_listings[0].id == listing1.id
    assert active_listings[0].seller.telegram_id == 123456789


@pytest.mark.asyncio
async def test_get_active_for_book_no_listings(
    db_session: AsyncSession,
    academic_year: AcademicYear,
):
    """Test getting active listings when none exist."""
    book_repo = BookRepository(db_session)
    listing_repo = ListingRepository(db_session)

    book = await book_repo.create(
        category="textbook",
        title="Math 6eme",
        catalog_year_id=academic_year.id,
    )
    await db_session.commit()

    active_listings = await listing_repo.get_active_for_book(book.id, academic_year.id)
    assert active_listings == []


@pytest.mark.asyncio
async def test_get_active_for_book_multiple_sellers(
    db_session: AsyncSession,
    academic_year: AcademicYear,
):
    """Test getting active listings from multiple sellers."""
    book_repo = BookRepository(db_session)
    user_repo = __import__("bot.database.repository", fromlist=["UserRepository"]).UserRepository(
        db_session
    )
    listing_repo = ListingRepository(db_session)

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

    active_listings = await listing_repo.get_active_for_book(book.id, academic_year.id)
    assert len(active_listings) == 2
    phones = {listing.contact_phone for listing in active_listings}
    assert "0612345678" in phones
    assert "0698765432" in phones
