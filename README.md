# CareGapScout MCP

MCP Superpower for Prompt Opinion. Identifies unaddressed care gaps for any
patient against USPSTF/HEDIS guidelines using FHIR R4 data, then surfaces
matching clinical trials for each gap. Works for 100% of patients at every
visit.

## Tools (7)
- identify_care_gaps — core engine: FHIR → guidelines → gap list
- generate_care_gap_report — 30-second clinician-ready report with CPT codes
- check_screening_status — quick single-screening check
- get_gap_details — full detail + trials for one gap
- get_recommended_orders — ready-to-paste EHR order list
- find_trials_for_gaps — trials grouped by gap condition
- explain_guideline — plain-language guideline explainer

## PO FHIR Extension
Server declares ai.promptopinion/fhir-context in initialize response.
Scopes: patient/Patient.rs (required), patient/Condition.rs (required),
patient/Observation.rs (required), patient/MedicationRequest.rs,
patient/Immunization.rs, patient/Procedure.rs

## Local run
pip install -r requirements.txt
python main.py
# Health: http://localhost:8000/health
# SSE: http://localhost:8000/sse

## DEMO_MODE
Set DEMO_MODE=true in .env to use fixture patient (no FHIR needed).
Fixture: 63yo male, Type 2 Diabetes + Hypertension, missing HbA1c + colorectal
screening + mammogram gap absent (male) — clean demo story.

## Deploy: Render.com → Docker → PORT=8000
## Register: PO workspace → MCP Servers → paste /sse URL → authorize FHIR scopes
