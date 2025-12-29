"""
Main Orchestration Script - Enhanced for Batch Processing
Processes all PDFs in input folder and provides consolidated JSON output with LLM metrics.
"""
import sys
import os
import json
import time
from datetime import datetime
from pathlib import Path
import click

from src.config import Config
from src.logger import create_logger
from src.utils.file_handler import FileHandler
from src.utils.token_tracker import TokenTracker
from src.extractors.pdf_extractor import PDFExtractor
from src.extractors.table_extractor import TableExtractor
from src.cleaners.deterministic_cleaner import DeterministicContentCleaner as TextCleaner


@click.command()
@click.option('--input', 'input_path', required=True, type=click.Path(exists=True), help='Input PDF file or folder path')
@click.option('--output', 'output_dir', default='./outputs', type=click.Path(), help='Output directory (default: ./outputs/)')
@click.option('--model', default=None, help=f'OpenRouter model name (default: {Config.DEFAULT_MODEL})')
@click.option('--temperature', default=None, type=float, help=f'LLM temperature 0.0-1.0 (default: {Config.TEMPERATURE})')
@click.option('--max-tokens', default=None, type=int, help=f'Max output tokens (default: {Config.MAX_TOKENS})')
@click.option('--extract-only', is_flag=True, help='Stop after extraction, skipping context generation and LLM')
@click.option('--context-only', is_flag=True, help='Generate full LLM context file but skip LLM call')
def main(input_path, output_dir, model, temperature, max_tokens, extract_only, context_only):
    """PDF Extraction & Retailer Hub Field Mapping System - Batch Processing"""
    start_time = time.time()
    
    # Validate and configure
    try:
        Config.validate()
    except ValueError as e:
        click.echo(f"❌ Configuration Error: {e}", err=True)
        sys.exit(1)
    
    if model:
        Config.DEFAULT_MODEL = model
    if temperature is not None:
        Config.TEMPERATURE = temperature
    if max_tokens:
        Config.MAX_TOKENS = max_tokens
    
    # Get input files early to determine naming strategy
    try:
        pdf_files, xlsx_files = FileHandler.get_input_files(input_path)
    except Exception as e:
        click.echo(f"❌ Error reading input: {e}", err=True)
        sys.exit(1)

    # Determine output naming prefix
    # If explicit file path OR detector found exactly one PDF (even in a folder) -> use that filename
    folder_prefix = ""
    input_path_obj = Path(input_path)
    
    if input_path_obj.is_file():
        folder_prefix = input_path_obj.stem
    elif len(pdf_files) == 1:
        folder_prefix = pdf_files[0].stem
    
    # Setup output (just validate base dir exists)
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # We will create loggers per file subsequently
    
    # Configure DSPy (initial check)
    # configure_dspy(logger) # Defer to loop
    
    # Initialize metrics aggregation
    all_results = []
    metrics = {
        "total_pdfs": 0, "successful": 0, "failed": 0,
        "total_input_tokens": 0, "total_output_tokens": 0, "total_tokens": 0, "total_cost": 0.0,
        "model": Config.DEFAULT_MODEL, "per_file_metrics": []
    }
    
    click.echo(f"\n📂 Found {len(pdf_files)} PDF(s) and {len(xlsx_files)} XLSX file(s)")
    
    if not pdf_files:
        click.echo("❌ No PDF files found in input path", err=True)
        sys.exit(1)
    
    metrics["total_pdfs"] = len(pdf_files)
    
    # Create per-file output for each PDF
    input_path_obj = Path(input_path).resolve()
    run_timestamp = datetime.now().strftime("%d%m%Y_%H%M%S")  # Date+Time for this run
    
    for idx, pdf_file in enumerate(pdf_files, 1):
        # Determine Output Folder Name based on Input Structure
        # Case 1: Flat structure (PDF is directly in input_path) -> Output Name: {filename}_{timestamp}_folder
        # Case 2: Nested structure (PDF is in a subfolder) -> Output Name: {subfolder_name}_{timestamp}
        
        if pdf_file.parent.resolve() == input_path_obj:
             # Case 1: Flat input
             output_folder_name = f"{pdf_file.stem}_{run_timestamp}"
        else:
             # Case 2: Nested input (Group Folder)
             output_folder_name = f"{pdf_file.parent.name}_{run_timestamp}"
        
        # Output base: ./outputs/{OutputFolderName}/
        file_output_path = Path(output_dir) / output_folder_name
        file_output_path.mkdir(parents=True, exist_ok=True)
        
        # 2. Filter XLSX files: Only use those in the SAME directory as the PDF
        local_xlsx_files = [x for x in xlsx_files if x.parent == pdf_file.parent]

        # Initialize logger for this file
        logger = create_logger(file_output_path, console_enabled=True)
        
        # Log visual separator
        logger.info("\n" + "="*80, console_only=True)
        logger.info(f"PROCESSING FILE {idx}/{len(pdf_files)}: {pdf_file.name}".center(80), console_only=True)
        logger.info("="*80 + "\n", console_only=True)
        
        logger.log_processing_start(pdf_file)
        
        try:

            # Determine if we should stop early
            should_stop_early = extract_only or context_only
            
            # Configure DSPy for this run (logger might change), ONLY if running full pipeline
            if not should_stop_early:
                configure_dspy(logger)
                logger.log_model_params(Config.get_model_params())

            result, file_metrics = process_pdf(pdf_file, file_output_path, local_xlsx_files, logger, idx, should_stop_early)
            
            if should_stop_early:
                logger.success(f"✓ Context generation completed for {pdf_file.name} (Skipped LLM)")
                logger.info(f"✅ Output saved to: {file_output_path}")
                metrics["successful"] += 1
                continue

            all_results.append(result)
            metrics["per_file_metrics"].append(file_metrics)
            metrics["successful"] += 1
            
            # Aggregate
            metrics["total_input_tokens"] += file_metrics["input_tokens"]
            metrics["total_output_tokens"] += file_metrics["output_tokens"]
            metrics["total_tokens"] += file_metrics["total_tokens"]
            metrics["total_cost"] += file_metrics["cost"]
            
            logger.log_processing_complete(file_output_path / "final_output", file_metrics["processing_time_seconds"])
            
        except Exception as e:
            logger.error(f"Failed to process {pdf_file.name}: {str(e)}")
            metrics["failed"] += 1
            metrics["per_file_metrics"].append({"file": pdf_file.name, "status": "failed", "error": str(e)})

    # Save consolidated output (in the last created folder or a summary folder?)
    # Saving to the output_dir root for summary
    metrics["processing_time_seconds"] = round(time.time() - start_time, 2)
    save_consolidated_output(Path(output_dir), all_results, metrics)
    
    print_summary(metrics)
    click.echo(f"\n✅ Batch Processing Complete! Output Root: {output_dir}")


