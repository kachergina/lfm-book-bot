"""Notification service for user and admin notifications."""

import logging

from aiogram import Bot
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.models import Listing, User
from bot.database.repository import UserRepository
from bot.locale import fr
from bot.utils.helpers import format_price

logger = logging.getLogger(__name__)

# Maps listing status to notification template
_STATUS_NOTIFICATION_MAP: dict[str, str] = {
    "reserved": fr.NOTIF_LISTING_RESERVED,
    "sold": fr.NOTIF_LISTING_SOLD,
    "active": fr.NOTIF_LISTING_ACTIVATED,
    "archived": fr.NOTIF_LISTING_ARCHIVED,
}


def _get_listing_notification_keyboard(listing_id: int) -> InlineKeyboardMarkup:
    """Get inline keyboard for listing notification quick actions.

    Args:
        listing_id: Listing ID.

    Returns:
        Inline keyboard with quick action buttons.
    """
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=fr.BTN_VIEW_LISTING,
                    callback_data=f"mylistings:view:{listing_id}",
                ),
            ],
        ],
    )


class NotificationService:
    """Service for sending Telegram notifications.

    Notifications are best-effort: delivery failures are logged but never
    break the calling operation.
    """

    def __init__(self, bot: Bot, session: AsyncSession) -> None:
        """Initialize notification service.

        Args:
            bot: Aiogram Bot instance for sending messages.
            session: Database session for user lookups.
        """
        self.bot = bot
        self.session = session
        self.user_repo = UserRepository(session)

    async def notify_seller_status_change(
        self,
        listing: Listing,
        old_status: str,
        new_status: str,
    ) -> bool:
        """Notify seller about a listing status change.

        Args:
            listing: The listing whose status changed.
            old_status: Previous status.
            new_status: New status.

        Returns:
            True if notification was sent, False otherwise.
        """
        template = _STATUS_NOTIFICATION_MAP.get(new_status)
        if template is None:
            return False

        seller = await self.user_repo.get_by_telegram_id(listing.seller.telegram_id)
        if seller is None:
            logger.warning(
                "seller_not_found_for_notification listing_id=%s seller_id=%s",
                listing.id,
                listing.seller_id,
            )
            return False

        book_title = listing.book.title if listing.book else "Livre inconnu"
        text = template.format(
            title=book_title,
            price=format_price(listing.price),
        )

        return await self._send_message(
            chat_id=seller.telegram_id,
            text=text,
            reply_markup=_get_listing_notification_keyboard(listing.id),
            context=f"seller_status_change(listing={listing.id}, {old_status}->{new_status})",
        )

    async def notify_admin_listing_created(
        self,
        listing: Listing,
        seller: User,
    ) -> bool:
        """Notify admins when a new listing is published.

        Args:
            listing: The newly created listing.
            seller: The seller who created the listing.

        Returns:
            True if notification was sent, False otherwise.
        """
        from bot.config import get_settings

        settings = get_settings()
        if not settings.bot_admin_ids:
            return False

        book_title = listing.book.title if listing.book else "Livre inconnu"
        seller_name = seller.username or seller.first_name or str(seller.telegram_id)

        text = fr.ADMIN_NOTIF_LISTING_CREATED.format(
            seller=seller_name,
            title=book_title,
            price=format_price(listing.price),
        )

        sent = False
        for admin_id in settings.bot_admin_ids:
            result = await self._send_message(
                chat_id=admin_id,
                text=text,
                context=f"admin_listing_created(listing={listing.id})",
            )
            if result:
                sent = True
        return sent

    async def notify_admin_error(
        self,
        error: Exception,
        user_id: int | None = None,
    ) -> bool:
        """Notify admins about critical/unhandled errors.

        Args:
            error: The exception that occurred.
            user_id: Optional user ID associated with the error.

        Returns:
            True if notification was sent, False otherwise.
        """
        from bot.config import get_settings

        settings = get_settings()
        if not settings.bot_admin_ids:
            return False

        user_str = str(user_id) if user_id else "inconnu"
        error_type = type(error).__name__
        error_msg = str(error)[:200] if str(error) else "Pas de détails"

        text = fr.ADMIN_NOTIF_ERROR_DETAIL.format(
            user_id=user_str,
            error=f"{error_type}: {error_msg}",
        )

        sent = False
        for admin_id in settings.bot_admin_ids:
            result = await self._send_message(
                chat_id=admin_id,
                text=text,
                context=f"admin_error(user={user_id})",
            )
            if result:
                sent = True
        return sent

    async def _send_message(
        self,
        chat_id: int,
        text: str,
        context: str = "",
        reply_markup: InlineKeyboardMarkup | None = None,
    ) -> bool:
        """Send a Telegram message with error handling.

        Args:
            chat_id: Target chat ID (Telegram user ID).
            text: Message text.
            context: Description for logging.
            reply_markup: Optional inline keyboard.

        Returns:
            True if message was sent successfully, False otherwise.
        """
        try:
            await self.bot.send_message(
                chat_id=chat_id,
                text=text,
                reply_markup=reply_markup,
            )
        except Exception:
            logger.exception(
                "notification_delivery_failed chat_id=%s context=%s",
                chat_id,
                context,
            )
            return False
        else:
            logger.info(
                "notification_sent chat_id=%s context=%s",
                chat_id,
                context,
            )
            return True
