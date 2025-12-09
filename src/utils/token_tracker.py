"""
Token Tracking and Cost Calculation
Handles token counting and usage cost estimation for various models.
"""
import tiktoken
from typing import Dict, Tuple


class TokenTracker:
    """Tracks token usage and calculates costs for LLM calls."""
    
    # Pricing per 1M tokens (as of Dec 2024)
    # Format: {model_name: (input_price_per_1M, output_price_per_1M)}
    PRICING = {
        "openai/gpt-4o": (2.50, 10.00),
        "openai/gpt-4o-mini": (0.15, 0.60),
        "openai/gpt-4-turbo": (10.00, 30.00),
        "anthropic/claude-3.5-sonnet": (3.00, 15.00),
        "anthropic/claude-3-opus": (15.00, 75.00),
        "anthropic/claude-3-haiku": (0.25, 1.25),
        "google/gemini-pro-1.5": (1.25, 5.00),
        "mistralai/mistral-large": (2.00, 6.00),
        "qwen/qwen-2.5-72b-instruct": (0.35, 0.70),
    }
    
    def __init__(self, model: str = "openai/gpt-4o"):
        """
        Initialize token tracker.
        
        Args:
            model: Model identifier for pricing lookup
        """
        self.model = model
        self.encoding = self._get_encoding(model)
    
    @staticmethod
    def _get_encoding(model: str):
        """Get appropriate tiktoken encoding for model."""
        try:
            # Most OpenRouter models use cl100k_base encoding
            return tiktoken.get_encoding("cl100k_base")
        except:
            # Fallback to gpt-3.5-turbo encoding
            return tiktoken.encoding_for_model("gpt-3.5-turbo")
    
    def count_tokens(self, text: str) -> int:
        """
        Count tokens in text.
        
        Args:
            text: Input text
        
        Returns:
            Token count
        """
        return len(self.encoding.encode(text))
    
    def calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """
        Calculate cost for token usage.
        
        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
        
        Returns:
            Total cost in USD
        """
        # Normalize model name (remove provider prefix if present for lookup)
        lookup_model = self.model.replace("openrouter/", "").replace("openai/", "")
        
        # Try direct lookup, then normalized, then default
        if self.model in self.PRICING:
            pricing = self.PRICING[self.model]
        elif lookup_model in self.PRICING:
            pricing = self.PRICING[lookup_model]
        else:
            # Fallback to similar model or default
            # Check for partial matches (e.g. qwen/qwen-2.5...)
            match = next((k for k in self.PRICING if k in self.model), "openai/gpt-4o")
            pricing = self.PRICING[match]
            
        input_price, output_price = pricing
        
        # Calculate cost
        input_cost = (input_tokens / 1_000_000) * input_price
        output_cost = (output_tokens / 1_000_000) * output_price
        
        return input_cost + output_cost
    
    def track_usage(self, prompt: str, response: str) -> Dict[str, any]:
        """
        Track usage for a complete LLM interaction.
        
        Args:
            prompt: Input prompt text
            response: Model response text
        
        Returns:
            Dictionary with usage statistics
        """
        input_tokens = self.count_tokens(prompt)
        output_tokens = self.count_tokens(response)
        total_tokens = input_tokens + output_tokens
        cost = self.calculate_cost(input_tokens, output_tokens)
        
        return {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": total_tokens,
            "cost": cost,
            "model": self.model
        }
