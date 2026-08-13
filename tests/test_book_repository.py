"""Tests for BookRepository import methods."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.models import AcademicYear
from bot.database.repository import BookMatchResult, BookRepository


class TestBookRepositoryImport:
    """Tests for BookRepository import methods."""

    @pytest.mark.asyncio
    async def test_create_book(self, db_session: AsyncSession, academic_year: AcademicYear):
        """Test creating a book."""
        repo = BookRepository(db_session)
        book = await repo.create(
            category="textbook",
            title="Mathématiques 6ème",
            catalog_year_id=academic_year.id,
            author="Jean Dupont",
            isbn="9782012345678",
            grade_level="6ème",
            subject="Mathématiques",
            publisher="Hachette",
            year_published=2023,
        )

        assert book.id is not None
        assert book.category == "textbook"
        assert book.title == "Mathématiques 6ème"
        assert book.author == "Jean Dupont"
        assert book.isbn == "9782012345678"
        assert book.grade_level == "6ème"
        assert book.subject == "Mathématiques"
        assert book.publisher == "Hachette"
        assert book.year_published == 2023
        assert book.catalog_year_id == academic_year.id

    @pytest.mark.asyncio
    async def test_create_book_minimal(self, db_session: AsyncSession, academic_year: AcademicYear):
        """Test creating a book with minimal data."""
        repo = BookRepository(db_session)
        book = await repo.create(
            category="literature",
            title="Le Petit Prince",
            catalog_year_id=academic_year.id,
        )

        assert book.id is not None
        assert book.category == "literature"
        assert book.title == "Le Petit Prince"
        assert book.author is None
        assert book.isbn is None
        assert book.grade_level is None
        assert book.subject is None
        assert book.publisher is None
        assert book.year_published is None

    @pytest.mark.asyncio
    async def test_get_by_isbn_found(self, db_session: AsyncSession, academic_year: AcademicYear):
        """Test getting book by ISBN (found)."""
        repo = BookRepository(db_session)
        await repo.create(
            category="textbook",
            title="Mathématiques 6ème",
            catalog_year_id=academic_year.id,
            isbn="9782012345678",
        )

        book = await repo.get_by_isbn("9782012345678", academic_year.id)
        assert book is not None
        assert book.title == "Mathématiques 6ème"

    @pytest.mark.asyncio
    async def test_get_by_isbn_not_found(
        self,
        db_session: AsyncSession,
        academic_year: AcademicYear,
    ):
        """Test getting book by ISBN (not found)."""
        repo = BookRepository(db_session)
        book = await repo.get_by_isbn("9999999999999", academic_year.id)
        assert book is None

    @pytest.mark.asyncio
    async def test_get_by_isbn_different_year(self, db_session: AsyncSession):
        """Test getting book by ISBN in different academic year."""
        repo = BookRepository(db_session)

        # Create two academic years
        from datetime import date

        from bot.database.models import AcademicYear

        year1 = AcademicYear(
            name="2024-2025",
            start_date=date(2024, 9, 1),
            end_date=date(2025, 6, 30),
            is_current=False,
        )
        year2 = AcademicYear(
            name="2025-2026",
            start_date=date(2025, 9, 1),
            end_date=date(2026, 6, 30),
            is_current=True,
        )
        db_session.add_all([year1, year2])
        await db_session.flush()

        # Create book in year1
        await repo.create(
            category="textbook",
            title="Mathématiques 6ème",
            catalog_year_id=year1.id,
            isbn="9782012345678",
        )

        # Should not find in year2
        book = await repo.get_by_isbn("9782012345678", year2.id)
        assert book is None

    @pytest.mark.asyncio
    async def test_find_or_create_new(self, db_session: AsyncSession, academic_year: AcademicYear):
        """Test find_or_create with new book."""
        repo = BookRepository(db_session)
        book, result = await repo.find_or_create(
            category="textbook",
            title="Mathématiques 6ème",
            catalog_year_id=academic_year.id,
            isbn="9782012345678",
        )

        assert book.id is not None
        assert book.title == "Mathématiques 6ème"
        assert result == BookMatchResult.CREATED

    @pytest.mark.asyncio
    async def test_find_or_create_existing_by_isbn(
        self,
        db_session: AsyncSession,
        academic_year: AcademicYear,
    ):
        """Test find_or_create with existing book by ISBN."""
        repo = BookRepository(db_session)

        # Create book
        book1 = await repo.create(
            category="textbook",
            title="Mathématiques 6ème",
            catalog_year_id=academic_year.id,
            isbn="9782012345678",
        )

        # Find or create same book by ISBN
        book2, result = await repo.find_or_create(
            category="textbook",
            title="Mathématiques 6ème (different title)",
            catalog_year_id=academic_year.id,
            isbn="9782012345678",
        )

        assert book1.id == book2.id
        assert book2.title == "Mathématiques 6ème"  # Title should not change
        assert result == BookMatchResult.EXISTING

    @pytest.mark.asyncio
    async def test_find_or_create_existing_by_identity(
        self,
        db_session: AsyncSession,
        academic_year: AcademicYear,
    ):
        """Test find_or_create with existing book by normalized identity (no ISBN)."""
        repo = BookRepository(db_session)

        # Create book without ISBN
        book1 = await repo.create(
            category="textbook",
            title="Mathématiques 6ème",
            catalog_year_id=academic_year.id,
            grade_level="6ème",
            subject="Mathématiques",
        )

        # Find or create same book by identity
        book2, result = await repo.find_or_create(
            category="textbook",
            title="Mathématiques 6ème",
            catalog_year_id=academic_year.id,
            grade_level="6ème",
            subject="Mathématiques",
        )

        assert book1.id == book2.id
        assert result == BookMatchResult.EXISTING

    @pytest.mark.asyncio
    async def test_find_or_create_different_grade_level(
        self,
        db_session: AsyncSession,
        academic_year: AcademicYear,
    ):
        """Test find_or_create with same title but different grade_level."""
        repo = BookRepository(db_session)

        # Create book in 6ème
        book1 = await repo.create(
            category="textbook",
            title="Mathématiques",
            catalog_year_id=academic_year.id,
            grade_level="6ème",
        )

        # Create book in 5ème (different grade level)
        book2, result = await repo.find_or_create(
            category="textbook",
            title="Mathématiques",
            catalog_year_id=academic_year.id,
            grade_level="5ème",
        )

        assert book1.id != book2.id  # Should be different books
        assert result == BookMatchResult.CREATED

    @pytest.mark.asyncio
    async def test_find_or_create_different_subject(
        self,
        db_session: AsyncSession,
        academic_year: AcademicYear,
    ):
        """Test find_or_create with same title but different subject."""
        repo = BookRepository(db_session)

        # Create book with Math subject
        book1 = await repo.create(
            category="textbook",
            title="Manuel",
            catalog_year_id=academic_year.id,
            subject="Mathématiques",
        )

        # Create book with French subject (different subject)
        book2, result = await repo.find_or_create(
            category="textbook",
            title="Manuel",
            catalog_year_id=academic_year.id,
            subject="Français",
        )

        assert book1.id != book2.id  # Should be different books
        assert result == BookMatchResult.CREATED

    @pytest.mark.asyncio
    async def test_find_or_create_same_book_different_year(self, db_session: AsyncSession):
        """Test find_or_create with same book in different academic years."""
        repo = BookRepository(db_session)

        # Create two academic years
        from datetime import date

        from bot.database.models import AcademicYear

        year1 = AcademicYear(
            name="2024-2025",
            start_date=date(2024, 9, 1),
            end_date=date(2025, 6, 30),
            is_current=False,
        )
        year2 = AcademicYear(
            name="2025-2026",
            start_date=date(2025, 9, 1),
            end_date=date(2026, 6, 30),
            is_current=True,
        )
        db_session.add_all([year1, year2])
        await db_session.flush()

        # Create book in year1
        book1 = await repo.create(
            category="textbook",
            title="Mathématiques 6ème",
            catalog_year_id=year1.id,
            isbn="9782012345678",
        )

        # Create same book in year2 (different year = different book)
        book2, result = await repo.find_or_create(
            category="textbook",
            title="Mathématiques 6ème",
            catalog_year_id=year2.id,
            isbn="9782012345678",
        )

        assert book1.id != book2.id  # Different years = different books
        assert result == BookMatchResult.CREATED

    @pytest.mark.asyncio
    async def test_find_or_create_no_isbn(
        self,
        db_session: AsyncSession,
        academic_year: AcademicYear,
    ):
        """Test find_or_create without ISBN uses identity comparison."""
        repo = BookRepository(db_session)

        # Create book without ISBN
        book1, result1 = await repo.find_or_create(
            category="textbook",
            title="Mathématiques 6ème",
            catalog_year_id=academic_year.id,
            isbn=None,
        )

        # Find same book without ISBN (should match by identity)
        book2, result2 = await repo.find_or_create(
            category="textbook",
            title="Mathématiques 6ème",
            catalog_year_id=academic_year.id,
            isbn=None,
        )

        assert book1.id == book2.id  # Should find existing
        assert result1 == BookMatchResult.CREATED
        assert result2 == BookMatchResult.EXISTING

    @pytest.mark.asyncio
    async def test_bulk_create(self, db_session: AsyncSession, academic_year: AcademicYear):
        """Test bulk creating books."""
        repo = BookRepository(db_session)

        books_data = [
            {
                "category": "textbook",
                "title": "Mathématiques 6ème",
                "catalog_year_id": academic_year.id,
                "isbn": "9782012345678",
            },
            {
                "category": "textbook",
                "title": "Histoire-Géographie 5ème",
                "catalog_year_id": academic_year.id,
                "isbn": "9782012345679",
            },
            {
                "category": "literature",
                "title": "Le Petit Prince",
                "catalog_year_id": academic_year.id,
                "isbn": "9782070612758",
            },
        ]

        books = await repo.bulk_create(books_data)

        assert len(books) == 3
        assert books[0].title == "Mathématiques 6ème"
        assert books[1].title == "Histoire-Géographie 5ème"
        assert books[2].title == "Le Petit Prince"

    @pytest.mark.asyncio
    async def test_bulk_create_empty(self, db_session: AsyncSession):
        """Test bulk creating with empty list."""
        repo = BookRepository(db_session)
        books = await repo.bulk_create([])
        assert len(books) == 0

    @pytest.mark.asyncio
    async def test_normalize_for_comparison(self):
        """Test normalization for comparison."""
        assert BookRepository._normalize_for_comparison("Mathématiques") == "mathematiques"
        assert BookRepository._normalize_for_comparison("  Mathématiques  ") == "mathematiques"
        assert BookRepository._normalize_for_comparison("MATHÉMATIQUES") == "mathematiques"
        assert BookRepository._normalize_for_comparison(None) == ""
        assert BookRepository._normalize_for_comparison("") == ""
