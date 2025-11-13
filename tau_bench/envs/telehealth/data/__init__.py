
import json
import os
from typing import Dict, Any

def load_data() -> Dict[str, Any]:
    """Load telehealth data from JSON files."""
    data_dir = os.path.dirname(__file__)
    
    # Load patients data
    with open(os.path.join(data_dir, "patients.json"), "r") as f:
        patients = json.load(f)
    
    # Load providers data
    with open(os.path.join(data_dir, "providers.json"), "r") as f:
        providers = json.load(f)
    
    # Load appointments data
    with open(os.path.join(data_dir, "appointments.json"), "r") as f:
        appointments = json.load(f)
    
    # Load medical records data
    with open(os.path.join(data_dir, "medical_records.json"), "r") as f:
        medical_records = json.load(f)

    # Load medication supplier data
    with open(os.path.join(data_dir, "medication_suppliers.json"), "r") as f:
        medication_suppliers = json.load(f)

    # Load drug interaction data
    with open(os.path.join(data_dir, "drug_interactions.json"), "r") as f:
        drug_interactions = json.load(f)

    # Load telemetry inventory (if present)
    telemetry_inventory_path = os.path.join(data_dir, "telemetry_inventory.json")
    if os.path.exists(telemetry_inventory_path):
        with open(telemetry_inventory_path, "r") as f:
            telemetry_inventory = json.load(f)
    else:
        telemetry_inventory = []

    # Load telemetry uploads (if present)
    telemetry_uploads_path = os.path.join(data_dir, "telemetry_uploads.json")
    if os.path.exists(telemetry_uploads_path):
        with open(telemetry_uploads_path, "r") as f:
            telemetry_uploads = json.load(f)
    else:
        telemetry_uploads = []

    # Load regimen plans (if present)
    regimen_plans_path = os.path.join(data_dir, "regimen_plans.json")
    if os.path.exists(regimen_plans_path):
        with open(regimen_plans_path, "r") as f:
            regimen_plans = json.load(f)
    else:
        regimen_plans = {}

    return {
        "patients": patients,
        "providers": providers,
        "appointments": appointments,
        "medical_records": medical_records,
        "medication_suppliers": medication_suppliers,
        "drug_interactions": drug_interactions,
        "telemetry_inventory": telemetry_inventory,
        "telemetry_uploads": telemetry_uploads,
        "regimen_plans": regimen_plans,
    }
