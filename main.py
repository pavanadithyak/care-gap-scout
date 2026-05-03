import os
import asyncio
from dotenv import load_dotenv
from fastmcp import FastMCP, Context

from fhir_context import get_fhir_context
from po_extension import PO_FHIR_EXTENSION
from tools.fhir import get_patient, get_conditions, get_observations, get_medications, get_immunizations
from tools.gaps import detect_care_gaps, calculate_age
from tools.trials import search_trials_for_condition
from tools.report import generate_report

load_dotenv()

DEMO_MODE = os.getenv("DEMO_MODE", "false").lower() == "true"

# Fixture patient for DEMO_MODE — no FHIR server needed
FIXTURE = {
    "patient_id": "demo-001",
    "demographics": {"name": "James Wilson", "birth_date": "1961-03-22", "gender": "male", "city": "Houston", "state": "TX"},
    "conditions": [{"display": "Type 2 Diabetes Mellitus", "icd10": "E11"}, {"display": "Essential Hypertension", "icd10": "I10"}],
    "observations": [
        {"display": "Hemoglobin A1c", "loinc": "4548-4", "date": "2023-11-01", "value": "8.1%"},
        {"display": "Blood Pressure", "loinc": "55284-4", "date": "2025-01-10", "value": "138/88"},
    ],
    "medications": [{"name": "Metformin 1000mg"}],
    "immunizations": [],
}

# FastMCP server with PO FHIR extension injected
mcp = FastMCP(
    "care-gap-scout",
    capabilities={"extensions": PO_FHIR_EXTENSION}
)

# ── TOOL 1 ──────────────────────────────────────────────────────────────────

@mcp.tool()
async def identify_care_gaps(ctx: Context, patient_id: str = "") -> dict:
    """
    Identify unaddressed care gaps for this patient against USPSTF/HEDIS guidelines.
    Reads patient demographics, conditions, labs, and immunizations from FHIR.
    Returns prioritized list of missing or overdue screenings and preventive care.
    Call this first — it drives all other tools.
    """
    if DEMO_MODE:
        d = FIXTURE
        pid = d["patient_id"]
        demo = d["demographics"]
        conditions = d["conditions"]
        obs = d["observations"]
        imms = d["immunizations"]
    else:
        fhir = get_fhir_context(ctx)
        pid = patient_id or fhir["patient_id"]
        if not pid:
            return {"error": "No patient ID found. Ensure FHIR context is authorized in PO platform settings."}

        patient_r, cond_r, obs_r, imm_r = await asyncio.gather(
            get_patient(pid, fhir["fhir_url"], fhir["token"]),
            get_conditions(pid, fhir["fhir_url"], fhir["token"]),
            get_observations(pid, fhir["fhir_url"], fhir["token"]),
            get_immunizations(pid, fhir["fhir_url"], fhir["token"]),
        )
        if patient_r["error"]:
            return {"error": f"FHIR patient fetch failed: {patient_r['error']}"}
        demo = patient_r["demographics"]
        conditions = cond_r["conditions"]
        obs = obs_r["observations"]
        imms = imm_r["immunizations"]

    age = calculate_age(demo.get("birth_date", ""))
    sex = demo.get("gender", "")
    gaps = detect_care_gaps(age, sex, conditions, obs, imms)

    return {
        "patient_id": pid,
        "patient_name": demo.get("name","").strip(),
        "age": age,
        "sex": sex,
        "conditions": [c["display"] for c in conditions],
        "gaps_found": len(gaps),
        "gaps": gaps,
        "demo_mode": DEMO_MODE,
    }

# ── TOOL 2 ──────────────────────────────────────────────────────────────────

