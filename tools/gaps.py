# Care gap detection engine.
# Compares applicable guidelines against patient's observation history
# to determine which recommended screenings/labs are missing or overdue.

from datetime import date, datetime
from tools.guidelines import get_applicable_guidelines

def calculate_age(birth_date_str: str) -> int:
    """Calculate age from FHIR birthDate string (YYYY-MM-DD or YYYY)."""
    try:
        if len(birth_date_str) == 4:
            return date.today().year - int(birth_date_str)
        bd = datetime.strptime(birth_date_str[:10], "%Y-%m-%d").date()
        today = date.today()
        return today.year - bd.year - ((today.month, today.day) < (bd.month, bd.day))
    except Exception:
        return 0

def find_last_done(guideline: dict, observations: list, immunizations: list) -> dict:
    """
    Find most recent observation/immunization satisfying this guideline.
    Returns {"found": bool, "date": str, "days_ago": int}
    """
    all_items = list(observations) + [
        {"display": i["name"], "loinc": "", "date": i["date"], "value": ""} for i in immunizations
    ]
    best_date = None

    for item in all_items:
        item_display = item.get("display", "").lower()
        item_loinc = item.get("loinc", "")
        item_date_str = item.get("date", "")

        # Check LOINC match
        loinc_match = item_loinc and item_loinc in guideline["loinc_codes"]
        # Check keyword match
        keyword_match = any(kw in item_display for kw in guideline["keywords"])

        if loinc_match or keyword_match:
            if item_date_str:
                try:
                    item_date = datetime.strptime(item_date_str[:10], "%Y-%m-%d").date()
                    if best_date is None or item_date > best_date:
                        best_date = item_date
                except Exception:
                    pass

    if best_date:
        days_ago = (date.today() - best_date).days
        return {"found": True, "date": str(best_date), "days_ago": days_ago}
    return {"found": False, "date": None, "days_ago": None}

def detect_care_gaps(
    age: int,
    sex: str,
    conditions: list,
    observations: list,
    immunizations: list
) -> list:
    """
    Core care gap detection. Returns list of gap dicts sorted by priority.
    Each gap has: id, name, status, last_done_date, days_overdue, priority,
    evidence, description, category, cpt_hint.
    """
    applicable = get_applicable_guidelines(age, sex, conditions)
    gaps = []

    CPT_HINTS = {
        "colorectal_screening":      "CPT 45378 (colonoscopy) or 82274 (FIT)",
        "breast_cancer_screening":   "CPT 77067 (screening mammogram)",
        "cervical_cancer_screening": "CPT 88141 (Pap smear)",
        "lung_cancer_screening":     "CPT 71250 (low-dose CT chest)",
        "blood_pressure_check":      "Document in vitals",
        "cholesterol_screening":     "CPT 80061 (lipid panel)",
        "abdominal_aortic_aneurysm": "CPT 76706 (AAA ultrasound)",
        "diabetes_screening":        "CPT 83036 (HbA1c) or 82947 (fasting glucose)",
        "diabetes_monitoring":       "CPT 83036 (HbA1c)",
        "depression_screening":      "Document PHQ-9 score in chart",
        "flu_vaccine":               "CPT 90686 (quadrivalent flu vaccine)",
        "pneumococcal_vaccine":      "CPT 90670 (PCV20)",
        "osteoporosis_screening":    "CPT 77080 (DEXA scan)",
    }

    for g in applicable:
        last = find_last_done(g, observations, immunizations)

        if not last["found"]:
            status = "MISSING"
            days_overdue = None
            overdue_note = "Never done — no record found in chart"
        elif g["frequency_days"] == 0:
            status = "DONE"  # one-time, already done
            continue
        else:
            overdue_by = last["days_ago"] - g["frequency_days"]
            if overdue_by > 0:
                status = "OVERDUE"
                days_overdue = overdue_by
                overdue_note = f"Last done {last['date']} ({last['days_ago']} days ago) — overdue by {overdue_by} days"
            else:
                status = "CURRENT"
                continue  # not a gap

        gaps.append({
            "id":            g["id"],
            "name":          g["name"],
            "category":      g["category"],
            "status":        status,
            "last_done":     last.get("date"),
            "days_overdue":  days_overdue,
            "overdue_note":  overdue_note,
            "priority":      g["priority"],
            "evidence":      g["evidence"],
            "description":   g["description"],
            "cpt_hint":      CPT_HINTS.get(g["id"], ""),
        })

    # Sort: priority asc, then OVERDUE before MISSING
    gaps.sort(key=lambda x: (x["priority"], 0 if x["status"] == "OVERDUE" else 1))
    return gaps
