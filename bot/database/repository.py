"""Repository layer for database operations."""

import enum
import unicodedata
from datetime import UTC, date
from typing import Any

from sqlalchemy import distinct, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from bot.database.models import AcademicYear, Book, Listing, User


class BookMatchResult(enum.Enum):
    """Result of book duplicate detection."""

    CREATED = "created"
    EXISTING = "existing"


class UserRepository:
    """Repository for user operations."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize repository.

        Args:
            session: Database session.
        """
        self.session = session

    async def get_by_telegram_id(self, telegram_id: int) -> User | None:
        """Get user by Telegram ID.

        Args:
            telegram_id: Telegram user ID.

        Returns:
            User if found, None otherwise.
        """
        result = await self.session.execute(
            select(User).where(User.telegram_id == telegram_id),
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, user_id: int) -> User | None:
        """Get user by internal ID.

        Args:
            user_id: Internal user ID.

        Returns:
            User if found, None otherwise.
        """
        result = await self.session.execute(
            select(User).where(User.id == user_id),
        )
        return result.scalar_one_or_none()

    async def create(
        self,
        telegram_id: int,
        username: str | None = None,
        first_name: str | None = None,
        last_name: str | None = None,
        language_code: str = "fr",
    ) -> User:
        """Create a new user.

        Args:
            telegram_id: Telegram user ID.
            username: Telegram username.
            first_name: User's first name.
            last_name: User's last name.
            language_code: Language code.

        Returns:
            Created user.
        """
        user = User(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
            language_code=language_code,
        )
        self.session.add(user)
        await self.session.flush()
        return user

    async def list_users(
        self,
        limit: int = 20,
        offset: int = 0,
    ) -> list[User]:
        """List users with pagination.

        Args:
            limit: Maximum number of users.
            offset: Number of users to skip.

        Returns:
            List of users.
        """
        result = await self.session.execute(
            select(User).order_by(User.created_at.desc()).limit(limit).offset(offset),
        )
        return list(result.scalars().all())

    async def search_by_username(self, query: str) -> list[User]:
        """Search users by username or name.

        Args:
            query: Search query.

        Returns:
            List of matching users.
        """
        pattern = f"%{query}%"
        result = await self.session.execute(
            select(User)
            .where(
                User.username.ilike(pattern)
                | User.first_name.ilike(pattern)
                | User.last_name.ilike(pattern),
            )
            .limit(20),
        )
        return list(result.scalars().all())

    async def ban_user(
        self,
        user_id: int,
        reason: str | None = None,
    ) -> User | None:
        """Ban a user.

        Args:
            user_id: Internal user ID.
            reason: Ban reason.

        Returns:
            Updated user if found, None otherwise.
        """
        user = await self.get_by_id(user_id)
        if user is None:
            return None
        user.is_banned = True
        user.ban_reason = reason
        await self.session.flush()
        return user

    async def unban_user(self, user_id: int) -> User | None:
        """Unban a user.

        Args:
            user_id: Internal user ID.

        Returns:
            Updated user if found, None otherwise.
        """
        user = await self.get_by_id(user_id)
        if user is None:
            return None
        user.is_banned = False
        user.ban_reason = None
        await self.session.flush()
        return user

    async def count_all(self) -> int:
        result = await self.session.execute(select(func.count(User.id)))
        return result.scalar_one()


