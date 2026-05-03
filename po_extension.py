# Implements Prompt Opinion's MCP FHIR context extension declaration.
# Reference: https://docs.promptopinion.ai/fhir-context/mcp-fhir-context
#
# Without this, Prompt Opinion will NOT send FHIR headers to your tools.
# This must be injected into the MCP initialize response capabilities.
#
# SMART scopes declared here:
#   patient/Patient.rs    — read current patient demographics (required)
#   patient/Condition.rs  — read patient conditions (required)
#   patient/Observation.rs — read lab results and vitals (required)
#   patient/MedicationRequest.rs — read medications (optional)
#   patient/Immunization.rs — read immunization history (optional)
#   patient/Procedure.rs  — read procedures (optional)

PO_FHIR_EXTENSION = {
    "ai.promptopinion/fhir-context": {
        "scopes": [
            {"name": "patient/Patient.rs", "required": True},
            {"name": "patient/Condition.rs", "required": True},
            {"name": "patient/Observation.rs", "required": True},
            {"name": "patient/MedicationRequest.rs"},
            {"name": "patient/Immunization.rs"},
            {"name": "patient/Procedure.rs"},
        ]
    }
}

def inject_fhir_extension(capabilities: dict) -> dict:
    """
    Merge the PO FHIR extension into existing MCP capabilities dict.
    Call this when building the initialize response.
    """
    if "extensions" not in capabilities:
        capabilities["extensions"] = {}
    capabilities["extensions"].update(PO_FHIR_EXTENSION)
    return capabilities
