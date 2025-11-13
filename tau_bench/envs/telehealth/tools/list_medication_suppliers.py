from __future__ import annotations

from typing import Any, Dict, List

from tau_bench.envs.tool import Tool


class ListMedicationSuppliers(Tool):
    @staticmethod
    def invoke(
        data: Dict[str, Any],
        medication: str,
        country_filter: str | None = None,
        limit: int | None = None,
    ) -> str:
        suppliers_map: Dict[str, List[Dict[str, Any]]] = data.get("medication_suppliers", {})

        # allow case-insensitive lookups
        canonical_map: Dict[str, str] = {
            key.lower(): key for key in suppliers_map.keys()
        }
        medication_key = canonical_map.get(medication.lower())
        suppliers = suppliers_map.get(medication_key) if medication_key else None

        if not suppliers and medication_key is None:
            # provide clearer guidance if casing caused the miss
            return (
                "No supplier information found for "
                f"{medication}. (Tip: ensure the medication name matches the catalog)"
            )
        if not suppliers:
            return f"No supplier information found for {medication}."

        filtered: List[Dict[str, Any]] = suppliers
        if country_filter:
            filtered = [item for item in filtered if item.get("country", "").lower() == country_filter.lower()]
            if not filtered:
                return f"No suppliers in {country_filter} for {medication}."

        filtered = sorted(filtered, key=lambda item: item.get("price_usd", float("inf")))
        if limit is not None and limit > 0:
            filtered = filtered[:limit]

        lines: List[str] = []
        for entry in filtered:
            company = entry.get("company")
            brand = entry.get("brand_name")
            country = entry.get("country")
            price = entry.get("price_usd")
            lines.append(f"{company} ({country}) | brand={brand} | price_usd={price:.2f}")
        return f"Suppliers for {medication}:\n" + "\n".join(lines)

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "list_medication_suppliers",
                "description": "List suppliers for a given medication, optionally filtered by country and sorted by price.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "medication": {
                            "type": "string",
                            "description": "Medication name to search for",
                        },
                        "country_filter": {
                            "type": "string",
                            "description": "Optional country name to filter suppliers",
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Optional maximum number of suppliers to list",
                        },
                    },
                    "required": ["medication"],
                },
            },
        }