class AcademicYearRepository:
    """Repository for academic year operations."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize repository.

        Args:
            session: Database session.
        """
        self.session = session

    async def get_current(self) -> AcademicYear | None:
        """Get current academic year.

        Returns:
            Current academic year if found, None otherwise.
        """
        result = await self.session.execute(
            select(AcademicYear).where(AcademicYear.is_current == True),  # noqa: E712
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, year_id: int) -> AcademicYear | None:
        """Get academic year by ID.

        Args:
            year_id: Academic year ID.

        Returns:
            Academic year if found, None otherwise.
        """
        result = await self.session.execute(
            select(AcademicYear).where(AcademicYear.id == year_id),
        )
        return result.scalar_one_or_none()

    async def get_by_name(self, name: str) -> AcademicYear | None:
        """Get academic year by name.

        Args:
            name: Academic year name (e.g., "2025-2026").

        Returns:
            Academic year if found, None otherwise.
        """
        result = await self.session.execute(
            select(AcademicYear).where(AcademicYear.name == name),
        )
        return result.scalar_one_or_none()

    async def list_all(self) -> list[AcademicYear]:
        """List all academic years ordered by start date descending.

        Returns:
            List of all academic years.
        """
        result = await self.session.execute(
            select(AcademicYear).order_by(AcademicYear.start_date.desc()),
        )
        return list(result.scalars().all())

    async def create(
        self,
        name: str,
        start_date: date,
        end_date: date,
        is_current: bool = False,
    ) -> AcademicYear:
        """Create a new academic year.

        Args:
            name: Year name (e.g., "2025-2026").
            start_date: Start date of the academic year.
            end_date: End date of the academic year.
            is_current: Whether this is the current year.

        Returns:
            Created academic year.
        """
        year = AcademicYear(
            name=name,
            start_date=start_date,
            end_date=end_date,
            is_current=is_current,
        )
        self.session.add(year)
        await self.session.flush()
        return year

    async def set_current(self, year_id: int) -> AcademicYear | None:
        """Set an academic year as current, unsetting all others.

        Args:
            year_id: Academic year ID to set as current.

        Returns:
            Updated academic year if found, None otherwise.
        """
        # Unset all current flags
        result = await self.session.execute(
            select(AcademicYear).where(AcademicYear.is_current == True),  # noqa: E712
        )
        for year in result.scalars().all():
            year.is_current = False

        # Set the target year as current
        target = await self.get_by_id(year_id)
        if target is None:
            return None
        target.is_current = True
        await self.session.flush()
        return target


