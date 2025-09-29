"""
Utilities for parsing and handling input documents.
"""
from abc import ABC, abstractmethod
from typing import List, Optional
import fitz  # PyMuPDF

class IPageData(ABC):
    """
    Abstract base class for page data. This allows for different types of
    documents (e.g., DOCX, HTML) to be processed by the pipeline.
    """
    @property
    @abstractmethod
    def page_number(self) -> int:
        """The page number of the document."""
        pass

    @abstractmethod
    def get_text(self) -> Optional[str]:
        """Returns the raw text of the page."""
        pass

    @abstractmethod
    def get_image(self) -> Optional[bytes]:
        """Returns a rendered image of the page."""
        pass

class PageData(IPageData):
    """
    A concrete implementation of `IPageData` that holds page data from a
    PyMuPDF document. It lazily loads the text and image of the page to
    optimize performance.
    """
    def __init__(self, page_num: int, page: fitz.Page):
        """
        Initializes the PageData object.

        Args:
            page_num: The page number (1-indexed).
            page: The `fitz.Page` object from PyMuPDF.
        """
        self._page_num = page_num
        self._page = page
        self._text: Optional[str] = None
        self._image: Optional[bytes] = None

    @property
    def page_number(self) -> int:
        """The page number of the document."""
        return self._page_num

    def get_text(self) -> Optional[str]:
        """
        Returns the raw text of the page, caching it after the first call.
        """
        if self._text is None:
            self._text = self._page.get_text()
        return self._text

    def get_image(self) -> Optional[bytes]:
        """
        Returns a rendered, high-quality PNG image of the page, caching it
        after the first call.
        """
        if self._image is None:
            # High quality rendering
            mat = fitz.Matrix(250 / 72, 250 / 72)
            pix = self._page.get_pixmap(matrix=mat)
            self._image = pix.tobytes("png")
        return self._image

class DocumentParser:
    """
    Parses a PDF document and provides access to its pages.

    This class acts as a wrapper around PyMuPDF, providing a simple interface
    for opening a document and retrieving its pages as `PageData` objects.
    """

    def __init__(self, file_path: str):
        """
        Initializes the DocumentParser and opens the PDF file.

        Args:
            file_path: The path to the PDF file.
        """
        self.file_path = file_path
        self.document = fitz.open(file_path)

    def __len__(self) -> int:
        """Returns the total number of pages in the document."""
        return len(self.document)

    def get_page(self, page_num: int) -> PageData:
        """
        Returns a `PageData` object for the given page number.

        Args:
            page_num: The page number to retrieve (0-indexed).
        """
        if not 0 <= page_num < len(self.document):
            raise IndexError("Page number out of range.")
        return PageData(page_num=page_num + 1, page=self.document[page_num])

    def close(self):
        """Closes the PDF document."""
        self.document.close()