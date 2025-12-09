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
    # Text Cleaning Patterns
    # Note: Regexes are designed to be non-greedy to verify they don't eat email body
    DISCLAIMER_PATTERNS = [
        r"CAUTION:.*?(?:\n\n|$)",
        r"(?:Disclaimer|CONFIDENTIALITY NOTICE|IMPORTANT):.*?(?:\n\n|$)",
        r"This (?:email|message) is intended only for.*?(?:\n\n|$)",
    ]
    
    FORWARDED_PATTERNS = [
        # Match standard forwarded header block (up to 10 lines of metadata)
        r"-{5,}\s*Forwarded [Mm]essage\s*-{5,}\n(?:.*?\n){0,10}?(?=\n)",
        r"Begin forwarded message:\n(?:.*?\n){0,10}?(?=\n)",
        r"From:.*?\nSent:.*?\nTo:.*?\nSubject:.*?\n",
    ]
    
    LINK_PATTERN = r"https?://[^\s]+"
    
    EMAIL_FOOTER_PATTERN = r"(?:Best [Rr]egards|Thanks|Sincerely|Regards),?\s*\n.*?(?:\n.*?){0,5}$"
    
    # Field Defaults
    DEFAULT_SCHEME_PERIOD = "Duration"
    DEFAULT_FSN_FILE = "No"
    DEFAULT_MIN_DISCOUNT_CLAIM = "FALSE"
    DEFAULT_REMOVE_GST = "Not Specified"
    DEFAULT_OVER_ABOVE = "FALSE"
    DEFAULT_SCHEME_TYPE = "SELL_SIDE"
    DEFAULT_SCHEME_SUBTYPE = "PUC/FDC"
    
    # Scheme Classification Keywords
    SCHEME_KEYWORDS = {
        "BUY_SIDE": {
            "PERIODIC_CLAIM": [
                "jbp", "joint business plan", "tot", "terms of trade",
                "sell in", "sell-in", "sellin", "buy side", "buyside",
                "periodic", "quarter", "q1", "q2", "q3", "q4",
                "annual", "fy", "yearly support", "marketing support",
                "gmv support", "nrv", "nrv-linked", "inwards",
                "net inwards", "inventory support", "business plan",
                "commercial alignment", "funding for fy"
            ],
            "PDC": [
                "price drop", "price protection", "pp", "pdc",
                "cost reduction", "nlc change", "cost change",
                "sellin price drop", "invoice cost correction",
                "backward margin", "revision in buy price"
            ]
        },
        "ONE_OFF": [
            "one off", "one-off", "one off buyside",
            "one off sell side", "ad-hoc approval", "special approval"
        ],
        "SELL_SIDE": {
            "PUC/FDC": [
                "sellout", "sell out", "sell-side", "puc", "cp", "fdc",
                "pricing support", "channel support", "market support",
                "discount on selling price", "rest all support"
            ],
            "COUPON": [
                "coupon", "vpc", "promo code", "offer code",
                "discount coupon", "voucher"
            ],
            "SUPER COIN": [
                "super coin", "sc funding", "loyalty coins"
            ],
            "PREXO": [
                "exchange", "prexo", "upgrade", "bump up", "bup",
                "exchange offer"
            ],
            "BANK OFFER": [
                "bank offer", "card offer", "hdfc offer", "axis offer",
                "icici offer", "cashback", "emi offer"
            ]
        }
    }
    
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
