"""
Configuration Management Module
Handles environment variables, API keys, model settings, and paths.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config:
    """Centralized configuration for the PDF extraction system."""
    
    # API Configuration
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
    OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
    
    # Model Settings
    DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "openrouter/qwen/qwen3-32b")
    TEMPERATURE = float(os.getenv("TEMPERATURE", "0.1"))
    MAX_TOKENS = int(os.getenv("MAX_TOKENS", "4000"))
    TOP_P = float(os.getenv("TOP_P", "1.0"))
    FREQUENCY_PENALTY = float(os.getenv("FREQUENCY_PENALTY", "0.0"))
    PRESENCE_PENALTY = float(os.getenv("PRESENCE_PENALTY", "0.0"))
    
    # Tesseract OCR
    TESSERACT_CMD = os.getenv("TESSERACT_CMD", "tesseract")
    
    # Directory Paths
    PROJECT_ROOT = Path(__file__).parent.parent
    OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR", "./outputs"))
    
    # Logging Configuration
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    ENABLE_CONSOLE_LOGGING = os.getenv("ENABLE_CONSOLE_LOGGING", "true").lower() == "true"
    
    # Text Cleaning Patterns
    # Note: Regexes are managed internally by src.cleaners.text_cleaners.ContentCleaner
    
    # Field Defaults
    DEFAULT_SCHEME_PERIOD = "Duration"
    DEFAULT_FSN_FILE = "No"
    DEFAULT_MIN_DISCOUNT_CLAIM = "FALSE"
    DEFAULT_REMOVE_GST = "Not Specified"
    DEFAULT_OVER_ABOVE = "FALSE"
    DEFAULT_SCHEME_TYPE = "SELL_SIDE"
    DEFAULT_SCHEME_SUBTYPE = "PUC"
    
    # Note: Scheme classification (scheme_type, scheme_subtype) is now done by the LLM
    # with Chain-of-Thought reasoning in the DSPy signatures, not keyword matching.
    
    @classmethod
    def validate(cls):
        """Validate critical configuration values."""
        errors = []
        
        if not cls.OPENROUTER_API_KEY:
            errors.append("OPENROUTER_API_KEY not set in environment")
        
        if not 0 <= cls.TEMPERATURE <= 1:
            errors.append(f"TEMPERATURE must be between 0 and 1, got {cls.TEMPERATURE}")
        
        if cls.MAX_TOKENS < 100:
            errors.append(f"MAX_TOKENS too low: {cls.MAX_TOKENS}")
        
        if errors:
            raise ValueError("Configuration errors:\n" + "\n".join(f"  - {e}" for e in errors))
    
    @classmethod
    def get_model_params(cls):
        """Get model parameters as a dictionary."""
        return {
            "model": cls.DEFAULT_MODEL,
            "temperature": cls.TEMPERATURE,
            "max_tokens": cls.MAX_TOKENS,
            "top_p": cls.TOP_P,
            "frequency_penalty": cls.FREQUENCY_PENALTY,
            "presence_penalty": cls.PRESENCE_PENALTY,
        }
