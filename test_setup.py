"""
Quick Test Script
Validates the setup and creates a simple test case.
"""
from pathlib import Path
from src.config import Config
from src.logger import create_logger

def test_config():
    """Test configuration loading."""
    print("Testing Configuration...")
    print(f"  ✓ API Key: {'***' + Config.OPENROUTER_API_KEY[-8:] if Config.OPENROUTER_API_KEY else 'NOT SET'}")
    print(f"  ✓ Model: {Config.DEFAULT_MODEL}")
    print(f"  ✓ Temperature: {Config.TEMPERATURE}")
    print(f"  ✓ Max Tokens: {Config.MAX_TOKENS}")
    return True

def test_logger():
    """Test logging functionality."""
    print("\nTesting Logger...")
    test_dir = Path("./test_output")
    test_dir.mkdir(exist_ok=True)
    
    logger = create_logger(test_dir, console_enabled=True)
    logger.section("Test Section")
    logger.success("Logger working correctly")
    logger.log_field_extraction(
        field_name="test_field",
        input_snippet="Sample input text",
        reasoning="This is a test",
        output_value="Test Value",
        confidence="High"
    )
    print("  ✓ Logger test passed")
    return True

def test_imports():
    """Test all critical imports."""
    print("\nTesting Imports...")
    try:
        import dspy
        print("  ✓ DSPy installed")
    except:
        print("  ✗ DSPy not installed")
        return False
    
    try:
        import fitz
        print("  ✓ PyMuPDF installed")
    except:
        print("  ✗ PyMuPDF not installed")
        return False
    
    try:
        import pdfplumber
        print("  ✓ pdfplumber installed")
    except:
        print("  ✗ pdfplumber not installed")
        return False
    
    try:
        import pytesseract
        print("  ✓ pytesseract installed")
    except:
        print("  ✗ pytesseract not installed")
        return False
    
    return True

if __name__ == "__main__":
    print("="*60)
    print("PDF EXTRACTOR 2.0 - SETUP VALIDATION")
    print("="*60)
    
    all_passed = True
    
    try:
        all_passed = test_config() and all_passed
    except Exception as e:
        print(f"  ✗ Config test failed: {e}")
        all_passed = False
    
    try:
        all_passed = test_imports() and all_passed
    except Exception as e:
        print(f"  ✗ Import test failed: {e}")
        all_passed = False
    
    try:
        all_passed = test_logger() and all_passed
    except Exception as e:
        print(f"  ✗ Logger test failed: {e}")
        all_passed = False
    
    print("\n" + "="*60)
    if all_passed:
        print("✅ ALL TESTS PASSED - System ready!")
    else:
        print("❌ SOME TESTS FAILED - Check errors above")
    print("="*60)
