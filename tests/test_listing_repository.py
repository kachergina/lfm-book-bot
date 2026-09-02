"""Tests for listing repository methods."""

from datetime import timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.models import AcademicYear, Listing, User
from bot.database.repository import BookRepository, ListingRepository, UserRepository
from bot.utils.datetime_utils import utc_now


@pytest.mark.asyncio
async def test_get_user_listings(
    db_session: AsyncSession,
    academic_year: AcademicYear,
    user: User,
):
    """Test getting user listings."""
    book_repo = BookRepository(db_session)
    listing_repo = ListingRepository(db_session)

    book = await book_repo.create(
        category="textbook",
        title="Math 6eme",
        catalog_year_id=academic_year.id,
    )
    await db_session.commit()

    # Create listings with different statuses
    listing1 = Listing(
        book_id=book.id,
        seller_id=user.id,
        academic_year_id=academic_year.id,
        price=15.00,
        condition="good",
        status="active",
        contact_phone="0612345678",
    )
    listing2 = Listing(
        book_id=book.id,
        seller_id=user.id,
        academic_year_id=academic_year.id,
        price=20.00,
        condition="new",
        status="sold",
        contact_phone="0612345678",
    )
    db_session.add_all([listing1, listing2])
    await db_session.commit()

    # Get all listings
    all_listings = await listing_repo.get_user_listings(user.id)
    assert len(all_listings) == 2

    # Get only active listings
    active_listings = await listing_repo.get_user_listings(user.id, "active")
    assert len(active_listings) == 1
    assert active_listings[0].status == "active"

    # Get only sold listings
    sold_listings = await listing_repo.get_user_listings(user.id, "sold")
    assert len(sold_listings) == 1
    assert sold_listings[0].status == "sold"


@pytest.mark.asyncio
async def test_get_user_listing_by_id(
    db_session: AsyncSession,
    academic_year: AcademicYear,
    user: User,
):
    """Test getting a specific user listing."""
    book_repo = BookRepository(db_session)
    listing_repo = ListingRepository(db_session)

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

    # Get existing listing
    found = await listing_repo.get_user_listing_by_id(listing.id, user.id)
    assert found is not None
    assert found.id == listing.id

    # Get non-existent listing
    not_found = await listing_repo.get_user_listing_by_id(999, user.id)
    assert not_found is None


@pytest.mark.asyncio
async def test_create_listing(
    db_session: AsyncSession,
    academic_year: AcademicYear,
    user: User,
):
    """Test creating a listing via repository."""
    book_repo = BookRepository(db_session)
    listing_repo = ListingRepository(db_session)

    book = await book_repo.create(
        category="textbook",
        title="Math 6eme",
        catalog_year_id=academic_year.id,
    )
    await db_session.commit()

    listing = await listing_repo.create_listing(
        book_id=book.id,
        seller_id=user.id,
        academic_year_id=academic_year.id,
        price=15.00,
        condition="good",
        contact_phone="0612345678",
        description="Test",
        photos=["file1", "file2"],
    )

    assert listing.id is not None
    assert listing.price == 15.00
    assert listing.condition == "good"
    assert listing.contact_phone == "0612345678"
    assert listing.description == "Test"
    assert listing.photos == ["file1", "file2"]
    assert listing.status == "active"


@pytest.mark.asyncio
async def test_update_status(
    db_session: AsyncSession,
    academic_year: AcademicYear,
    user: User,
):
    """Test updating listing status."""
    book_repo = BookRepository(db_session)
    listing_repo = ListingRepository(db_session)

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

    # Update to reserved
    updated = await listing_repo.update_status(listing.id, "reserved")
    assert updated.status == "reserved"
    assert updated.reserved_at is not None
    assert updated.reserved_at.tzinfo is None

    # Update to sold
    updated = await listing_repo.update_status(listing.id, "sold")
    assert updated.status == "sold"
    assert updated.sold_at is not None
    assert updated.sold_at.tzinfo is None

    # Update non-existent listing
    not_found = await listing_repo.update_status(999, "archived")
    assert not_found is None