class BookRepository:
    """Repository for book operations.

    Duplicate Detection Strategy:
    ─────────────────────────────
    1. If ISBN is provided and found within the same academic year → EXISTING
    2. Otherwise, normalize and compare:
       - catalog_year_id
       - category (lowercased, trimmed)
       - title (lowercased, trimmed, accents preserved for display but normalized for comparison)
       - grade_level (lowercased, trimmed)
       - subject (lowercased, trimmed)
    3. All four fields must match for a book to be considered the same entity.
    4. Books from different academic years are NEVER merged.
    5. Two books with the same title but different grade_level are different entities.
    6. Two books with the same title but different subject are different entities.
    """

    def __init__(self, session: AsyncSession) -> None:
        """Initialize repository.

        Args:
            session: Database session.
        """
        self.session = session

    @staticmethod
    def _normalize_for_comparison(value: str | None) -> str:
        """Normalize a string value for duplicate comparison.

        Converts to lowercase, trims whitespace, and normalizes Unicode
        for consistent comparison while preserving the original for display.

        Args:
            value: String value to normalize.

        Returns:
            Normalized string for comparison.
        """
        if value is None:
            return ""
        normalized = str(value).strip().lower()
        normalized = unicodedata.normalize("NFKD", normalized)
        normalized = "".join(c for c in normalized if not unicodedata.combining(c))
        return normalized  # noqa: RET504

    def _build_identity_key(
        self,
        catalog_year_id: int,
        category: str,
        title: str,
        grade_level: str | None,
        subject: str | None,
    ) -> tuple[str, str, str, str, str]:
        """Build a normalized identity key for duplicate comparison.

        Args:
            catalog_year_id: Academic year ID.
            category: Book category.
            title: Book title.
            grade_level: Grade level.
            subject: Subject name.

        Returns:
            Tuple of normalized values for comparison.
        """
        return (
            str(catalog_year_id),
            self._normalize_for_comparison(category),
            self._normalize_for_comparison(title),
            self._normalize_for_comparison(grade_level),
            self._normalize_for_comparison(subject),
        )

    async def get_by_id(self, book_id: int) -> Book | None:
        """Get book by ID.

        Args:
            book_id: Book ID.

        Returns:
            Book if found, None otherwise.
        """
        result = await self.session.execute(select(Book).where(Book.id == book_id))
        return result.scalar_one_or_none()

    async def get_by_isbn(self, isbn: str, catalog_year_id: int) -> Book | None:
        """Get book by ISBN within a catalog year.

        Args:
            isbn: ISBN-13 string.
            catalog_year_id: Academic year ID.

        Returns:
            Book if found, None otherwise.
        """
        result = await self.session.execute(
            select(Book).where(
                Book.isbn == isbn,
                Book.catalog_year_id == catalog_year_id,
            ),
        )
        return result.scalar_one_or_none()

    async def find_existing(
        self,
        catalog_year_id: int,
        category: str,
        title: str,
        isbn: str | None = None,
        grade_level: str | None = None,
        subject: str | None = None,
    ) -> Book | None:
        """Find an existing book that matches the given identity.

        Strategy:
        1. If ISBN is provided, check ISBN match first (strongest identifier).
        2. Otherwise, compare normalized identity (year + category + title + grade + subject).

        Args:
            catalog_year_id: Academic year ID.
            category: Book category.
            title: Book title.
            isbn: ISBN (optional).
            grade_level: Grade level (optional).
            subject: Subject name (optional).

        Returns:
            Matching book if found, None otherwise.
        """
        # Strongest match: ISBN within same year
        if isbn:
            existing = await self.get_by_isbn(isbn, catalog_year_id)
            if existing:
                return existing

        # Fallback: normalized identity comparison
        target_key = self._build_identity_key(
            catalog_year_id,
            category,
            title,
            grade_level,
            subject,
        )

        result = await self.session.execute(
            select(Book).where(Book.catalog_year_id == catalog_year_id),
        )
        all_books = result.scalars().all()

        for book in all_books:
            book_key = self._build_identity_key(
                book.catalog_year_id,
                book.category,
                book.title,
                book.grade_level,
                book.subject,
            )
            if book_key == target_key:
                return book

        return None

    async def create(
        self,
        category: str,
        title: str,
        catalog_year_id: int,
        author: str | None = None,
        isbn: str | None = None,
        grade_level: str | None = None,
        subject: str | None = None,
        publisher: str | None = None,
        year_published: int | None = None,
        cover_image_url: str | None = None,
    ) -> Book:
        """Create a new book.

        Args:
            category: Book category ('textbook' or 'literature').
            title: Book title.
            catalog_year_id: Academic year ID.
            author: Book author.
            isbn: ISBN-13.
            grade_level: Grade level.
            subject: Subject name.
            publisher: Publisher name.
            year_published: Year published.
            cover_image_url: Cover image URL.

        Returns:
            Created book.
        """
        book = Book(
            category=category,
            title=title,
            catalog_year_id=catalog_year_id,
            author=author,
            isbn=isbn,
            grade_level=grade_level,
            subject=subject,
            publisher=publisher,
            year_published=year_published,
            cover_image_url=cover_image_url,
        )
        self.session.add(book)
        await self.session.flush()
        return book

    async def find_or_create(
        self,
        category: str,
        title: str,
        catalog_year_id: int,
        author: str | None = None,
        isbn: str | None = None,
        grade_level: str | None = None,
        subject: str | None = None,
        publisher: str | None = None,
        year_published: int | None = None,
        cover_image_url: str | None = None,
    ) -> tuple[Book, BookMatchResult]:
        """Find an existing book or create a new one.

        Duplicate detection uses the strategy documented in the class docstring.
        If an existing book is found, it is returned unchanged (no overwrite).
        If no match is found, a new book is created.

        Args:
            category: Book category ('textbook' or 'literature').
            title: Book title.
            catalog_year_id: Academic year ID.
            author: Book author.
            isbn: ISBN-13.
            grade_level: Grade level.
            subject: Subject name.
            publisher: Publisher name.
            year_published: Year published.
            cover_image_url: Cover image URL.

        Returns:
            Tuple of (book, BookMatchResult) indicating whether book was
            created or already existed.
        """
        existing = await self.find_existing(
            catalog_year_id=catalog_year_id,
            category=category,
            title=title,
            isbn=isbn,
            grade_level=grade_level,
            subject=subject,
        )

        if existing:
            return existing, BookMatchResult.EXISTING

        book = await self.create(
            category=category,
            title=title,
            catalog_year_id=catalog_year_id,
            author=author,
            isbn=isbn,
            grade_level=grade_level,
            subject=subject,
            publisher=publisher,
            year_published=year_published,
            cover_image_url=cover_image_url,
        )
        return book, BookMatchResult.CREATED

    async def bulk_create(
        self,
        books_data: list[dict[str, Any]],
    ) -> list[Book]:
        """Bulk create books.

        Args:
            books_data: List of dicts with book data.

        Returns:
            List of created books.
        """
        books = []
        for data in books_data:
            book = Book(**data)
            self.session.add(book)
            books.append(book)
        await self.session.flush()
        return books

    async def get_categories(self, catalog_year_id: int) -> list[str]:
        """Get distinct categories for an academic year.

        Args:
            catalog_year_id: Academic year ID.

        Returns:
            List of distinct category strings.
        """
        result = await self.session.execute(
            select(distinct(Book.category)).where(
                Book.catalog_year_id == catalog_year_id,
            ),
        )
        return [row[0] for row in result.all()]

    async def get_grade_levels(
        self,
        catalog_year_id: int,
        category: str,
    ) -> list[str]:
        """Get distinct grade levels for a category.

        Args:
            catalog_year_id: Academic year ID.
            category: Book category.

        Returns:
            List of distinct grade level strings.
        """
        result = await self.session.execute(
            select(distinct(Book.grade_level)).where(
                Book.catalog_year_id == catalog_year_id,
                Book.category == category,
                Book.grade_level.isnot(None),
                Book.grade_level != "",
            ),
        )
        return [row[0] for row in result.all()]

    async def get_subjects(
        self,
        catalog_year_id: int,
        category: str,
        grade_level: str,
    ) -> list[str]:
        """Get distinct subjects for a category and grade level.

        Args:
            catalog_year_id: Academic year ID.
            category: Book category.
            grade_level: Grade level.

        Returns:
            List of distinct subject strings.
        """
        result = await self.session.execute(
            select(distinct(Book.subject)).where(
                Book.catalog_year_id == catalog_year_id,
                Book.category == category,
                Book.grade_level == grade_level,
                Book.subject.isnot(None),
            ),
        )
        return [row[0] for row in result.all()]

    async def get_books_for_browsing(
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
        result = await self.session.execute(
            select(Book).where(
                Book.catalog_year_id == catalog_year_id,
                Book.category == category,
                Book.grade_level == grade_level,
                Book.subject == subject,
            ),
        )
        return list(result.scalars().all())

    async def get_books_by_category(
        self,
        catalog_year_id: int,
        category: str,
    ) -> list[Book]:
        """Get all books in a category (no grade/subject filter).

        Args:
            catalog_year_id: Academic year ID.
            category: Book category.

        Returns:
            List of books in the category.
        """
        result = await self.session.execute(
            select(Book)
            .where(
                Book.catalog_year_id == catalog_year_id,
                Book.category == category,
            )
            .order_by(Book.title),
        )
        return list(result.scalars().all())


class ListingRepository:
    """Repository for listing operations."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize repository.

        Args:
            session: Database session.
        """
        self.session = session

    async def get_by_id(self, listing_id: int) -> Listing | None:
        """Get listing by ID.

        Args:
            listing_id: Listing ID.

        Returns:
            Listing if found, None otherwise.
        """
        result = await self.session.execute(
            select(Listing).where(Listing.id == listing_id),
        )
        return result.scalar_one_or_none()

    async def get_active_for_book(
        self,
        book_id: int,
        academic_year_id: int,
    ) -> list[Listing]:
        """Get active listings for a book.

        Args:
            book_id: Book ID.
            academic_year_id: Academic year ID.

        Returns:
            List of active listings with seller info.
        """
        result = await self.session.execute(
            select(Listing)
            .options(selectinload(Listing.seller))
            .where(
                Listing.book_id == book_id,
                Listing.academic_year_id == academic_year_id,
                Listing.status == "active",
            ),
        )
        return list(result.scalars().all())

    async def get_user_listings(
        self,
        seller_id: int,
        status: str | None = None,
    ) -> list[Listing]:
        """Get listings for a specific user, optionally filtered by status.

        Args:
            seller_id: User (seller) ID.
            status: Optional status filter.

        Returns:
            List of listings with book info loaded.
        """
        query = (
            select(Listing)
            .options(selectinload(Listing.book))
            .where(Listing.seller_id == seller_id)
        )
        if status is not None:
            query = query.where(Listing.status == status)
        query = query.order_by(Listing.created_at.desc())
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_user_listing_by_id(
        self,
        listing_id: int,
        seller_id: int,
    ) -> Listing | None:
        """Get a specific listing owned by a user.

        Args:
            listing_id: Listing ID.
            seller_id: User (seller) ID.

        Returns:
            Listing if found and owned by user, None otherwise.
        """
        result = await self.session.execute(
            select(Listing)
            .options(selectinload(Listing.book), selectinload(Listing.seller))
            .where(
                Listing.id == listing_id,
                Listing.seller_id == seller_id,
            ),
        )
        return result.scalar_one_or_none()

    async def create_listing(
        self,
        book_id: int,
        seller_id: int,
        academic_year_id: int,
        price: float,
        condition: str,
        contact_phone: str,
        contact_method: str = "phone",
        description: str | None = None,
        photos: list[str] | None = None,
    ) -> Listing:
        """Create a new listing.

        Args:
            book_id: Book ID.
            seller_id: User (seller) ID.
            academic_year_id: Academic year ID.
            price: Listing price.
            condition: Book condition.
            contact_phone: Seller's contact value (phone or telegram).
            contact_method: Contact method ('phone' or 'telegram').
            description: Optional description.
            photos: Optional list of Telegram file_ids.

        Returns:
            Created listing.
        """
        listing = Listing(
            book_id=book_id,
            seller_id=seller_id,
            academic_year_id=academic_year_id,
            price=price,
            condition=condition,
            contact_phone=contact_phone,
            contact_method=contact_method,
            description=description,
            photos=photos,
            status="active",
        )
        self.session.add(listing)
        await self.session.flush()
        return listing

    async def update_status(
        self,
        listing_id: int,
        new_status: str,
    ) -> Listing | None:
        """Update listing status with appropriate timestamp.

        Args:
            listing_id: Listing ID.
            new_status: New status value.

        Returns:
            Updated listing if found, None otherwise.
        """
        from datetime import datetime

        listing = await self.get_by_id(listing_id)
        if listing is None:
            return None

        listing.status = new_status
        now = datetime.now(UTC)

        if new_status == "reserved":
            listing.reserved_at = now
        elif new_status == "sold":
            listing.sold_at = now
        elif new_status == "archived":
            listing.archived_at = now

        await self.session.flush()
        return listing

    async def update_field(
        self,
        listing_id: int,
        field: str,
        value: object,
    ) -> Listing | None:
        """Update a single field on a listing.

        Args:
            listing_id: Listing ID.
            field: Field name to update.
            value: New value.

        Returns:
            Updated listing if found, None otherwise.
        """
        listing = await self.get_by_id(listing_id)
        if listing is None:
            return None

        if not hasattr(listing, field):
            return None

        setattr(listing, field, value)
        await self.session.flush()
        return listing

    async def count_active_by_user(self, seller_id: int) -> int:
        """Count active listings for a user.

        Args:
            seller_id: User (seller) ID.

        Returns:
            Number of active listings.
        """
        from sqlalchemy import func as sqlfunc

        result = await self.session.execute(
            select(sqlfunc.count(Listing.id)).where(
                Listing.seller_id == seller_id,
                Listing.status == "active",
            ),
        )
        return result.scalar() or 0

    async def get_active_reserved_by_year(
        self,
        academic_year_id: int,
    ) -> list[Listing]:
        """Get all active and reserved listings for an academic year.

        Args:
            academic_year_id: Academic year ID.

        Returns:
            List of active/reserved listings with seller and book info.
        """
        result = await self.session.execute(
            select(Listing)
            .options(selectinload(Listing.seller), selectinload(Listing.book))
            .where(
                Listing.academic_year_id == academic_year_id,
                Listing.status.in_(["active", "reserved"]),
            ),
        )
        return list(result.scalars().all())

    async def bulk_archive_by_year(self, academic_year_id: int) -> int:
        """Archive all active and reserved listings for an academic year.

        Args:
            academic_year_id: Academic year ID.

        Returns:
            Number of listings archived.
        """
        from datetime import datetime

        result = await self.session.execute(
            select(Listing).where(
                Listing.academic_year_id == academic_year_id,
                Listing.status.in_(["active", "reserved"]),
            ),
        )
        listings = result.scalars().all()
        now = datetime.now(UTC)
        count = 0
        for listing in listings:
            listing.status = "archived"
            listing.archived_at = now
            count += 1
        if count > 0:
            await self.session.flush()
        return count

    async def get_expired_listings(self, expiry_days: int) -> list[Listing]:
        """Get active listings that have passed their expiry date.

        Args:
            expiry_days: Number of days after creation for expiry.

        Returns:
            List of expired listings with seller and book info.
        """
        from datetime import datetime, timedelta

        cutoff = datetime.now(UTC) - timedelta(days=expiry_days)
        result = await self.session.execute(
            select(Listing)
            .options(selectinload(Listing.seller), selectinload(Listing.book))
            .where(
                Listing.status == "active",
                Listing.created_at <= cutoff,
            ),
        )
        return list(result.scalars().all())

    async def bulk_expire(self, listing_ids: list[int]) -> int:
        """Mark listings as expired.

        Args:
            listing_ids: List of listing IDs to expire.

        Returns:
            Number of listings expired.
        """
        from datetime import datetime

        if not listing_ids:
            return 0

        result = await self.session.execute(
            select(Listing).where(Listing.id.in_(listing_ids)),
        )
        listings = result.scalars().all()
        now = datetime.now(UTC)
        count = 0
        for listing in listings:
            if listing.status == "active":
                listing.status = "expired"
                listing.expires_at = now
                count += 1
        if count > 0:
            await self.session.flush()
        return count

    async def count_all(self) -> int:
        result = await self.session.execute(select(func.count(Listing.id)))
        return result.scalar_one()

    async def count_sold(self) -> int:
        result = await self.session.execute(
            select(func.count(Listing.id)).where(Listing.status == "sold"),
        )
        return result.scalar_one()
