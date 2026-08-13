"""Academic year management service."""

from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.models import AcademicYear
from bot.database.repository import AcademicYearRepository, ListingRepository


class AcademicYearError(Exception):
    """Raised when academic year operation fails."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class AcademicYearService:
    """Service for academic year management and transitions."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize service.

        Args:
            session: Database session.
        """
        self.session = session
        self.year_repo = AcademicYearRepository(session)
        self.listing_repo = ListingRepository(session)

    async def list_years(self) -> list[AcademicYear]:
        """List all academic years.

        Returns:
            List of academic years ordered by start date descending.
        """
        return await self.year_repo.list_all()

    async def get_current_year(self) -> AcademicYear | None:
        """Get the current academic year.

        Returns:
            Current academic year or None.
        """
        return await self.year_repo.get_current()

    async def get_year_by_id(self, year_id: int) -> AcademicYear:
        """Get academic year by ID.

        Args:
            year_id: Academic year ID.

        Returns:
            The academic year.

        Raises:
            AcademicYearError: If year not found.
        """
        year = await self.year_repo.get_by_id(year_id)
        if year is None:
            raise AcademicYearError("Année scolaire non trouvée.")
        return year

    async def create_year(
        self,
        name: str,
        start_date: date,
        end_date: date,
    ) -> AcademicYear:
        """Create a new academic year.

        Args:
            name: Year name (e.g., "2025-2026").
            start_date: Start date.
            end_date: End date.

        Returns:
            Created academic year.

        Raises:
            AcademicYearError: If validation fails.
        """
        # Validate name format
        if not name or len(name.strip()) < 4:
            raise AcademicYearError("Le nom de l'année scolaire est invalide.")

        # Validate dates
        if end_date <= start_date:
            raise AcademicYearError("La date de fin doit être postérieure à la date de début.")

        # Check name uniqueness
        existing = await self.year_repo.get_by_name(name.strip())
        if existing is not None:
            raise AcademicYearError(f"L'année scolaire « {name} » existe déjà.")

        return await self.year_repo.create(
            name=name.strip(),
            start_date=start_date,
            end_date=end_date,
        )

    async def set_current_year(self, year_id: int) -> AcademicYear:
        """Set an academic year as current.

        Args:
            year_id: Academic year ID.

        Returns:
            Updated academic year.

        Raises:
            AcademicYearError: If year not found.
        """
        year = await self.year_repo.set_current(year_id)
        if year is None:
            raise AcademicYearError("Année scolaire non trouvée.")
        return year

    async def transition_to_year(
        self,
        target_year_id: int,
    ) -> dict[str, object]:
        """Transition to a new academic year.

        This operation:
        1. Validates the target year exists and is not already current.
        2. Archives all active/reserved listings from the old year.
        3. Sets the old year as not current.
        4. Sets the new year as current.

        Args:
            target_year_id: ID of the year to activate.

        Returns:
            Dict with transition results (archived_count, old_year, new_year).

        Raises:
            AcademicYearError: If transition fails.
        """
        # 1. Validate target year
        target_year = await self.year_repo.get_by_id(target_year_id)
        if target_year is None:
            raise AcademicYearError("L'année scolaire cible n'existe pas.")

        # 2. Get current year
        current_year = await self.year_repo.get_current()

        # 3. If target is already current, nothing to do
        if current_year is not None and current_year.id == target_year_id:
            raise AcademicYearError("Cette année scolaire est déjà l'année courante.")

        # 4. Archive active/reserved listings from old year
        archived_count = 0
        if current_year is not None:
            archived_count = await self.listing_repo.bulk_archive_by_year(
                current_year.id,
            )

        # 5. Unset old year, set new year as current
        await self.year_repo.set_current(target_year_id)

        return {
            "archived_count": archived_count,
            "old_year": current_year,
            "new_year": target_year,
        }

    async def get_affected_sellers(
        self,
        academic_year_id: int,
    ) -> list[int]:
        """Get unique seller IDs with active/reserved listings for a year.

        Args:
            academic_year_id: Academic year ID.

        Returns:
            List of unique seller telegram_ids.
        """
        listings = await self.listing_repo.get_active_reserved_by_year(
            academic_year_id,
        )
        seller_ids: set[int] = set()
        for listing in listings:
            if listing.seller is not None:
                seller_ids.add(listing.seller.telegram_id)
        return list(seller_ids)