def configure_dspy(logger):
    """Configure DSPy with OpenRouter LLM."""
    import dspy # Lazy import to avoid loading issues if not used
    try:
        # Set environment variables for OpenRouter/LiteLLM
        os.environ["OPENROUTER_API_KEY"] = Config.OPENROUTER_API_KEY
        os.environ["OPENAI_API_KEY"] = Config.OPENROUTER_API_KEY
        os.environ["OPENAI_API_BASE"] = Config.OPENROUTER_BASE_URL
        
        # Use dspy.LM for OpenRouter (OpenAI-compatible)
        # Note: Model name in Config should include 'openrouter/' prefix for non-OpenAI models
        lm = dspy.LM(
            model=Config.DEFAULT_MODEL,
            api_key=Config.OPENROUTER_API_KEY,
            api_base=Config.OPENROUTER_BASE_URL,
            temperature=Config.TEMPERATURE,
            max_tokens=Config.MAX_TOKENS,
            top_p=Config.TOP_P
        )
        
        dspy.configure(lm=lm)
        logger.success(f"DSPy configured with model: {Config.DEFAULT_MODEL}")
        
        # Log model parameters
        logger.log_model_params(Config.get_model_params())
    
    except Exception as e:
        logger.error(f"DSPy configuration failed: {str(e)}")
        # Fallback to older dspy.OpenAI if dspy.LM fails or for older versions
        try:
            if hasattr(dspy, 'OpenAI'):
                lm = dspy.OpenAI(
                    model=Config.DEFAULT_MODEL,
                    api_key=Config.OPENROUTER_API_KEY,
                    api_base=Config.OPENROUTER_BASE_URL,
                    temperature=Config.TEMPERATURE,
                    max_tokens=Config.MAX_TOKENS,
                    top_p=Config.TOP_P
                )
                dspy.settings.configure(lm=lm)
                logger.success(f"DSPy configured with legacy dspy.OpenAI")
                return
        except:
            pass
        raise e


