"""Tests for database models."""

from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from bot.database.base import Base
from bot.database.models import AcademicYear, Book, Listing, User


@pytest.fixture
def db_session() -> Session:
    """Create a test database session.

    Yields:
        Test database session.
    """
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    Base.metadata.drop_all(engine)


class TestAcademicYear:
    """Tests for AcademicYear model."""

    def test_create_academic_year(self, db_session: Session) -> None:
        """Test creating an academic year."""
        academic_year = AcademicYear(
            name="2024-2025",
            start_date=date(2024, 9, 1),
            end_date=date(2025, 6, 30),
            is_current=True,
        )
        db_session.add(academic_year)
        db_session.commit()

        assert academic_year.id is not None
        assert academic_year.name == "2024-2025"
        assert academic_year.is_current is True


class TestUser:
    """Tests for User model."""

    def test_create_user(self, db_session: Session) -> None:
        """Test creating a user."""
        user = User(
            telegram_id=123456789,
            username="testuser",
            first_name="Test",
            last_name="User",
            language_code="fr",
        )
        db_session.add(user)
        db_session.commit()

        assert user.id is not None
        assert user.telegram_id == 123456789
        assert user.username == "testuser"
        assert user.is_active is True
        assert user.is_banned is False


class TestBook:
    """Tests for Book model."""

    def test_create_book(self, db_session: Session) -> None:
        """Test creating a book."""
        academic_year = AcademicYear(
            name="2024-2025",
            start_date=date(2024, 9, 1),
            end_date=date(2025, 6, 30),
        )
        db_session.add(academic_year)
        db_session.commit()

        book = Book(
            category="textbook",
            title="Mathématiques 6ème",
            author="Dupont",
            isbn="978-1234567890",
            grade_level="6ème",
            subject="Mathématiques",
            publisher="Éditions Scolaires",
            year_published=2024,
            catalog_year_id=academic_year.id,
        )
        db_session.add(book)
        db_session.commit()

        assert book.id is not None
        assert book.category == "textbook"
        assert book.title == "Mathématiques 6ème"
        assert book.catalog_year_id == academic_year.id


class TestListing:
    """Tests for Listing model."""

    def test_create_listing(self, db_session: Session) -> None:
        """Test creating a listing."""
        academic_year = AcademicYear(
            name="2024-2025",
            start_date=date(2024, 9, 1),
            end_date=date(2025, 6, 30),
        )
        db_session.add(academic_year)
        db_session.commit()

        user = User(telegram_id=123456789)
        db_session.add(user)
        db_session.commit()

        book = Book(
            category="textbook",
            title="Mathématiques 6ème",
            catalog_year_id=academic_year.id,
        )
        db_session.add(book)
        db_session.commit()

        listing = Listing(
            book_id=book.id,
            seller_id=user.id,
            academic_year_id=academic_year.id,
            price=Decimal("15.00"),
            condition="good",
            status="active",
            contact_phone="0612345678",
        )
        db_session.add(listing)
        db_session.commit()

        assert listing.id is not None
        assert listing.price == Decimal("15.00")
        assert listing.condition == "good"
        assert listing.status == "active"
        assert listing.contact_phone == "0612345678"
