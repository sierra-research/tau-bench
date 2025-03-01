"""
Utility functions for Tau-bench, for example for retrying LLM provider calls.
"""

# Import required libraries
import time
import httpx
import random
import litellm
import functools
from litellm import completion
from typing import List, Dict, Any, Tuple, Type

# Decorator function that implements exponential backoff retry logic
def retry_with_exponential_backoff(
    max_retries: int = 10,  # Maximum number of retry attempts
    base_delay: int = 60,  # Initial delay in seconds before the first retry
    retry_exceptions: Tuple[Type[Exception], ...] = (  # Tuple of exception types that should trigger retries
        litellm.exceptions.RateLimitError,  # Retry on rate limiting
        httpx.HTTPStatusError,  # Retry on HTTP errors
        litellm.llms.bedrock.common_utils.BedrockError,  # Retry on AWS Bedrock specific errors
        litellm.ServiceUnavailableError,  # Retry when service is unavailable
        litellm.exceptions.APIConnectionError,  # Retry on connection issues
        litellm.exceptions.BadRequestError # Retry on incorrectly formatted requests (because they could themselves be LLM generated)
    )
):
    """
    Creates a decorator that retries a function with exponential backoff when specific exceptions occur.
    
    Args:
        max_retries: Maximum number of retry attempts before giving up
        base_delay: Initial delay in seconds before the first retry
        retry_exceptions: Tuple of exception types that should trigger a retry
    
    Returns:
        Decorator function that can be applied to other functions
    """
    def decorator(func):
        """
        The actual decorator that wraps the target function.
        
        Args:
            func: The function to be wrapped with retry logic
            
        Returns:
            Wrapped function with retry capability
        """
        @functools.wraps(func)  # Preserves the metadata of the original function
        def wrapper(*args, **kwargs):
            """
            Wrapper that adds retry logic to the decorated function.
            
            Args:
                *args, **kwargs: Arguments passed to the original function
                
            Returns:
                Result of the successful function call
                
            Raises:
                The last exception encountered if all retries fail
            """
            for attempt in range(max_retries):
                try:
                    # Attempt to call the original function
                    return func(*args, **kwargs)
                except retry_exceptions as e:
                    # If this is the last attempt, log and re-raise the exception
                    if attempt == max_retries - 1:
                        print(f"Rate limit exceeded after {max_retries} attempts: {str(e)}")
                        raise
                    
                    # Calculate delay with exponential backoff and random jitter
                    # Formula: base_delay * (2^attempt) + random_jitter
                    delay = base_delay * (2 ** attempt) + random.uniform(0, 0.5)
                    
                    # Log the exception and retry information
                    print(
                        f"exception={e}, rate limit hit on attempt {attempt+1}/{max_retries}. "
                        f"Retrying in {delay:.2f} seconds..."
                    )
                    
                    # Wait before next retry
                    time.sleep(delay)
                except Exception as e:
                    # For any unhandled exceptions, log and re-raise without retry
                    print(f"exception={e}, unhandled exception")
                    raise
            
            # This return statement should never be reached due to the raise in the final attempt
            # It's included for code completeness
            return None
        
        return wrapper
    
    return decorator

# Apply the retry decorator to a function that makes LLM API calls
@retry_with_exponential_backoff(max_retries=10, base_delay=60)
def completion_w_retry(
    model: str,  # The LLM model to use (e.g., "gpt-4", "claude-3")
    custom_llm_provider: str,  # The provider of the LLM (e.g., "openai", "bedrock")
    messages: List[Dict[str, Any]], # The conversation messages in the format expected by the API
    **kwargs
):
    """
    Wrapper function for litellm.completion that adds retry capability.
    
    Args:
        model: The name of the LLM model to use
        custom_llm_provider: The provider of the LLM service
        messages: List of message dictionaries in the format expected by the API
        
    Returns:
        The completion response from the LLM provider
    """
    return completion(
        model=model,
        custom_llm_provider=custom_llm_provider,
        messages=messages,
        **kwargs
    )
