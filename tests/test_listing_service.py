"""Tests for listing service."""

from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.models import AcademicYear, User
from bot.database.repository import BookRepository, UserRepository
from bot.services.listing import (
    InvalidTransitionError,
    ListingOwnershipError,
    ListingService,
    ListingValidationError,
)


class TestListingServiceValidation:
    """Tests for listing service validation methods."""

    def test_validate_price_valid(self):
        """Test valid price validation."""
        assert ListingService.validate_price("15.00") == Decimal("15.00")
        assert ListingService.validate_price("0.01") == Decimal("0.01")
        assert ListingService.validate_price("99999.99") == Decimal("99999.99")
        assert ListingService.validate_price("10") == Decimal("10.00")

    def test_validate_price_invalid(self):
        """Test invalid price validation."""
        with pytest.raises(ListingValidationError):
            ListingService.validate_price("abc")
        with pytest.raises(ListingValidationError):
            ListingService.validate_price("-5")
        with pytest.raises(ListingValidationError):
            ListingService.validate_price("0")
        with pytest.raises(ListingValidationError):
            ListingService.validate_price("100000")

    def test_validate_condition_valid(self):
        """Test valid condition validation."""
        assert ListingService.validate_condition("new") == "new"
        assert ListingService.validate_condition("like_new") == "like_new"
        assert ListingService.validate_condition("good") == "good"
        assert ListingService.validate_condition("fair") == "fair"
        assert ListingService.validate_condition("poor") == "poor"

    def test_validate_condition_invalid(self):
        """Test invalid condition validation."""
        with pytest.raises(ListingValidationError):
            ListingService.validate_condition("invalid")
        with pytest.raises(ListingValidationError):
            ListingService.validate_condition("")

    def test_validate_phone_valid(self):
        """Test valid phone validation."""
        assert ListingService.validate_phone("+79991234567") == "+79991234567"
        assert ListingService.validate_phone("+33612345678") == "+33612345678"
        assert ListingService.validate_phone("+44 7911 123456") == "+447911123456"
        assert ListingService.validate_phone("+1-555-123-4567") == "+15551234567"

    def test_validate_phone_invalid(self):
        """Test invalid phone validation."""
        with pytest.raises(ListingValidationError):
            ListingService.validate_phone("12345")
        with pytest.raises(ListingValidationError):
            ListingService.validate_phone("abcdefghij")
        with pytest.raises(ListingValidationError):
            ListingService.validate_phone("")

    def test_validate_description_valid(self):
        """Test valid description validation."""
        assert ListingService.validate_description(None) is None
        assert ListingService.validate_description("") is None
        assert ListingService.validate_description("  ") is None
        assert ListingService.validate_description("Test description") == "Test description"

    def test_validate_description_too_long(self):
        """Test description too long validation."""
        with pytest.raises(ListingValidationError):
            ListingService.validate_description("x" * 501)

    def test_validate_photos_valid(self):
        """Test valid photos validation."""
        assert ListingService.validate_photos(None) is None
        assert ListingService.validate_photos([]) is None
        assert ListingService.validate_photos(["file1", "file2"]) == ["file1", "file2"]
        assert ListingService.validate_photos(["file1", ""]) == ["file1"]

    def test_validate_photos_too_many(self):
        """Test too many photos validation."""
        with pytest.raises(ListingValidationError):
            ListingService.validate_photos(["f1", "f2", "f3", "f4", "f5", "f6"])


