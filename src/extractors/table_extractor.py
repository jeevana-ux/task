"""
Table Extraction Module
Consolidates all tables into a single CSV file.
"""
import pdfplumber
import pandas as pd
from pathlib import Path
from typing import List
try:
    import fitz  # PyMuPDF
except ImportError:
    pass  # PyMuPDF is optional here
from PIL import Image
from io import BytesIO
try:
    from img2table.document import PDF
    from img2table.ocr import TesseractOCR
    IMG2TABLE_AVAILABLE = True
except ImportError:
    IMG2TABLE_AVAILABLE = False


class TableExtractor:
    """Extracts tables from PDFs and consolidates to CSV."""
    
    def __init__(self):
        """Initialize table extractor."""
        self.ocr = TesseractOCR() if IMG2TABLE_AVAILABLE else None
    
    def extract_tables_pdfplumber(self, pdf_path: Path) -> List[pd.DataFrame]:
        """
        Extract tables using pdfplumber.
        
        Args:
            pdf_path: Path to PDF file
        
        Returns:
            List of DataFrames (one per table)
        """
        tables = []
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages, 1):
                    page_tables = page.extract_tables()
                    
                    for table_idx, table in enumerate(page_tables):
                        if table:
                            # Handle duplicate column names
                            columns = table[0]
                            if columns:
                                seen = {}
                                new_columns = []
                                for col in columns:
                                    col_str = str(col) if col is not None else "col" # Handle None or non-string
                                    if col_str in seen:
                                        seen[col_str] += 1
                                        new_columns.append(f"{col_str}_{seen[col_str]}")
                                    else:
                                        seen[col_str] = 0
                                        new_columns.append(col_str)
                                columns = new_columns
                            
                            # Convert to DataFrame
                            df = pd.DataFrame(table[1:], columns=columns)
                            
                            # Add metadata columns
                            df.insert(0, 'source_page', page_num)
                            df.insert(1, 'table_id', f"p{page_num}_t{table_idx + 1}")
                            
                            tables.append(df)
        
        except Exception as e:
            print(f"pdfplumber table extraction warning: {str(e)}")
        
        return tables
    
    def extract_tables_img2table(self, pdf_path: Path) -> List[pd.DataFrame]:
        """
        Extract tables using img2table (for image-based tables).
        
        Args:
            pdf_path: Path to PDF file
        
        Returns:
            List of DataFrames
        """
        if not IMG2TABLE_AVAILABLE:
            return []
        
        tables = []
        
        try:
            # Extract tables
            pdf = PDF(str(pdf_path))
            extracted_tables = pdf.extract_tables(ocr=self.ocr, implicit_rows=True)
            
            for page_num, page_tables in enumerate(extracted_tables, 1):
                for table_idx, table in enumerate(page_tables):
                    # Convert to DataFrame
                    df = table.df
                    
                    # Add metadata
                    df.insert(0, 'source_page', page_num)
                    df.insert(1, 'table_id', f"p{page_num}_t{table_idx + 1}")
                    
                    tables.append(df)
        
        except Exception as e:
            print(f"img2table extraction warning: {str(e)}")
        
        return tables
    
    def extract_and_consolidate(self, pdf_path: Path, output_csv: Path) -> int:
        """
        Extract all tables and save to single CSV.
        
        Args:
            pdf_path: Path to PDF file
            output_csv: Path to output CSV file
        
        Returns:
            Number of tables extracted
        """
        all_tables = []
        
        # Try pdfplumber first
        tables = self.extract_tables_pdfplumber(pdf_path)
        all_tables.extend(tables)
        
        # If no tables found, try img2table
        if not all_tables and IMG2TABLE_AVAILABLE:
            tables = self.extract_tables_img2table(pdf_path)
            all_tables.extend(tables)
        
        # Consolidate and save
        if all_tables:
            consolidated_df = pd.concat(all_tables, ignore_index=True)
            consolidated_df.to_csv(output_csv, index=False, encoding='utf-8')
            return len(all_tables)
        else:
            # Create empty CSV with header
            pd.DataFrame(columns=['source_page', 'table_id', 'note']).to_csv(
                output_csv, index=False
            )
            return 0
