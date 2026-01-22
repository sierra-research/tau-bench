"""Provider setup utilities for tau-bench.

This module handles configuration for different LLM providers:
- OpenRouter: Uses openrouter/ prefix for model routing
- DashScope (Alibaba): Uses dashscope/ prefix for Qwen models
- Local models: Uses OpenAI-compatible endpoints with api_base

Environment variables required:
- OPENROUTER_API_KEY: For OpenRouter models
- DASHSCOPE_API_KEY: For DashScope/Alibaba models
- OPENAI_API_KEY: For OpenAI models (and user simulator)
"""
import os
from typing import Optional, Tuple

try:
    from dotenv import load_dotenv
    HAS_DOTENV = True
except ImportError:
    HAS_DOTENV = False


def load_env_file(env_path: Optional[str] = None) -> None:
    """
    Load environment variables from a .env file.
    
    Args:
        env_path: Path to .env file. If None, loads from current directory.
    """
    if not HAS_DOTENV:
        if env_path:
            print("Warning: python-dotenv not installed. Cannot load .env file.")
            print("Install with: pip install python-dotenv")
        return
    
    if env_path:
        if os.path.exists(env_path):
            load_dotenv(env_path)
            print(f"Loaded environment from: {env_path}")
        else:
            print(f"Warning: .env file not found at {env_path}")
    else:
        load_dotenv()


def setup_provider(
    model: str,
    provider: str,
    base_url: Optional[str] = None
) -> Tuple[str, str, Optional[str]]:
    """
    Set up model name and provider for litellm.
    
    Handles provider-specific model name formatting:
    - OpenRouter: Prepends 'openrouter/' if not present
    - DashScope: Prepends 'dashscope/' if not present  
    - Local: Uses 'openai' provider with custom api_base
    
    Args:
        model: Model name (e.g., 'qwen/qwen3-8b', 'qwen3-8b', 'gpt-4o')
        provider: Provider name ('openrouter', 'dashscope', 'local', 'openai', etc.)
        base_url: Base URL for local/custom endpoints
        
    Returns:
        Tuple of (formatted_model, provider, api_base)
    """
    # For OpenRouter: prepend prefix if not already present
    if provider == "openrouter":
        if not model.startswith("openrouter/"):
            model = f"openrouter/{model}"
        return model, provider, None
    
    # For DashScope (Alibaba Qwen): prepend prefix if not already present  
    if provider == "dashscope":
        if not model.startswith("dashscope/"):
            model = f"dashscope/{model}"
        return model, provider, None
    
    # For local models: use OpenAI-compatible endpoint
    if provider == "local":
        if not base_url:
            raise ValueError(
                "Local provider requires --model-base-url or --user-model-base-url. "
                "Example: --model-base-url http://localhost:8000/v1"
            )
        # Use openai provider with custom base URL
        if not model.startswith("openai/"):
            model = f"openai/{model}"
        return model, "openai", base_url
    
    # Standard providers (openai, anthropic, google, mistral, etc.)
    # No modification needed
    return model, provider, base_url