class TestListingServiceCreation:
    """Tests for listing creation."""

    @pytest.mark.asyncio
    async def test_create_listing(
        self,
        db_session: AsyncSession,
        academic_year: AcademicYear,
        user: User,
    ):
        """Test creating a listing."""
        book_repo = BookRepository(db_session)
        book = await book_repo.create(
            category="textbook",
            title="Math 6eme",
            catalog_year_id=academic_year.id,
        )
        await db_session.commit()

        service = ListingService(db_session)
        listing = await service.create_listing(
            book_id=book.id,
            seller_id=user.id,
            price=Decimal("15.00"),
            condition="good",
            phone="0612345678",
            description="Test description",
        )

        assert listing.id is not None
        assert listing.price == 15.00
        assert listing.condition == "good"
        assert listing.contact_phone == "0612345678"
        assert listing.description == "Test description"
        assert listing.status == "active"

    @pytest.mark.asyncio
    async def test_create_listing_book_not_found(
        self,
        db_session: AsyncSession,
        user: User,
    ):
        """Test creating a listing with non-existent book."""
        service = ListingService(db_session)

        with pytest.raises(ListingValidationError) as exc_info:
            await service.create_listing(
                book_id=999,
                seller_id=user.id,
                price=Decimal("15.00"),
                condition="good",
                phone="0612345678",
            )
        assert "Livre non trouvé" in str(exc_info.value)


class TestListingServiceStatusTransitions:
    """Tests for listing status transitions."""

    @pytest.mark.asyncio
    async def test_active_to_reserved(
        self,
        db_session: AsyncSession,
        academic_year: AcademicYear,
        user: User,
    ):
        """Test transitioning from active to reserved."""
        book_repo = BookRepository(db_session)
        book = await book_repo.create(
            category="textbook",
            title="Math 6eme",
            catalog_year_id=academic_year.id,
        )
        await db_session.commit()

        service = ListingService(db_session)
        listing = await service.create_listing(
            book_id=book.id,
            seller_id=user.id,
            price=Decimal("15.00"),
            condition="good",
            phone="0612345678",
        )

        updated = await service.update_status(listing.id, user.id, "reserved")
        assert updated.status == "reserved"
        assert updated.reserved_at is not None

    @pytest.mark.asyncio
    async def test_active_to_sold(
        self,
        db_session: AsyncSession,
        academic_year: AcademicYear,
        user: User,
    ):
        """Test transitioning from active directly to sold."""
        book_repo = BookRepository(db_session)
        book = await book_repo.create(
            category="textbook",
            title="Math 6eme",
            catalog_year_id=academic_year.id,
        )
        await db_session.commit()

        service = ListingService(db_session)
        listing = await service.create_listing(
            book_id=book.id,
            seller_id=user.id,
            price=Decimal("15.00"),
            condition="good",
            phone="0612345678",
        )

        updated = await service.update_status(listing.id, user.id, "sold")
        assert updated.status == "sold"
        assert updated.sold_at is not None

    @pytest.mark.asyncio
    async def test_reserved_to_sold(
        self,
        db_session: AsyncSession,
        academic_year: AcademicYear,
        user: User,
    ):
        """Test transitioning from reserved to sold."""
        book_repo = BookRepository(db_session)
        book = await book_repo.create(
            category="textbook",
            title="Math 6eme",
            catalog_year_id=academic_year.id,
        )
        await db_session.commit()

        service = ListingService(db_session)
        listing = await service.create_listing(
            book_id=book.id,
            seller_id=user.id,
            price=Decimal("15.00"),
            condition="good",
            phone="0612345678",
        )
        await service.update_status(listing.id, user.id, "reserved")

        updated = await service.update_status(listing.id, user.id, "sold")
        assert updated.status == "sold"
        assert updated.sold_at is not None

    @pytest.mark.asyncio
    async def test_active_to_archived(
        self,
        db_session: AsyncSession,
        academic_year: AcademicYear,
        user: User,
    ):
        """Test transitioning from active to archived."""
        book_repo = BookRepository(db_session)
        book = await book_repo.create(
            category="textbook",
            title="Math 6eme",
            catalog_year_id=academic_year.id,
        )
        await db_session.commit()

        service = ListingService(db_session)
        listing = await service.create_listing(
            book_id=book.id,
            seller_id=user.id,
            price=Decimal("15.00"),
            condition="good",
            phone="0612345678",
        )

        updated = await service.update_status(listing.id, user.id, "archived")
        assert updated.status == "archived"
        assert updated.archived_at is not None

    @pytest.mark.asyncio
    async def test_invalid_transition_sold_to_active(
        self,
        db_session: AsyncSession,
        academic_year: AcademicYear,
        user: User,
    ):
        """Test invalid transition from sold to active."""
        book_repo = BookRepository(db_session)
        book = await book_repo.create(
            category="textbook",
            title="Math 6eme",
            catalog_year_id=academic_year.id,
        )
        await db_session.commit()

        service = ListingService(db_session)
        listing = await service.create_listing(
            book_id=book.id,
            seller_id=user.id,
            price=Decimal("15.00"),
            condition="good",
            phone="0612345678",
        )
        await service.update_status(listing.id, user.id, "reserved")
        await service.update_status(listing.id, user.id, "sold")

        with pytest.raises(InvalidTransitionError):
            await service.update_status(listing.id, user.id, "active")

    @pytest.mark.asyncio
    async def test_invalid_transition_archived_to_sold(
        self,
        db_session: AsyncSession,
        academic_year: AcademicYear,
        user: User,
    ):
        """Test invalid transition from archived to sold."""
        book_repo = BookRepository(db_session)
        book = await book_repo.create(
            category="textbook",
            title="Math 6eme",
            catalog_year_id=academic_year.id,
        )
        await db_session.commit()

        service = ListingService(db_session)
        listing = await service.create_listing(
            book_id=book.id,
            seller_id=user.id,
            price=Decimal("15.00"),
            condition="good",
            phone="0612345678",
        )
        await service.update_status(listing.id, user.id, "archived")

        with pytest.raises(InvalidTransitionError):
            await service.update_status(listing.id, user.id, "sold")

    @pytest.mark.asyncio
    async def test_reserved_to_active(
        self,
        db_session: AsyncSession,
        academic_year: AcademicYear,
        user: User,
    ):
        """Test transitioning from reserved back to active."""
        book_repo = BookRepository(db_session)
        book = await book_repo.create(
            category="textbook",
            title="Math 6eme",
            catalog_year_id=academic_year.id,
        )
        await db_session.commit()

        service = ListingService(db_session)
        listing = await service.create_listing(
            book_id=book.id,
            seller_id=user.id,
            price=Decimal("15.00"),
            condition="good",
            phone="0612345678",
        )
        await service.update_status(listing.id, user.id, "reserved")

        updated = await service.update_status(listing.id, user.id, "active")
        assert updated.status == "active"


