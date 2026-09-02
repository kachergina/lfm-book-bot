"""Tests for datetime utilities."""

from datetime import UTC, datetime, timedelta

import pytest

from bot.utils.datetime_utils import utc_now


class TestUtcNow:
    """Tests for utc_now helper."""

    def test_returns_naive_datetime(self) -> None:
        """PostgreSQL TIMESTAMP WITHOUT TIME ZONE requires naive datetimes."""
        now = utc_now()
        assert now.tzinfo is None

    def test_represents_current_utc_time(self) -> None:
        """Naive value should match current UTC within tolerance."""
        now = utc_now()
        aware_utc = datetime.now(UTC).replace(microsecond=0)
        assert now.replace(microsecond=0) == aware_utc.replace(tzinfo=None)

    def test_can_compare_with_naive_timestamps(self) -> None:
        """Naive UTC values must subtract without timezone errors."""
        old = utc_now() - timedelta(days=200)
        cutoff = utc_now() - timedelta(days=180)
        assert old <= cutoff

    def test_aware_datetime_comparison_raises_type_error(self) -> None:
        """Aware UTC cutoffs must not be compared with naive DB values."""
        naive_db_value = utc_now() - timedelta(days=200)
        aware_cutoff = datetime.now(UTC) - timedelta(days=180)
        with pytest.raises(TypeError):
            _ = naive_db_value <= aware_cutoff
