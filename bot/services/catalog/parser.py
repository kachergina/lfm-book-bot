"""Parser for Excel and CSV catalog files."""

import csv
from pathlib import Path
from typing import Any

import openpyxl


class ParseError(Exception):
    """Raised when parsing fails."""


class CatalogParser:
    """Parse catalog files (Excel or CSV) into dictionaries."""

    # Column name mapping (French/English variants to internal names)
    COLUMN_MAP = {
        "category": ["category", "categorie", "type", "type_livre"],
        "title": ["title", "titre", "nom", "nom_livre"],
        "author": ["author", "auteur", "auteur_nom", "ecrivain"],
        "isbn": ["isbn", "isbn13", "isbn_13", "code_isbn"],
        "grade_level": ["grade_level", "niveau", "classe", "niveau_scolaire"],
        "subject": ["subject", "matiere", "discipline", "matiere_scolaire"],
        "publisher": ["publisher", "editeur", "maison_edition"],
        "year_published": ["year_published", "annee", "annee_publication", "annee_edition"],
        "cover_image_url": ["cover_image_url", "image", "couverture", "url_image"],
    }

    VALID_CATEGORIES = {"textbook", "literature"}

    def parse(self, file_path: str | Path) -> list[dict[str, Any]]:
        """Parse a catalog file.

        Args:
            file_path: Path to Excel or CSV file.

        Returns:
            List of dictionaries with book data.

        Raises:
            ParseError: If file cannot be parsed.
        """
        path = Path(file_path)
        if not path.exists():
            raise ParseError(f"Fichier introuvable : {path}")

        suffix = path.suffix.lower()
        if suffix == ".xlsx":
            return self._parse_excel(path)
        if suffix == ".csv":
            return self._parse_csv(path)
        raise ParseError(f"Format de fichier non supporté : {suffix}. Utilisez .xlsx ou .csv")

    def _parse_excel(self, path: Path) -> list[dict[str, Any]]:
        """Parse Excel file.

        Args:
            path: Path to Excel file.

        Returns:
            List of dictionaries with book data.

        Raises:
            ParseError: If Excel file cannot be parsed.
        """
        try:
            wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
        except Exception as e:
            raise ParseError(f"Échec de la lecture du fichier Excel : {e}")

        ws = wb.active
        if ws is None:
            raise ParseError("Le fichier Excel n'a pas de feuille active")

        rows = list(ws.iter_rows(values_only=True))
        wb.close()

        if len(rows) < 2:
            raise ParseError("Le fichier Excel n'a pas de lignes de données")

        header_row = rows[0]
        column_map = self._build_column_map(header_row)

        books = []
        for row_num, row in enumerate(rows[1:], start=2):
            try:
                book = self._row_to_dict(row, column_map, row_num)
                if book:
                    books.append(book)
            except ParseError:
                raise
            except Exception as e:
                raise ParseError(f"Error parsing row {row_num}: {e}")

        return books

    def _parse_csv(self, path: Path) -> list[dict[str, Any]]:
        """Parse CSV file.

        Args:
            path: Path to CSV file.

        Returns:
            List of dictionaries with book data.

        Raises:
            ParseError: If CSV file cannot be parsed.
        """
        try:
            with path.open(newline="", encoding="utf-8-sig") as f:
                reader = csv.reader(f)
                rows = list(reader)
        except Exception as e:
            raise ParseError(f"Échec de la lecture du fichier CSV : {e}")

        if len(rows) < 2:
            raise ParseError("Le fichier CSV n'a pas de lignes de données")

        header_row = rows[0]
        column_map = self._build_column_map(header_row)

        books = []
        for row_num, row in enumerate(rows[1:], start=2):
            try:
                book = self._row_to_dict(row, column_map, row_num)
                if book:
                    books.append(book)
            except ParseError:
                raise
            except Exception as e:
                raise ParseError(f"Error parsing row {row_num}: {e}")

        return books

    def _build_column_map(self, header_row: tuple | list) -> dict[str, int]:
        """Build mapping from internal field names to column indices.

        Args:
            header_row: Tuple of column headers.

        Returns:
            Dict mapping internal field names to column indices.
        """
        column_map = {}
        headers_lower = [str(h).strip().lower() if h else "" for h in header_row]

        for field_name, variants in self.COLUMN_MAP.items():
            for variant in variants:
                try:
                    idx = headers_lower.index(variant)
                    column_map[field_name] = idx
                    break
                except ValueError:
                    continue

        return column_map

    def _row_to_dict(
        self,
        row: tuple | list,
        column_map: dict[str, int],
        row_num: int,
    ) -> dict[str, Any] | None:
        """Convert a row to a dictionary.

        Args:
            row: Row data.
            column_map: Column mapping.
            row_num: Row number for error messages.

        Returns:
            Dictionary with book data, or None if row is empty.

        Raises:
            ParseError: If required fields are missing.
        """

        def get_value(field: str, default: Any = None) -> Any:
            idx = column_map.get(field)
            if idx is None or idx >= len(row):
                return default
            val = row[idx]
            if val is None or (isinstance(val, str) and val.strip() == ""):
                return default
            return val

        title = get_value("title")
        if not title:
            raise ParseError(f"Ligne {row_num} : Champ requis 'title' manquant")

        # Category is REQUIRED - no default
        category = get_value("category")
        if not category:
            raise ParseError(
                f"Ligne {row_num} : Champ requis 'category' manquant. "
                "Valeurs valides : 'textbook' ou 'literature'",
            )
        category = str(category).strip().lower()

        # Normalize category to internal values
        category_map = {
            "manuel scolaire": "textbook",
            "manuel": "textbook",
            "textbook": "textbook",
            "livre de littérature": "literature",
            "littérature": "literature",
            "literature": "literature",
        }
        category = category_map.get(category, category)

        book = {
            "category": category,
            "title": str(title).strip(),
            "author": get_value("author"),
            "isbn": self._normalize_isbn(get_value("isbn")),
            "grade_level": get_value("grade_level"),
            "subject": get_value("subject"),
            "publisher": get_value("publisher"),
            "year_published": self._parse_int(get_value("year_published")),
            "cover_image_url": get_value("cover_image_url"),
        }

        return book  # noqa: RET504

    def _normalize_isbn(self, isbn: Any) -> str | None:
        """Normalize ISBN by removing hyphens and spaces.

        Args:
            isbn: Raw ISBN value.

        Returns:
            Normalized ISBN or None.
        """
        if isbn is None:
            return None
        if isinstance(isbn, float):
            isbn = str(int(isbn))
        normalized = str(isbn).replace("-", "").replace(" ", "").strip()
        if not normalized:
            return None
        return normalized

    def _parse_int(self, value: Any) -> int | None:
        """Parse integer value.

        Args:
            value: Value to parse.

        Returns:
            Integer or None.
        """
        if value is None:
            return None
        if isinstance(value, (int, float)):
            return int(value)
        try:
            return int(str(value).strip())
        except (ValueError, TypeError):
            return None
