"""Validator for catalog data.

Validates book catalog data before import. Category is REQUIRED.
Valid internal values: 'textbook', 'literature'.
French user-facing labels: 'Manuel scolaire', 'Livre de littérature'.
"""

from typing import Any


class ValidationError(Exception):
    """Raised when validation fails."""


class CatalogValidator:
    """Validate catalog data before import.

    Note: This validator is for catalog books only.
    Listing-specific validation (condition, price, etc.) is separate.
    """

    VALID_CATEGORIES = {"textbook", "literature"}

    def validate(self, books: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Validate a list of book records.

        Args:
            books: List of book dictionaries.

        Returns:
            List of validated books.

        Raises:
            ValidationError: If validation fails.
        """
        if not books:
            raise ValidationError("Aucun livre à valider")

        validated = []
        errors = []

        for idx, book in enumerate(books, start=1):
            try:
                validated_book = self._validate_book(book, idx)
                validated.append(validated_book)
            except ValidationError as e:
                errors.append(str(e))

        if errors:
            error_msg = f"Échec de la validation pour {len(errors)} livre(s) :\n" + "\n".join(
                errors[:10]
            )
            if len(errors) > 10:
                error_msg += f"\n... et {len(errors) - 10} erreurs supplémentaires"
            raise ValidationError(error_msg)

        return validated

    def _validate_book(self, book: dict[str, Any], row_num: int) -> dict[str, Any]:
        """Validate a single book record.

        Args:
            book: Book dictionary.
            row_num: Row number for error messages.

        Returns:
            Validated book dictionary.

        Raises:
            ValidationError: If validation fails.
        """
        errors = []

        # Validate required fields
        if not book.get("title"):
            errors.append("Le titre est requis")

        # Validate category - REQUIRED, no default
        category = book.get("category")
        if not category:
            errors.append("La catégorie est requise (doit être 'textbook' ou 'literature')")
        elif category not in self.VALID_CATEGORIES:
            errors.append(
                f"La catégorie doit être parmi {self.VALID_CATEGORIES}, reçu '{category}'"
            )

        # Validate ISBN if present
        isbn = book.get("isbn")
        if isbn and not self._is_valid_isbn(isbn):
            errors.append(f"L'ISBN '{isbn}' n'est pas valide (doit contenir 10 ou 13 chiffres)")

        # Validate year_published if present
        year = book.get("year_published")
        if year is not None and (not isinstance(year, int) or year < 1900 or year > 2100):
            errors.append(f"L'année de publication doit être entre 1900 et 2100, reçue '{year}'")

        # Validate string lengths
        if book.get("title") and len(str(book["title"])) > 255:
            errors.append("Le titre doit faire 255 caractères ou moins")

        if book.get("author") and len(str(book["author"])) > 255:
            errors.append("L'auteur doit faire 255 caractères ou moins")

        if book.get("subject") and len(str(book["subject"])) > 100:
            errors.append("La matière doit faire 100 caractères ou moins")

        if book.get("publisher") and len(str(book["publisher"])) > 100:
            errors.append("L'éditeur doit faire 100 caractères ou moins")

        if book.get("grade_level") and len(str(book["grade_level"])) > 20:
            errors.append("La classe doit faire 20 caractères ou moins")

        if book.get("isbn") and len(str(book["isbn"])) > 13:
            errors.append("L'ISBN doit faire 13 caractères ou moins")

        if errors:
            raise ValidationError(f"Row {row_num}: " + "; ".join(errors))

        return {
            "category": category,
            "title": str(book["title"]).strip(),
            "author": book.get("author"),
            "isbn": isbn,
            "grade_level": book.get("grade_level"),
            "subject": book.get("subject"),
            "publisher": book.get("publisher"),
            "year_published": book.get("year_published"),
            "cover_image_url": book.get("cover_image_url"),
        }

    def _is_valid_isbn(self, isbn: str) -> bool:
        """Check if ISBN is valid.

        Args:
            isbn: ISBN string.

        Returns:
            True if valid.
        """
        cleaned = str(isbn).replace("-", "").replace(" ", "")
        if not cleaned.isdigit():
            return False
        return len(cleaned) in (10, 13)
