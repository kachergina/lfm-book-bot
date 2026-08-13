"""Tests for Milestone 5: Academic Year & Admin."""

from datetime import UTC, date, datetime, timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.models import AcademicYear, User
from bot.database.repository import (
    AcademicYearRepository,
    BookRepository,
    ListingRepository,
    UserRepository,
)
from bot.services.academic_year import AcademicYearError, AcademicYearService
from bot.services.admin import AdminError, AdminService
from bot.services.listing import ListingService

# ===== ACADEMIC YEAR REPOSITORY TESTS =====


class TestAcademicYearRepository:
    """Tests for AcademicYearRepository CRUD."""

    @pytest.mark.asyncio
    async def test_create_academic_year(self, db_session: AsyncSession):
        """Test creating an academic year."""
        repo = AcademicYearRepository(db_session)
        year = await repo.create(
            name="2026-2027",
            start_date=date(2026, 9, 1),
            end_date=date(2027, 6, 30),
        )
        assert year.id is not None
        assert year.name == "2026-2027"
        assert year.is_current is False

    @pytest.mark.asyncio
    async def test_get_by_id(self, db_session: AsyncSession):
        """Test getting academic year by ID."""
        repo = AcademicYearRepository(db_session)
        year = await repo.create(
            name="2026-2027",
            start_date=date(2026, 9, 1),
            end_date=date(2027, 6, 30),
        )

        found = await repo.get_by_id(year.id)
        assert found is not None
        assert found.name == "2026-2027"

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, db_session: AsyncSession):
        """Test getting non-existent academic year."""
        repo = AcademicYearRepository(db_session)
        found = await repo.get_by_id(999)
        assert found is None

    @pytest.mark.asyncio
    async def test_get_by_name(self, db_session: AsyncSession):
        """Test getting academic year by name."""
        repo = AcademicYearRepository(db_session)
        await repo.create(
            name="2026-2027",
            start_date=date(2026, 9, 1),
            end_date=date(2027, 6, 30),
        )

        found = await repo.get_by_name("2026-2027")
        assert found is not None
        assert found.name == "2026-2027"

    @pytest.mark.asyncio
    async def test_list_all(self, db_session: AsyncSession):
        """Test listing all academic years."""
        repo = AcademicYearRepository(db_session)
        await repo.create(
            name="2025-2026",
            start_date=date(2025, 9, 1),
            end_date=date(2026, 6, 30),
        )
        await repo.create(
            name="2026-2027",
            start_date=date(2026, 9, 1),
            end_date=date(2027, 6, 30),
        )

        years = await repo.list_all()
        assert len(years) == 2
        # Ordered by start_date desc
        assert years[0].name == "2026-2027"

    @pytest.mark.asyncio
    async def test_set_current(self, db_session: AsyncSession):
        """Test setting a year as current."""
        repo = AcademicYearRepository(db_session)
        year1 = await repo.create(
            name="2025-2026",
            start_date=date(2025, 9, 1),
            end_date=date(2026, 6, 30),
            is_current=True,
        )
        year2 = await repo.create(
            name="2026-2027",
            start_date=date(2026, 9, 1),
            end_date=date(2027, 6, 30),
        )

        result = await repo.set_current(year2.id)
        assert result is not None
        assert result.is_current is True

        # Verify old year is no longer current
        refreshed = await repo.get_by_id(year1.id)
        assert refreshed is not None
        assert refreshed.is_current is False

    @pytest.mark.asyncio
    async def test_set_current_not_found(self, db_session: AsyncSession):
        """Test setting non-existent year as current."""
        repo = AcademicYearRepository(db_session)
        result = await repo.set_current(999)
        assert result is None


# ===== ACADEMIC YEAR SERVICE TESTS =====


