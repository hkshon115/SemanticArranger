import pytest
import os
from backend.utils.validators import PDFValidator

@pytest.fixture
def valid_pdf(tmp_path):
    """Creates a valid, temporary PDF file for testing."""
    file_path = tmp_path / "valid.pdf"
    # A minimal valid PDF
    file_path.write_bytes(b"%PDF-1.0\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj 2 0 obj<</Type/Pages/Count 1/Kids[3 0 R]>>endobj 3 0 obj<</Type/Page/MediaBox[0 0 3 3]>>endobj\nxref\n0 4\n0000000000 65535 f\n0000000010 00000 n\n0000000058 00000 n\n0000000111 00000 n\ntrailer<</Size 4/Root 1 0 R>>\nstartxref\n178\n%%EOF")
    return str(file_path)

@pytest.fixture
def corrupted_pdf(tmp_path):
    """Creates a corrupted, temporary PDF file."""
    file_path = tmp_path / "corrupted.pdf"
    file_path.write_text("This is not a PDF.")
    return str(file_path)

def test_pdf_validator_success(valid_pdf):
    """
    Tests that a valid PDF passes all validation checks.
    """
    validator = PDFValidator(valid_pdf)
    assert validator.validate() is None

def test_pdf_validator_file_not_found():
    """
    Tests that the validator returns an error for a non-existent file.
    """
    validator = PDFValidator("non_existent_file.pdf")
    assert "File not found" in validator.validate()

def test_pdf_validator_empty_file(tmp_path):
    """
    Tests that the validator returns an error for an empty file.
    """
    empty_file = tmp_path / "empty.pdf"
    empty_file.touch()
    validator = PDFValidator(str(empty_file))
    assert "File is empty" in validator.validate()

def test_pdf_validator_oversized_file(valid_pdf):
    """
    Tests that the validator returns an error for a file that exceeds the size limit.
    """
    validator = PDFValidator(valid_pdf, max_size_mb=0.00001)
    assert "exceeds the limit" in validator.validate()

def test_pdf_validator_corrupted_file(corrupted_pdf):
    """
    Tests that the validator returns an error for a corrupted PDF.
    """
    validator = PDFValidator(corrupted_pdf)
    assert "Failed to open PDF" in validator.validate()
