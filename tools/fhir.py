# FHIR R4 data fetcher.
# All functions return result dicts with an 'error' key — never raise.
# Callers must check result['error'] before using data.

import httpx
TIMEOUT = 12

async def _get(url: str, token: str) -> dict:
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    try:
        async with httpx.AsyncClient() as client:
            r = await client.get(url, headers=headers, timeout=TIMEOUT)
            r.raise_for_status()
            return {"data": r.json(), "error": None}
    except httpx.TimeoutException:
        return {"data": None, "error": f"FHIR timeout after {TIMEOUT}s — server may be down"}
    except httpx.HTTPStatusError as e:
        return {"data": None, "error": f"FHIR HTTP {e.response.status_code}"}
    except Exception as e:
        return {"data": None, "error": str(e)}

async def get_patient(patient_id: str, fhir_url: str, token: str = "") -> dict:
    """Fetch patient demographics: name, birthDate, gender, address."""
    r = await _get(f"{fhir_url}/Patient/{patient_id}", token)
    if r["error"]:
        return {"demographics": {}, "error": r["error"]}
    p = r["data"]
    name_entry = p.get("name", [{}])[0]
    addr = p.get("address", [{}])[0]
    given = " ".join(name_entry.get("given", []))
    family = name_entry.get("family", "")
    full_name = f"{given} {family}".strip()
    return {
        "demographics": {
            "name": full_name,
            "birth_date": p.get("birthDate", ""),
            "gender": p.get("gender", ""),
            "city": addr.get("city", ""),
            "state": addr.get("state", ""),
        },
        "error": None
    }

async def get_conditions(patient_id: str, fhir_url: str, token: str = "") -> dict:
    """Fetch active conditions. Returns list of {code, display, icd10}."""
    r = await _get(
        f"{fhir_url}/Condition?patient={patient_id}&clinical-status=active",
        token
    )
    if r["error"]:
        return {"conditions": [], "error": r["error"]}
    conditions = []
    for entry in r["data"].get("entry", []):
        res = entry.get("resource", {})
        cc = res.get("code", {})
        codings = cc.get("coding", [{}])
        display = cc.get("text") or codings[0].get("display", "")
        icd10 = next((c.get("code", "") for c in codings if "icd" in c.get("system", "").lower()), "")
        if display:
            conditions.append({"display": display, "icd10": icd10})
    return {"conditions": conditions, "error": None}

async def get_observations(patient_id: str, fhir_url: str, token: str = "") -> dict:
    """Fetch most recent observations/labs sorted by date desc."""
    r = await _get(
        f"{fhir_url}/Observation?patient={patient_id}&_sort=-date&_count=50",
        token
    )
    if r["error"]:
        return {"observations": [], "error": r["error"]}
    obs = []
    for entry in r["data"].get("entry", []):
        res = entry.get("resource", {})
        cc = res.get("code", {})
        display = cc.get("text") or (cc.get("coding", [{}])[0].get("display", ""))
        loinc = next((c.get("code", "") for c in cc.get("coding", []) if "loinc" in c.get("system", "").lower()), "")
        effective = res.get("effectiveDateTime", res.get("effectivePeriod", {}).get("start", ""))
        value = res.get("valueQuantity", res.get("valueString", res.get("valueCodeableConcept", {})))
        if display:
            obs.append({"display": display, "loinc": loinc, "date": effective, "value": value})
    return {"observations": obs, "error": None}

async def get_medications(patient_id: str, fhir_url: str, token: str = "") -> dict:
    """Fetch active medication requests."""
    r = await _get(
        f"{fhir_url}/MedicationRequest?patient={patient_id}&status=active",
        token
    )
    if r["error"]:
        return {"medications": [], "error": r["error"]}
    meds = []
    for entry in r["data"].get("entry", []):
        res = entry.get("resource", {})
        mc = res.get("medicationCodeableConcept", {})
        name = mc.get("text") or (mc.get("coding", [{}])[0].get("display", ""))
        if name:
            meds.append({"name": name})
    return {"medications": meds, "error": None}

async def get_immunizations(patient_id: str, fhir_url: str, token: str = "") -> dict:
    """Fetch completed immunizations."""
    r = await _get(
        f"{fhir_url}/Immunization?patient={patient_id}&status=completed",
        token
    )
    if r["error"]:
        return {"immunizations": [], "error": r["error"]}
    imms = []
    for entry in r["data"].get("entry", []):
        res = entry.get("resource", {})
        vc = res.get("vaccineCode", {})
        name = vc.get("text") or (vc.get("coding", [{}])[0].get("display", ""))
        date = res.get("occurrenceDateTime", "")
        if name:
            imms.append({"name": name, "date": date})
    return {"immunizations": imms, "error": None}
