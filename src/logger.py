"""
======================================================================================
ENTERPRISE LOGGING MODULE - INDUSTRY GRADE
======================================================================================

This module provides comprehensive, beginner-friendly logging for the PDF extraction
and LLM field mapping pipeline. Every stage of processing is logged with detailed
explanations to help anyone understand what's happening.

WHAT THIS MODULE DOES:
----------------------
1. Creates detailed log files that explain every step of the pipeline
2. Shows colorful console output for real-time monitoring
3. Tracks performance metrics (how long each step takes)
4. Logs complete reasoning from the LLM for debugging
5. Provides cost tracking for LLM API usage

LOG LEVELS EXPLAINED:
---------------------
- DEBUG: Detailed technical information (logged to file only)
- INFO: General progress updates (logged to file and console)
- WARNING: Something unexpected but not critical (yellow in console)
- ERROR: Something went wrong (red in console)
- SUCCESS: An operation completed successfully (green in console)

Author: AI Assistant
Version: 2.0 - Enhanced for Beginners
======================================================================================
"""

import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List
import textwrap
import json
from colorama import init, Fore, Style, Back

# Initialize colorama for cross-platform colored terminal output
init(autoreset=True)


class FieldLevelLogger:
    """
    =================================================================================
    INDUSTRY-GRADE FIELD LEVEL LOGGER
    =================================================================================
    
    This class handles ALL logging for the PDF extraction pipeline. It provides:
    
    FOR BEGINNERS:
    - Human-readable messages explaining what's happening
    - Color-coded console output (green=success, red=error, yellow=warning)
    - Detailed reasoning logged to file for later analysis
    
    FOR ADVANCED USERS:
    - Complete LLM prompt/response tracking
    - Performance profiling for each pipeline stage
    - Token usage and cost analysis
    - Few-shot example tracking
    
    HOW LOGGING WORKS:
    ------------------
    1. File Logging: EVERYTHING is logged to the processing.log file in great detail
    2. Console Logging: Only important messages are shown in the terminal (colorful!)
    
    =================================================================================
    """
    
    def __init__(self, log_file: Optional[Path] = None, console_enabled: bool = True):
        """
        Initialize the logger with file and console handlers.
        
        PARAMETERS:
        -----------
        log_file : Path, optional
            Where to save the detailed log file. If None, only console logging is used.
        console_enabled : bool
            Whether to show colorful output in the terminal. Default is True.
        
        WHAT HAPPENS:
        -------------
        1. Creates a unique Python logger instance (prevents duplicate logs)
        2. Sets up file handler for detailed logging
        3. Initializes performance tracking metrics
        """
        # Create unique logger per instance to avoid handler duplication
        # WHY: If we reuse the same logger name, handlers accumulate and logs duplicate
        self.logger = logging.getLogger(f"PDFExtractor_{datetime.now().strftime('%H%M%S')}_{id(self)}")
        self.logger.setLevel(logging.DEBUG)  # Capture ALL log levels
        self.logger.handlers.clear()  # Remove any existing handlers
        self.console_enabled = console_enabled
        self.log_file = log_file
        
        # Performance tracking - we'll measure how long each stage takes
        self._start_time = datetime.now()
        self._stage_times: Dict[str, float] = {}
        
        # Pipeline stage tracking
        self._current_stage = ""
        self._stage_count = 0
        self._total_stages = 5  # PDF extraction, table extraction, cleaning, LLM, saving
        
        # Set up file handler for detailed logging
        if log_file:
            log_file.parent.mkdir(parents=True, exist_ok=True)
            fh = logging.FileHandler(log_file, encoding='utf-8', mode='w')
            fh.setLevel(logging.DEBUG)
            fh.setFormatter(logging.Formatter(
                '[%(asctime)s] [%(levelname)-8s] %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            ))
            self.logger.addHandler(fh)
            
            # Write initial log file header
            self._write_log_file_header()
    
    def _write_log_file_header(self):
        """Write an explanatory header at the top of the log file."""
        header = """
╔══════════════════════════════════════════════════════════════════════════════════════════════════╗
║                                                                                                  ║
║                     PDF EXTRACTION & LLM FIELD MAPPING - DETAILED LOG FILE                       ║
║                                                                                                  ║
╠══════════════════════════════════════════════════════════════════════════════════════════════════╣
║                                                                                                  ║
║  WHAT IS THIS LOG FILE?                                                                          ║
║  ----------------------                                                                          ║
║  This log file contains a complete record of everything that happened during the PDF             ║
║  extraction and LLM field mapping process. It's designed to be readable by anyone,               ║
║  even if you're new to programming or data engineering.                                          ║
║                                                                                                  ║
║  THE PIPELINE STAGES:                                                                            ║
║  --------------------                                                                            ║
║  STAGE 1: PDF TEXT EXTRACTION - We read the text content from the PDF file                       ║
║  STAGE 2: TABLE EXTRACTION    - We find and extract any tables in the PDF                        ║
║  STAGE 3: TEXT CLEANING       - We remove email signatures, disclaimers, etc.                    ║
║  STAGE 4: LLM PROCESSING      - We send the cleaned text to an AI model for analysis             ║
║  STAGE 5: OUTPUT GENERATION   - We create the final JSON files with extracted fields             ║
║                                                                                                  ║
║  LOG LEVEL MEANINGS:                                                                             ║
║  -------------------                                                                             ║
║  [DEBUG]   = Technical details for developers (you can ignore these)                             ║
║  [INFO]    = Normal progress updates (what's happening right now)                                ║
║  [WARNING] = Something unexpected but we can continue (pay attention)                            ║
║  [ERROR]   = Something went wrong (needs investigation)                                          ║
║                                                                                                  ║
╚══════════════════════════════════════════════════════════════════════════════════════════════════╝
"""
        self.logger.info(header)
    
    # =========================================================================
    # CORE LOGGING METHODS
    # =========================================================================
    
    def _console(self, message: str, color: str = Fore.WHITE, prefix: str = ""):
        """
        Print a message to the console with color.
        
        PARAMETERS:
        -----------
        message : str
            The message to display
        color : str
            The colorama color code (Fore.RED, Fore.GREEN, etc.)
        prefix : str
            An emoji or symbol to put before the message (e.g., "✓ ", "❌ ")
        """
        if self.console_enabled:
            print(f"{color}{prefix}{message}{Style.RESET_ALL}")
    
    def _log_file(self, message: str, level: str = "INFO"):
        """
        Log a message to the file only.
        
        PARAMETERS:
        -----------
        message : str
            The message to log
        level : str
            The log level: "DEBUG", "INFO", "WARNING", "ERROR"
        """
        getattr(self.logger, level.lower())(message)
    
    def info(self, message: str, console_only: bool = False):
        """
        Log an informational message.
        
        Use this for general progress updates like "Processing file X" or "Step 1 complete".
        
        PARAMETERS:
        -----------
        message : str
            The information to log
        console_only : bool
            If True, only show in console (not in log file). Default is False.
        """
        if console_only:
            self._console(message, Fore.CYAN, "ℹ ")
        else:
            self._log_file(message)
            self._console(message, Fore.WHITE)
    
    def debug(self, message: str):
        """
        Log a debug message (file only, not shown in console).
        
        Use this for technical details that are only useful for debugging.
        For example: variable values, memory usage, internal state, etc.
        """
        self._log_file(message, "DEBUG")
    
    def warning(self, message: str):
        """
        Log a warning message.
        
        Use this when something unexpected happens but the process can continue.
        For example: "Table extraction failed for page 3, skipping" or
        "LLM response was truncated, using defaults for some fields".
        """
        self._log_file(f"⚠️  WARNING: {message}", "WARNING")
        self._console(message, Fore.YELLOW, "⚠️  ")
    
    def error(self, message: str):
        """
        Log an error message.
        
        Use this when something goes wrong and needs attention.
        For example: "Failed to read PDF file" or "LLM API request failed".
        """
        self._log_file(f"❌ ERROR: {message}", "ERROR")
        self._console(message, Fore.RED, "❌ ")
    
    def success(self, message: str):
        """
        Log a success message.
        
        Use this when an operation completes successfully.
        For example: "PDF extracted successfully" or "All fields mapped".
        """
        self._log_file(f"✓ SUCCESS: {message}")
        self._console(message, Fore.GREEN, "✓ ")
    
    def section(self, title: str):
        """
        Log a section header (visual separator for stages).
        
        Use this to mark the beginning of a new processing stage.
        For example: "LLM Field Extraction with DSPy Chain-of-Thought"
        """
        # File logging - detailed box
        file_sep = "=" * 95
        self._log_file(f"\n{file_sep}\n{title.upper().center(95)}\n{file_sep}")
        
        # Console logging - shorter separator
        console_sep = "=" * 60
        self._console(f"\n{console_sep}\n{title}\n{console_sep}", Fore.MAGENTA)
    
    # =========================================================================
    # STAGE START/END LOGGING - Detailed Pipeline Tracking
    # =========================================================================
    
    def log_stage_start(self, stage_number: int, stage_name: str, description: str):
        """
        Log the start of a pipeline stage with explanation.
        
        This method provides detailed context about what's about to happen,
        which is especially helpful for beginners trying to understand the pipeline.
        
        PARAMETERS:
        -----------
        stage_number : int
            Which stage this is (1, 2, 3, etc.)
        stage_name : str
            The name of the stage (e.g., "PDF Text Extraction")
        description : str
            A beginner-friendly explanation of what this stage does
        """
        self._current_stage = stage_name
        self._stage_count = stage_number
        
        stage_header = f"""

╔══════════════════════════════════════════════════════════════════════════════════════════════════╗
║ STAGE {stage_number}/{self._total_stages}: {stage_name.upper():<84}║
╠══════════════════════════════════════════════════════════════════════════════════════════════════╣
║                                                                                                  ║
║ WHAT HAPPENS IN THIS STAGE:                                                                      ║"""
        
        # Wrap the description to fit in the box
        desc_lines = textwrap.wrap(description, width=90)
        for line in desc_lines:
            stage_header += f"\n║ {line:<96}║"
        
        stage_header += """
║                                                                                                  ║
╚══════════════════════════════════════════════════════════════════════════════════════════════════╝
"""
        self._log_file(stage_header)
        self._console(f"\n📌 Stage {stage_number}/{self._total_stages}: {stage_name}", Fore.CYAN)
    
    def log_stage_end(self, stage_name: str, duration: float, summary: str):
        """
        Log the completion of a pipeline stage.
        
        PARAMETERS:
        -----------
        stage_name : str
            The name of the completed stage
        duration : float
            How long the stage took in seconds
        summary : str
            A brief summary of what was accomplished
        """
        self._stage_times[stage_name] = duration
        
        completion_msg = f"""
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│ ✓ STAGE COMPLETE: {stage_name:<78}│
├──────────────────────────────────────────────────────────────────────────────────────────────────┤
│ Duration: {duration:.3f} seconds                                                                      │
│ Summary: {summary:<87}│
└──────────────────────────────────────────────────────────────────────────────────────────────────┘
"""
        self._log_file(completion_msg)
        self._console(f"   ✓ Complete ({duration:.2f}s): {summary[:50]}", Fore.GREEN)
    
    # =========================================================================
    # PROCESSING START/END LOGGING
    # =========================================================================
    
    def log_processing_start(self, input_path):
        """
        Log the start of processing a PDF file.
        
        This creates a detailed header in the log file showing:
        - Timestamp (when processing started)
        - Input file path
        - Log file location
        
        PARAMETERS:
        -----------
        input_path : Path
            The path to the PDF file being processed
        """
        self._start_time = datetime.now()
        ts = self._start_time.strftime('%Y-%m-%d %H:%M:%S')
        
        header = f"""

╔══════════════════════════════════════════════════════════════════════════════════════════════════╗
║                                                                                                  ║
║                           PDF EXTRACTION & FIELD MAPPING PIPELINE                                ║
║                                                                                                  ║
╠══════════════════════════════════════════════════════════════════════════════════════════════════╣
║                                                                                                  ║
║  PROCESSING STARTED                                                                              ║
║  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  ║
║                                                                                                  ║
║  Timestamp:     {ts:<80}║
║  Input File:    {str(input_path):<80}║
║  Log File:      {str(self.log_file) if self.log_file else 'Console Only':<80}║
║                                                                                                  ║
║  THE PIPELINE WILL:                                                                              ║
║  1. Extract text from the PDF file                                                               ║
║  2. Extract any tables present in the PDF                                                        ║
║  3. Clean the text (remove signatures, disclaimers, headers)                                     ║
║  4. Send cleaned text to an LLM (Large Language Model) for field extraction                      ║
║  5. Generate JSON output files with the extracted data                                           ║
║                                                                                                  ║
╚══════════════════════════════════════════════════════════════════════════════════════════════════╝
"""
        self._log_file(header)
        self._console(f"\n🔄 [{ts[11:]}] Processing: {input_path}", Fore.CYAN)
    
    def log_processing_complete(self, output_path: Path, duration: float):
        """
        Log the completion of processing.
        
        PARAMETERS:
        -----------
        output_path : Path
            Where the output files were saved
        duration : float
            Total processing time in seconds
        """
        footer = f"""

╔══════════════════════════════════════════════════════════════════════════════════════════════════╗
║                                                                                                  ║
║                              ✓ PROCESSING COMPLETE ✓                                             ║
║                                                                                                  ║
╠══════════════════════════════════════════════════════════════════════════════════════════════════╣
║                                                                                                  ║
║  Total Duration:    {duration:.2f} seconds                                                              ║
║  Output Location:   {str(output_path):<76}║
║                                                                                                  ║
║  OUTPUT FILES CREATED:                                                                           ║
║  • *_output.json    - The extracted field values (what you need for auto-punching)               ║
║  • *_config.json    - The FSN configuration file (based on scheme type)                          ║
║  • *_reasoning.json - Full LLM reasoning for debugging (why each field was extracted)            ║
║                                                                                                  ║
╚══════════════════════════════════════════════════════════════════════════════════════════════════╝
"""
        self._log_file(footer)
        
        # Also log performance summary
        self.log_performance_summary()
        
        self._console(f"\n✅ Complete: {output_path} ({duration:.2f}s)", Fore.GREEN)
    
    # =========================================================================
    # MODEL & CONFIGURATION LOGGING
    # =========================================================================
    
    def log_model_params(self, params: Dict[str, Any]):
        """
        Log the LLM model configuration.
        
        This shows which AI model is being used and its settings.
        Understanding these parameters helps with debugging and optimization.
        
        PARAMETERS EXPLAINED:
        ---------------------
        - model: The name of the AI model (e.g., "gpt-4", "claude-3")
        - temperature: Creativity level (0=focused, 1=creative). We use low values for accuracy.
        - max_tokens: Maximum output length. Increase if responses are being cut off.
        - top_p: Another creativity control (0.9 is a good balance)
        """
        model_name = params.get('model', 'N/A')
        temp = params.get('temperature', 'N/A')
        max_tokens = params.get('max_tokens', 'N/A')
        top_p = params.get('top_p', 'N/A')
        
        log_entry = f"""
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│ LLM MODEL CONFIGURATION                                                                          │
├──────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                  │
│ Model Name:      {model_name:<79}│
│                  ↳ This is the AI model that will analyze your PDF content                       │
│                                                                                                  │
│ Temperature:     {str(temp):<79}│
│                  ↳ How "creative" the model should be. 0.0=very focused, 1.0=very creative       │
│                  ↳ We use low values (0.1-0.3) for accurate extraction                           │
│                                                                                                  │
│ Max Tokens:      {str(max_tokens):<79}│
│                  ↳ Maximum length of the model's response (1 token ≈ 4 characters)               │
│                  ↳ If you see "truncated" warnings, increase this value                          │
│                                                                                                  │
│ Top P:           {str(top_p):<79}│
│                  ↳ Another way to control output diversity (0.9 is a good balance)               │
│                                                                                                  │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘
"""
        self._log_file(log_entry)
    
    # =========================================================================
    # EXTRACTION LOGGING
    # =========================================================================
    
    def log_pdf_extraction_details(self, pdf_path: str, num_pages: int, text_length: int, method: str):
        """
        Log detailed information about PDF text extraction.
        
        PARAMETERS:
        -----------
        pdf_path : str
            Path to the PDF file
        num_pages : int
            Number of pages in the PDF
        text_length : int
            Number of characters extracted
        method : str
            Extraction method used (e.g., "PyMuPDF", "pdfplumber", "OCR")
        """
        log_entry = f"""
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│ PDF TEXT EXTRACTION DETAILS                                                                      │
├──────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                  │
│ File:            {pdf_path:<79}│
│ Pages:           {num_pages:<79}│
│ Characters:      {text_length:,} characters extracted                                                   │
│ Method:          {method:<79}│
│                                                                                                  │
│ WHAT THIS MEANS:                                                                                 │
│ ↳ We successfully read {num_pages} page(s) from the PDF                                                 │
│ ↳ The raw text contains {text_length:,} characters (before cleaning)                                     │
│ ↳ We used {method} to extract the text (different methods work better for different PDFs)       │
│                                                                                                  │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘
"""
        self._log_file(log_entry)
    
    def log_extraction_summary(self, pdf_pages: int, text_chars: int, tables_extracted: int, cleaned_chars: int):
        """
        Log a summary of all extraction results.
        
        This shows what was extracted from the PDF and how much was cleaned.
        The reduction percentage tells you how much "noise" (signatures, headers, etc.) was removed.
        """
        reduction = ((text_chars - cleaned_chars) / text_chars * 100) if text_chars > 0 else 0
        
        log_entry = f"""
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│ EXTRACTION SUMMARY                                                                               │
├──────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                  │
│ ┌─ WHAT WE EXTRACTED ─────────────────────────────────────────────────────────────────────────┐  │
│ │                                                                                              │  │
│ │  PDF Pages Processed:    {pdf_pages:<70}│  │
│ │  Raw Text Characters:    {text_chars:,} characters                                                   │  │
│ │  Tables Extracted:       {tables_extracted:<70}│  │
│ │                                                                                              │  │
│ └──────────────────────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                                  │
│ ┌─ AFTER CLEANING ────────────────────────────────────────────────────────────────────────────┐  │
│ │                                                                                              │  │
│ │  Cleaned Characters:     {cleaned_chars:,} characters                                                │  │
│ │  Content Reduction:      {reduction:.1f}% removed (signatures, headers, disclaimers)              │  │
│ │                                                                                              │  │
│ │  💡 TIP: A reduction of 30-70% is normal for email PDFs. This means we successfully          │  │
│ │     removed boilerplate content that would confuse the LLM.                                  │  │
│ │                                                                                              │  │
│ └──────────────────────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                                  │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘
"""
        self._log_file(log_entry)
        self._console(f"   📄 Pages: {pdf_pages} | Tables: {tables_extracted} | Chars: {text_chars:,}→{cleaned_chars:,} ({reduction:.0f}% reduction)", Fore.CYAN)
    
    def log_table_extraction(self, num_tables: int, table_details: List[Dict] = None):
        """
        Log details about table extraction.
        
        PARAMETERS:
        -----------
        num_tables : int
            Number of tables found
        table_details : List[Dict], optional
            Details about each table (rows, columns, page)
        """
        if num_tables == 0:
            msg = """
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│ TABLE EXTRACTION RESULTS                                                                         │
├──────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                  │
│ ⚠️  No tables were found in this PDF.                                                             │
│                                                                                                  │
│ This is normal for emails that don't contain product lists or data tables.                       │
│ The LLM will extract information from the text content instead.                                  │
│                                                                                                  │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘
"""
        else:
            table_info = f"{num_tables} table(s) found"
            if table_details:
                table_info += ":\n"
                for i, t in enumerate(table_details[:5], 1):  # Show max 5 tables
                    table_info += f"│    Table {i}: {t.get('rows', '?')} rows × {t.get('cols', '?')} columns (page {t.get('page', '?')})\n"
            
            msg = f"""
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│ TABLE EXTRACTION RESULTS                                                                         │
├──────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                  │
│ ✓ {table_info:<93}│
│                                                                                                  │
│ Tables often contain important information like:                                                 │
│  • FSN/SKU lists (product identifiers)                                                           │
│  • Discount slabs (percentage breakdowns)                                                        │
│  • Pricing information                                                                           │
│                                                                                                  │
│ The LLM will use this table data along with the email text.                                      │
│                                                                                                  │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘
"""
        self._log_file(msg)
    
    # =========================================================================
    # CLEANING LOGGING
    # =========================================================================
    
    def log_cleaning_details(self, removed_items: List[Dict], total_removed: int):
        """
        Log what was removed during text cleaning.
        
        PARAMETERS:
        -----------
        removed_items : List[Dict]
            List of items that were removed, each with 'category' and 'preview'
        total_removed : int
            Total number of items removed
        """
        log_entry = f"""
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│ TEXT CLEANING DETAILS                                                                            │
├──────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                  │
│ WHAT WE REMOVED ({total_removed} items):                                                              │
│                                                                                                  │
│ The cleaner removes content that would confuse the LLM, such as:                                 │
│  • Email signatures (names, phone numbers, "Regards, ...")                                       │
│  • Disclaimers ("This email is confidential...")                                                 │
│  • CC lists and forwarding headers                                                               │
│  • Legal notices and cautions                                                                    │
│                                                                                                  │
│ REMOVAL LOG:                                                                                     │
"""
        
        # Add details of removed items (limit to 10 for readability)
        for item in removed_items[:10]:
            category = item.get('category', 'Unknown')[:20]
            preview = item.get('text_preview', '')[:60]
            log_entry += f"│  [{category:<20}] \"{preview}...\"\n"
        
        if len(removed_items) > 10:
            log_entry += f"│  ... and {len(removed_items) - 10} more items\n"
        
        log_entry += """│                                                                                                  │
│ 💡 WHY THIS MATTERS:                                                                              │
│    Removing noise helps the LLM focus on the actual scheme/offer content.                        │
│    If too much important content is removed, adjust the cleaning rules.                          │
│                                                                                                  │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘
"""
        self._log_file(log_entry)
    
    # =========================================================================
    # INPUT CONTEXT LOGGING (What we send to LLM)
    # =========================================================================
    
    def log_input_context(self, email_text: str, table_data: str, xlsx_data: str):
        """
        Log the complete input context being sent to the LLM.
        
        This is CRUCIAL for debugging. If the LLM gives wrong outputs,
        check this section to see exactly what information it received.
        """
        email_text = email_text or ""
        table_data = table_data or ""
        xlsx_data = xlsx_data or ""
        
        log_entry = f"""
╔══════════════════════════════════════════════════════════════════════════════════════════════════╗
║                                                                                                  ║
║                               LLM INPUT CONTEXT                                                  ║
║                                                                                                  ║
║  This is the EXACT data we're sending to the Large Language Model (LLM) for analysis.           ║
║  If the LLM gives incorrect outputs, review this section to understand what it "saw".            ║
║                                                                                                  ║
╚══════════════════════════════════════════════════════════════════════════════════════════════════╝

┌─ EMAIL TEXT ({len(email_text):,} characters) ─────────────────────────────────────────────────────────────────
│ 
│ This is the cleaned email content after removing signatures, disclaimers, etc.
│ The LLM uses this to understand the scheme, vendor, dates, and other key information.
│ 
├──────────────────────────────────────────────────────────────────────────────────────────────────
{email_text[:3000]}
{'...[TRUNCATED - Full content in cleaned text files]' if len(email_text) > 3000 else ''}
└──────────────────────────────────────────────────────────────────────────────────────────────────

┌─ TABLE DATA ({len(table_data):,} characters) ─────────────────────────────────────────────────────────────────
│ 
│ Tables extracted from the PDF (FSN lists, discount slabs, pricing data, etc.)
│ 
├──────────────────────────────────────────────────────────────────────────────────────────────────
{table_data[:2000]}
{'...[TRUNCATED - Full content in extracted CSV files]' if len(table_data) > 2000 else ''}
└──────────────────────────────────────────────────────────────────────────────────────────────────

┌─ XLSX DATA ({len(xlsx_data):,} characters) ──────────────────────────────────────────────────────────────────
│ 
│ Data from any Excel files included with the PDF (DMRP files, product lists, etc.)
│ 
├──────────────────────────────────────────────────────────────────────────────────────────────────
{xlsx_data[:1000] if xlsx_data else 'No XLSX data provided'}
{'...[TRUNCATED]' if len(xlsx_data) > 1000 else ''}
└──────────────────────────────────────────────────────────────────────────────────────────────────
"""
        self._log_file(log_entry, "DEBUG")
    
    # =========================================================================
    # FIELD-LEVEL REASONING LOGGING (DETAILED)
    # =========================================================================
    
    def log_field_extraction(
        self,
        field_name: str,
        input_snippet: str,
        reasoning: str,
        output_value: Any,
        confidence: str = "Medium"
    ):
        """
        Log detailed information about a single field extraction.
        
        This is the most important logging for debugging LLM outputs.
        For each field, we log:
        - The field name (e.g., "scheme_type", "vendor_name")
        - The LLM's reasoning (WHY it chose this value)
        - The extracted value
        - Confidence level (High/Medium/Low)
        
        PARAMETERS:
        -----------
        field_name : str
            Name of the field being extracted
        input_snippet : str
            Relevant part of the input text (for context)
        reasoning : str
            The LLM's explanation for why it chose this value
        output_value : Any
            The extracted value
        confidence : str
            How confident we are in this extraction (High/Medium/Low)
        """
        # Handle None values safely
        reasoning = str(reasoning) if reasoning else "No reasoning provided"
        output_value = str(output_value) if output_value else "N/A"
        
        # Wrap reasoning to fit in the box
        reasoning_lines = textwrap.wrap(reasoning, width=92)
        if not reasoning_lines:
            reasoning_lines = ["No reasoning provided."]
        
        # Build the log entry
        log_entry = f"""
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│ FIELD: {field_name:<89}│
├──────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                  │
│ LLM REASONING (Why this value was chosen):                                                       │
"""
        for line in reasoning_lines:
            log_entry += f"│   {line:<93}│\n"
        
        log_entry += f"""│                                                                                                  │
├──────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                  │
│ EXTRACTED VALUE:  {output_value[:75]:<77}│
│ CONFIDENCE:       {confidence:<77}│
│                                                                                                  │
│ CONFIDENCE MEANINGS:                                                                             │
│   • High   = Strong evidence in the text, clear match                                            │
│   • Medium = Some evidence, but could be ambiguous                                               │
│   • Low    = Weak evidence or using default value                                                │
│                                                                                                  │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘
"""
        self._log_file(log_entry)
        
        # Condensed console output with color based on confidence
        conf_color = {"High": Fore.GREEN, "Medium": Fore.YELLOW, "Low": Fore.RED}.get(confidence, Fore.WHITE)
        display_value = output_value[:50] + "..." if len(output_value) > 50 else output_value
        self._console(f"  {field_name:<35} → {display_value}", conf_color)
    
    def log_all_field_extractions(self, extractions: List[Dict[str, Any]]):
        """
        Log all field extractions in a structured format.
        """
        header = """
╔══════════════════════════════════════════════════════════════════════════════════════════════════╗
║                                                                                                  ║
║                              FIELD EXTRACTION RESULTS                                            ║
║                                                                                                  ║
║  Below are ALL the fields extracted by the LLM, with reasoning for each.                         ║
║  Review this section to understand WHY the LLM made each decision.                               ║
║                                                                                                  ║
╚══════════════════════════════════════════════════════════════════════════════════════════════════╝
"""
        self._log_file(header)
        
        for extraction in extractions:
            self.log_field_extraction(
                field_name=extraction.get("field_name", "Unknown"),
                input_snippet=extraction.get("input_snippet", ""),
                reasoning=extraction.get("reasoning", "No reasoning provided"),
                output_value=extraction.get("output_value", "N/A"),
                confidence=extraction.get("confidence", "Medium")
            )
        
        self._log_file("═" * 98)
    
    # =========================================================================
    # FEW-SHOT LEARNING LOGGING
    # =========================================================================
    
    def log_few_shot_context(self, demos: List[Any]):
        """
        Log the few-shot examples being used.
        
        WHAT IS FEW-SHOT LEARNING?
        --------------------------
        Instead of just telling the LLM what to do, we show it examples of correct
        input→output pairs. The LLM learns the pattern from these examples and applies
        it to new inputs. This significantly improves accuracy.
        
        PARAMETERS:
        -----------
        demos : List
            List of example (input, output) pairs being used
        """
        if not demos:
            return
        
        header = f"""
╔══════════════════════════════════════════════════════════════════════════════════════════════════╗
║                                                                                                  ║
║                           FEW-SHOT LEARNING EXAMPLES                                             ║
║                                                                                                  ║
╠══════════════════════════════════════════════════════════════════════════════════════════════════╣
║                                                                                                  ║
║  WHAT IS FEW-SHOT LEARNING?                                                                      ║
║  ──────────────────────────────────────────────────────────────────────────────────────────────  ║
║  Instead of just giving the LLM instructions, we show it {len(demos)} example(s) of correct             ║
║  extractions. The LLM learns from these patterns and applies them to new PDFs.                   ║
║                                                                                                  ║
║  This is like teaching by example: "Here's what a correct extraction looks like"                 ║
║                                                                                                  ║
║  WHY WE USE IT:                                                                                  ║
║  • Improves accuracy significantly (from ~60% to ~90%+)                                          ║
║  • Helps with edge cases and ambiguous text                                                      ║
║  • The LLM understands the exact output format we need                                           ║
║                                                                                                  ║
║  NOTE: More examples = more tokens = higher cost. We balance 2-3 examples for efficiency.        ║
║                                                                                                  ║
╚══════════════════════════════════════════════════════════════════════════════════════════════════╝

EXAMPLES BEING USED:
────────────────────────────────────────────────────────────────────────────────────────────────────
"""
        self._log_file(header)
        
        for idx, demo in enumerate(demos, 1):
            # Safe extraction logic for DSPy Example objects
            try:
                if hasattr(demo, 'toDict'):
                    data = demo.toDict()
                elif isinstance(demo, dict):
                    data = demo
                else:
                    data = getattr(demo, '_store', vars(demo))
            except:
                data = {}
            
            # Extract fields with safe fallbacks
            email_text = str(data.get('email_text', getattr(demo, 'email_text', 'N/A')))[:200]
            reasoning = str(data.get('reasoning', getattr(demo, 'reasoning', 'N/A')))[:300]
            scheme_type = data.get('scheme_type', getattr(demo, 'scheme_type', 'N/A'))
            scheme_subtype = data.get('scheme_subtype', getattr(demo, 'scheme_subtype', 'N/A'))
            
            demo_entry = f"""
┌─ EXAMPLE #{idx} ─────────────────────────────────────────────────────────────────────────────────────
│
│ INPUT (Email Text Preview):
│   "{email_text}..."
│
│ LLM'S REASONING (for this example):
│   "{reasoning}..."
│
│ OUTPUT:
│   scheme_type: {scheme_type}
│   scheme_subtype: {scheme_subtype}
│
└──────────────────────────────────────────────────────────────────────────────────────────────────────
"""
            self._log_file(demo_entry)
    
    # =========================================================================
    # TOKEN USAGE & COST LOGGING
    # =========================================================================
    
    def log_token_usage(self, input_tokens: int, output_tokens: int, total_tokens: int, model: str, cost: float):
        """
        Log token usage and estimated cost.
        
        WHAT ARE TOKENS?
        ----------------
        Tokens are the "units" that LLMs use to process text. Roughly:
        - 1 token ≈ 4 characters in English
        - 1 token ≈ 0.75 words
        
        WHY THIS MATTERS:
        -----------------
        - LLM APIs charge per token
        - More tokens = higher cost
        - Input tokens: what we send to the LLM
        - Output tokens: what the LLM generates (usually more expensive)
        """
        log_entry = f"""
╔══════════════════════════════════════════════════════════════════════════════════════════════════╗
║                                                                                                  ║
║                              TOKEN USAGE & COST ANALYSIS                                         ║
║                                                                                                  ║
╠══════════════════════════════════════════════════════════════════════════════════════════════════╣
║                                                                                                  ║
║  WHAT ARE TOKENS?                                                                                ║
║  ────────────────────────────────────────────────────────────────────────────────────────────    ║
║  Tokens are the "units" LLMs use. 1 token ≈ 4 characters ≈ 0.75 words                            ║
║                                                                                                  ║
║  TOKEN BREAKDOWN:                                                                                ║
║  ────────────────────────────────────────────────────────────────────────────────────────────    ║
║                                                                                                  ║
║  Model:            {model:<76}║
║                                                                                                  ║
║  Input Tokens:     {input_tokens:,} tokens                                                                  ║
║                    ↳ This is what we sent TO the LLM (email text, context, examples)             ║
║                                                                                                  ║
║  Output Tokens:    {output_tokens:,} tokens                                                                 ║
║                    ↳ This is what the LLM sent back (extracted fields, reasoning)                ║
║                                                                                                  ║
║  Total Tokens:     {total_tokens:,} tokens                                                                   ║
║                                                                                                  ║
║  ────────────────────────────────────────────────────────────────────────────────────────────    ║
║                                                                                                  ║
║  💰 ESTIMATED COST:   ${cost:.4f}                                                                      ║
║                                                                                                  ║
║  Cost varies by model. To reduce cost:                                                           ║
║   • Use fewer few-shot examples                                                                  ║
║   • Choose a cheaper model (e.g., gpt-3.5 vs gpt-4)                                              ║
║   • Reduce max_tokens if outputs are being padded                                                ║
║                                                                                                  ║
╚══════════════════════════════════════════════════════════════════════════════════════════════════╝
"""
        self._log_file(log_entry)
        self._console(f"\n📊 Tokens: {input_tokens:,} in | {output_tokens:,} out | Total: {total_tokens:,} | Cost: ${cost:.4f}", Fore.YELLOW)
    
    # =========================================================================
    # PERFORMANCE LOGGING
    # =========================================================================
    
    def log_performance(self, stage: str, duration: float):
        """
        Log performance metric for a processing stage.
        
        This helps identify bottlenecks in the pipeline.
        """
        self._stage_times[stage] = duration
        self._log_file(f"[PERFORMANCE] {stage}: {duration:.3f} seconds")
        self._console(f"   ⏱️  {stage}: {duration:.3f}s", Fore.BLUE)
    
    def log_performance_summary(self):
        """
        Log a complete performance breakdown.
        
        Shows how long each stage took and what percentage of total time it consumed.
        """
        if not self._stage_times:
            return
        
        total = sum(self._stage_times.values())
        
        log_entry = """
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│ PERFORMANCE BREAKDOWN                                                                            │
├──────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                  │
│ This shows how long each stage took. Use this to identify bottlenecks.                           │
│                                                                                                  │
│ STAGE                                           DURATION           % OF TOTAL                    │
│ ─────────────────────────────────────────────────────────────────────────────────────────────    │
"""
        for stage, duration in self._stage_times.items():
            pct = (duration / total * 100) if total > 0 else 0
            bar = "█" * int(pct / 5)  # Visual progress bar
            log_entry += f"│ {stage:<40} {duration:>8.3f}s     {pct:>5.1f}%  {bar:<20}│\n"
        
        log_entry += f"""│ ─────────────────────────────────────────────────────────────────────────────────────────────    │
│ TOTAL                                           {total:>8.3f}s    100.0%                          │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘
"""
        self._log_file(log_entry)
    
    # =========================================================================
    # OUTPUT LOGGING
    # =========================================================================
    
    def log_final_output(self, output_json: Dict[str, Any]):
        """
        Log the final JSON output with explanations.
        """
        log_entry = f"""
╔══════════════════════════════════════════════════════════════════════════════════════════════════╗
║                                                                                                  ║
║                                   FINAL OUTPUT JSON                                              ║
║                                                                                                  ║
║  This is the final extracted data that will be saved to the output JSON file.                   ║
║  Use this for auto-punching into the Retailer Hub system.                                        ║
║                                                                                                  ║
╚══════════════════════════════════════════════════════════════════════════════════════════════════╝

OUTPUT JSON:
────────────────────────────────────────────────────────────────────────────────────────────────────

{json.dumps(output_json, indent=2, ensure_ascii=False)}

────────────────────────────────────────────────────────────────────────────────────────────────────

FIELD EXPLANATIONS:
────────────────────────────────────────────────────────────────────────────────────────────────────
• scheme_type    : The main category (BUY_SIDE, SELL_SIDE, OFC, or PDC)
• scheme_subtype : The specific sub-category (PERIODIC_CLAIM, PDC, PUC, LS, CP, PRX, SC, OFC)
• scheme_name    : A short name/title for this scheme
• vendor_name    : The brand/company offering this scheme
• start_date     : When the scheme becomes active (DD/MM/YYYY format)
• end_date       : When the scheme expires (DD/MM/YYYY format)
• duration       : The full date range (start to end)
────────────────────────────────────────────────────────────────────────────────────────────────────
"""
        self._log_file(log_entry)
    
    # =========================================================================
    # UTILITY METHODS
    # =========================================================================
    
    def log_llm_context(self, context: str):
        """Log full LLM context (file only)."""
        self._log_file(f"FULL LLM CONTEXT:\n{context}", "DEBUG")


def create_logger(output_dir: Path, console_enabled: bool = True) -> FieldLevelLogger:
    """
    Factory function to create a configured logger.
    
    PARAMETERS:
    -----------
    output_dir : Path
        Directory where the log file will be saved
    console_enabled : bool
        Whether to show colorful console output
    
    RETURNS:
    --------
    FieldLevelLogger
        A configured logger instance ready for use
    """
    log_file = output_dir / "processing.log"
    return FieldLevelLogger(log_file=log_file, console_enabled=console_enabled)
