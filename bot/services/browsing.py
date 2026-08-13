"""Browsing service for catalog navigation."""

from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.models import AcademicYear, Book, Listing
from bot.database.repository import (
    AcademicYearRepository,
    BookRepository,
    ListingRepository,
)


class BrowsingService:
    """Service for catalog browsing operations."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize browsing service.

        Args:
            session: Database session.
        """
        self.session = session
        self.academic_year_repo = AcademicYearRepository(session)
        self.book_repo = BookRepository(session)
        self.listing_repo = ListingRepository(session)

    async def get_current_academic_year(self) -> AcademicYear | None:
        """Get current academic year.

        Returns:
            Current academic year or None.
        """
        return await self.academic_year_repo.get_current()

    async def get_categories(self, catalog_year_id: int) -> list[str]:
        """Get available categories for an academic year.

        Args:
            catalog_year_id: Academic year ID.

        Returns:
            List of category strings.
        """
        return await self.book_repo.get_categories(catalog_year_id)

    async def get_grade_levels(
        self,
        catalog_year_id: int,
        category: str,
    ) -> list[str]:
        """Get available grade levels for a category.

        Args:
            catalog_year_id: Academic year ID.
            category: Book category.

        Returns:
            List of grade level strings.
        """
        return await self.book_repo.get_grade_levels(catalog_year_id, category)

    async def get_subjects(
        self,
        catalog_year_id: int,
        category: str,
        grade_level: str,
    ) -> list[str]:
        """Get available subjects for a category and grade level.

        Args:
            catalog_year_id: Academic year ID.
            category: Book category.
            grade_level: Grade level.

        Returns:
            List of subject strings.
        """
        return await self.book_repo.get_subjects(
            catalog_year_id,
            category,
            grade_level,
        )

    async def get_books(
        self,
        catalog_year_id: int,
        category: str,
        grade_level: str,
        subject: str,
    ) -> list[Book]:
        """Get books matching browsing filters.

        Args:
            catalog_year_id: Academic year ID.
            category: Book category.
            grade_level: Grade level.
            subject: Subject.

        Returns:
            List of matching books.
        """
        return await self.book_repo.get_books_for_browsing(
            catalog_year_id,
            category,
            grade_level,
            subject,
        )

    async def get_books_by_category(
        self,
        catalog_year_id: int,
        category: str,
    ) -> list[Book]:
        """Get all books in a category without grade/subject filters.

        Args:
            catalog_year_id: Academic year ID.
            category: Book category.

        Returns:
            List of books in the category.
        """
        return await self.book_repo.get_books_by_category(catalog_year_id, category)

    async def get_active_listings(
        self,
        book_id: int,
        academic_year_id: int,
    ) -> list[Listing]:
        """Get active listings for a book.

        Args:
            book_id: Book ID.
            academic_year_id: Academic year ID.

        Returns:
            List of active listings.
        """
        return await self.listing_repo.get_active_for_book(
            book_id,
            academic_year_id,
        )
