"""
Enterprise Logging Module
Industry-grade structured logging with complete field-level reasoning tracking.
"""
import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List
import textwrap
from colorama import init, Fore, Style

init(autoreset=True)


class FieldLevelLogger:
    """
    Industry-grade logger with:
    - Structured file logging (detailed)
    - Console logging (condensed)
    - Complete field-level reasoning tracking
    - Performance metrics
    - Input/Output tracing
    """
    
    def __init__(self, log_file: Optional[Path] = None, console_enabled: bool = True):
        """Initialize logger with file and console handlers."""
        # Create unique logger per instance to avoid handler duplication
        self.logger = logging.getLogger(f"PDFExtractor_{datetime.now().strftime('%H%M%S')}_{id(self)}")
        self.logger.setLevel(logging.DEBUG)
        self.logger.handlers.clear()
        self.console_enabled = console_enabled
        self.log_file = log_file
        
        # Metrics tracking
        self._start_time = datetime.now()
        self._stage_times: Dict[str, float] = {}
        
        # File handler - detailed logging
        if log_file:
            log_file.parent.mkdir(parents=True, exist_ok=True)
            fh = logging.FileHandler(log_file, encoding='utf-8', mode='w')
            fh.setLevel(logging.DEBUG)
            fh.setFormatter(logging.Formatter(
                '[%(asctime)s] [%(levelname)-8s] %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            ))
            self.logger.addHandler(fh)
    
    # =========================================================================
    # CORE LOGGING METHODS
    # =========================================================================
    
    def _console(self, message: str, color: str = Fore.WHITE, prefix: str = ""):
        """Print to console if enabled."""
        if self.console_enabled:
            print(f"{color}{prefix}{message}{Style.RESET_ALL}")
    
    def _log_file(self, message: str, level: str = "INFO"):
        """Log to file only."""
        getattr(self.logger, level.lower())(message)
    
    def info(self, message: str, console_only: bool = False):
        """Log info message."""
        if console_only:
            self._console(message, Fore.CYAN, "ℹ ")
        else:
            self._log_file(message)
            self._console(message, Fore.WHITE)
    
    def debug(self, message: str):
        """Log debug (file only)."""
        self._log_file(message, "DEBUG")
    
    def warning(self, message: str):
        """Log warning."""
        self._log_file(f"WARNING: {message}", "WARNING")
        self._console(message, Fore.YELLOW, "⚠️  ")
    
    def error(self, message: str):
        """Log error."""
        self._log_file(f"ERROR: {message}", "ERROR")
        self._console(message, Fore.RED, "❌ ")
    
    def success(self, message: str):
        """Log success."""
        self._log_file(message)
        self._console(message, Fore.GREEN, "✓ ")
    
    def section(self, title: str):
        """Log section header."""
        sep = "=" * 80
        self._log_file(f"\n{sep}\n{title.upper()}\n{sep}")
        self._console(f"\n{'='*60}\n{title}\n{'='*60}", Fore.MAGENTA)
    
    # =========================================================================
    # PROCESSING START/END LOGGING
    # =========================================================================
    
    def log_processing_start(self, input_path):
        """Log processing start with full context."""
        self._start_time = datetime.now()
        ts = self._start_time.strftime('%Y-%m-%d %H:%M:%S')
        
        header = f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    PDF EXTRACTION & FIELD MAPPING PIPELINE                    ║
╠══════════════════════════════════════════════════════════════════════════════╣
║ Timestamp:    {ts:<63}║
║ Input File:   {str(input_path):<63}║
║ Log File:     {str(self.log_file) if self.log_file else 'Console Only':<63}║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
        self._log_file(header)
        self._console(f"\n🔄 [{ts[11:]}] Processing: {input_path}", Fore.CYAN)
    
    def log_processing_complete(self, output_path: Path, duration: float):
        """Log processing completion."""
        footer = f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                           PROCESSING COMPLETE                                 ║
╠══════════════════════════════════════════════════════════════════════════════╣
║ Duration:     {duration:.2f} seconds{' '*(54-len(f'{duration:.2f}'))}║
║ Output:       {str(output_path):<63}║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
        self._log_file(footer)
        self._console(f"✅ Complete: {output_path} ({duration:.2f}s)", Fore.GREEN)
    
    # =========================================================================
    # MODEL & CONFIGURATION LOGGING
    # =========================================================================
    
    def log_model_params(self, params: Dict[str, Any]):
        """Log model configuration parameters."""
        log_entry = f"""
┌──────────────────────────────────────────────────────────────────────────────┐
│ MODEL CONFIGURATION                                                          │
├──────────────────────────────────────────────────────────────────────────────┤
│ Model:          {params.get('model', 'N/A'):<60}│
│ Temperature:    {params.get('temperature', 'N/A'):<60}│
│ Max Tokens:     {params.get('max_tokens', 'N/A'):<60}│
│ Top P:          {params.get('top_p', 'N/A'):<60}│
└──────────────────────────────────────────────────────────────────────────────┘
"""
        self._log_file(log_entry)
    
    # =========================================================================
    # EXTRACTION SUMMARY LOGGING
    # =========================================================================
    
    def log_extraction_summary(self, pdf_pages: int, text_chars: int, tables_extracted: int, cleaned_chars: int):
        """Log detailed extraction summary."""
        reduction = ((text_chars - cleaned_chars) / text_chars * 100) if text_chars > 0 else 0
        
        log_entry = f"""
┌──────────────────────────────────────────────────────────────────────────────┐
│ EXTRACTION SUMMARY                                                           │
├──────────────────────────────────────────────────────────────────────────────┤
│ PDF Pages Processed:    {pdf_pages:<52}│
│ Raw Text Characters:    {text_chars:,}{' '*(52-len(f'{text_chars:,}'))}│
│ Tables Extracted:       {tables_extracted:<52}│
│ Cleaned Characters:     {cleaned_chars:,}{' '*(52-len(f'{cleaned_chars:,}'))}│
│ Content Reduction:      {reduction:.1f}%{' '*(51-len(f'{reduction:.1f}%'))}│
└──────────────────────────────────────────────────────────────────────────────┘
"""
        self._log_file(log_entry)
        self._console(f"   📄 Pages: {pdf_pages} | Tables: {tables_extracted} | Chars: {text_chars:,}→{cleaned_chars:,} ({reduction:.0f}% reduction)", Fore.CYAN)
    
    # =========================================================================
    # INPUT CONTEXT LOGGING
    # =========================================================================
    
    def log_input_context(self, email_text: str, table_data: str, xlsx_data: str):
        """Log the complete input context being sent to LLM."""
        log_entry = f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                           LLM INPUT CONTEXT                                   ║
╚══════════════════════════════════════════════════════════════════════════════╝

┌─ EMAIL TEXT ({len(email_text)} characters) ─────────────────────────────────────────────────────
{email_text[:2000]}{'...[TRUNCATED]' if len(email_text) > 2000 else ''}
└──────────────────────────────────────────────────────────────────────────────

┌─ TABLE DATA ({len(table_data)} characters) ─────────────────────────────────────────────────────
{table_data[:1500]}{'...[TRUNCATED]' if len(table_data) > 1500 else ''}
└──────────────────────────────────────────────────────────────────────────────

┌─ XLSX DATA ({len(xlsx_data)} characters) ──────────────────────────────────────────────────────
{xlsx_data[:500]}{'...[TRUNCATED]' if len(xlsx_data) > 500 else ''}
└──────────────────────────────────────────────────────────────────────────────
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
        """Log detailed field extraction with full reasoning."""
        # Fix: Use textwrap to support unlimited reasoning length in file logs
        reasoning_lines = textwrap.wrap(str(reasoning), width=76)
        if not reasoning_lines:
            reasoning_lines = ["No reasoning provided."]
            
        # Create multiline reasoning block for the box
        reasoning_block = "\n".join([f"│ {line:<76}│" for line in reasoning_lines])
        
        # Detailed file logging (FULL REASONING)
        log_entry = f"""
┌──────────────────────────────────────────────────────────────────────────────┐
│ FIELD: {field_name:<69}│
├──────────────────────────────────────────────────────────────────────────────┤
│ REASONING:                                                                   │
{reasoning_block}
├──────────────────────────────────────────────────────────────────────────────┤
│ OUTPUT VALUE: {str(output_value)[:62]:<62}│
│ CONFIDENCE:   {confidence:<62}│
└──────────────────────────────────────────────────────────────────────────────┘
"""
        self._log_file(log_entry)
        
        # Condensed console output
        conf_color = {"High": Fore.GREEN, "Medium": Fore.YELLOW, "Low": Fore.RED}.get(confidence, Fore.WHITE)
        display_value = str(output_value)[:50] + "..." if len(str(output_value)) > 50 else str(output_value)
        self._console(f"  {field_name:<35} → {display_value}", conf_color)
        
        # Show reasoning snippet in console
        reasoning_short = reasoning_lines[0][:90] + "..." if len(reasoning) > 90 else reasoning_lines[0]
        self._console(f"  {Style.DIM}↳ {reasoning_short}{Style.RESET_ALL}")
    
    def log_all_field_extractions(self, extractions: List[Dict[str, Any]]):
        """Log all field extractions in a structured format."""
        header = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                      FIELD EXTRACTION RESULTS                                 ║
╠══════════════════════════════════════════════════════════════════════════════╣
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
        
        self._log_file("╚══════════════════════════════════════════════════════════════════════════════╝")
    
    # =========================================================================
    # TOKEN USAGE & COST LOGGING
    # =========================================================================
    
    def log_token_usage(self, input_tokens: int, output_tokens: int, total_tokens: int, model: str, cost: float):
        """Log token usage and cost analysis."""
        log_entry = f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                        TOKEN USAGE & COST ANALYSIS                            ║
╠══════════════════════════════════════════════════════════════════════════════╣
║ Model:            {model:<58}║
║ Input Tokens:     {input_tokens:,}{' '*(58-len(f'{input_tokens:,}'))}║
║ Output Tokens:    {output_tokens:,}{' '*(58-len(f'{output_tokens:,}'))}║
║ Total Tokens:     {total_tokens:,}{' '*(58-len(f'{total_tokens:,}'))}║
║ Estimated Cost:   ${cost:.4f}{' '*(57-len(f'${cost:.4f}'))}║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
        self._log_file(log_entry)
        self._console(f"\n📊 Tokens: {input_tokens:,} in | {output_tokens:,} out | ${cost:.4f}", Fore.YELLOW)
    
    # =========================================================================
    # PERFORMANCE LOGGING
    # =========================================================================
    
    def log_performance(self, stage: str, duration: float):
        """Log performance metric for a processing stage."""
        self._stage_times[stage] = duration
        self._log_file(f"[PERFORMANCE] {stage}: {duration:.3f}s")
        self._console(f"   ⏱️  {stage}: {duration:.3f}s", Fore.BLUE)
    
    def log_performance_summary(self):
        """Log complete performance summary."""
        if not self._stage_times:
            return
        
        log_entry = """
┌──────────────────────────────────────────────────────────────────────────────┐
│ PERFORMANCE BREAKDOWN                                                        │
├──────────────────────────────────────────────────────────────────────────────┤
"""
        total = 0
        for stage, duration in self._stage_times.items():
            total += duration
            log_entry += f"│ {stage:<40} {duration:>8.3f}s{' '*26}│\n"
        
        log_entry += f"├──────────────────────────────────────────────────────────────────────────────┤\n"
        log_entry += f"│ TOTAL{' '*35} {total:>8.3f}s{' '*26}│\n"
        log_entry += f"└──────────────────────────────────────────────────────────────────────────────┘"
        
        self._log_file(log_entry)
    
    # =========================================================================
    # OUTPUT LOGGING
    # =========================================================================
    
    def log_final_output(self, output_json: Dict[str, Any]):
        """Log the final JSON output."""
        import json
        
        log_entry = f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                            FINAL OUTPUT JSON                                  ║
╚══════════════════════════════════════════════════════════════════════════════╝

{json.dumps(output_json, indent=2, ensure_ascii=False)}

════════════════════════════════════════════════════════════════════════════════
"""
        self._log_file(log_entry)
    
    # =========================================================================
    # UTILITY METHODS
    # =========================================================================
    

    
    def log_llm_context(self, context: str):
        """Log full LLM context (file only, truncated)."""
        self._log_file(f"LLM CONTEXT (first 3000 chars):\n{context[:3000]}...", "DEBUG")
        
    def log_few_shot_context(self, demos: List[Any]):
        """Log the few-shot examples (demos) being used in the prompt."""
        if not demos:
            return
            
        header = f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    ACTIVE FEW-SHOT EXAMPLES (PROMPT)                          ║
╠══════════════════════════════════════════════════════════════════════════════╣
║ The following {len(demos)} examples are being injected into the prompt.            ║
║ The LLM will use these patterns to reason about the new input.               ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
        self._log_file(header)
        
        for idx, demo in enumerate(demos, 1):
            # Safe extraction logic for DSPy Example objects
            # They behave like dicts but sometimes need explicit casting
            try:
                # Try dict access if possible, or fallback to object attributes
                if hasattr(demo, 'toDict'):
                    data = demo.toDict()
                elif isinstance(demo, dict):
                    data = demo
                else:
                    data = getattr(demo, '_store', vars(demo))
            except:
                data = {}

            # Extract fields with safe fallbacks
            email_text = data.get('email_text', getattr(demo, 'email_text', 'N/A'))
            reasoning = data.get('reasoning', getattr(demo, 'reasoning', 'N/A'))
            scheme_type = data.get('scheme_type', getattr(demo, 'scheme_type', 'N/A'))
            
            # Format truncated demo
            demo_entry = f"""
┌─ EXAMPLE #{idx} ──────────────────────────────────────────────────────────────────
│ INPUT (Email): {str(email_text)[:100]}...
│
│ REASONING: {str(reasoning)[:200]}...
│
│ OUTPUT (Scheme Type): {scheme_type}
└──────────────────────────────────────────────────────────────────────────────
"""
            self._log_file(demo_entry)


def create_logger(output_dir: Path, console_enabled: bool = True) -> FieldLevelLogger:
    """Factory function to create a configured logger."""
    log_file = output_dir / "processing.log"
    return FieldLevelLogger(log_file=log_file, console_enabled=console_enabled)
