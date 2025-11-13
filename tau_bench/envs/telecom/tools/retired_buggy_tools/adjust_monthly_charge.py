import json
from typing import Any, Dict

from tau_bench.envs.tool import Tool


class AdjustMonthlyCharge(Tool):
    @staticmethod
    def invoke(
        data: Dict[str, Any],
        customer_id: str,
        charge_key: str,
        amount: float | int | str,
    ) -> str:
        billing = data.get("billing", {})
        if customer_id not in billing:
            return f"Error: No billing information found for customer: {customer_id}"

        entry = billing[customer_id]
        monthly_charges = entry.get("monthly_charges")
        if not isinstance(monthly_charges, dict):
            return f"Error: Monthly charges missing for customer: {customer_id}"

        if charge_key not in monthly_charges:
            return f"Error: Charge '{charge_key}' not found for customer: {customer_id}"

        try:
            amount_value = float(amount)
        except (TypeError, ValueError):
            return "Error: amount must be a number"

        monthly_charges[charge_key] = round(amount_value, 2)
        entry["total_monthly"] = round(sum(monthly_charges.values()), 2)

        return json.dumps(
            {
                "customer_id": customer_id,
                "charge_key": charge_key,
                "amount": f"{monthly_charges[charge_key]:.2f}",
                "total_monthly": f"{entry['total_monthly']:.2f}",
            }
        )

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "adjust_monthly_charge",
                "description": "Update a specific monthly charge for a customer and recalculate their billing total.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "customer_id": {
                            "type": "string",
                            "description": "Unique customer identifier, e.g. 'john_smith_1234'.",
                        },
                        "charge_key": {
                            "type": "string",
                            "description": "Billing line item to adjust, e.g. 'tv_premium'.",
                        },
                        "amount": {
                            "type": "number",
                            "description": "New monthly amount for the specified charge.",
                        },
                    },
                    "required": ["customer_id", "charge_key", "amount"],
                },
            },
        }
