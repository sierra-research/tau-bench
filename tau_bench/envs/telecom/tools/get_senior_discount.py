from typing import Any, Dict

from tau_bench.envs.tool import Tool


class GetSeniorDiscount(Tool):
    @staticmethod
    def invoke(data: Dict[str, Any], original_price: str) -> str:
        try:
            price = float(original_price)
        except (TypeError, ValueError):
            return "Error: original_price must be a number"

        discounted_price = max(price - 5.0, 0.0)
        return f"{discounted_price:.2f}"

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "get_senior_discount",
                "description": "Apply a fixed $5 senior discount to the provided service price.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "original_price": {
                            "type": "string",
                            "description": "Original price before applying the senior discount, e.g. '95.00'.",
                        },
                    },
                    "required": ["original_price"],
                },
            },
        }
