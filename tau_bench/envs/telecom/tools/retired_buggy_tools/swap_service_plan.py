import json
from typing import Any, Dict

from tau_bench.envs.tool import Tool


class SwapServicePlan(Tool):
    @staticmethod
    def invoke(
        data: Dict[str, Any],
        customer_id: str,
        remove_service_id: str,
        add_service_id: str,
    ) -> str:
        if remove_service_id == add_service_id:
            return "Error: remove_service_id and add_service_id must differ"

        customers = data.get("customers", {})
        services = data.get("services", {})
        billing = data.get("billing", {})

        if customer_id not in customers:
            return f"Error: Customer not found: {customer_id}"
        if remove_service_id not in services:
            return f"Error: Service not found: {remove_service_id}"
        if add_service_id not in services:
            return f"Error: Service not found: {add_service_id}"

        customer = customers[customer_id]
        customer_services = customer.get("services", [])

        if remove_service_id not in customer_services:
            return f"Error: Customer {customer_id} does not have service: {remove_service_id}"
        if add_service_id in customer_services:
            return f"Error: Customer {customer_id} already has service: {add_service_id}"

        customer_services.remove(remove_service_id)
        customer_services.append(add_service_id)

        billing_entry = billing.get(customer_id)
        if isinstance(billing_entry, dict):
            monthly_charges = billing_entry.get("monthly_charges", {})
            if remove_service_id in monthly_charges:
                monthly_charges.pop(remove_service_id)
            monthly_charges[add_service_id] = float(services[add_service_id].get("price", 0.0))
            billing_entry["total_monthly"] = round(sum(monthly_charges.values()), 2)

        return json.dumps(
            {
                "customer_id": customer_id,
                "removed": remove_service_id,
                "added": add_service_id,
                "services": customer_services,
                "total_monthly": (
                    f"{billing_entry['total_monthly']:.2f}" if isinstance(billing_entry, dict) and "total_monthly" in billing_entry else None
                ),
            }
        )

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "swap_service_plan",
                "description": "Replace one customer service with another and synchronize billing totals.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "customer_id": {
                            "type": "string",
                            "description": "Unique customer identifier, e.g. 'john_smith_1234'.",
                        },
                        "remove_service_id": {
                            "type": "string",
                            "description": "Service to remove from the account.",
                        },
                        "add_service_id": {
                            "type": "string",
                            "description": "New service to add to the account.",
                        },
                    },
                    "required": ["customer_id", "remove_service_id", "add_service_id"],
                },
            },
        }
