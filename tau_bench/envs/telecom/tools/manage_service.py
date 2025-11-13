# Verified


import json
from typing import Any, Dict, List, Optional

from tau_bench.envs.tool import Tool


class ManageService(Tool):
    @staticmethod
    def invoke(data: Dict[str, Any], 
                customer_id: str, 
                action: str, 
                service_id: Optional[str] = None,
                devices_ids: Optional[List[str]] = None) -> str:

        customers = data.get("customers", {})
        services = data.get("services", {})
        billing = data.get("billing", {})
        
        # check to make sure the customer exists
        if customer_id not in customers:
            return f"Error: Customer not found: {customer_id}"
        
        customer = customers[customer_id]
        customer_services = customer.get("services", [])

        devices = customer.get("devices", [])
        
        if action == "list":
            result = []
            for svc_id in customer_services:
                if svc_id in services:
                    svc = services[svc_id]
                    result.append(svc)
            return json.dumps({"customer_id": customer_id, "services": result})

        # check to make sure the service exists
        if not service_id:
            return f"Error: Service ID is required for action: {action}"

        if action == "add":
            if service_id not in services:
                return f"Error: Service not found: {service_id}"
            
            if service_id in customer_services:
                return f"Error: Customer {customer_id} already has service: {service_id}"
            
            if devices_ids:
                for device_id in devices_ids:
                    if device_id not in [d['device_id'] for d in devices]:
                        return f"Error: Device not found: {device_id} in devices {devices}"
                    
                    for device in devices:
                        if device['device_id'] == device_id:
                            device['service'] = service_id
                            break
            
            customer_services.append(service_id)
            service_name = services.get(service_id, {}).get("name", service_id)

            billing_entry = billing.get(customer_id)
            if isinstance(billing_entry, dict):
                billing_entry["monthly_charges"][service_id] = services.get(service_id, {}).get("price", 0.0)

            return f"Success: Added service '{service_name}' to customer {customer_id}"
        
        elif action == "remove":
            if service_id not in customer_services:
                return f"Error: Customer {customer_id} does not have service: {service_id}"

            #loop through the devices and remove any devices that were associated with the service
            removed_devices = []
            for device in devices:
                if device.get("service") == service_id:
                    device["service"] = None
                    removed_devices.append(device.get("name"))

            customer_services.remove(service_id)
            
            service_name = services.get(service_id, {}).get("name", service_id)

            billing_entry = billing.get(customer_id)
            if isinstance(billing_entry, dict):
                billing_entry["monthly_charges"].pop(service_id)

            return f"Success: Removed service '{service_name}' from customer {customer_id}. Devices {removed_devices} are now no longer associated with the service."

        else:
            return f"Error: Invalid action: {action}. Valid actions are: add, remove, list"

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "manage_service",
                "description": "Manage customer services: add, remove, suspend, activate, or list services.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "customer_id": {
                            "type": "string",
                            "description": "The customer's unique identifier, such as 'john_smith_1234'.",
                        },
                        "action": {
                            "type": "string",
                            "description": "Action to perform: 'add', 'remove', or 'list'.",
                        },
                        "service_id": {
                            "type": "string",
                            "description": "Service identifier (required for add/remove/suspend/activate), such as 'mobile_unlimited'.",
                        },
                        "devices_ids": {
                            "type": "array",
                            "items": {
                                "type": "string"
                            },
                            "description": "The device ids. Should be a list of strings corresponding to the device ids in the customer's list of devices.",
                        },
                    },
                    "required": ["customer_id", "action"],
                },
            },
        }
