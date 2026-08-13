"""Shared test fixtures."""

import csv
import os
from datetime import date
from unittest.mock import patch

import openpyxl
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from bot.database.base import Base
from bot.database.models import AcademicYear, User
from bot.database.repository import UserRepository


@pytest.fixture(autouse=True)
def env_vars() -> None:
    """Set up test environment variables."""
    test_env = {
        "TELEGRAM_BOT_TOKEN": "test-token-123456789",
        "DATABASE_URL": "sqlite+aiosqlite:///:memory:",
        "ENVIRONMENT": "test",
    }
    with patch.dict(os.environ, test_env, clear=False):
        yield


@pytest_asyncio.fixture
async def db_session():
    """Create a test database session."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session

    await engine.dispose()


@pytest_asyncio.fixture
async def academic_year(db_session: AsyncSession) -> AcademicYear:
    """Create a test academic year."""
    year = AcademicYear(
        name="2025-2026",
        start_date=date(2025, 9, 1),
        end_date=date(2026, 6, 30),
        is_current=True,
    )
    db_session.add(year)
    await db_session.commit()
    return year


@pytest_asyncio.fixture
async def user(db_session: AsyncSession) -> User:
    """Create a test user."""
    repo = UserRepository(db_session)
    return await repo.create(
        telegram_id=123456789,
        username="test_user",
        first_name="Test",
        last_name="User",
    )


@pytest.fixture
def sample_books_data() -> list[dict]:
    """Create sample book data for testing."""
    return [
        {
            "category": "textbook",
            "title": "Mathématiques 6ème",
            "author": "Jean Dupont",
            "isbn": "9782012345678",
            "grade_level": "6ème",
            "subject": "Mathématiques",
            "publisher": "Hachette",
            "year_published": 2023,
            "cover_image_url": None,
        },
        {
            "category": "textbook",
            "title": "Histoire-Géographie 5ème",
            "author": "Marie Martin",
            "isbn": "9782012345679",
            "grade_level": "5ème",
            "subject": "Histoire-Géographie",
            "publisher": "Nathan",
            "year_published": 2023,
            "cover_image_url": None,
        },
        {
            "category": "literature",
            "title": "Le Petit Prince",
            "author": "Antoine de Saint-Exupéry",
            "isbn": "9782070612758",
            "grade_level": None,
            "subject": "Littérature",
            "publisher": "Gallimard",
            "year_published": 1943,
            "cover_image_url": None,
        },
    ]


@pytest.fixture
def sample_excel_file(tmp_path) -> str:
    """Create a sample Excel file for testing."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Catalogue"

    # Headers
    headers = [
        "category",
        "title",
        "author",
        "isbn",
        "grade_level",
        "subject",
        "publisher",
        "year_published",
    ]
    ws.append(headers)

    # Data rows
    ws.append(
        [
            "textbook",
            "Mathématiques 6ème",
            "Jean Dupont",
            "9782012345678",
            "6ème",
            "Mathématiques",
            "Hachette",
            2023,
        ]
    )
    ws.append(
        [
            "textbook",
            "Histoire-Géographie 5ème",
            "Marie Martin",
            "9782012345679",
            "5ème",
            "Histoire-Géographie",
            "Nathan",
            2023,
        ]
    )
    ws.append(
        [
            "literature",
            "Le Petit Prince",
            "Antoine de Saint-Exupéry",
            "9782070612758",
            None,
            "Littérature",
            "Gallimard",
            1943,
        ]
    )

    file_path = tmp_path / "test_catalog.xlsx"
    wb.save(file_path)
    wb.close()

    return str(file_path)


@pytest.fixture
def sample_csv_file(tmp_path) -> str:
    """Create a sample CSV file for testing."""
    file_path = tmp_path / "test_catalog.csv"

    with file_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "category",
                "title",
                "author",
                "isbn",
                "grade_level",
                "subject",
                "publisher",
                "year_published",
            ]
        )
        writer.writerow(
            [
                "textbook",
                "Mathématiques 6ème",
                "Jean Dupont",
                "9782012345678",
                "6ème",
                "Mathématiques",
                "Hachette",
                2023,
            ]
        )
        writer.writerow(
            [
                "textbook",
                "Histoire-Géographie 5ème",
                "Marie Martin",
                "9782012345679",
                "5ème",
                "Histoire-Géographie",
                "Nathan",
                2023,
            ]
        )
        writer.writerow(
            [
                "literature",
                "Le Petit Prince",
                "Antoine de Saint-Exupéry",
                "9782070612758",
                "",
                "Littérature",
                "Gallimard",
                1943,
            ]
        )

    return str(file_path)


@pytest.fixture
def empty_excel_file(tmp_path) -> str:
    """Create an empty Excel file for testing."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Catalogue"

    # Only headers, no data
    headers = [
        "category",
        "title",
        "author",
        "isbn",
        "grade_level",
        "subject",
        "publisher",
        "year_published",
    ]
    ws.append(headers)

    file_path = tmp_path / "empty_catalog.xlsx"
    wb.save(file_path)
    wb.close()

    return str(file_path)


@pytest.fixture
def books_without_isbn() -> list[dict]:
    """Create sample book data without ISBN for testing."""
    return [
        {
            "category": "textbook",
            "title": "Mathématiques 6ème",
            "author": "Jean Dupont",
            "isbn": None,
            "grade_level": "6ème",
            "subject": "Mathématiques",
            "publisher": "Hachette",
            "year_published": 2023,
        },
        {
            "category": "textbook",
            "title": "Mathématiques 5ème",
            "author": "Marie Martin",
            "isbn": None,
            "grade_level": "5ème",
            "subject": "Mathématiques",
            "publisher": "Nathan",
            "year_published": 2023,
        },
    ]


@pytest.fixture
def invalid_books_data() -> list[dict]:
    """Create invalid book data for testing."""
    return [
        {
            "category": "textbook",
            "title": "",  # Empty title
            "author": "Jean Dupont",
            "isbn": "9782012345678",
            "grade_level": "6ème",
            "subject": "Mathématiques",
            "publisher": "Hachette",
            "year_published": 2023,
        },
        {
            "category": "invalid_category",  # Invalid category
            "title": "Histoire-Géographie 5ème",
            "author": "Marie Martin",
            "isbn": "9782012345679",
            "grade_level": "5ème",
            "subject": "Histoire-Géographie",
            "publisher": "Nathan",
            "year_published": 2023,
        },
        {
            "category": "textbook",
            "title": "Le Petit Prince",
            "author": "Antoine de Saint-Exupéry",
            "isbn": "invalid_isbn",  # Invalid ISBN
            "grade_level": None,
            "subject": "Littérature",
            "publisher": "Gallimard",
            "year_published": 1943,
        },
    ]