class TestAcademicYearService:
    """Tests for AcademicYearService."""

    @pytest.mark.asyncio
    async def test_create_year(self, db_session: AsyncSession):
        """Test creating an academic year via service."""
        service = AcademicYearService(db_session)
        year = await service.create_year(
            name="2026-2027",
            start_date=date(2026, 9, 1),
            end_date=date(2027, 6, 30),
        )
        assert year.name == "2026-2027"

    @pytest.mark.asyncio
    async def test_create_year_duplicate_name(self, db_session: AsyncSession):
        """Test creating duplicate year fails."""
        service = AcademicYearService(db_session)
        await service.create_year(
            name="2026-2027",
            start_date=date(2026, 9, 1),
            end_date=date(2027, 6, 30),
        )

        with pytest.raises(AcademicYearError) as exc_info:
            await service.create_year(
                name="2026-2027",
                start_date=date(2026, 9, 1),
                end_date=date(2027, 6, 30),
            )
        assert "existe déjà" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_create_year_invalid_dates(self, db_session: AsyncSession):
        """Test creating year with end before start fails."""
        service = AcademicYearService(db_session)
        with pytest.raises(AcademicYearError) as exc_info:
            await service.create_year(
                name="2026-2027",
                start_date=date(2027, 6, 30),
                end_date=date(2026, 9, 1),
            )
        assert "postérieure" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_create_year_invalid_name(self, db_session: AsyncSession):
        """Test creating year with invalid name fails."""
        service = AcademicYearService(db_session)
        with pytest.raises(AcademicYearError):
            await service.create_year(
                name="",
                start_date=date(2026, 9, 1),
                end_date=date(2027, 6, 30),
            )

    @pytest.mark.asyncio
    async def test_set_current_year(self, db_session: AsyncSession):
        """Test setting current year."""
        service = AcademicYearService(db_session)
        year = await service.create_year(
            name="2026-2027",
            start_date=date(2026, 9, 1),
            end_date=date(2027, 6, 30),
        )

        result = await service.set_current_year(year.id)
        assert result.is_current is True

    @pytest.mark.asyncio
    async def test_set_current_year_not_found(self, db_session: AsyncSession):
        """Test setting non-existent year as current."""
        service = AcademicYearService(db_session)
        with pytest.raises(AcademicYearError):
            await service.set_current_year(999)

    @pytest.mark.asyncio
    async def test_transition_to_year(self, db_session: AsyncSession):
        """Test year transition archives old listings."""
        service = AcademicYearService(db_session)
        old_year = await service.create_year(
            name="2025-2026",
            start_date=date(2025, 9, 1),
            end_date=date(2026, 6, 30),
        )
        new_year = await service.create_year(
            name="2026-2027",
            start_date=date(2026, 9, 1),
            end_date=date(2027, 6, 30),
        )
        await service.set_current_year(old_year.id)

        # Create a book and listing in old year
        book_repo = BookRepository(db_session)
        book = await book_repo.create(
            category="textbook",
            title="Math 6eme",
            catalog_year_id=old_year.id,
        )
        user_repo = UserRepository(db_session)
        user = await user_repo.create(telegram_id=12345, username="seller")
        listing_repo = ListingRepository(db_session)
        await listing_repo.create_listing(
            book_id=book.id,
            seller_id=user.id,
            academic_year_id=old_year.id,
            price=15.00,
            condition="good",
            contact_phone="0612345678",
        )

        # Perform transition
        result = await service.transition_to_year(new_year.id)
        assert result["archived_count"] == 1
        assert result["new_year"].name == "2026-2027"

        # Verify old year is not current
        old_refreshed = await service.get_year_by_id(old_year.id)
        assert old_refreshed.is_current is False

        # Verify new year is current
        new_refreshed = await service.get_year_by_id(new_year.id)
        assert new_refreshed.is_current is True

    @pytest.mark.asyncio
    async def test_transition_already_current(self, db_session: AsyncSession):
        """Test transition to already current year fails."""
        service = AcademicYearService(db_session)
        year = await service.create_year(
            name="2026-2027",
            start_date=date(2026, 9, 1),
            end_date=date(2027, 6, 30),
        )
        await service.set_current_year(year.id)

        with pytest.raises(AcademicYearError) as exc_info:
            await service.transition_to_year(year.id)
        assert "déjà l'année courante" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_transition_not_found(self, db_session: AsyncSession):
        """Test transition to non-existent year fails."""
        service = AcademicYearService(db_session)
        with pytest.raises(AcademicYearError):
            await service.transition_to_year(999)


