# Hardcoded USPSTF Grade A/B recommendations + key HEDIS measures.
# Source: https://www.uspreventiveservicestaskforce.org/uspstf/recommendation-topics
# No external API needed — these are stable public guidelines.
#
# Structure per measure:
#   id          — unique key
#   name        — human-readable name
#   category    — screening | immunization | counseling | lab
#   condition   — FHIR Condition text to trigger (if conditional)
#   age_min     — minimum age (inclusive)
#   age_max     — maximum age (inclusive, 999 = no max)
#   sex         — M | F | ALL
#   loinc_codes — LOINC codes that satisfy this gap if found in Observations
#   keywords    — observation display text keywords that satisfy this gap
#   frequency_days — how often required (0 = once, 365 = annually, etc.)
#   priority    — 1 (highest) to 3
#   evidence    — USPSTF grade or HEDIS
#   description — what clinician should order.

GUIDELINES = [
    # ── CANCER SCREENINGS ──
    {
        "id": "colorectal_screening",
        "name": "Colorectal Cancer Screening",
        "category": "screening",
        "condition": None,
        "age_min": 45, "age_max": 75,
        "sex": "ALL",
        "loinc_codes": ["29544-4","77353-1","72093-3","2335-8"],
        "keywords": ["colonoscopy","colorectal","fobt","cologuard","stool dna","sigmoidoscopy","fit test"],
        "frequency_days": 3650,
        "priority": 1,
        "evidence": "USPSTF Grade A",
        "description": "Order colorectal cancer screening (colonoscopy, FIT, or Cologuard). Due every 10yr (colonoscopy) or annually (FIT)."
    },
    {
        "id": "breast_cancer_screening",
        "name": "Breast Cancer Screening (Mammogram)",
        "category": "screening",
        "condition": None,
        "age_min": 40, "age_max": 74,
        "sex": "F",
        "loinc_codes": ["24606-6","26346-7","26347-5"],
        "keywords": ["mammogram","mammography","breast imaging"],
        "frequency_days": 730,
        "priority": 1,
        "evidence": "USPSTF Grade B",
        "description": "Order screening mammogram. Recommended every 1–2 years for women aged 40–74."
    },
    {
        "id": "cervical_cancer_screening",
        "name": "Cervical Cancer Screening (Pap Smear)",
        "category": "screening",
        "condition": None,
        "age_min": 21, "age_max": 65,
        "sex": "F",
        "loinc_codes": ["10524-7","19762-4","33717-0"],
        "keywords": ["pap smear","cervical cytology","pap test","hpv co-test"],
        "frequency_days": 1095,
        "priority": 1,
        "evidence": "USPSTF Grade A",
        "description": "Order Pap smear every 3 years (or Pap + HPV co-test every 5 years) for women 21–65."
    },
    {
        "id": "lung_cancer_screening",
        "name": "Lung Cancer Screening (Low-Dose CT)",
        "category": "screening",
        "condition": "smoking",
        "age_min": 50, "age_max": 80,
        "sex": "ALL",
        "loinc_codes": ["24647-0"],
        "keywords": ["low dose ct","ldct","lung ct","lung cancer screen"],
        "frequency_days": 365,
        "priority": 1,
        "evidence": "USPSTF Grade B",
        "description": "Order annual low-dose CT lung cancer screening for current/former smokers aged 50–80 with 20+ pack-year history."
    },
    # ── CARDIOVASCULAR ──
    {
        "id": "blood_pressure_check",
        "name": "Blood Pressure Screening",
        "category": "screening",
        "condition": None,
        "age_min": 18, "age_max": 999,
        "sex": "ALL",
        "loinc_codes": ["55284-4","8480-6","8462-4"],
        "keywords": ["blood pressure","bp","systolic","diastolic"],
        "frequency_days": 365,
        "priority": 2,
        "evidence": "USPSTF Grade A",
        "description": "Blood pressure measurement. Due annually for adults 18+."
    },
    {
        "id": "cholesterol_screening",
        "name": "Lipid Panel / Cholesterol Screening",
        "category": "lab",
        "condition": None,
        "age_min": 35, "age_max": 999,
        "sex": "ALL",
        "loinc_codes": ["2093-3","13457-7","18262-6","2085-9","35200-5"],
        "keywords": ["cholesterol","lipid panel","ldl","hdl","triglycerides"],
        "frequency_days": 1825,
        "priority": 2,
        "evidence": "USPSTF Grade A",
        "description": "Order fasting lipid panel. Recommended every 4–5 years for adults at average risk."
    },
    {
        "id": "abdominal_aortic_aneurysm",
        "name": "Abdominal Aortic Aneurysm Screening (AAA)",
        "category": "screening",
        "condition": "smoking",
        "age_min": 65, "age_max": 75,
        "sex": "M",
        "loinc_codes": ["40701008"],
        "keywords": ["aortic aneurysm","aaa ultrasound","abdominal aorta"],
        "frequency_days": 0,
        "priority": 2,
        "evidence": "USPSTF Grade B",
        "description": "One-time abdominal ultrasound for AAA screening in male smokers aged 65–75."
    },
    # ── METABOLIC ──
    {
        "id": "diabetes_screening",
        "name": "Diabetes / Prediabetes Screening (HbA1c or FPG)",
        "category": "lab",
        "condition": None,
        "age_min": 35, "age_max": 70,
        "sex": "ALL",
        "loinc_codes": ["4548-4","17856-6","2345-7","1558-6"],
        "keywords": ["hba1c","hemoglobin a1c","fasting glucose","fasting plasma glucose","a1c"],
        "frequency_days": 1095,
        "priority": 1,
        "evidence": "USPSTF Grade B",
        "description": "Order HbA1c or fasting plasma glucose for diabetes screening. Due every 3 years for overweight/obese adults 35–70."
    },
    {
        "id": "diabetes_monitoring",
        "name": "Diabetes HbA1c Monitoring",
        "category": "lab",
        "condition": "diabetes",
        "age_min": 18, "age_max": 999,
        "sex": "ALL",
        "loinc_codes": ["4548-4","17856-6"],
        "keywords": ["hba1c","hemoglobin a1c","a1c"],
        "frequency_days": 90,
        "priority": 1,
        "evidence": "HEDIS CDC",
        "description": "HbA1c monitoring for diabetes management. Due every 3–6 months."
    },
    # ── MENTAL HEALTH ──
    {
        "id": "depression_screening",
        "name": "Depression Screening (PHQ-9)",
        "category": "screening",
        "condition": None,
        "age_min": 18, "age_max": 999,
        "sex": "ALL",
        "loinc_codes": ["44249-1","55757-9"],
        "keywords": ["phq","depression screen","phq-9","phq-2","depression assessment"],
        "frequency_days": 365,
        "priority": 2,
        "evidence": "USPSTF Grade B",
        "description": "Administer PHQ-9 depression screening. Recommended annually for all adults."
    },
    # ── IMMUNIZATIONS ──
    {
        "id": "flu_vaccine",
        "name": "Annual Influenza Vaccine",
        "category": "immunization",
        "condition": None,
        "age_min": 6, "age_max": 999,
        "sex": "ALL",
        "loinc_codes": [],
        "keywords": ["influenza","flu vaccine","flu shot","inactivated influenza"],
        "frequency_days": 365,
        "priority": 2,
        "evidence": "USPSTF Grade B",
        "description": "Administer annual influenza vaccine."
    },
    {
        "id": "pneumococcal_vaccine",
        "name": "Pneumococcal Vaccine (PCV20 or PPSV23)",
        "category": "immunization",
        "condition": None,
        "age_min": 65, "age_max": 999,
        "sex": "ALL",
        "loinc_codes": [],
        "keywords": ["pneumococcal","pneumonia vaccine","pcv","ppsv"],
        "frequency_days": 0,
        "priority": 2,
        "evidence": "USPSTF Grade B",
        "description": "Administer pneumococcal vaccine for adults 65+."
    },
    # ── BONE HEALTH ──
    {
        "id": "osteoporosis_screening",
        "name": "Osteoporosis Screening (DEXA Scan)",
        "category": "screening",
        "condition": None,
        "age_min": 65, "age_max": 999,
        "sex": "F",
        "loinc_codes": ["38263-0","24701-5"],
        "keywords": ["dexa","bone density","dxa","dual energy"],
        "frequency_days": 730,
        "priority": 2,
        "evidence": "USPSTF Grade B",
        "description": "Order DEXA bone density scan for women 65+ or postmenopausal women under 65 at elevated risk."
    },
]

def get_applicable_guidelines(age: int, sex: str, conditions: list) -> list:
    """Filter guidelines applicable to this patient by age, sex, and conditions."""
    condition_text = " ".join([c.get("display", "").lower() for c in conditions])
    applicable = []
    sex_upper = sex.upper()[0] if sex else "U"  # M/F/U

    for g in GUIDELINES:
        # Age check
        if not (g["age_min"] <= age <= g["age_max"]):
            continue
        # Sex check
        if g["sex"] != "ALL":
            if g["sex"] == "M" and sex_upper != "M":
                continue
            if g["sex"] == "F" and sex_upper != "F":
                continue
        # Condition-gated check
        if g["condition"]:
            if g["condition"].lower() not in condition_text:
                continue
        applicable.append(g)
    return applicable