class TestListingServiceOwnership:
    """Tests for listing ownership verification."""

    @pytest.mark.asyncio
    async def test_get_own_listing(
        self,
        db_session: AsyncSession,
        academic_year: AcademicYear,
        user: User,
    ):
        """Test getting own listing."""
        book_repo = BookRepository(db_session)
        book = await book_repo.create(
            category="textbook",
            title="Math 6eme",
            catalog_year_id=academic_year.id,
        )
        await db_session.commit()

        service = ListingService(db_session)
        listing = await service.create_listing(
            book_id=book.id,
            seller_id=user.id,
            price=Decimal("15.00"),
            condition="good",
            phone="0612345678",
        )

        retrieved = await service.get_user_listing(listing.id, user.id)
        assert retrieved.id == listing.id

    @pytest.mark.asyncio
    async def test_get_other_user_listing(
        self,
        db_session: AsyncSession,
        academic_year: AcademicYear,
        user: User,
    ):
        """Test getting another user's listing."""
        book_repo = BookRepository(db_session)
        user_repo = UserRepository(db_session)

        book = await book_repo.create(
            category="textbook",
            title="Math 6eme",
            catalog_year_id=academic_year.id,
        )
        other_user = await user_repo.create(telegram_id=999999999, username="other")
        await db_session.commit()

        service = ListingService(db_session)
        listing = await service.create_listing(
            book_id=book.id,
            seller_id=user.id,
            price=Decimal("15.00"),
            condition="good",
            phone="0612345678",
        )

        with pytest.raises(ListingOwnershipError):
            await service.get_user_listing(listing.id, other_user.id)