# ===== USER REPOSITORY TESTS =====


class TestUserRepository:
    """Tests for UserRepository new methods."""

    @pytest.mark.asyncio
    async def test_get_by_id(self, db_session: AsyncSession):
        """Test getting user by ID."""
        repo = UserRepository(db_session)
        user = await repo.create(telegram_id=12345, username="test")
        found = await repo.get_by_id(user.id)
        assert found is not None
        assert found.username == "test"

    @pytest.mark.asyncio
    async def test_list_users(self, db_session: AsyncSession):
        """Test listing users."""
        repo = UserRepository(db_session)
        await repo.create(telegram_id=111, username="user1")
        await repo.create(telegram_id=222, username="user2")

        users = await repo.list_users()
        assert len(users) == 2

    @pytest.mark.asyncio
    async def test_search_by_username(self, db_session: AsyncSession):
        """Test searching users."""
        repo = UserRepository(db_session)
        await repo.create(telegram_id=111, username="alice")
        await repo.create(telegram_id=222, username="bob")
        await repo.create(telegram_id=333, username="charlie")

        results = await repo.search_by_username("ali")
        assert len(results) == 1
        assert results[0].username == "alice"

    @pytest.mark.asyncio
    async def test_ban_user(self, db_session: AsyncSession):
        """Test banning a user."""
        repo = UserRepository(db_session)
        user = await repo.create(telegram_id=12345, username="test")

        result = await repo.ban_user(user.id, "spam")
        assert result is not None
        assert result.is_banned is True
        assert result.ban_reason == "spam"

    @pytest.mark.asyncio
    async def test_unban_user(self, db_session: AsyncSession):
        """Test unbanning a user."""
        repo = UserRepository(db_session)
        user = await repo.create(telegram_id=12345, username="test")
        await repo.ban_user(user.id, "spam")

        result = await repo.unban_user(user.id)
        assert result is not None
        assert result.is_banned is False
        assert result.ban_reason is None


# ===== ADMIN SERVICE TESTS =====


class TestAdminService:
    """Tests for AdminService."""

    @pytest.mark.asyncio
    async def test_ban_user(self, db_session: AsyncSession):
        """Test banning a user via admin service."""
        service = AdminService(db_session)
        target = await UserRepository(db_session).create(telegram_id=99999, username="baduser")

        result = await service.ban_user(
            admin_telegram_id=12345,
            target_user_id=target.id,
            reason="spam",
        )
        assert result["user_id"] == target.id
        assert result["reason"] == "spam"

    @pytest.mark.asyncio
    async def test_ban_self_fails(self, db_session: AsyncSession):
        """Test admin cannot ban themselves."""
        service = AdminService(db_session)
        admin = await UserRepository(db_session).create(telegram_id=12345, username="admin")

        with pytest.raises(AdminError) as exc_info:
            await service.ban_user(
                admin_telegram_id=12345,
                target_user_id=admin.id,
            )
        assert "vous-même" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_ban_admin_fails(self, db_session: AsyncSession):
        """Test banning another admin fails."""
        service = AdminService(db_session)
        other_admin = await UserRepository(db_session).create(
            telegram_id=99999, username="other_admin"
        )
        # Manually set admin role
        other_admin.role = "admin"
        await db_session.commit()

        with pytest.raises(AdminError) as exc_info:
            await service.ban_user(
                admin_telegram_id=12345,
                target_user_id=other_admin.id,
            )
        assert "administrateur" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_ban_already_banned_fails(self, db_session: AsyncSession):
        """Test banning already banned user fails."""
        service = AdminService(db_session)
        target = await UserRepository(db_session).create(telegram_id=99999, username="baduser")
        await service.ban_user(
            admin_telegram_id=12345,
            target_user_id=target.id,
        )

        with pytest.raises(AdminError) as exc_info:
            await service.ban_user(
                admin_telegram_id=12345,
                target_user_id=target.id,
            )
        assert "déjà banni" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_unban_user(self, db_session: AsyncSession):
        """Test unbanning a user."""
        service = AdminService(db_session)
        target = await UserRepository(db_session).create(telegram_id=99999, username="baduser")
        await service.ban_user(
            admin_telegram_id=12345,
            target_user_id=target.id,
        )

        result = await service.unban_user(target.id)
        assert result["user_id"] == target.id

    @pytest.mark.asyncio
    async def test_unban_not_banned_fails(self, db_session: AsyncSession):
        """Test unbanning non-banned user fails."""
        service = AdminService(db_session)
        target = await UserRepository(db_session).create(telegram_id=99999, username="gooduser")

        with pytest.raises(AdminError) as exc_info:
            await service.unban_user(target.id)
        assert "pas banni" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_is_user_banned(self, db_session: AsyncSession):
        """Test checking ban status."""
        service = AdminService(db_session)
        target = await UserRepository(db_session).create(telegram_id=99999, username="testuser")

        assert await service.is_user_banned(99999) is False

        await service.ban_user(
            admin_telegram_id=12345,
            target_user_id=target.id,
        )

        assert await service.is_user_banned(99999) is True