def process_pdf(pdf_file: Path, output_root: Path, xlsx_files: list, logger, file_idx: int, stop_early: bool = False):
    """Process single PDF and return results + metrics."""
    file_start = time.time()
    
    # Define subdirectories
    file_extracted_dir = output_root / "extracted_text"
    file_cleaned_dir = output_root / "llm_context"
    final_root = output_root / "final_output"
    
    file_extracted_dir.mkdir(parents=True, exist_ok=True)
    file_cleaned_dir.mkdir(parents=True, exist_ok=True)
    if not stop_early:
        final_root.mkdir(parents=True, exist_ok=True)
    
    # Extract text
    stage_start = time.time()
    logger.info(f"\nProcessing: {pdf_file.name}")
    logger.info("Step 1/5: Extracting text from PDF...", console_only=True)
    pdf_extractor = PDFExtractor()
    raw_text, num_pages = pdf_extractor.extract(pdf_file)
    FileHandler.save_text(raw_text, file_extracted_dir / f"{pdf_file.stem}_raw.txt")
    logger.log_performance("PDF Text Extraction", time.time() - stage_start)
    
    # Extract tables
    stage_start = time.time()
    logger.info("Step 2/5: Extracting tables...", console_only=True)
    table_extractor = TableExtractor()
    table_csv_path = file_extracted_dir / f"{pdf_file.stem}_tables.csv"
    num_tables = table_extractor.extract_and_consolidate(pdf_file, table_csv_path)
    table_text = FileHandler.read_file(table_csv_path) if num_tables > 0 else ""
    logger.log_performance("Table Extraction", time.time() - stage_start)
    
    # Clean text
    stage_start = time.time()
    logger.info("Step 3/5: Cleaning text...", console_only=True)
    text_cleaner = TextCleaner(logger=logger)
    cleaned_text = text_cleaner.clean(raw_text)
    
    # Audit logging
    audit_summary = text_cleaner.get_audit_summary()
    if audit_summary["removed"] > 0:
        logger.info(f"Cleaner: Removed {audit_summary['removed']} paragraphs (Boilerplate/Signatures/Headers)")
        for entry in audit_summary["audit_log"]:
             logger.debug(f"Audit [{entry['category']}]: Removed '{entry['text_preview']}'")

    stats = text_cleaner.get_cleaning_stats(raw_text, cleaned_text)
    logger.log_extraction_summary(num_pages, stats["original_length"], num_tables, stats["cleaned_length"])
    FileHandler.save_text(cleaned_text, file_cleaned_dir / f"{pdf_file.stem}_cleaned.txt")
    logger.log_performance("Text Cleaning", time.time() - stage_start)
    
    # Process XLSX
    xlsx_text = ""
    if xlsx_files:
        stage_start = time.time()
        logger.info("Step 4/5: Processing XLSX files...", console_only=True)
        for xlsx_file in xlsx_files:
            xlsx_text += FileHandler.xlsx_to_text(xlsx_file)
        logger.log_performance("XLSX Processing", time.time() - stage_start)
    
    # LLM extraction
    stage_start = time.time()

    tracker = TokenTracker(model=Config.DEFAULT_MODEL)
    
    # Prepare full context for LLM
    full_context = f"{cleaned_text}\n\n=== EXTRACTED TABLES ===\n{table_text}\n\n=== EXTRACTED XLSX ===\n{xlsx_text}".strip()
    
    # Save full context to cleaned_data
    FileHandler.save_text(full_context, file_cleaned_dir / f"{pdf_file.stem}_full_context.txt")
    
    # Log full context to debug log
    logger.log_llm_context(full_context)
    
    # Check if we should stop here (Context Only / Extract Only)
    if stop_early:
        return {}, {
            "tokens": 0, "cost": 0.0, "time": time.time() - file_start,
            "status": "context_generated", "pdf_file": pdf_file.name,
            "input_tokens": 0, "output_tokens": 0, "total_tokens": 0,
            "processing_time_seconds": time.time() - file_start
        }



    # LLM extraction
    # Lazy import to avoid crash if dspy is broken and we only wanted context
    from src.dspy_modules.field_extractor import RetailerHubFieldExtractor
    
    stage_start = time.time()
    field_extractor = RetailerHubFieldExtractor(logger)
    output_json, reasoning_json, actual_token_stats = field_extractor.extract_fields(cleaned_text, table_text, xlsx_text)
    logger.log_performance("LLM Field Extraction", time.time() - stage_start)
    
    # Save final JSON output (Clean Values)
    logger.info("Step 5/5: Saving output JSON...", console_only=True)
    final_json_path = final_root / f"{pdf_file.stem}_output.json"
    FileHandler.save_json(json.dumps(output_json, indent=2, ensure_ascii=False), final_json_path)
    
    # Save Reasoning JSON (Values + reasoning + confidence)
    reasoning_json_path = final_root / f"{pdf_file.stem}_reasoning.json"
    FileHandler.save_json(json.dumps(reasoning_json, indent=2, ensure_ascii=False), reasoning_json_path)
    
    # Use actual token stats from DSPy if available, otherwise fall back to estimate
    if actual_token_stats.get("input_tokens", 0) > 0:
        input_tokens = actual_token_stats["input_tokens"]
        output_tokens = actual_token_stats["output_tokens"]
        total_tokens = input_tokens + output_tokens
        cost = tracker.calculate_cost(input_tokens, output_tokens)
    else:
        # Fallback to estimate
        usage_stats = tracker.track_usage(full_context, json.dumps(output_json))
        input_tokens = usage_stats["input_tokens"]
        output_tokens = usage_stats["output_tokens"]
        total_tokens = usage_stats["total_tokens"]
        cost = usage_stats["cost"]
    
    logger.log_token_usage(input_tokens, output_tokens, total_tokens, tracker.model, cost)
    
    file_metrics = {
        "file": pdf_file.name, "status": "success", "pages": num_pages, "tables_extracted": num_tables,
        "input_tokens": input_tokens, "output_tokens": output_tokens,
        "total_tokens": total_tokens, "cost": cost,
        "processing_time_seconds": round(time.time() - file_start, 2),
        "output_directory": str(file_extracted_dir.parent.name)  # Relative to output root
    }
    
    result = {
        "source_file": pdf_file.name, "extracted_fields": output_json,
        "metadata": {"pages": num_pages, "tables": num_tables, "processing_time": file_metrics["processing_time_seconds"]}
    }
    
    logger.success(f"Completed processing for {pdf_file.name}")
    return result, file_metrics


