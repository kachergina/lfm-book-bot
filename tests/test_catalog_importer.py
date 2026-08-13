"""Tests for catalog import service."""

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.models import AcademicYear, Book
from bot.services.catalog.importer import CatalogImportService, ImportResult


class TestCatalogImportService:
    """Tests for CatalogImportService."""

    @pytest.mark.asyncio
    async def test_import_from_file_excel(
        self,
        db_session: AsyncSession,
        academic_year: AcademicYear,
        sample_excel_file: str,
    ):
        """Test importing from Excel file."""
        service = CatalogImportService(db_session)
        result = await service.import_from_file(sample_excel_file, academic_year.id)

        assert result.success is True
        assert result.total_parsed == 3
        assert result.total_created == 3
        assert result.total_existing == 0
        assert result.total_skipped == 0
        assert len(result.errors) == 0

    @pytest.mark.asyncio
    async def test_import_from_file_csv(
        self,
        db_session: AsyncSession,
        academic_year: AcademicYear,
        sample_csv_file: str,
    ):
        """Test importing from CSV file."""
        service = CatalogImportService(db_session)
        result = await service.import_from_file(sample_csv_file, academic_year.id)

        assert result.success is True
        assert result.total_parsed == 3
        assert result.total_created == 3
        assert result.total_existing == 0
        assert result.total_skipped == 0
        assert len(result.errors) == 0

    @pytest.mark.asyncio
    async def test_import_from_file_not_found(self, db_session: AsyncSession):
        """Test importing from non-existent file."""
        service = CatalogImportService(db_session)
        result = await service.import_from_file("/nonexistent/file.xlsx")

        assert result.success is False
        assert len(result.errors) > 0
        assert "Échec de l'analyse du fichier" in result.errors[0]

    @pytest.mark.asyncio
    async def test_import_from_file_empty(
        self,
        db_session: AsyncSession,
        academic_year: AcademicYear,
        empty_excel_file: str,
    ):
        """Test importing from empty file."""
        service = CatalogImportService(db_session)
        result = await service.import_from_file(empty_excel_file, academic_year.id)

        assert result.success is False
        assert result.total_parsed == 0
        assert len(result.errors) > 0
        assert "Échec de l'analyse du fichier" in result.errors[0]

    @pytest.mark.asyncio
    async def test_import_from_data(
        self,
        db_session: AsyncSession,
        academic_year: AcademicYear,
        sample_books_data: list[dict],
    ):
        """Test importing from pre-parsed data."""
        service = CatalogImportService(db_session)
        result = await service.import_from_data(sample_books_data, academic_year.id)

        assert result.success is True
        assert result.total_parsed == 3
        assert result.total_created == 3
        assert result.total_existing == 0
        assert result.total_skipped == 0
        assert len(result.errors) == 0

    @pytest.mark.asyncio
    async def test_import_from_data_empty(
        self,
        db_session: AsyncSession,
        academic_year: AcademicYear,
    ):
        """Test importing from empty data."""
        service = CatalogImportService(db_session)
        result = await service.import_from_data([], academic_year.id)

        assert result.success is False
        assert result.total_parsed == 0
        assert len(result.errors) > 0
        assert "Aucun livre à importer" in result.errors[0]

    @pytest.mark.asyncio
    async def test_import_from_data_invalid(
        self,
        db_session: AsyncSession,
        academic_year: AcademicYear,
        invalid_books_data: list[dict],
    ):
        """Test importing invalid data."""
        service = CatalogImportService(db_session)
        result = await service.import_from_data(invalid_books_data, academic_year.id)

        assert result.success is False
        assert result.total_parsed == 3
        assert len(result.errors) > 0

    @pytest.mark.asyncio
    async def test_import_duplicate_isbn(
        self,
        db_session: AsyncSession,
        academic_year: AcademicYear,
        sample_books_data: list[dict],
    ):
        """Test importing duplicate ISBN books."""
        service = CatalogImportService(db_session)

        # First import
        result1 = await service.import_from_data(sample_books_data, academic_year.id)
        assert result1.success is True
        assert result1.total_created == 3
        assert result1.total_existing == 0

        # Second import (duplicates)
        result2 = await service.import_from_data(sample_books_data, academic_year.id)
        assert result2.success is True
        assert result2.total_created == 0
        assert result2.total_existing == 3  # All should be found as existing

    @pytest.mark.asyncio
    async def test_import_creates_books_in_database(
        self,
        db_session: AsyncSession,
        academic_year: AcademicYear,
        sample_books_data: list[dict],
    ):
        """Test that import creates books in database."""
        service = CatalogImportService(db_session)
        await service.import_from_data(sample_books_data, academic_year.id)

        # Check database
        count = await db_session.scalar(select(func.count(Book.id)))
        assert count == 3

    @pytest.mark.asyncio
    async def test_import_preserves_book_data(
        self,
        db_session: AsyncSession,
        academic_year: AcademicYear,
        sample_books_data: list[dict],
    ):
        """Test that import preserves book data correctly."""
        service = CatalogImportService(db_session)
        await service.import_from_data(sample_books_data, academic_year.id)

        # Check first book
        result = await db_session.execute(
            select(Book).where(Book.title == "Mathématiques 6ème"),
        )
        book = result.scalar_one()

        assert book.category == "textbook"
        assert book.author == "Jean Dupont"
        assert book.isbn == "9782012345678"
        assert book.grade_level == "6ème"
        assert book.subject == "Mathématiques"
        assert book.publisher == "Hachette"
        assert book.year_published == 2023
        assert book.catalog_year_id == academic_year.id

    @pytest.mark.asyncio
    async def test_import_without_academic_year(
        self,
        db_session: AsyncSession,
        sample_books_data: list[dict],
    ):
        """Test import without specifying academic year (should use current)."""
        service = CatalogImportService(db_session)
        result = await service.import_from_data(sample_books_data, None)

        assert result.success is False
        assert len(result.errors) > 0
        assert "Aucune année scolaire courante trouvée" in result.errors[0]

    @pytest.mark.asyncio
    async def test_import_invalid_academic_year(
        self,
        db_session: AsyncSession,
        sample_books_data: list[dict],
    ):
        """Test import with non-existent academic year."""
        service = CatalogImportService(db_session)
        result = await service.import_from_data(sample_books_data, 99999)

        assert result.success is False
        assert len(result.errors) > 0
        assert "non trouvée" in result.errors[0]

    @pytest.mark.asyncio
    async def test_import_result_success_property(self):
        """Test ImportResult success property."""
        result1 = ImportResult(total_parsed=3, total_created=3)
        assert result1.success is True

        result2 = ImportResult(total_parsed=3, errors=["Error"])
        assert result2.success is False

        result3 = ImportResult(total_parsed=3)
        assert result3.success is True

    @pytest.mark.asyncio
    async def test_import_duplicate_without_isbn_same_title_same_grade(
        self,
        db_session: AsyncSession,
        academic_year: AcademicYear,
    ):
        """Test duplicate detection without ISBN - same title and grade."""
        service = CatalogImportService(db_session)

        books = [
            {
                "category": "textbook",
                "title": "Mathématiques 6ème",
                "grade_level": "6ème",
                "subject": "Mathématiques",
            },
        ]

        # First import
        result1 = await service.import_from_data(books, academic_year.id)
        assert result1.total_created == 1

        # Second import - should find existing
        result2 = await service.import_from_data(books, academic_year.id)
        assert result2.total_created == 0
        assert result2.total_existing == 1

    @pytest.mark.asyncio
    async def test_import_duplicate_without_isbn_same_title_different_grade(
        self,
        db_session: AsyncSession,
        academic_year: AcademicYear,
    ):
        """Test duplicate detection without ISBN - same title but different grade."""
        service = CatalogImportService(db_session)

        books_6eme = [
            {
                "category": "textbook",
                "title": "Mathématiques",
                "grade_level": "6ème",
            },
        ]

        books_5eme = [
            {
                "category": "textbook",
                "title": "Mathématiques",
                "grade_level": "5ème",
            },
        ]

        # Import 6ème
        result1 = await service.import_from_data(books_6eme, academic_year.id)
        assert result1.total_created == 1

        # Import 5ème - should create new (different grade)
        result2 = await service.import_from_data(books_5eme, academic_year.id)
        assert result2.total_created == 1

        # Check both exist
        count = await db_session.scalar(select(func.count(Book.id)))
        assert count == 2

    @pytest.mark.asyncio
    async def test_import_same_book_different_academic_years(self, db_session: AsyncSession):
        """Test same book in different academic years."""
        service = CatalogImportService(db_session)

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
        await db_session.commit()

        books = [
            {
                "category": "textbook",
                "title": "Mathématiques 6ème",
                "isbn": "9782012345678",
            },
        ]

        # Import to year1
        result1 = await service.import_from_data(books, year1.id)
        assert result1.total_created == 1

        # Import to year2 - should create new (different year)
        result2 = await service.import_from_data(books, year2.id)
        assert result2.total_created == 1

        # Check both exist
        count = await db_session.scalar(select(func.count(Book.id)))
        assert count == 2

    @pytest.mark.asyncio
    async def test_import_validation_failure_no_database_changes(
        self,
        db_session: AsyncSession,
        academic_year: AcademicYear,
    ):
        """Test that validation failure causes no database changes."""
        service = CatalogImportService(db_session)

        # Try to import invalid data
        invalid_books = [
            {"category": None, "title": ""},  # Missing both required fields
        ]

        result = await service.import_from_data(invalid_books, academic_year.id)
        assert result.success is False

        # Check no books were created
        count = await db_session.scalar(select(func.count(Book.id)))
        assert count == 0

    @pytest.mark.asyncio
    async def test_import_result_counters(
        self,
        db_session: AsyncSession,
        academic_year: AcademicYear,
    ):
        """Test import result counters are accurate."""
        service = CatalogImportService(db_session)

        books = [
            {"category": "textbook", "title": "Book 1", "isbn": "9782012345678"},
            {"category": "textbook", "title": "Book 2", "isbn": "9782012345679"},
        ]

        # First import - should create 2
        result1 = await service.import_from_data(books, academic_year.id)
        assert result1.total_created == 2
        assert result1.total_existing == 0

        # Second import - should find 2 existing
        result2 = await service.import_from_data(books, academic_year.id)
        assert result2.total_created == 0
        assert result2.total_existing == 2
