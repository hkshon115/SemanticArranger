import pytest
import os
from backend.utils.document_parser import DocumentParser, PageData

@pytest.fixture
def golden_pdf_path():
    """Returns the path to a golden test PDF."""
    return os.path.join(os.path.dirname(__file__), "..", "fixtures", "golden_pdfs", "sample_report.pdf")

def test_document_parser_opens_pdf(golden_pdf_path):
    """
    Tests that the DocumentParser can successfully open a PDF file.
    """
    parser = DocumentParser(golden_pdf_path)
    assert len(parser) > 0
    parser.close()

def test_document_parser_get_page(golden_pdf_path):
    """
    Tests that the DocumentParser can retrieve a specific page as a PageData object.
    """
    parser = DocumentParser(golden_pdf_path)
    page_data = parser.get_page(0)
    
    assert isinstance(page_data, PageData)
    assert page_data.page_number == 1
    assert "This is a sample report." in page_data.get_text()
    
    parser.close()

def test_document_parser_page_out_of_range(golden_pdf_path):
    """
    Tests that the DocumentParser raises an IndexError for an invalid page number.
    """
    parser = DocumentParser(golden_pdf_path)
    with pytest.raises(IndexError):
        parser.get_page(100) # Assuming the sample PDF has fewer than 100 pages
    parser.close()
