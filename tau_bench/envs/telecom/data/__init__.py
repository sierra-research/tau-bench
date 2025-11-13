
import json
import os
from typing import Dict, Any

def load_data() -> Dict[str, Any]:
    """Load all telecom data from JSON files."""
    data_dir = os.path.dirname(__file__)
    
    data = {}
    
    # Load customers data
    with open(os.path.join(data_dir, "customers.json"), "r") as f:
        data["customers"] = json.load(f)
    
    # Load services data
    with open(os.path.join(data_dir, "services.json"), "r") as f:
        data["services"] = json.load(f)
    
    # Load devices data
    with open(os.path.join(data_dir, "devices.json"), "r") as f:
        data["devices"] = json.load(f)
    
    # Load billing data
    with open(os.path.join(data_dir, "billing.json"), "r") as f:
        data["billing"] = json.load(f)
  
    # Load support tickets data
    with open(os.path.join(data_dir, "support_tickets.json"), "r") as f:
        data["support_tickets"] = json.load(f)
    
    return data
