from __future__ import annotations

from typing import Any, Dict, List

from tau_bench.envs.tool import Tool


class GetRegimenOptions(Tool):
    @staticmethod
    def invoke(data: Dict[str, Any], patient_id: str) -> str:
        plans: Dict[str, Any] = data.get("regimen_plans", {})
        patient_plan = plans.get(patient_id)
        if not patient_plan:
            return f"No regimen optimization data available for patient {patient_id}."

        def _format_component(component: Dict[str, Any]) -> str:
            return (
                f"{component.get('medication')} | dosage={component.get('dosage')} | "
                f"daily_dose={component.get('daily_dose')} | monthly_units={component.get('monthly_units')} | "
                f"unit_type={component.get('unit_type')} | brand={component.get('preferred_brand')} | "
                f"supplier={component.get('supplier')} | unit_cost_usd={component.get('unit_cost_usd'):.2f}"
            )

        lines: List[str] = []

        current = patient_plan.get("current_regimen", {})
        lines.append("Current regimen components:")
        for component in current.get("components", []):
            lines.append(f"- {_format_component(component)}")

        pill_burden = current.get("pill_burden")
        if pill_burden:
            lines.append(
                "Current pill burden: "
                f"tablets_per_day={pill_burden.get('tablets_per_day')} | "
                f"devices_per_month={pill_burden.get('devices_per_month')}"
            )

        notes = current.get("notes", [])
        if notes:
            lines.append("Current regimen notes:")
            for note in notes:
                lines.append(f"  * {note}")

        lines.append("Optimized regimen options:")
        for idx, regimen in enumerate(patient_plan.get("optimized_regimens", []), start=1):
            lines.append(f"Option {idx}: {regimen.get('name')}")
            lines.append(f"  Focus: {regimen.get('focus')}")
            for component in regimen.get("components", []):
                lines.append(f"  - {_format_component(component)}")
            pill_burden = regimen.get("pill_burden")
            if pill_burden:
                lines.append(
                    "  Pill burden: "
                    f"tablets_per_day={pill_burden.get('tablets_per_day')} | "
                    f"devices_per_month={pill_burden.get('devices_per_month')}"
                )
            synergy_notes = regimen.get("synergy_notes", [])
            if synergy_notes:
                lines.append("  Synergy notes:")
                for note in synergy_notes:
                    lines.append(f"    - {note}")

        return "\n".join(lines)

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "get_regimen_options",
                "description": "Retrieve current regimen components and optimized alternative combinations for a patient, including costs and pill burden details.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "patient_id": {
                            "type": "string",
                            "description": "ID of the patient",
                        },
                    },
                    "required": ["patient_id"],
                },
            },
        }
