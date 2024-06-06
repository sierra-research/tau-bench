# Copyright Sierra

import json
from typing import Any, Dict


def get_product_details(data: Dict[str, Any], product_id: str) -> str:
    products = data["products"]
    if product_id in products:
        return json.dumps(products[product_id])
    return "Error: product not found"


get_product_details.__info__ = {
    "type": "function",
    "function": {
        "name": "get_product_details",
        "description": "Get the inventory details of a product.",
        "parameters": {
            "type": "object",
            "properties": {
                "product_id": {
                    "type": "string",
                    "description": "The product id, such as '6086499569'. Be careful the product id is different from the item id.",
                },
            },
            "required": ["product_id"],
        },
    },
}
