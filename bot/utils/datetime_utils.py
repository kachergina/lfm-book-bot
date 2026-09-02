"""Datetime helpers for database timestamps."""

from datetime import UTC, datetime


def utc_now() -> datetime:
    """Return current UTC time as a naive datetime.

    PostgreSQL columns use TIMESTAMP WITHOUT TIME ZONE. asyncpg returns naive
    datetimes for those columns, so application code must not use timezone-aware
    values when comparing or writing timestamps.
    """
    return datetime.now(UTC).replace(tzinfo=None)
