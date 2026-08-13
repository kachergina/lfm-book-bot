"""Admin service for user moderation and administrative operations."""

from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.repository import UserRepository


class AdminError(Exception):
    """Raised when admin operation fails."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class AdminService:
    """Service for admin moderation operations."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize service.

        Args:
            session: Database session.
        """
        self.session = session
        self.user_repo = UserRepository(session)

    async def list_users(
        self,
        limit: int = 20,
        offset: int = 0,
    ) -> list[dict]:
        """List users with pagination.

        Args:
            limit: Maximum number of users.
            offset: Number of users to skip.

        Returns:
            List of user info dicts.
        """
        users = await self.user_repo.list_users(limit, offset)
        return [
            {
                "id": u.id,
                "telegram_id": u.telegram_id,
                "username": u.username,
                "first_name": u.first_name,
                "last_name": u.last_name,
                "role": u.role,
                "is_banned": u.is_banned,
                "ban_reason": u.ban_reason,
            }
            for u in users
        ]

    async def search_users(self, query: str) -> list[dict]:
        """Search users by username or name.

        Args:
            query: Search query.

        Returns:
            List of matching user info dicts.
        """
        users = await self.user_repo.search_by_username(query)
        return [
            {
                "id": u.id,
                "telegram_id": u.telegram_id,
                "username": u.username,
                "first_name": u.first_name,
                "last_name": u.last_name,
                "role": u.role,
                "is_banned": u.is_banned,
                "ban_reason": u.ban_reason,
            }
            for u in users
        ]

    async def ban_user(
        self,
        admin_telegram_id: int,
        target_user_id: int,
        reason: str | None = None,
    ) -> dict:
        """Ban a user.

        Args:
            admin_telegram_id: Telegram ID of the admin performing the action.
            target_user_id: Internal ID of the user to ban.
            reason: Ban reason.

        Returns:
            Dict with ban result info.

        Raises:
            AdminError: If operation fails.
        """
        # Prevent admin from banning themselves
        admin_user = await self.user_repo.get_by_telegram_id(admin_telegram_id)
        if admin_user is not None and admin_user.id == target_user_id:
            raise AdminError("Vous ne pouvez pas vous bannir vous-même.")

        # Prevent banning other admins
        target_user = await self.user_repo.get_by_id(target_user_id)
        if target_user is None:
            raise AdminError("Utilisateur non trouvé.")

        if target_user.role == "admin":
            raise AdminError("Impossible de bannir un administrateur.")

        if target_user.is_banned:
            raise AdminError("Cet utilisateur est déjà banni.")

        await self.user_repo.ban_user(target_user_id, reason)
        return {
            "user_id": target_user_id,
            "telegram_id": target_user.telegram_id,
            "username": target_user.username,
            "reason": reason,
        }

    async def unban_user(
        self,
        target_user_id: int,
    ) -> dict:
        """Unban a user.

        Args:
            target_user_id: Internal ID of the user to unban.

        Returns:
            Dict with unban result info.

        Raises:
            AdminError: If operation fails.
        """
        target_user = await self.user_repo.get_by_id(target_user_id)
        if target_user is None:
            raise AdminError("Utilisateur non trouvé.")

        if not target_user.is_banned:
            raise AdminError("Cet utilisateur n'est pas banni.")

        await self.user_repo.unban_user(target_user_id)
        return {
            "user_id": target_user_id,
            "telegram_id": target_user.telegram_id,
            "username": target_user.username,
        }

    async def is_user_banned(self, telegram_id: int) -> bool:
        """Check if a user is banned.

        Args:
            telegram_id: Telegram user ID.

        Returns:
            True if user is banned, False otherwise.
        """
        user = await self.user_repo.get_by_telegram_id(telegram_id)
        if user is None:
            return False
        return user.is_banned
