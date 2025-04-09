from openai import OpenAI
import os
import logfire
from abc import ABC, abstractmethod
from functools import wraps
from typing import List, Dict, Any, Tuple, Callable

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Base class for AtlaOrbit agents
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class AtlaOrbitBase(ABC):
    def __init__(self, mode: str):
        self.mode = mode
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

    @abstractmethod
    def evaluate_response(self, func: Callable, *args, **kwargs) -> Tuple:
        pass

    @abstractmethod
    def improve_response(self, func: Callable, *args, **kwargs) -> Tuple:
        pass

    def __call__(self, func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            with logfire.span(f"AtlaOrbit: {self.mode}"):
                if self.mode == "evaluate":
                    return self.evaluate_response(func, *args, **kwargs)
                elif self.mode == "improve":
                    return self.improve_response(func, *args, **kwargs)
                else:
                    return func(*args, **kwargs)
        return wrapper
