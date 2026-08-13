"""CLI command for importing book catalogs.

Usage:
    python -m bot.import_catalog catalog.xlsx
    python -m bot.import_catalog catalog.xlsx --year-id 2
"""

import argparse
import asyncio
import sys
from pathlib import Path

from bot.config import get_settings
from bot.database.base import close_db, get_session, init_db, init_engine
from bot.services.catalog.importer import CatalogImportService


async def import_catalog(file_path: str, year_id: int | None = None) -> None:
    """Import catalog from file.

    Args:
        file_path: Path to catalog file.
        year_id: Academic year ID.
    """
    settings = get_settings()
    init_engine(settings.database_url)
    await init_db()

    try:
        async for session in get_session():
            service = CatalogImportService(session)
            result = await service.import_from_file(file_path, year_id)

            print("\n=== Import Result ===")
            print(f"Parsed:    {result.total_parsed} books")
            print(f"Created:   {result.total_created} books (new entries)")
            print(f"Existing:  {result.total_existing} books (already in catalog)")
            print(f"Skipped:   {result.total_skipped} books")

            if result.errors:
                print("\nErrors:")
                for error in result.errors:
                    print(f"  - {error}")
            else:
                print("\nImport completed successfully!")
    except Exception as e:
        print(f"\nError: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        await close_db()


def main() -> None:
    """CLI entry point for catalog import."""
    parser = argparse.ArgumentParser(
        description="Import book catalog from Excel or CSV file",
    )
    parser.add_argument(
        "file",
        help="Path to catalog file (.xlsx or .csv)",
    )
    parser.add_argument(
        "--year-id",
        type=int,
        help="Academic year ID (default: current year)",
    )

    args = parser.parse_args()

    file_path = Path(args.file)
    if not file_path.exists():
        print(f"Error: File not found: {file_path}", file=sys.stderr)
        sys.exit(1)

    asyncio.run(import_catalog(str(file_path), args.year_id))


if __name__ == "__main__":
    main()
