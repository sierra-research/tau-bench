from __future__ import annotations

from typing import Any, Dict, List

from tau_bench.envs.tool import Tool


class CheckDrugInteractions(Tool):
    @staticmethod
    def invoke(
        data: Dict[str, Any],
        primary_medication: str,
        current_medications: List[str],
    ) -> str:
        interactions: Dict[str, Dict[str, Dict[str, Any]]] = data.get("drug_interactions", {})

        canonical_name: Dict[str, str] = {}
        for outer_key, inner in interactions.items():
            canonical_name.setdefault(outer_key.lower(), outer_key)
            for inner_key in inner.keys():
                canonical_name.setdefault(inner_key.lower(), inner_key)

        def canonical(med: str) -> str:
            return canonical_name.get(med.lower(), med)

        def lookup(med_a: str, med_b: str) -> Dict[str, Any] | None:
            key_a = canonical(med_a)
            key_b = canonical(med_b)
            med_a_data = interactions.get(key_a, {})
            for candidate, details in med_a_data.items():
                if candidate.lower() == key_b.lower():
                    return details
            med_b_data = interactions.get(key_b, {})
            for candidate, details in med_b_data.items():
                if candidate.lower() == key_a.lower():
                    return details
            return None

        lines: List[str] = []
        skip_set: set[str] = set()
        emergency = False
        max_overlap = 0
        highest_severity = "none"

        severity_ranking = {"low": 1, "moderate": 2, "high": 3}
        severity_reason = None

        for medication in current_medications:
            details = lookup(primary_medication, medication)
            if not details:
                continue
            severity = details.get("severity", "unknown")
            risk = details.get("risk_score")
            overlap = details.get("time_overlap_hours", 0)
            action = details.get("action", "Monitor.")
            skip_set.update(details.get("skip", []))
            emergency = emergency or details.get("emergency", False)
            max_overlap = max(max_overlap, overlap)
            display_primary = canonical(primary_medication)
            display_med = canonical(medication)
            lines.append(
                f"{display_primary} + {display_med}: severity={severity}, risk_score={risk}, overlap_hours={overlap}. {action}"
            )
            if severity_ranking.get(severity, 0) > severity_ranking.get(highest_severity, 0):
                highest_severity = severity
                severity_reason = f"{display_primary} + {display_med}"

        # Evaluate interactions among current medications themselves for completeness
        for idx, med_a in enumerate(current_medications):
            for med_b in current_medications[idx + 1 :]:
                details = lookup(med_a, med_b)
                if not details:
                    continue
                severity = details.get("severity", "unknown")
                risk = details.get("risk_score")
                overlap = details.get("time_overlap_hours", 0)
                action = details.get("action", "Monitor.")
                skip_set.update(details.get("skip", []))
                emergency = emergency or details.get("emergency", False)
                max_overlap = max(max_overlap, overlap)
                display_a = canonical(med_a)
                display_b = canonical(med_b)
                lines.append(
                    f"{display_a} + {display_b}: severity={severity}, risk_score={risk}, overlap_hours={overlap}. {action}"
                )
                if severity_ranking.get(severity, 0) > severity_ranking.get(highest_severity, 0):
                    highest_severity = severity
                    severity_reason = f"{display_a} + {display_b}"

        if not lines:
            return (
                "No documented high-risk interactions found for the supplied medications. Continue monitoring as per care plan."
            )

        summary_lines = [
            "Drug interaction analysis:",
            *lines,
            "",
            f"Medications to hold today: {', '.join(sorted(skip_set)) if skip_set else 'None'}",
            f"Emergency escalation required: {'Yes' if emergency else 'No'}",
            f"Peak overlap risk window (hours): {max_overlap}",
        ]
        if severity_reason:
            summary_lines.append(
                f"Highest severity interaction: {severity_reason} ({highest_severity})"
            )
        return "\n".join(summary_lines)

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "check_drug_interactions",
                "description": "Evaluate potential interactions between an incident medication and a patient’s current regimen.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "primary_medication": {
                            "type": "string",
                            "description": "The medication that was taken accidentally or requires review.",
                        },
                        "current_medications": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of the patient’s active medications.",
                        },
                    },
                    "required": ["primary_medication", "current_medications"],
                },
            },
        }
