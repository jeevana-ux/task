"""
Enterprise Logging Module
Industry-grade logging with structured output, performance tracking, and field-level tracing.
"""
import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any
from colorama import init, Fore, Style

# Initialize colorama for Windows console colors
init(autoreset=True)


class FieldLevelLogger:
    """Enterprise-grade logger with structured field-level tracking for DSPy extraction."""
    
    def __init__(self, log_file: Optional[Path] = None, console_enabled: bool = True):
        """
        Initialize logger with file and console handlers.
        
        Args:
            log_file: Path to log file. If None, logging goes to console only.
            console_enabled: Whether to enable console output
        """
        self.logger = logging.getLogger("PDFExtractor")
        self.logger.setLevel(logging.DEBUG)
        self.logger.handlers.clear()
        
        # Create formatters
        file_formatter = logging.Formatter(
            '[%(asctime)s] [%(levelname)-8s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        console_formatter = logging.Formatter(
            '%(message)s'
        )
        
        # File handler (if log file provided)
        if log_file:
            log_file.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(file_formatter)
            self.logger.addHandler(file_handler)
        
        # Console handler
        if console_enabled:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(logging.INFO)
            console_handler.setFormatter(console_formatter)
            self.logger.addHandler(console_handler)
        
        self.log_file = log_file
        self._section_counter = 0
    
    def info(self, message: str, console_only: bool = False):
        """Log info level message with optional coloring."""
        if console_only:
            print(f"{Fore.CYAN}ℹ {message}{Style.RESET_ALL}")
        else:
            self.logger.info(message)
    
    def debug(self, message: str):
        """Log debug level message."""
        self.logger.debug(message)
    
    def warning(self, message: str):
        """Log warning level message."""
        self.logger.warning(message)
        print(f"{Fore.YELLOW}⚠️  {message}{Style.RESET_ALL}")
    
    def error(self, message: str):
        """Log error level message."""
        self.logger.error(message)
        print(f"{Fore.RED}❌ {message}{Style.RESET_ALL}")
    
    def success(self, message: str):
        """Log success message."""
        self.logger.info(message)
        print(f"{Fore.GREEN}✓ {message}{Style.RESET_ALL}")
    
    def section(self, title: str):
        """Log section header."""
        self._section_counter += 1
        separator = "=" * 80
        section_msg = f"\n{separator}\n[{self._section_counter}] {title.upper()}\n{separator}"
        self.logger.info(section_msg)
        print(f"\n{Fore.MAGENTA}{'='*60}\n{title}\n{'='*60}{Style.RESET_ALL}")
    
    def log_field_extraction(
        self,
        field_name: str,
        input_snippet: str,
        reasoning: str,
        output_value: Any,
        confidence: str = "Medium"
    ):
        """
        Log detailed field extraction with Chain-of-Thought reasoning.
        
        Args:
            field_name: Name of the field being extracted
            input_snippet: Relevant text snippet used for extraction
            reasoning: Step-by-step reasoning process
            output_value: Final extracted value
            confidence: Confidence level (High/Medium/Low)
        """
        # Structured logging format
        log_entry = f"""
{'─' * 80}
FIELD: {field_name}
{'─' * 80}
INPUT SNIPPET:
{self._truncate(str(input_snippet), 300)}

REASONING:
{reasoning}

CONFIDENCE: {confidence}
OUTPUT: {output_value}
{'─' * 80}
"""
        self.logger.info(log_entry)
        
        # Console output (condensed)
        conf_color = {
            "High": Fore.GREEN,
            "Medium": Fore.YELLOW,
            "Low": Fore.RED
        }.get(confidence, Fore.WHITE)
        
        print(f"  {Fore.CYAN}{field_name:<35}{Style.RESET_ALL} → {conf_color}{output_value}{Style.RESET_ALL}")
    
    def log_token_usage(
        self,
        input_tokens: int,
        output_tokens: int,
        total_tokens: int,
        model: str,
        cost: float
    ):
        """
        Log token usage and cost information.
        
        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            total_tokens: Total tokens used
            model: Model identifier
            cost: Estimated cost in USD
        """
        log_entry = f"""
{'═' * 80}
TOKEN USAGE & COST ANALYSIS
{'═' * 80}
Model:          {model}
Input Tokens:   {input_tokens:,}
Output Tokens:  {output_tokens:,}
Total Tokens:   {total_tokens:,}
Estimated Cost: ${cost:.4f}
{'═' * 80}
"""
        self.logger.info(log_entry)
        
        # Console output
        print(f"\n{Fore.YELLOW}📊 Token Usage:{Style.RESET_ALL}")
        print(f"   Input: {input_tokens:,} | Output: {output_tokens:,} | Total: {total_tokens:,}")
        print(f"   {Fore.GREEN}Cost: ${cost:.4f}{Style.RESET_ALL}")
    
    def log_model_params(self, params: Dict[str, Any]):
        """
        Log model parameters used for LLM call.
        
        Args:
            params: Dictionary of model parameters
        """
        log_entry = "\nMODEL PARAMETERS:\n"
        log_entry += "─" * 40 + "\n"
        for key, value in params.items():
            log_entry += f"  {key:<20}: {value}\n"
        log_entry += "─" * 40 + "\n"
        
        self.logger.info(log_entry)
    
    def log_processing_start(self, input_path: str):
        """Log start of processing."""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        header = f"""
{'╔' + '═' * 78 + '╗'}
║ PDF EXTRACTION & FIELD MAPPING PIPELINE                                     ║
║ Timestamp: {timestamp:<62} ║
║ Input: {str(input_path):<70} ║
{'╚' + '═' * 78 + '╝'}
"""
        self.logger.info(header)
        print(f"{Fore.CYAN}{header}{Style.RESET_ALL}")
    
    def log_processing_complete(self, output_path: Path, duration: float):
        """
        Log completion of processing.
        
        Args:
            output_path: Path to output JSON
            duration: Processing duration in seconds
        """
        footer = f"""
{'╔' + '═' * 78 + '╗'}
║ PROCESSING COMPLETE                                                          ║
║ Duration: {duration:.2f}s{' ' * (69 - len(f'{duration:.2f}s'))}║
║ Output: {str(output_path):<70} ║
{'╚' + '═' * 78 + '╝'}
"""
        self.logger.info(footer)
        print(f"\n{Fore.GREEN}{footer}{Style.RESET_ALL}")
    
    def log_extraction_summary(
        self,
        pdf_pages: int,
        text_chars: int,
        tables_extracted: int,
        cleaned_chars: int
    ):
        """
        Log summary of PDF extraction.
        
        Args:
            pdf_pages: Number of pages processed
            text_chars: Character count of raw text
            tables_extracted: Number of tables extracted
            cleaned_chars: Character count after cleaning
        """
        reduction_pct = ((text_chars - cleaned_chars) / text_chars * 100) if text_chars > 0 else 0
        
        log_entry = f"""
EXTRACTION SUMMARY:
  Pages Processed:    {pdf_pages}
  Raw Text:           {text_chars:,} characters
  Tables Extracted:   {tables_extracted}
  Cleaned Text:       {cleaned_chars:,} characters
  Content Reduction:  {reduction_pct:.1f}%
"""
        self.logger.info(log_entry)
        
        print(f"\n{Fore.CYAN}📄 Extraction Summary:{Style.RESET_ALL}")
        print(f"   Pages: {pdf_pages} | Tables: {tables_extracted}")
        print(f"   Text: {text_chars:,} → {cleaned_chars:,} chars ({reduction_pct:.1f}% reduction)")
    
    def log_performance(self, stage: str, duration: float):
        """
        Log performance metrics for a stage.
        
        Args:
            stage: Name of the processing stage
            duration: Duration in seconds
        """
        self.logger.info(f"[PERFORMANCE] {stage}: {duration:.3f}s")
        print(f"   {Fore.BLUE}⏱️  {stage}: {duration:.3f}s{Style.RESET_ALL}")
    
    def log_llm_context(self, context: str):
        """
        Log the full context passed to the LLM (Debug only).
        
        Args:
            context: The full context string
        """
        log_entry = f"""
{'=' * 80}
FULL LLM CONTEXT (Input Data)
{'=' * 80}
{context}
{'=' * 80}
"""
        self.logger.debug(log_entry)
        print(f"{Fore.WHITE}{log_entry}{Style.RESET_ALL}")

    @staticmethod
    def _truncate(text: str, max_length: int) -> str:
        """Truncate text to max length with ellipsis."""
        if len(text) <= max_length:
            return text
        return text[:max_length] + "..."


def create_logger(output_dir: Path, console_enabled: bool = True) -> FieldLevelLogger:
    """
    Factory function to create a configured logger.
    
    Args:
        output_dir: Directory where log file will be created
        console_enabled: Whether to enable console logging
    
    Returns:
        Configured FieldLevelLogger instance
    """
    log_file = output_dir / "processing.log"
    return FieldLevelLogger(log_file=log_file, console_enabled=console_enabled)

