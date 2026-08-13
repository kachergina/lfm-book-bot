"""Tests for notification service."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.models import AcademicYear, Book, Listing, User
from bot.database.repository import BookRepository


def _create_mock_bot() -> MagicMock:
    """Create a mock Bot instance."""
    bot = MagicMock()
    bot.send_message = AsyncMock(return_value=True)
    return bot


def _create_listing_with_relationships(
    db_session: AsyncSession,
    academic_year: AcademicYear,
    user: User,
) -> tuple[Book, Listing]:
    """Create a listing with book and seller relationships loaded."""
    book_repo = BookRepository(db_session)
    book = (
        book_repo.create_sync(
            category="textbook",
            title="Math 6eme",
            catalog_year_id=academic_year.id,
        )
        if hasattr(book_repo, "create_sync")
        else None
    )

    # Use async approach
    import asyncio

    loop = asyncio.new_event_loop()
    book = loop.run_until_complete(
        book_repo.create(
            category="textbook",
            title="Math 6eme",
            catalog_year_id=academic_year.id,
        )
    )
    loop.run_until_complete(db_session.commit())

    from bot.database.models import Listing

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
    loop.run_until_complete(db_session.commit())

    # Refresh with relationships
    loop.run_until_complete(db_session.refresh(listing, ["book", "seller"]))
    loop.close()

    return book, listing


class TestNotificationServiceSellerNotifications:
    """Tests for seller notification methods."""

    @pytest.mark.asyncio
    async def test_notify_seller_status_change_reserved(
        self,
        db_session: AsyncSession,
        academic_year: AcademicYear,
        user: User,
    ):
        """Test notification sent when listing is reserved."""
        book_repo = BookRepository(db_session)
        book = await book_repo.create(
            category="textbook",
            title="Math 6eme",
            catalog_year_id=academic_year.id,
        )
        await db_session.commit()

        from bot.database.models import Listing

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
        await db_session.refresh(listing, ["book", "seller"])

        mock_bot = _create_mock_bot()
        from bot.services.notification import NotificationService

        service = NotificationService(mock_bot, db_session)
        result = await service.notify_seller_status_change(
            listing=listing,
            old_status="active",
            new_status="reserved",
        )

        assert result is True
        mock_bot.send_message.assert_called_once()
        call_kwargs = mock_bot.send_message.call_args
        assert call_kwargs.kwargs["chat_id"] == user.telegram_id
        assert "Math 6eme" in call_kwargs.kwargs["text"]
        assert "réservée" in call_kwargs.kwargs["text"].lower()

    @pytest.mark.asyncio
    async def test_notify_seller_status_change_sold(
        self,
        db_session: AsyncSession,
        academic_year: AcademicYear,
        user: User,
    ):
        """Test notification sent when listing is sold."""
        book_repo = BookRepository(db_session)
        book = await book_repo.create(
            category="textbook",
            title="Math 6eme",
            catalog_year_id=academic_year.id,
        )
        await db_session.commit()

        from bot.database.models import Listing

        listing = Listing(
            book_id=book.id,
            seller_id=user.id,
            academic_year_id=academic_year.id,
            price=15.00,
            condition="good",
            status="reserved",
            contact_phone="0612345678",
        )
        db_session.add(listing)
        await db_session.commit()
        await db_session.refresh(listing, ["book", "seller"])

        mock_bot = _create_mock_bot()
        from bot.services.notification import NotificationService

        service = NotificationService(mock_bot, db_session)
        result = await service.notify_seller_status_change(
            listing=listing,
            old_status="reserved",
            new_status="sold",
        )

        assert result is True
        mock_bot.send_message.assert_called_once()
        call_kwargs = mock_bot.send_message.call_args
        assert "vendue" in call_kwargs.kwargs["text"].lower()

    @pytest.mark.asyncio
    async def test_notify_seller_status_change_activated(
        self,
        db_session: AsyncSession,
        academic_year: AcademicYear,
        user: User,
    ):
        """Test notification sent when listing is reactivated."""
        book_repo = BookRepository(db_session)
        book = await book_repo.create(
            category="textbook",
            title="Math 6eme",
            catalog_year_id=academic_year.id,
        )
        await db_session.commit()

        from bot.database.models import Listing

        listing = Listing(
            book_id=book.id,
            seller_id=user.id,
            academic_year_id=academic_year.id,
            price=15.00,
            condition="good",
            status="reserved",
            contact_phone="0612345678",
        )
        db_session.add(listing)
        await db_session.commit()
        await db_session.refresh(listing, ["book", "seller"])

        mock_bot = _create_mock_bot()
        from bot.services.notification import NotificationService

        service = NotificationService(mock_bot, db_session)
        result = await service.notify_seller_status_change(
            listing=listing,
            old_status="reserved",
            new_status="active",
        )

        assert result is True
        call_kwargs = mock_bot.send_message.call_args
        assert "remise en vente" in call_kwargs.kwargs["text"].lower()

    @pytest.mark.asyncio
    async def test_notify_seller_status_change_archived(
        self,
        db_session: AsyncSession,
        academic_year: AcademicYear,
        user: User,
    ):
        """Test notification sent when listing is archived."""
        book_repo = BookRepository(db_session)
        book = await book_repo.create(
            category="textbook",
            title="Math 6eme",
            catalog_year_id=academic_year.id,
        )
        await db_session.commit()

        from bot.database.models import Listing

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
        await db_session.refresh(listing, ["book", "seller"])

        mock_bot = _create_mock_bot()
        from bot.services.notification import NotificationService

        service = NotificationService(mock_bot, db_session)
        result = await service.notify_seller_status_change(
            listing=listing,
            old_status="active",
            new_status="archived",
        )

        assert result is True
        call_kwargs = mock_bot.send_message.call_args
        assert "archivée" in call_kwargs.kwargs["text"].lower()

    @pytest.mark.asyncio
    async def test_notify_seller_status_change_no_template(
        self,
        db_session: AsyncSession,
        academic_year: AcademicYear,
        user: User,
    ):
        """Test notification skipped when no template exists for status."""
        book_repo = BookRepository(db_session)
        book = await book_repo.create(
            category="textbook",
            title="Math 6eme",
            catalog_year_id=academic_year.id,
        )
        await db_session.commit()

        from bot.database.models import Listing

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
        await db_session.refresh(listing, ["book", "seller"])

        mock_bot = _create_mock_bot()
        from bot.services.notification import NotificationService

        service = NotificationService(mock_bot, db_session)
        result = await service.notify_seller_status_change(
            listing=listing,
            old_status="active",
            new_status="expired",
        )

        assert result is False
        mock_bot.send_message.assert_not_called()

    @pytest.mark.asyncio
    async def test_notify_seller_delivery_failure(
        self,
        db_session: AsyncSession,
        academic_year: AcademicYear,
        user: User,
    ):
        """Test notification failure does not raise exception."""
        book_repo = BookRepository(db_session)
        book = await book_repo.create(
            category="textbook",
            title="Math 6eme",
            catalog_year_id=academic_year.id,
        )
        await db_session.commit()

        from bot.database.models import Listing

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
        await db_session.refresh(listing, ["book", "seller"])

        mock_bot = _create_mock_bot()
        mock_bot.send_message = AsyncMock(side_effect=Exception("Telegram API error"))

        from bot.services.notification import NotificationService

        service = NotificationService(mock_bot, db_session)
        # Should not raise, just return False
        result = await service.notify_seller_status_change(
            listing=listing,
            old_status="active",
            new_status="reserved",
        )

        assert result is False

    @pytest.mark.asyncio
    async def test_notification_includes_quick_action_keyboard(
        self,
        db_session: AsyncSession,
        academic_year: AcademicYear,
        user: User,
    ):
        """Test notification includes inline quick-action keyboard."""
        book_repo = BookRepository(db_session)
        book = await book_repo.create(
            category="textbook",
            title="Math 6eme",
            catalog_year_id=academic_year.id,
        )
        await db_session.commit()

        from bot.database.models import Listing

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
        await db_session.refresh(listing, ["book", "seller"])

        mock_bot = _create_mock_bot()
        from bot.services.notification import NotificationService

        service = NotificationService(mock_bot, db_session)
        await service.notify_seller_status_change(
            listing=listing,
            old_status="active",
            new_status="reserved",
        )

        call_kwargs = mock_bot.send_message.call_args
        reply_markup = call_kwargs.kwargs.get("reply_markup")
        assert reply_markup is not None
        # Check that the keyboard has a "Voir l'annonce" button
        button_texts = [btn.text for row in reply_markup.inline_keyboard for btn in row]
        assert any("Voir l'annonce" in text for text in button_texts)


class TestNotificationServiceAdminNotifications:
    """Tests for admin notification methods."""

    @pytest.mark.asyncio
    async def test_notify_admin_listing_created(
        self,
        db_session: AsyncSession,
        academic_year: AcademicYear,
        user: User,
    ):
        """Test admin notification when listing is created."""
        book_repo = BookRepository(db_session)
        book = await book_repo.create(
            category="textbook",
            title="Math 6eme",
            catalog_year_id=academic_year.id,
        )
        await db_session.commit()

        from bot.database.models import Listing

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
        await db_session.refresh(listing, ["book"])

        mock_bot = _create_mock_bot()

        with patch("bot.config.get_settings") as mock_settings:
            mock_settings.return_value.bot_admin_ids = [999999]
            from bot.services.notification import NotificationService

            service = NotificationService(mock_bot, db_session)
            result = await service.notify_admin_listing_created(
                listing=listing,
                seller=user,
            )

            assert result is True
            mock_bot.send_message.assert_called_once()
            call_kwargs = mock_bot.send_message.call_args
            assert call_kwargs.kwargs["chat_id"] == 999999
            assert "Math 6eme" in call_kwargs.kwargs["text"]

    @pytest.mark.asyncio
    async def test_notify_admin_listing_created_no_admins(
        self,
        db_session: AsyncSession,
        academic_year: AcademicYear,
        user: User,
    ):
        """Test admin notification skipped when no admins configured."""
        book_repo = BookRepository(db_session)
        book = await book_repo.create(
            category="textbook",
            title="Math 6eme",
            catalog_year_id=academic_year.id,
        )
        await db_session.commit()

        from bot.database.models import Listing

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
        await db_session.refresh(listing, ["book"])

        mock_bot = _create_mock_bot()

        with patch("bot.config.get_settings") as mock_settings:
            mock_settings.return_value.bot_admin_ids = []
            from bot.services.notification import NotificationService

            service = NotificationService(mock_bot, db_session)
            result = await service.notify_admin_listing_created(
                listing=listing,
                seller=user,
            )

            assert result is False
            mock_bot.send_message.assert_not_called()

    @pytest.mark.asyncio
    async def test_notify_admin_error(
        self,
        db_session: AsyncSession,
    ):
        """Test admin notification for errors."""
        mock_bot = _create_mock_bot()

        with patch("bot.config.get_settings") as mock_settings:
            mock_settings.return_value.bot_admin_ids = [999999]
            from bot.services.notification import NotificationService

            service = NotificationService(mock_bot, db_session)
            error = ValueError("Something went wrong")
            result = await service.notify_admin_error(
                error=error,
                user_id=12345,
            )

            assert result is True
            mock_bot.send_message.assert_called_once()
            call_kwargs = mock_bot.send_message.call_args
            assert call_kwargs.kwargs["chat_id"] == 999999
            assert "12345" in call_kwargs.kwargs["text"]
            assert "ValueError" in call_kwargs.kwargs["text"]

    @pytest.mark.asyncio
    async def test_notify_admin_error_no_admins(
        self,
        db_session: AsyncSession,
    ):
        """Test admin error notification skipped when no admins configured."""
        mock_bot = _create_mock_bot()

        with patch("bot.config.get_settings") as mock_settings:
            mock_settings.return_value.bot_admin_ids = []
            from bot.services.notification import NotificationService

            service = NotificationService(mock_bot, db_session)
            error = ValueError("Something went wrong")
            result = await service.notify_admin_error(error=error)

            assert result is False
            mock_bot.send_message.assert_not_called()

    @pytest.mark.asyncio
    async def test_notify_admin_error_delivery_failure(
        self,
        db_session: AsyncSession,
    ):
        """Test admin error notification failure does not raise."""
        mock_bot = _create_mock_bot()
        mock_bot.send_message = AsyncMock(side_effect=Exception("Telegram API error"))

        with patch("bot.config.get_settings") as mock_settings:
            mock_settings.return_value.bot_admin_ids = [999999]
            from bot.services.notification import NotificationService

            service = NotificationService(mock_bot, db_session)
            error = ValueError("Something went wrong")
            # Should not raise
            result = await service.notify_admin_error(error=error)

            assert result is False


class TestNotificationServiceEdgeCases:
    """Tests for notification service edge cases."""

    @pytest.mark.asyncio
    async def test_seller_not_found_in_database(
        self,
        db_session: AsyncSession,
        academic_year: AcademicYear,
        user: User,
    ):
        """Test notification when seller user not found in database."""
        book_repo = BookRepository(db_session)
        book = await book_repo.create(
            category="textbook",
            title="Math 6eme",
            catalog_year_id=academic_year.id,
        )
        await db_session.commit()

        from bot.database.models import Listing

        # Create listing with a non-existent seller_id
        listing = Listing(
            book_id=book.id,
            seller_id=99999,  # Non-existent user
            academic_year_id=academic_year.id,
            price=15.00,
            condition="good",
            status="active",
            contact_phone="0612345678",
        )
        db_session.add(listing)
        await db_session.commit()

        # Manually set book and seller relationships for the test
        listing.book = book
        listing.seller = user  # Use the existing user for the seller object

        mock_bot = _create_mock_bot()
        from bot.services.notification import NotificationService

        # Mock the user repo to return None (seller not found)
        service = NotificationService(mock_bot, db_session)
        with patch.object(
            service.user_repo, "get_by_telegram_id", new_callable=AsyncMock
        ) as mock_get:
            mock_get.return_value = None
            result = await service.notify_seller_status_change(
                listing=listing,
                old_status="active",
                new_status="reserved",
            )

            assert result is False
            mock_bot.send_message.assert_not_called()