@pytest.mark.asyncio
async def test_update_field(
    db_session: AsyncSession,
    academic_year: AcademicYear,
    user: User,
):
    """Test updating listing field."""
    book_repo = BookRepository(db_session)
    listing_repo = ListingRepository(db_session)

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

    # Update price
    updated = await listing_repo.update_field(listing.id, "price", 20.00)
    assert updated.price == 20.00

    # Update condition
    updated = await listing_repo.update_field(listing.id, "condition", "new")
    assert updated.condition == "new"

    # Update invalid field
    not_found = await listing_repo.update_field(listing.id, "invalid_field", "value")
    assert not_found is None


@pytest.mark.asyncio
async def test_count_active_by_user(
    db_session: AsyncSession,
    academic_year: AcademicYear,
    user: User,
):
    """Test counting active listings by user."""
    book_repo = BookRepository(db_session)
    listing_repo = ListingRepository(db_session)
    user_repo = UserRepository(db_session)

    book = await book_repo.create(
        category="textbook",
        title="Math 6eme",
        catalog_year_id=academic_year.id,
    )
    other_user = await user_repo.create(telegram_id=999999999, username="other")
    await db_session.commit()

    # Create listings
    listing1 = Listing(
        book_id=book.id,
        seller_id=user.id,
        academic_year_id=academic_year.id,
        price=15.00,
        condition="good",
        status="active",
        contact_phone="0612345678",
    )
    listing2 = Listing(
        book_id=book.id,
        seller_id=user.id,
        academic_year_id=academic_year.id,
        price=20.00,
        condition="new",
        status="active",
        contact_phone="0612345678",
    )
    listing3 = Listing(
        book_id=book.id,
        seller_id=user.id,
        academic_year_id=academic_year.id,
        price=25.00,
        condition="fair",
        status="sold",
        contact_phone="0612345678",
    )
    listing4 = Listing(
        book_id=book.id,
        seller_id=other_user.id,
        academic_year_id=academic_year.id,
        price=30.00,
        condition="good",
        status="active",
        contact_phone="0612345678",
    )
    db_session.add_all([listing1, listing2, listing3, listing4])
    await db_session.commit()

    # Count active listings for user
    count = await listing_repo.count_active_by_user(user.id)
    assert count == 2

    # Count active listings for other user
    other_count = await listing_repo.count_active_by_user(other_user.id)
    assert other_count == 1


@pytest.mark.asyncio
async def test_get_expired_listings_with_naive_created_at(
    db_session: AsyncSession,
    academic_year: AcademicYear,
    user: User,
):
    """Regression: naive PostgreSQL timestamps must compare with naive UTC cutoff."""
    book_repo = BookRepository(db_session)
    listing_repo = ListingRepository(db_session)

    book = await book_repo.create(
        category="textbook",
        title="Math 6eme",
        catalog_year_id=academic_year.id,
    )
    await db_session.commit()

    listing = await listing_repo.create_listing(
        book_id=book.id,
        seller_id=user.id,
        academic_year_id=academic_year.id,
        price=15.00,
        condition="good",
        contact_phone="0612345678",
    )
    listing.created_at = utc_now() - timedelta(days=200)
    assert listing.created_at.tzinfo is None
    await db_session.commit()

    expired = await listing_repo.get_expired_listings(expiry_days=180)
    expired_ids = [item.id for item in expired]
    assert listing.id in expired_ids


@pytest.mark.asyncio
async def test_bulk_expire_sets_naive_expires_at(
    db_session: AsyncSession,
    academic_year: AcademicYear,
    user: User,
):
    """Regression: expires_at must be stored as naive UTC for PostgreSQL."""
    book_repo = BookRepository(db_session)
    listing_repo = ListingRepository(db_session)

    book = await book_repo.create(
        category="textbook",
        title="Math 6eme",
        catalog_year_id=academic_year.id,
    )
    await db_session.commit()

    listing = await listing_repo.create_listing(
        book_id=book.id,
        seller_id=user.id,
        academic_year_id=academic_year.id,
        price=15.00,
        condition="good",
        contact_phone="0612345678",
    )
    await db_session.commit()

    await listing_repo.bulk_expire([listing.id])
    await db_session.refresh(listing)

    assert listing.status == "expired"
    assert listing.expires_at is not None
    assert listing.expires_at.tzinfo is None