def save_consolidated_output(output_path: Path, results: list, metrics: dict):
    """Save consolidated output with all results and LLM metrics."""
    consolidated = {
        "summary": {
            "total_files": metrics["total_pdfs"], "successful": metrics["successful"], 
            "failed": metrics["failed"], "model": metrics["model"],
            "processing_time_seconds": metrics["processing_time_seconds"]
        },
        "llm_metrics": {
            "total_input_tokens": metrics["total_input_tokens"],
            "total_output_tokens": metrics["total_output_tokens"],
            "total_tokens": metrics["total_tokens"],
            "total_cost_usd": round(metrics["total_cost"], 4),
            "average_tokens_per_file": round(metrics["total_tokens"] / max(metrics["successful"], 1), 2),
            "average_cost_per_file": round(metrics["total_cost"] / max(metrics["successful"], 1), 4)
        },
        "per_file_metrics": metrics["per_file_metrics"],
        "results": results
    }
    
    # Save consolidated output (creates a summary folder automatically via FileHandler if needed, but we pass path)
    # Just save directly to the output root provided
    FileHandler.save_json(json.dumps(consolidated, indent=2, ensure_ascii=False), 
                         output_path / f"batch_summary_{time.strftime('%d%m%Y%H%M')}.json")
    
    # Save metrics-only file
    metrics_only = {"summary": consolidated["summary"], "llm_metrics": consolidated["llm_metrics"],
                    "per_file_metrics": consolidated["per_file_metrics"]}
    FileHandler.save_json(json.dumps(metrics_only, indent=2), output_path / f"batch_metrics_{time.strftime('%d%m%Y%H%M')}.json")


def print_summary(metrics: dict):
    """Print processing summary."""
    from colorama import Fore, Style
    print(f"\n{Fore.CYAN}{'='*60}\nPROCESSING SUMMARY\n{'='*60}{Style.RESET_ALL}")
    print(f"  Files Processed:  {metrics['successful']}/{metrics['total_pdfs']}")
    print(f"  Failed:           {metrics['failed']}")
    print(f"  Total Time:       {metrics['processing_time_seconds']:.2f}s")
    print(f"\n{Fore.YELLOW}LLM METRICS:{Style.RESET_ALL}")
    print(f"  Model:            {metrics['model']}")
    print(f"  Total Tokens:     {metrics['total_tokens']:,}")
    print(f"  Input Tokens:     {metrics['total_input_tokens']:,}")
    print(f"  Output Tokens:    {metrics['total_output_tokens']:,}")
    print(f"  {Fore.GREEN}Total Cost:       ${metrics['total_cost']:.4f}{Style.RESET_ALL}")
    if metrics['successful'] > 0:
        print(f"  Avg Cost/File:    ${metrics['total_cost'] / metrics['successful']:.4f}")


if __name__ == "__main__":
    main()
