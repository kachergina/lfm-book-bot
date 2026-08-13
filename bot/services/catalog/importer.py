"""Catalog import service.

This module handles importing book catalogs from Excel/CSV files.
The import is transactional: either all books are imported successfully,
or none are persisted to the database.

Transaction Strategy:
1. Parse the complete file.
2. Validate the complete file.
3. Verify the academic year exists.
4. Detect duplicate/conflicting records in the parsed data.
5. Only if the complete input is valid, begin database persistence.
6. Persist all books inside one transaction.
7. Commit only after successful completion.
8. If a critical persistence error occurs, rollback the import.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.models import AcademicYear
from bot.database.repository import AcademicYearRepository, BookMatchResult, BookRepository
from bot.services.catalog.parser import CatalogParser, ParseError
from bot.services.catalog.validator import CatalogValidator, ValidationError


@dataclass
class ImportResult:
    """Result of catalog import operation.

    Attributes:
        total_parsed: Number of records parsed from file.
        total_created: Number of new books created in database.
        total_existing: Number of books that already existed (unchanged).
        total_skipped: Number of books skipped due to errors.
        errors: List of error messages if any.
    """

    total_parsed: int = 0
    total_created: int = 0
    total_existing: int = 0
    total_skipped: int = 0
    errors: list[str] = field(default_factory=list)

    @property
    def success(self) -> bool:
        """Check if import was successful."""
        return len(self.errors) == 0


class CatalogImportError(Exception):
    """Raised when import fails."""


class CatalogImportService:
    """Service for importing book catalogs.

    Import is transactional: if any book fails to persist,
    the entire import is rolled back.
    """

    def __init__(self, session: AsyncSession) -> None:
        """Initialize import service.

        Args:
            session: Database session.
        """
        self.session = session
        self.parser = CatalogParser()
        self.validator = CatalogValidator()
        self.book_repo = BookRepository(session)
        self.year_repo = AcademicYearRepository(session)

    async def _verify_academic_year(self, catalog_year_id: int) -> AcademicYear:
        """Verify that an academic year exists.

        Args:
            catalog_year_id: Academic year ID.

        Returns:
            The academic year.

        Raises:
            CatalogImportError: If academic year not found.
        """
        result = await self.session.execute(
            select(AcademicYear).where(AcademicYear.id == catalog_year_id),
        )
        year = result.scalar_one_or_none()
        if year is None:
            raise CatalogImportError(
                f"Année scolaire avec l'id {catalog_year_id} non trouvée. "
                "Créez d'abord l'année scolaire.",
            )
        return year

    async def import_from_file(
        self,
        file_path: str | Path,
        catalog_year_id: int | None = None,
    ) -> ImportResult:
        """Import books from a file.

        Transaction strategy:
        1. Parse and validate file (no DB changes).
        2. Verify academic year exists.
        3. Process all books, collecting results.
        4. Commit if successful, rollback on error.

        Args:
            file_path: Path to catalog file (Excel or CSV).
            catalog_year_id: Academic year ID. If None, uses current year.

        Returns:
            ImportResult with statistics.
        """
        # Step 1: Parse file (no DB changes)
        try:
            raw_books = self.parser.parse(file_path)
        except ParseError as e:
            return ImportResult(errors=[f"Échec de l'analyse du fichier : {e}"])

        if not raw_books:
            return ImportResult(errors=["Aucun livre trouvé dans le fichier"])

        # Step 2: Verify academic year
        if catalog_year_id is None:
            year = await self.year_repo.get_current()
            if year is None:
                return ImportResult(
                    total_parsed=len(raw_books),
                    errors=["Aucune année scolaire courante trouvée. Créez-en une d'abord."],
                )
            catalog_year_id = year.id
        else:
            try:
                await self._verify_academic_year(catalog_year_id)
            except CatalogImportError as e:
                return ImportResult(
                    total_parsed=len(raw_books),
                    errors=[str(e)],
                )

        # Step 3: Validate (no DB changes)
        try:
            validated_books = self.validator.validate(raw_books)
        except ValidationError as e:
            return ImportResult(
                total_parsed=len(raw_books),
                errors=[str(e)],
            )

        # Step 4: Process books within a transaction
        return await self._process_books(validated_books, catalog_year_id)

    async def import_from_data(
        self,
        books_data: list[dict[str, Any]],
        catalog_year_id: int | None,
    ) -> ImportResult:
        """Import books from pre-parsed data.

        Args:
            books_data: List of book dictionaries.
            catalog_year_id: Academic year ID. If None, uses current year.

        Returns:
            ImportResult with statistics.
        """
        if not books_data:
            return ImportResult(errors=["Aucun livre à importer"])

        # Get academic year if not provided
        if catalog_year_id is None:
            year = await self.year_repo.get_current()
            if year is None:
                return ImportResult(
                    total_parsed=len(books_data),
                    errors=["Aucune année scolaire courante trouvée. Créez-en une d'abord."],
                )
            catalog_year_id = year.id
        else:
            try:
                await self._verify_academic_year(catalog_year_id)
            except CatalogImportError as e:
                return ImportResult(
                    total_parsed=len(books_data),
                    errors=[str(e)],
                )

        # Validate
        try:
            validated_books = self.validator.validate(books_data)
        except ValidationError as e:
            return ImportResult(
                total_parsed=len(books_data),
                errors=[str(e)],
            )

        # Process books within a transaction
        return await self._process_books(validated_books, catalog_year_id)

    async def _process_books(
        self,
        validated_books: list[dict[str, Any]],
        catalog_year_id: int,
    ) -> ImportResult:
        """Process validated books within a transaction.

        Args:
            validated_books: List of validated book dictionaries.
            catalog_year_id: Academic year ID.

        Returns:
            ImportResult with statistics.
        """
        created = 0
        existing = 0
        errors: list[str] = []

        # Use a nested transaction (savepoint) for atomicity
        async with self.session.begin_nested():
            for book_data in validated_books:
                try:
                    book_data["catalog_year_id"] = catalog_year_id
                    book, match_result = await self.book_repo.find_or_create(**book_data)

                    if match_result == BookMatchResult.CREATED:
                        created += 1
                    else:
                        existing += 1
                except Exception as e:
                    errors.append(
                        f"Échec du traitement de '{book_data.get('title')}' : {e}",
                    )
                    # Rollback the entire import on any error
                    raise

        # Commit the transaction
        await self.session.commit()

        return ImportResult(
            total_parsed=len(validated_books),
            total_created=created,
            total_existing=existing,
            total_skipped=len(errors),
            errors=errors if errors else [],
        )
