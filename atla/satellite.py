from openai import OpenAI
import os
import logfire
from abc import ABC, abstractmethod
from typing import Any, Dict, Tuple, TypeVar, Generic, Callable, Union, Optional
from functools import wraps

T = TypeVar('T')

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Base class for AtlaSatellite agents
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class AtlaSatelliteBase(ABC, Generic[T]):
    def __init__(self) -> None:
        self.client = OpenAI(
            base_url="http://localhost:8000/v1", 
            api_key=os.environ["ATLA_DEV_API_KEY"]
        )
        logfire.instrument_openai(self.client)

    def call_selene_mini(self, prompt: str) -> str:
        with logfire.span("Evaluating with Selene Mini", _tags=['judge']):
            response = self.client.chat.completions.create(
                model="atla-selene-mini-20250127",
                messages=[{"role": "user", "content": prompt}],
            )
            return response.choices[0].message.content

    def orbit(self, func: Optional[Callable[..., T]] = None) -> Union[Callable[..., Tuple[T, Dict[str, Any]]], Callable[[Callable[..., T]], Callable[..., Tuple[T, Dict[str, Any]]]]]:
        if func is None:
            # Used as a decorator
            def decorator(f: Callable[..., T]):
                @wraps(f)
                def wrapper(*args: Any, **kwargs: Any) -> Tuple[T, Dict[str, Any]]:
                    return self.orbit_function(f, *args, **kwargs)
                return wrapper
            return decorator
        else:
            # Used as a wrapper
            @wraps(func)
            def wrapper(*args: Any, **kwargs: Any) -> Tuple[T, Dict[str, Any]]:
                return self.orbit_function(func, *args, **kwargs)
            return wrapper

    @abstractmethod
    def orbit_function(self, func: Callable[..., T], *args: Any, **kwargs: Any) -> Tuple[T, Dict[str, Any]]:
        """
        This method should be implemented by subclasses to define an "orbit" function that 
        wraps around a completion function, adding evaluation, improvement, and other functionalities.
        
        Args:
            func (Callable): The completion function to be executed with a return type of T.
            *args: Variable length argument list for the completion function.
            **kwargs: Arbitrary keyword arguments for the completion function.
            
        Returns:
            Tuple[T, Dict[str, Any]]: The result of the completion function and a dictionary with metadata.
            The type of the result is determined by the completion function.
            The metadata dictionary contains evaluation results, messages, and other relevant information.
            
        Raises:
            NotImplementedError: If the method is not implemented by a subclass.
        """
        pass
    

# Example subclass:
# class MySatellite(AtlaSatelliteBase):
#     def orbit_function(self, func, *args, **kwargs):
#         result = func(*args, **kwargs)
#         return result, {"metadata": "example"}

# Example usage:
# sat = MySatellite()
# 
# # As wrapper
# def foo(x): return x * 2
# wrapped_foo = sat.orbit(foo)
# result, metadata = wrapped_foo(5)
# 
# # As decorator
# @sat.orbit()
# def bar(x): return x * 3
# result, metadata = bar(5)