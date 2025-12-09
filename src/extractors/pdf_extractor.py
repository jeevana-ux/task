"""
PDF Text Extraction Module
Uses pdfplumber as primary extractor (PyMuPDF is optional due to Windows DLL issues).
"""
# Make PyMuPDF optional - use pdfplumber as primary
try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False
    print("⚠️  PyMuPDF not available, using pdfplumber")

import pdfplumber
import pytesseract
from PIL import Image
from pathlib import Path
from typing import Tuple, Optional

from ..config import Config


class PDFExtractor:
    """Extracts text from PDFs using pdfplumber (primary) with OCR fallback."""
    
    def __init__(self, tesseract_cmd: Optional[str] = None):
        """Initialize PDF extractor."""
        if tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
        elif Config.TESSERACT_CMD:
            pytesseract.pytesseract.tesseract_cmd = Config.TESSERACT_CMD
    
    def extract_text_pdfplumber(self, pdf_path: Path) -> Tuple[str, int]:
        """
        Extract text using pdfplumber (primary method).
        
        Args:
            pdf_path: Path to PDF file
        
        Returns:
            Tuple of (extracted_text, num_pages)
        """
        text_parts = []
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                num_pages = len(pdf.pages)
                
                for page_num, page in enumerate(pdf.pages, 1):
                    text = page.extract_text()
                    
                    if text:
                        text_parts.append(f"\n--- Page {page_num} ---\n")
                        text_parts.append(text)
                
                return "\n".join(text_parts), num_pages
        
        except Exception as e:
            raise Exception(f"pdfplumber extraction failed: {str(e)}")
    
    def extract_text_ocr(self, pdf_path: Path) -> Tuple[str, int]:
        """
        Extract text using OCR (for scanned PDFs).
        Uses pdfplumber to render pages to images for OCR.
        
        Args:
            pdf_path: Path to PDF file
        
        Returns:
            Tuple of (extracted_text, num_pages)
        """
        text_parts = []
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                num_pages = len(pdf.pages)
                
                for page_num, page in enumerate(pdf.pages, 1):
                    # Convert page to image
                    im = page.to_image(resolution=200)
                    
                    # Perform OCR on the PIL image
                    text = pytesseract.image_to_string(im.original)
                    
                    if text.strip():
                        text_parts.append(f"\n--- Page {page_num} (OCR) ---\n")
                        text_parts.append(text)
                
                return "\n".join(text_parts), num_pages
        
        except Exception as e:
            raise Exception(f"OCR extraction failed: {str(e)}")
    
    def extract(self, pdf_path: Path) -> Tuple[str, int]:
        """
        Extract text with automatic fallback strategy.
        
        Strategy:
        1. Try pdfplumber (reliable for most PDFs)
        2. If minimal text, try OCR
        
        Args:
            pdf_path: Path to PDF file
        
        Returns:
            Tuple of (extracted_text, num_pages)
        """
        # Try pdfplumber first
        try:
            text, num_pages = self.extract_text_pdfplumber(pdf_path)
            
            # Check if we got meaningful text (more than 100 chars)
            if len(text.strip()) > 100:
                return text, num_pages
            
            # Not enough text, use OCR
            print(f"  Minimal text found, trying OCR for {pdf_path.name}...")
            text, num_pages = self.extract_text_ocr(pdf_path)
            return text, num_pages
        
        except Exception as e:
            # Last resort: OCR
            try:
                print(f"  Standard extraction failed, trying OCR for {pdf_path.name}...")
                return self.extract_text_ocr(pdf_path)
            except Exception as ocr_error:
                raise Exception(f"All extraction methods failed. Last error: {str(ocr_error)}")
