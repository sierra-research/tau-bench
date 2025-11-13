import json
from typing import Any, Dict

from tau_bench.envs.tool import Tool


class RecordPayment(Tool):
    @staticmethod
    def invoke(
        data: Dict[str, Any],
        customer_id: str,
        amount: float | int | str,
        method: str,
        date: str,
    ) -> str:
        billing = data.get("billing", {})
        if customer_id not in billing:
            return f"Error: No billing information found for customer: {customer_id}"

        try:
            amount_value = round(float(amount), 2)
        except (TypeError, ValueError):
            return "Error: amount must be a number"

        entry = billing[customer_id]
        current_balance = float(entry.get("current_balance", 0.0))
        new_balance = max(round(current_balance - amount_value, 2), 0.0)
        entry["current_balance"] = new_balance

        payment_record = {
            "date": date,
            "amount": amount_value,
            "status": "completed",
        }
        history = entry.setdefault("payment_history", [])
        history.append(payment_record)

        entry["last_payment"] = {
            "amount": amount_value,
            "date": date,
            "method": method,
            "status": "completed",
        }

        return json.dumps(
            {
                "customer_id": customer_id,
                "amount": f"{amount_value:.2f}",
                "method": method,
                "date": date,
                "current_balance": f"{new_balance:.2f}",
            }
        )

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "record_payment",
                "description": "Apply a payment to a customer account and update the remaining balance.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "customer_id": {
                            "type": "string",
                            "description": "Unique customer identifier, e.g. 'lisa_chen_3456'.",
                        },
                        "amount": {
                            "type": "number",
                            "description": "Payment amount to apply.",
                        },
                        "method": {
                            "type": "string",
                            "description": "Payment method used. Options: credit_card, bank_transfer  .",
                        },
                        "date": {
                            "type": "string",
                            "description": "Payment date in ISO format, e.g. '2025-09-18'.",
                        },
                    },
                    "required": ["customer_id", "amount", "method", "date"],
                },
            },
        }
