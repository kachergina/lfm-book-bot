"""Tests for catalog parser."""

import pytest

from bot.services.catalog.parser import CatalogParser, ParseError


class TestCatalogParser:
    """Tests for CatalogParser."""

    def setup_method(self):
        """Set up test fixtures."""
        self.parser = CatalogParser()

    def test_parse_excel_file(self, sample_excel_file: str):
        """Test parsing Excel file."""
        books = self.parser.parse(sample_excel_file)

        assert len(books) == 3
        assert books[0]["title"] == "Mathématiques 6ème"
        assert books[0]["category"] == "textbook"
        assert books[0]["isbn"] == "9782012345678"
        assert books[0]["grade_level"] == "6ème"
        assert books[0]["subject"] == "Mathématiques"
        assert books[0]["publisher"] == "Hachette"
        assert books[0]["year_published"] == 2023

    def test_parse_csv_file(self, sample_csv_file: str):
        """Test parsing CSV file."""
        books = self.parser.parse(sample_csv_file)

        assert len(books) == 3
        assert books[0]["title"] == "Mathématiques 6ème"
        assert books[0]["category"] == "textbook"
        assert books[0]["isbn"] == "9782012345678"

    def test_parse_file_not_found(self):
        """Test parsing non-existent file."""
        with pytest.raises(ParseError, match="Fichier introuvable"):
            self.parser.parse("/nonexistent/file.xlsx")

    def test_parse_unsupported_format(self, tmp_path):
        """Test parsing unsupported file format."""
        file_path = tmp_path / "test.txt"
        file_path.write_text("test")

        with pytest.raises(ParseError, match="Format de fichier non supporté"):
            self.parser.parse(file_path)

    def test_parse_empty_excel(self, empty_excel_file: str):
        """Test parsing empty Excel file."""
        with pytest.raises(ParseError, match="pas de lignes de données"):
            self.parser.parse(empty_excel_file)

    def test_normalize_isbn_with_hyphens(self):
        """Test ISBN normalization with hyphens."""
        isbn = self.parser._normalize_isbn("978-2-01-234567-8")
        assert isbn == "9782012345678"

    def test_normalize_isbn_with_spaces(self):
        """Test ISBN normalization with spaces."""
        isbn = self.parser._normalize_isbn("978 2 01 234567 8")
        assert isbn == "9782012345678"

    def test_normalize_isbn_float(self):
        """Test ISBN normalization from float."""
        isbn = self.parser._normalize_isbn(9782012345678.0)
        assert isbn == "9782012345678"

    def test_normalize_isbn_none(self):
        """Test ISBN normalization with None."""
        isbn = self.parser._normalize_isbn(None)
        assert isbn is None

    def test_normalize_isbn_empty(self):
        """Test ISBN normalization with empty string."""
        isbn = self.parser._normalize_isbn("")
        assert isbn is None

    def test_parse_int_valid(self):
        """Test integer parsing with valid value."""
        result = self.parser._parse_int("2023")
        assert result == 2023

    def test_parse_int_float(self):
        """Test integer parsing with float."""
        result = self.parser._parse_int(2023.0)
        assert result == 2023

    def test_parse_int_none(self):
        """Test integer parsing with None."""
        result = self.parser._parse_int(None)
        assert result is None

    def test_parse_int_invalid(self):
        """Test integer parsing with invalid value."""
        result = self.parser._parse_int("not_a_number")
        assert result is None

    def test_build_column_map(self):
        """Test column mapping."""
        headers = [
            "category",
            "title",
            "author",
            "isbn",
            "grade_level",
            "subject",
            "publisher",
            "year_published",
        ]
        column_map = self.parser._build_column_map(headers)

        assert "category" in column_map
        assert "title" in column_map
        assert "author" in column_map
        assert "isbn" in column_map
        assert "grade_level" in column_map
        assert "subject" in column_map
        assert "publisher" in column_map
        assert "year_published" in column_map

    def test_build_column_map_french_headers(self):
        """Test column mapping with French headers."""
        headers = ["categorie", "titre", "auteur", "isbn", "niveau", "matiere", "editeur", "annee"]
        column_map = self.parser._build_column_map(headers)

        assert "category" in column_map
        assert "title" in column_map
        assert "author" in column_map
        assert "isbn" in column_map
        assert "grade_level" in column_map
        assert "subject" in column_map
        assert "publisher" in column_map
        assert "year_published" in column_map

    def test_row_to_dict_missing_title(self):
        """Test row conversion with missing title."""
        row = ["textbook", "", "Author", "9782012345678", "6ème", "Math", "Publisher", 2023]
        column_map = {
            "category": 0,
            "title": 1,
            "author": 2,
            "isbn": 3,
            "grade_level": 4,
            "subject": 5,
            "publisher": 6,
            "year_published": 7,
        }

        with pytest.raises(ParseError, match="Champ requis 'title' manquant"):
            self.parser._row_to_dict(row, column_map, 1)

    def test_row_to_dict_valid(self):
        """Test valid row conversion."""
        row = [
            "textbook",
            "Math 6ème",
            "Author",
            "9782012345678",
            "6ème",
            "Math",
            "Publisher",
            2023,
        ]
        column_map = {
            "category": 0,
            "title": 1,
            "author": 2,
            "isbn": 3,
            "grade_level": 4,
            "subject": 5,
            "publisher": 6,
            "year_published": 7,
        }

        book = self.parser._row_to_dict(row, column_map, 1)
        assert book is not None
        assert book["title"] == "Math 6ème"
        assert book["category"] == "textbook"
        assert book["isbn"] == "9782012345678"
