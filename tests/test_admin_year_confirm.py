"""Tests for academic year creation confirmation callbacks."""

from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from bot.handlers.admin import (
    AdminYearCreateFlow,
    _is_year_detail_callback,
    handle_year_create_confirm,
    handle_year_create_modify,
)


@pytest.fixture
def mock_callback() -> CallbackQuery:
    cb = MagicMock(spec=CallbackQuery)
    cb.from_user = MagicMock()
    cb.from_user.id = 123456789
    cb.message = MagicMock()
    cb.message.edit_text = AsyncMock()
    cb.answer = AsyncMock()
    cb.data = "admin:year:create:confirm"
    return cb


@pytest.fixture
def mock_state() -> FSMContext:
    state = AsyncMock(spec=FSMContext)
    state.get_data = AsyncMock(
        return_value={
            "year_name": "2026-2027",
            "year_start": "2026-09-01",
            "year_end": "2027-06-30",
        }
    )
    state.set_state = AsyncMock()
    state.clear = AsyncMock()
    return state


class TestYearCreateConfirm:
    @pytest.mark.asyncio
    async def test_confirm_creates_year(
        self, mock_callback: CallbackQuery, mock_state: FSMContext
    ) -> None:
        mock_session = AsyncMock(spec=AsyncSession)

        with (
            patch("bot.handlers.admin._require_admin", return_value=True),
            patch("bot.services.academic_year.AcademicYearService") as mock_service_cls,
        ):
            mock_service = AsyncMock()
            created_year = MagicMock()
            created_year.name = "2026-2027"
            mock_service.create_year = AsyncMock(return_value=created_year)
            mock_service_cls.return_value = mock_service

            await handle_year_create_confirm(mock_callback, mock_state, mock_session)

            mock_service.create_year.assert_called_once_with(
                "2026-2027", date(2026, 9, 1), date(2027, 6, 30)
            )
            mock_state.clear.assert_called_once()
            mock_callback.answer.assert_called_once()

    @pytest.mark.asyncio
    async def test_confirm_rejects_non_admin(
        self, mock_callback: CallbackQuery, mock_state: FSMContext
    ) -> None:
        mock_session = AsyncMock(spec=AsyncSession)

        with patch("bot.handlers.admin._require_admin", return_value=False):
            await handle_year_create_confirm(mock_callback, mock_state, mock_session)

            mock_callback.answer.assert_not_called()
            mock_state.get_data.assert_not_called()


class TestYearCreateModify:
    @pytest.mark.asyncio
    async def test_modify_resets_to_name_state(
        self, mock_callback: CallbackQuery, mock_state: FSMContext
    ) -> None:
        with patch("bot.handlers.admin._require_admin", return_value=True):
            await handle_year_create_modify(mock_callback, mock_state)

            mock_state.set_state.assert_called_once_with(AdminYearCreateFlow.entering_name)
            mock_callback.answer.assert_called_once()

    @pytest.mark.asyncio
    async def test_modify_rejects_non_admin(
        self, mock_callback: CallbackQuery, mock_state: FSMContext
    ) -> None:
        with patch("bot.handlers.admin._require_admin", return_value=False):
            await handle_year_create_modify(mock_callback, mock_state)

            mock_state.set_state.assert_not_called()


class TestYearDetailFilterExcludesCreateCallbacks:
    def test_create_confirm_excluded(self) -> None:
        assert _is_year_detail_callback("admin:year:create:confirm") is False

    def test_create_modify_excluded(self) -> None:
        assert _is_year_detail_callback("admin:year:create:modify") is False

    def test_create_anything_excluded(self) -> None:
        assert _is_year_detail_callback("admin:year:create:foo") is False

    def test_year_detail_included(self) -> None:
        assert _is_year_detail_callback("admin:year:42") is True

    def test_set_current_included(self) -> None:
        assert _is_year_detail_callback("admin:year:set_current:42") is True

    def test_none_excluded(self) -> None:
        assert _is_year_detail_callback(None) is False

    def test_unrelated_excluded(self) -> None:
        assert _is_year_detail_callback("admin:years") is False