# ===== LISTING EXPIRY TESTS =====


class TestListingExpiry:
    """Tests for listing expiry job."""

    @pytest.mark.asyncio
    async def test_expire_old_listings(
        self,
        db_session: AsyncSession,
        academic_year: AcademicYear,
        user: User,
    ):
        """Test that old listings get expired."""
        book_repo = BookRepository(db_session)
        book = await book_repo.create(
            category="textbook",
            title="Math 6eme",
            catalog_year_id=academic_year.id,
        )
        await db_session.commit()

        listing_repo = ListingRepository(db_session)
        listing = await listing_repo.create_listing(
            book_id=book.id,
            seller_id=user.id,
            academic_year_id=academic_year.id,
            price=15.00,
            condition="good",
            contact_phone="0612345678",
        )
        await db_session.commit()

        # Manually set created_at to be old

        old_date = datetime.now(UTC) - timedelta(days=200)
        listing.created_at = old_date
        await db_session.commit()

        service = ListingService(db_session)
        expired = await service.expire_listings(expiry_days=180)

        assert len(expired) >= 1
        expired_ids = [e.id for e in expired]
        assert listing.id in expired_ids

    @pytest.mark.asyncio
    async def test_recent_listings_not_expired(
        self,
        db_session: AsyncSession,
        academic_year: AcademicYear,
        user: User,
    ):
        """Test that recent listings are not expired."""
        book_repo = BookRepository(db_session)
        book = await book_repo.create(
            category="textbook",
            title="Math 6eme",
            catalog_year_id=academic_year.id,
        )
        await db_session.commit()

        listing_repo = ListingRepository(db_session)
        listing = await listing_repo.create_listing(
            book_id=book.id,
            seller_id=user.id,
            academic_year_id=academic_year.id,
            price=15.00,
            condition="good",
            contact_phone="0612345678",
        )
        await db_session.commit()

        service = ListingService(db_session)
        expired = await service.expire_listings(expiry_days=180)

        # Recent listing should not be expired
        expired_ids = [e.id for e in expired]
        assert listing.id not in expired_ids

    @pytest.mark.asyncio
    async def test_expire_idempotent(
        self,
        db_session: AsyncSession,
        academic_year: AcademicYear,
        user: User,
    ):
        """Test that running expiry twice doesn't double-expire."""
        book_repo = BookRepository(db_session)
        book = await book_repo.create(
            category="textbook",
            title="Math 6eme",
            catalog_year_id=academic_year.id,
        )
        await db_session.commit()

        listing_repo = ListingRepository(db_session)
        listing = await listing_repo.create_listing(
            book_id=book.id,
            seller_id=user.id,
            academic_year_id=academic_year.id,
            price=15.00,
            condition="good",
            contact_phone="0612345678",
        )
        await db_session.commit()

        # Make it old

        old_date = datetime.now(UTC) - timedelta(days=200)
        listing.created_at = old_date
        await db_session.commit()

        service = ListingService(db_session)
        expired1 = await service.expire_listings(expiry_days=180)
        expired2 = await service.expire_listings(expiry_days=180)

        # Second run should find nothing to expire
        assert len(expired2) == 0

    @pytest.mark.asyncio
    async def test_reserved_not_expired(
        self,
        db_session: AsyncSession,
        academic_year: AcademicYear,
        user: User,
    ):
        """Test that reserved listings are not expired (only active)."""
        book_repo = BookRepository(db_session)
        book = await book_repo.create(
            category="textbook",
            title="Math 6eme",
            catalog_year_id=academic_year.id,
        )
        await db_session.commit()

        listing_repo = ListingRepository(db_session)
        listing = await listing_repo.create_listing(
            book_id=book.id,
            seller_id=user.id,
            academic_year_id=academic_year.id,
            price=15.00,
            condition="good",
            contact_phone="0612345678",
        )
        await db_session.commit()

        # Mark as reserved

        listing.status = "reserved"
        old_date = datetime.now(UTC) - timedelta(days=200)
        listing.created_at = old_date
        await db_session.commit()

        service = ListingService(db_session)
        expired = await service.expire_listings(expiry_days=180)

        expired_ids = [e.id for e in expired]
        assert listing.id not in expired_ids