class TestListingServiceFieldUpdate:
    """Tests for listing field updates."""

    @pytest.mark.asyncio
    async def test_update_price(
        self,
        db_session: AsyncSession,
        academic_year: AcademicYear,
        user: User,
    ):
        """Test updating listing price."""
        book_repo = BookRepository(db_session)
        book = await book_repo.create(
            category="textbook",
            title="Math 6eme",
            catalog_year_id=academic_year.id,
        )
        await db_session.commit()

        service = ListingService(db_session)
        listing = await service.create_listing(
            book_id=book.id,
            seller_id=user.id,
            price=Decimal("15.00"),
            condition="good",
            phone="0612345678",
        )

        updated = await service.update_field(listing.id, user.id, "price", "20.00")
        assert updated.price == 20.00

    @pytest.mark.asyncio
    async def test_update_condition(
        self,
        db_session: AsyncSession,
        academic_year: AcademicYear,
        user: User,
    ):
        """Test updating listing condition."""
        book_repo = BookRepository(db_session)
        book = await book_repo.create(
            category="textbook",
            title="Math 6eme",
            catalog_year_id=academic_year.id,
        )
        await db_session.commit()

        service = ListingService(db_session)
        listing = await service.create_listing(
            book_id=book.id,
            seller_id=user.id,
            price=Decimal("15.00"),
            condition="good",
            phone="0612345678",
        )

        updated = await service.update_field(listing.id, user.id, "condition", "new")
        assert updated.condition == "new"

    @pytest.mark.asyncio
    async def test_update_phone(
        self,
        db_session: AsyncSession,
        academic_year: AcademicYear,
        user: User,
    ):
        """Test updating listing phone."""
        book_repo = BookRepository(db_session)
        book = await book_repo.create(
            category="textbook",
            title="Math 6eme",
            catalog_year_id=academic_year.id,
        )
        await db_session.commit()

        service = ListingService(db_session)
        listing = await service.create_listing(
            book_id=book.id,
            seller_id=user.id,
            price=Decimal("15.00"),
            condition="good",
            phone="0612345678",
        )

        updated = await service.update_field(listing.id, user.id, "contact_phone", "0798765432")
        assert updated.contact_phone == "0798765432"

    @pytest.mark.asyncio
    async def test_update_description(
        self,
        db_session: AsyncSession,
        academic_year: AcademicYear,
        user: User,
    ):
        """Test updating listing description."""
        book_repo = BookRepository(db_session)
        book = await book_repo.create(
            category="textbook",
            title="Math 6eme",
            catalog_year_id=academic_year.id,
        )
        await db_session.commit()

        service = ListingService(db_session)
        listing = await service.create_listing(
            book_id=book.id,
            seller_id=user.id,
            price=Decimal("15.00"),
            condition="good",
            phone="0612345678",
        )

        updated = await service.update_field(listing.id, user.id, "description", "New description")
        assert updated.description == "New description"

    @pytest.mark.asyncio
    async def test_update_invalid_field(
        self,
        db_session: AsyncSession,
        academic_year: AcademicYear,
        user: User,
    ):
        """Test updating invalid field."""
        book_repo = BookRepository(db_session)
        book = await book_repo.create(
            category="textbook",
            title="Math 6eme",
            catalog_year_id=academic_year.id,
        )
        await db_session.commit()

        service = ListingService(db_session)
        listing = await service.create_listing(
            book_id=book.id,
            seller_id=user.id,
            price=Decimal("15.00"),
            condition="good",
            phone="0612345678",
        )

        with pytest.raises(ListingValidationError):
            await service.update_field(listing.id, user.id, "invalid_field", "value")