@mcp.tool()
async def generate_care_gap_report(ctx: Context, patient_id: str = "", include_trials: bool = True) -> dict:
    """
    Generate a clinician-ready care gap report readable in 30 seconds.
    Combines patient FHIR data, identified gaps, CPT order codes, and
    optionally matches clinical trials for each gap condition.
    This is the primary output tool — use after identify_care_gaps.
    """
    gap_result = await identify_care_gaps(ctx, patient_id=patient_id)
    if "error" in gap_result:
        return gap_result

    if DEMO_MODE:
        demo = FIXTURE["demographics"]
        pid = FIXTURE["patient_id"]
    else:
        fhir = get_fhir_context(ctx)
        pid = gap_result["patient_id"]
        patient_r = await get_patient(pid, fhir["fhir_url"], fhir["token"])
        demo = patient_r["demographics"] if not patient_r["error"] else {}

    gaps = gap_result["gaps"]
    trials_by_gap = {}

    if include_trials and gaps:
        # Fetch trials for top 3 gaps in parallel
        top_gaps = gaps[:3]
        trial_results = await asyncio.gather(*[
            search_trials_for_condition(g["name"], max_results=3)
            for g in top_gaps
        ])
        for g, t in zip(top_gaps, trial_results):
            if t:
                trials_by_gap[g["id"]] = t

    report_text = generate_report(demo, pid, gaps, trials_by_gap)

    return {
        "patient_id": pid,
        "gaps_found": len(gaps),
        "trials_found": sum(len(v) for v in trials_by_gap.values()),
        "report": report_text,
    }

# ── TOOL 3 ──────────────────────────────────────────────────────────────────

@mcp.tool()
async def check_screening_status(ctx: Context, screening: str, patient_id: str = "") -> dict:
    """
    Quick check: is this patient current on a specific screening?
    screening examples: 'mammogram', 'colorectal', 'diabetes', 'blood pressure', 'depression'
    Returns: CURRENT / OVERDUE / MISSING with last date and days overdue.
    """
    gap_result = await identify_care_gaps(ctx, patient_id=patient_id)
    if "error" in gap_result:
        return gap_result

    screening_lower = screening.lower()
    for gap in gap_result["gaps"]:
        if (screening_lower in gap["name"].lower() or
            screening_lower in gap["id"].lower() or
            screening_lower in gap.get("description","").lower()):
            return {
                "screening": gap["name"],
                "status": gap["status"],
                "last_done": gap.get("last_done"),
                "overdue_note": gap["overdue_note"],
                "action": gap["description"],
                "cpt_hint": gap["cpt_hint"],
                "evidence": gap["evidence"],
            }

    return {
        "screening": screening,
        "status": "CURRENT_OR_NOT_APPLICABLE",
        "message": f"No gap found for '{screening}' — patient is current or this screening does not apply.",
    }

# ── TOOL 4 ──────────────────────────────────────────────────────────────────

@mcp.tool()
async def get_gap_details(gap_id: str, ctx: Context, patient_id: str = "") -> dict:
    """
    Get full detail on a specific care gap by ID.
    gap_id comes from identify_care_gaps results (e.g. 'colorectal_screening', 'diabetes_monitoring').
    Returns complete clinical context including matching trials.
    """
    gap_result = await identify_care_gaps(ctx, patient_id=patient_id)
    if "error" in gap_result:
        return gap_result

    gap = next((g for g in gap_result["gaps"] if g["id"] == gap_id), None)
    if not gap:
        return {"error": f"Gap '{gap_id}' not found or not applicable for this patient."}

    trials = await search_trials_for_condition(gap["name"], max_results=5)
    return {
        **gap,
        "patient_id": gap_result["patient_id"],
        "matching_trials": trials,
    }

# ── TOOL 5 ──────────────────────────────────────────────────────────────────

@mcp.tool()
async def get_recommended_orders(ctx: Context, patient_id: str = "") -> dict:
    """
    Return a ready-to-use order list for all identified care gaps.
    Each item includes CPT code hint, description, and priority.
    Designed to be pasted directly into EHR order entry workflow.
    """
    gap_result = await identify_care_gaps(ctx, patient_id=patient_id)
    if "error" in gap_result:
        return gap_result

    orders = []
    for gap in gap_result["gaps"]:
        orders.append({
            "priority": gap["priority"],
            "order": gap["name"],
            "status": gap["status"],
            "cpt_hint": gap["cpt_hint"],
            "action": gap["description"],
            "evidence": gap["evidence"],
        })

    return {
        "patient_id": gap_result["patient_id"],
        "order_count": len(orders),
        "orders": orders,
        "note": "CPT codes are hints only — verify with your billing team before submitting."
    }

