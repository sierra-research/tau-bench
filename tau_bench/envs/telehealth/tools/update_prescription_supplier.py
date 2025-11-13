import json
from typing import Any, Dict

from tau_bench.envs.tool import Tool


class UpdatePrescriptionSupplier(Tool):
    @staticmethod
    def invoke(
        data: Dict[str, Any],
        record_id: str,
        medication: str,
        supplier_company: str,
        brand_name: str,
        price_usd: float,
        currency: str = "USD",
    ) -> str:
        records = data["medical_records"]
        if record_id not in records:
            return "Error: medical record not found"

        record = records[record_id]
        prescriptions = record.get("prescriptions", [])
        if not prescriptions:
            return "Error: medical record has no prescriptions"

        # build a case-insensitive lookup map of medications in the record
        normalized_map = {
            prescription.get("medication", "").strip().lower(): prescription
            for prescription in prescriptions
        }

        # normalize the requested medication (strip dosage text and lowercase)
        normalized_name = medication.strip().lower()
        # attempt direct match
        prescription = normalized_map.get(normalized_name)

        if prescription is None:
            # fall back to partial match (handles appended dosage info like "lamotrigine 100mg BID")
            for key, value in normalized_map.items():
                if normalized_name.startswith(key) or key.startswith(normalized_name):
                    prescription = value
                    break

        if prescription is None:
            return f"Error: medication {medication} not found in record {record_id}"

        prescription["pharmacy"] = f"{supplier_company} ({brand_name})"
        prescription["supplier"] = {
            "company": supplier_company,
            "brand_name": brand_name,
            "price_usd": float(price_usd),
            "currency": currency,
        }
        return json.dumps(record)

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "update_prescription_supplier",
                "description": "Update the supplier information for a prescription in a medical record.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "record_id": {
                            "type": "string",
                            "description": "The medical record identifier, such as 'REC001'.",
                        },
                        "medication": {
                            "type": "string",
                            "description": "Name of the medication to update.",
                        },
                        "supplier_company": {
                            "type": "string",
                            "description": "Name of the supplier company providing the medication.",
                        },
                        "brand_name": {
                            "type": "string",
                            "description": "Brand name used by the supplier for this medication.",
                        },
                        "price_usd": {
                            "type": "number",
                            "description": "Price in USD from the supplier catalog.",
                        },
                        "currency": {
                            "type": "string",
                            "description": "Currency code for the quoted price (defaults to 'USD').",
                        },
                    },
                    "required": [
                        "record_id",
                        "medication",
                        "supplier_company",
                        "brand_name",
                        "price_usd",
                    ],
                },
            },
        }