# ===== BANNED USER MIDDLEWARE TESTS =====


class TestBannedUserRestriction:
    """Tests for banned user restriction behavior."""

    @pytest.mark.asyncio
    async def test_banned_user_detected(self, db_session: AsyncSession):
        """Test that banned user is detected."""
        user_repo = UserRepository(db_session)
        user = await user_repo.create(telegram_id=99999, username="banned")
        await user_repo.ban_user(user.id, "spam")

        from bot.services.admin import AdminService

        service = AdminService(db_session)
        assert await service.is_user_banned(99999) is True

    @pytest.mark.asyncio
    async def test_non_banned_user_not_detected(self, db_session: AsyncSession):
        """Test that non-banned user is not detected."""
        user_repo = UserRepository(db_session)
        await user_repo.create(telegram_id=88888, username="good")

        from bot.services.admin import AdminService

        service = AdminService(db_session)
        assert await service.is_user_banned(88888) is False


# ===== LISTING REPOSITORY YEAR TRANSITION TESTS =====


class TestListingRepositoryYearTransition:
    """Tests for listing repository year transition methods."""

    @pytest.mark.asyncio
    async def test_bulk_archive_by_year(
        self,
        db_session: AsyncSession,
        academic_year: AcademicYear,
        user: User,
    ):
        """Test bulk archiving listings by year."""
        book_repo = BookRepository(db_session)
        book = await book_repo.create(
            category="textbook",
            title="Math 6eme",
            catalog_year_id=academic_year.id,
        )
        await db_session.commit()

        listing_repo = ListingRepository(db_session)
        await listing_repo.create_listing(
            book_id=book.id,
            seller_id=user.id,
            academic_year_id=academic_year.id,
            price=15.00,
            condition="good",
            contact_phone="0612345678",
        )
        await db_session.commit()

        count = await listing_repo.bulk_archive_by_year(academic_year.id)
        assert count == 1

        # Verify listing is archived
        listings = await listing_repo.get_user_listings(user.id)
        assert listings[0].status == "archived"

    @pytest.mark.asyncio
    async def test_get_active_reserved_by_year(
        self,
        db_session: AsyncSession,
        academic_year: AcademicYear,
        user: User,
    ):
        """Test getting active/reserved listings by year."""
        book_repo = BookRepository(db_session)
        book = await book_repo.create(
            category="textbook",
            title="Math 6eme",
            catalog_year_id=academic_year.id,
        )
        await db_session.commit()

        listing_repo = ListingRepository(db_session)
        listing = await listing_repo.create_listing(
            book_id=book.id,
            seller_id=user.id,
            academic_year_id=academic_year.id,
            price=15.00,
            condition="good",
            contact_phone="0612345678",
        )
        await db_session.commit()

        result = await listing_repo.get_active_reserved_by_year(academic_year.id)
        assert len(result) == 1
        assert result[0].status == "active"
