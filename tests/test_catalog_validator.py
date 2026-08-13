"""Tests for catalog validator."""

import pytest

from bot.services.catalog.validator import CatalogValidator, ValidationError


class TestCatalogValidator:
    """Tests for CatalogValidator."""

    def setup_method(self):
        """Set up test fixtures."""
        self.validator = CatalogValidator()

    def test_validate_valid_books(self, sample_books_data: list[dict]):
        """Test validation of valid books."""
        validated = self.validator.validate(sample_books_data)

        assert len(validated) == 3
        assert validated[0]["title"] == "Mathématiques 6ème"
        assert validated[0]["category"] == "textbook"
        assert validated[0]["isbn"] == "9782012345678"

    def test_validate_empty_list(self):
        """Test validation of empty list."""
        with pytest.raises(ValidationError, match="Aucun livre à valider"):
            self.validator.validate([])

    def test_validate_missing_title(self):
        """Test validation with missing title."""
        books = [{"category": "textbook", "title": ""}]
        with pytest.raises(ValidationError, match="Le titre est requis"):
            self.validator.validate(books)

    def test_validate_missing_category(self):
        """Test validation with missing category."""
        books = [{"category": None, "title": "Test"}]
        with pytest.raises(ValidationError, match="La catégorie est requise"):
            self.validator.validate(books)

    def test_validate_empty_category(self):
        """Test validation with empty category."""
        books = [{"category": "", "title": "Test"}]
        with pytest.raises(ValidationError, match="La catégorie est requise"):
            self.validator.validate(books)

    def test_validate_invalid_category(self):
        """Test validation with invalid category."""
        books = [{"category": "invalid", "title": "Test"}]
        with pytest.raises(ValidationError, match="La catégorie doit être parmi"):
            self.validator.validate(books)

    def test_validate_valid_textbook_category(self):
        """Test validation with valid textbook category."""
        books = [{"category": "textbook", "title": "Test"}]
        validated = self.validator.validate(books)
        assert validated[0]["category"] == "textbook"

    def test_validate_valid_literature_category(self):
        """Test validation with valid literature category."""
        books = [{"category": "literature", "title": "Test"}]
        validated = self.validator.validate(books)
        assert validated[0]["category"] == "literature"

    def test_validate_invalid_isbn(self):
        """Test validation with invalid ISBN."""
        books = [{"category": "textbook", "title": "Test", "isbn": "invalid"}]
        with pytest.raises(ValidationError, match="L'ISBN .* n'est pas valide"):
            self.validator.validate(books)

    def test_validate_valid_isbn_10(self):
        """Test validation with valid ISBN-10."""
        books = [{"category": "textbook", "title": "Test", "isbn": "0123456789"}]
        validated = self.validator.validate(books)
        assert validated[0]["isbn"] == "0123456789"

    def test_validate_valid_isbn_13(self):
        """Test validation with valid ISBN-13."""
        books = [{"category": "textbook", "title": "Test", "isbn": "9782012345678"}]
        validated = self.validator.validate(books)
        assert validated[0]["isbn"] == "9782012345678"

    def test_validate_invalid_year_published(self):
        """Test validation with invalid year_published."""
        books = [{"category": "textbook", "title": "Test", "year_published": 1800}]
        with pytest.raises(
            ValidationError, match="L'année de publication doit être entre 1900 et 2100"
        ):
            self.validator.validate(books)

    def test_validate_title_too_long(self):
        """Test validation with title too long."""
        books = [{"category": "textbook", "title": "A" * 256}]
        with pytest.raises(ValidationError, match="Le titre doit faire 255 caractères ou moins"):
            self.validator.validate(books)

    def test_validate_author_too_long(self):
        """Test validation with author too long."""
        books = [{"category": "textbook", "title": "Test", "author": "A" * 256}]
        with pytest.raises(ValidationError, match="L'auteur doit faire 255 caractères ou moins"):
            self.validator.validate(books)

    def test_validate_subject_too_long(self):
        """Test validation with subject too long."""
        books = [{"category": "textbook", "title": "Test", "subject": "A" * 101}]
        with pytest.raises(ValidationError, match="La matière doit faire 100 caractères ou moins"):
            self.validator.validate(books)

    def test_validate_publisher_too_long(self):
        """Test validation with publisher too long."""
        books = [{"category": "textbook", "title": "Test", "publisher": "A" * 101}]
        with pytest.raises(ValidationError, match="L'éditeur doit faire 100 caractères ou moins"):
            self.validator.validate(books)

    def test_validate_grade_level_too_long(self):
        """Test validation with grade_level too long."""
        books = [{"category": "textbook", "title": "Test", "grade_level": "A" * 21}]
        with pytest.raises(ValidationError, match="La classe doit faire 20 caractères ou moins"):
            self.validator.validate(books)

    def test_validate_isbn_too_long(self):
        """Test validation with isbn too long."""
        books = [{"category": "textbook", "title": "Test", "isbn": "1" * 14}]
        with pytest.raises(ValidationError, match="L'ISBN doit faire 13 caractères ou moins"):
            self.validator.validate(books)

    def test_validate_multiple_errors(self):
        """Test validation with multiple errors."""
        books = [
            {"category": "invalid", "title": ""},  # Two errors
        ]
        with pytest.raises(ValidationError, match="Échec de la validation pour 1 livre"):
            self.validator.validate(books)

    def test_validate_valid_with_optional_fields(self):
        """Test validation with optional fields."""
        books = [
            {
                "category": "textbook",
                "title": "Test",
                "author": "Author",
                "isbn": "9782012345678",
                "grade_level": "6ème",
                "subject": "Math",
                "publisher": "Publisher",
                "year_published": 2023,
                "cover_image_url": "http://example.com/image.jpg",
            },
        ]
        validated = self.validator.validate(books)
        assert len(validated) == 1
        assert validated[0]["author"] == "Author"
        assert validated[0]["cover_image_url"] == "http://example.com/image.jpg"

    def test_is_valid_isbn_valid(self):
        """Test ISBN validation with valid ISBN."""
        assert self.validator._is_valid_isbn("9782012345678") is True
        assert self.validator._is_valid_isbn("0123456789") is True

    def test_is_valid_isbn_invalid(self):
        """Test ISBN validation with invalid ISBN."""
        assert self.validator._is_valid_isbn("invalid") is False
        assert self.validator._is_valid_isbn("123") is False
        assert self.validator._is_valid_isbn("12345678901234") is False
