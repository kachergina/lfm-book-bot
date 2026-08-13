"""Database models for the School Books Marketplace."""

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from bot.database.base import Base


class AcademicYear(Base):
    """Academic year model."""

    __tablename__ = "academic_years"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    is_current: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    books: Mapped[list["Book"]] = relationship(back_populates="catalog_year")
    listings: Mapped[list["Listing"]] = relationship(back_populates="academic_year")

    __table_args__ = (CheckConstraint("end_date > start_date", name="chk_academic_year_dates"),)


class User(Base):
    """Telegram user model."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)
    username: Mapped[str | None] = mapped_column(String(100), nullable=True)
    first_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    last_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    language_code: Mapped[str] = mapped_column(String(10), default="fr")
    role: Mapped[str] = mapped_column(String(20), default="user")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_banned: Mapped[bool] = mapped_column(Boolean, default=False)
    ban_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    listings: Mapped[list["Listing"]] = relationship(back_populates="seller")


class Book(Base):
    """Book catalog model (imported from external files)."""

    __tablename__ = "books"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    category: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )  # 'textbook' or 'literature'
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    author: Mapped[str | None] = mapped_column(String(255), nullable=True)
    isbn: Mapped[str | None] = mapped_column(String(13), nullable=True)
    grade_level: Mapped[str | None] = mapped_column(String(20), nullable=True)
    subject: Mapped[str | None] = mapped_column(String(100), nullable=True)
    publisher: Mapped[str | None] = mapped_column(String(100), nullable=True)
    year_published: Mapped[int | None] = mapped_column(Integer, nullable=True)
    catalog_year_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("academic_years.id"),
        nullable=False,
    )
    cover_image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    catalog_year: Mapped["AcademicYear"] = relationship(back_populates="books")
    listings: Mapped[list["Listing"]] = relationship(back_populates="book")


class Listing(Base):
    """Book listing model for sale."""

    __tablename__ = "listings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    book_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("books.id"),
        nullable=False,
    )
    seller_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
    )
    academic_year_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("academic_years.id"),
        nullable=False,
    )
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    condition: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )  # 'new', 'like_new', 'good', 'fair', 'poor'
    status: Mapped[str] = mapped_column(
        String(20),
        default="active",
        nullable=False,
    )  # 'active', 'reserved', 'sold', 'archived', 'expired'
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    photos: Mapped[list | None] = mapped_column(JSON, nullable=True)  # Array of Telegram file_ids
    contact_phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    contact_method: Mapped[str | None] = mapped_column(String(10), nullable=True, default="phone")
    view_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    reserved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    sold_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    archived_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Relationships
    book: Mapped["Book"] = relationship(back_populates="listings")
    seller: Mapped["User"] = relationship(back_populates="listings")
    academic_year: Mapped["AcademicYear"] = relationship(back_populates="listings")
