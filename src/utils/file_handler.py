"""
File Handler Utilities
Manages file I/O, timestamp-based folder creation, and XLSX conversion.
"""
import os
import shutil
from pathlib import Path
from datetime import datetime
from typing import List, Tuple
import openpyxl
import pandas as pd


class FileHandler:
    """Handles file operations and output directory management."""
    
    @staticmethod
    def create_timestamp_folder(base_dir: Path, prefix: str = "") -> Path:
        """
        Create output folder with timestamp naming.
        Format: {prefix}_{DDMMYYYYHHMM} or just {DDMMYYYYHHMM} if no prefix.
        
        Args:
            base_dir: Base output directory
            prefix: Optional prefix for the folder name
        
        Returns:
            Path to created timestamp folder
        """
        timestamp = datetime.now().strftime("%d%m%Y%H%M")
        folder_name = f"{prefix}_{timestamp}" if prefix else timestamp
        output_path = base_dir / folder_name
        output_path.mkdir(parents=True, exist_ok=True)
        
        
        return output_path
    
    @staticmethod
    def resolve_prefix(input_path: str, pdf_files: List[Path]) -> str:
        """
        Logic to determine a smart prefix for output folders based on input.
        """
        input_path_obj = Path(input_path)
        if input_path_obj.is_file():
            return input_path_obj.stem
        elif len(pdf_files) == 1:
            return pdf_files[0].stem
        return ""

    @staticmethod
    def get_output_folder_name(pdf_file: Path, input_root: Path, timestamp: str) -> str:
        """
        Determines the output subfolder name based on whether input is flat or nested.
        """
        if pdf_file.parent.resolve() == input_root.resolve():
            # Flat structure
            return f"{pdf_file.stem}_{timestamp}"
        else:
            # Nested structure (use parent folder name)
            return f"{pdf_file.parent.name}_{timestamp}"
    
    @staticmethod
    def get_input_files(input_path: str) -> Tuple[List[Path], List[Path]]:
        """
        Get all PDF and XLSX files from input path.
        
        Args:
            input_path: Path to file or directory
        
        Returns:
            Tuple of (pdf_files, xlsx_files) as lists of Path objects
        """
        input_path = Path(input_path)
        pdf_files = []
        xlsx_files = []
        
        if input_path.is_file():
            if input_path.suffix.lower() == '.pdf':
                pdf_files.append(input_path)
            elif input_path.suffix.lower() in ['.xlsx', '.xls']:
                xlsx_files.append(input_path)
        elif input_path.is_dir():
            pdf_files = list(input_path.glob("**/*.pdf"))
            xlsx_files = list(input_path.glob("**/*.xlsx")) + list(input_path.glob("**/*.xls"))
        else:
            raise FileNotFoundError(f"Input path not found: {input_path}")
        
        return pdf_files, xlsx_files
    
    @staticmethod
    def xlsx_to_text(xlsx_path: Path, row_limit: int = 50) -> str:
        """
        Convert XLSX file to text representation, limiting the number of rows.
        
        Args:
            xlsx_path: Path to XLSX file
            row_limit: Maximum number of data rows to include per sheet
        
        Returns:
            Text representation of all sheets (up to row_limit each)
        """
        text_parts = []
        
        try:
            # Load workbook
            wb = openpyxl.load_workbook(xlsx_path, data_only=True)
            
            for sheet_name in wb.sheetnames:
                sheet = wb[sheet_name]
                text_parts.append(f"\n=== Sheet: {sheet_name} ===\n")
                
                # Convert to pandas for easier text conversion
                data = sheet.values
                try:
                    cols = next(data)
                    df = pd.DataFrame(data, columns=cols)
                    
                    # Apply row limit
                    if row_limit and len(df) > row_limit:
                        df = df.head(row_limit)
                        trunc_msg = f"[NOTE: Only first {row_limit} rows shown for this sheet]"
                        text_parts.append(trunc_msg + "\n")
                    
                    # Convert to string
                    text_parts.append(df.to_string(index=False))
                    text_parts.append("\n")
                except StopIteration:
                    text_parts.append("[Empty Sheet]\n")
            
            return "\n".join(text_parts)
        
        except Exception as e:
            return f"[Error reading XLSX: {str(e)}]"
    
    @staticmethod
    def save_text(content: str, output_path: Path):
        """
        Save text content to file.
        
        Args:
            content: Text content to save
            output_path: Destination file path
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    @staticmethod
    def save_json(content: str, output_path: Path):
        """
        Save JSON content to file.
        
        Args:
            content: JSON content as string
            output_path: Destination file path
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    @staticmethod
    def read_file(file_path: Path) -> str:
        """
        Read text file content.
        
        Args:
            file_path: Path to file
        
        Returns:
            File content as string
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