# ── TOOL 6 ──────────────────────────────────────────────────────────────────

@mcp.tool()
async def find_trials_for_gaps(ctx: Context, patient_id: str = "", max_per_gap: int = 3) -> dict:
    """
    Find recruiting clinical trials for each identified care gap condition.
    Combines care gap detection with ClinicalTrials.gov search.
    Returns trials grouped by gap — shows which trial addresses which gap.
    """
    gap_result = await identify_care_gaps(ctx, patient_id=patient_id)
    if "error" in gap_result:
        return gap_result

    gaps = gap_result["gaps"][:5]
    if not gaps:
        return {"patient_id": gap_result["patient_id"], "message": "No gaps found — no trials to fetch.", "trials": {}}

    trial_results = await asyncio.gather(*[
        search_trials_for_condition(g["name"], max_results=max_per_gap)
        for g in gaps
    ])

    trials_by_gap = {}
    total = 0
    for g, t in zip(gaps, trial_results):
        if t:
            trials_by_gap[g["name"]] = t
            total += len(t)

    return {
        "patient_id": gap_result["patient_id"],
        "gaps_with_trials": len(trials_by_gap),
        "total_trials": total,
        "trials_by_gap": trials_by_gap,
    }

# ── TOOL 7 ──────────────────────────────────────────────────────────────────

@mcp.tool()
async def explain_guideline(guideline_name: str) -> dict:
    """
    Explain why a specific screening or preventive measure is recommended.
    In plain language suitable for patient education or non-specialist review.
    guideline_name: e.g. 'colorectal cancer screening', 'mammogram', 'HbA1c'
    """
    from tools.guidelines import GUIDELINES
    name_lower = guideline_name.lower()
    match = next((g for g in GUIDELINES
                  if name_lower in g["name"].lower() or name_lower in g["id"].lower()), None)
    if not match:
        return {"error": f"No guideline found matching '{guideline_name}'"}

    age_range = f"Ages {match['age_min']}–{match['age_max'] if match['age_max'] < 999 else '+'}"
    freq = {0: "Once", 365: "Annually", 730: "Every 2 years",
            1095: "Every 3 years", 1825: "Every 5 years", 3650: "Every 10 years"
           }.get(match["frequency_days"], f"Every {match['frequency_days']//365} years")

    return {
        "name": match["name"],
        "evidence_grade": match["evidence"],
        "who_needs_it": f"{age_range}, Sex: {match['sex']}" + (f", Condition: {match['condition']}" if match["condition"] else ""),
        "how_often": freq,
        "what_to_order": match["description"],
        "cpt_hint": f"Coding guidance: {match.get('cpt_hint','')}",
        "plain_language": (
            f"The {match['name']} is recommended by {match['evidence']} because "
            f"catching this condition early significantly improves outcomes. "
            f"It is recommended for patients aged {match['age_min']}–{match['age_max']} "
            f"and should be done {freq.lower()}."
        )
    }

# ── HEALTH CHECK ─────────────────────────────────────────────────────────────

@mcp.custom_route("/health", methods=["GET"])
async def health_check(request):
    from starlette.responses import JSONResponse
    return JSONResponse({
        "status": "ok",
        "server": "care-gap-scout",
        "tools": 7,
        "demo_mode": DEMO_MODE,
        "fhir_extension": "ai.promptopinion/fhir-context",
        "fhir_headers": ["X-FHIR-Server-URL", "X-FHIR-Access-Token", "X-Patient-ID"]
    })

# ── ENTRY POINT ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    print(f"Starting CareGapScout on port {port}")
    print(f"Demo mode: {DEMO_MODE}")
    print(f"Health: http://localhost:{port}/health")
    print(f"SSE:    http://localhost:{port}/sse")
    print(f"PO FHIR extension: ai.promptopinion/fhir-context declared")
    mcp.run(transport="sse", host="0.0.0.0", port=port)
