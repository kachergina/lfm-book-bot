"""Tests for browsing service."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.models import AcademicYear, Listing, User
from bot.database.repository import BookRepository
from bot.services.browsing import BrowsingService


@pytest.mark.asyncio
async def test_get_current_academic_year(
    db_session: AsyncSession,
    academic_year: AcademicYear,
):
    """Test getting current academic year."""
    service = BrowsingService(db_session)
    year = await service.get_current_academic_year()
    assert year is not None
    assert year.id == academic_year.id


@pytest.mark.asyncio
async def test_get_current_academic_year_none(db_session: AsyncSession):
    """Test getting current academic year when none exists."""
    service = BrowsingService(db_session)
    year = await service.get_current_academic_year()
    assert year is None


@pytest.mark.asyncio
async def test_get_categories(
    db_session: AsyncSession,
    academic_year: AcademicYear,
):
    """Test getting categories."""
    service = BrowsingService(db_session)

    book_repo = BookRepository(db_session)
    await book_repo.create(
        category="textbook",
        title="Math",
        catalog_year_id=academic_year.id,
    )
    await book_repo.create(
        category="literature",
        title="Novel",
        catalog_year_id=academic_year.id,
    )
    await db_session.commit()

    categories = await service.get_categories(academic_year.id)
    assert sorted(categories) == ["literature", "textbook"]


@pytest.mark.asyncio
async def test_get_grade_levels(
    db_session: AsyncSession,
    academic_year: AcademicYear,
):
    """Test getting grade levels."""
    service = BrowsingService(db_session)

    book_repo = BookRepository(db_session)
    await book_repo.create(
        category="textbook",
        title="Math 6eme",
        catalog_year_id=academic_year.id,
        grade_level="6ème",
    )
    await book_repo.create(
        category="textbook",
        title="Math 5eme",
        catalog_year_id=academic_year.id,
        grade_level="5ème",
    )
    await db_session.commit()

    grades = await service.get_grade_levels(academic_year.id, "textbook")
    assert sorted(grades) == ["5ème", "6ème"]


@pytest.mark.asyncio
async def test_get_subjects(
    db_session: AsyncSession,
    academic_year: AcademicYear,
):
    """Test getting subjects."""
    service = BrowsingService(db_session)

    book_repo = BookRepository(db_session)
    await book_repo.create(
        category="textbook",
        title="Math 6eme",
        catalog_year_id=academic_year.id,
        grade_level="6ème",
        subject="Mathématiques",
    )
    await book_repo.create(
        category="textbook",
        title="Francais 6eme",
        catalog_year_id=academic_year.id,
        grade_level="6ème",
        subject="Français",
    )
    await db_session.commit()

    subjects = await service.get_subjects(academic_year.id, "textbook", "6ème")
    assert sorted(subjects) == ["Français", "Mathématiques"]


@pytest.mark.asyncio
async def test_get_books(
    db_session: AsyncSession,
    academic_year: AcademicYear,
):
    """Test getting books."""
    service = BrowsingService(db_session)

    book_repo = BookRepository(db_session)
    book1 = await book_repo.create(
        category="textbook",
        title="Math 6eme",
        catalog_year_id=academic_year.id,
        grade_level="6ème",
        subject="Mathématiques",
    )
    await book_repo.create(
        category="textbook",
        title="Francais 6eme",
        catalog_year_id=academic_year.id,
        grade_level="6ème",
        subject="Français",
    )
    await db_session.commit()

    books = await service.get_books(
        academic_year.id,
        "textbook",
        "6ème",
        "Mathématiques",
    )
    assert len(books) == 1
    assert books[0].id == book1.id


@pytest.mark.asyncio
async def test_get_active_listings(
    db_session: AsyncSession,
    academic_year: AcademicYear,
    user: User,
):
    """Test getting active listings."""
    service = BrowsingService(db_session)

    book_repo = BookRepository(db_session)
    book = await book_repo.create(
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

    listings = await service.get_active_listings(book.id, academic_year.id)
    assert len(listings) == 1
    assert listings[0].contact_phone == "0612345678"


@pytest.mark.asyncio
async def test_get_active_listings_filters_sold(
    db_session: AsyncSession,
    academic_year: AcademicYear,
    user: User,
):
    """Test that sold listings are not returned."""
    service = BrowsingService(db_session)

    book_repo = BookRepository(db_session)
    book = await book_repo.create(
        category="textbook",
        title="Math 6eme",
        catalog_year_id=academic_year.id,
    )
    await db_session.commit()

    active_listing = Listing(
        book_id=book.id,
        seller_id=user.id,
        academic_year_id=academic_year.id,
        price=15.00,
        condition="good",
        status="active",
        contact_phone="0612345678",
    )
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

    listings = await service.get_active_listings(book.id, academic_year.id)
    assert len(listings) == 1
    assert listings[0].status == "active"
