"""Database engine and session management."""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """SQLAlchemy declarative base for all models."""


# Global engine and session factory - initialized by init_engine()
engine = None
async_session_factory = None


def init_engine(database_url: str, echo: bool = False) -> None:
    """Initialize the database engine.

    Args:
        database_url: Database connection URL.
        echo: Whether to echo SQL statements.
    """
    global engine, async_session_factory
    engine = create_async_engine(database_url, echo=echo)
    async_session_factory = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )


async def get_session() -> AsyncGenerator[AsyncSession]:
    """Get an async database session.

    Yields:
        AsyncSession: A database session.
    """
    if async_session_factory is None:
        raise RuntimeError("Database engine not initialized. Call init_engine() first.")
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """Initialize database tables."""
    if engine is None:
        raise RuntimeError("Database engine not initialized. Call init_engine() first.")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """Close database engine connections."""
    if engine is not None:
        await engine.dispose()
