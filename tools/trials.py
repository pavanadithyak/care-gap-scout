import httpx, time

CT_BASE = "https://clinicaltrials.gov/api/v2/studies"
_cache: dict = {}
CACHE_TTL = 300

async def search_trials_for_condition(condition: str, max_results: int = 5) -> list:
    """Search ClinicalTrials.gov for recruiting trials. Cached 5 min."""
    key = f"{condition}|{max_results}"
    now = time.time()
    if key in _cache and now - _cache[key][0] < CACHE_TTL:
        return _cache[key][1]
    try:
        async with httpx.AsyncClient() as client:
            r = await client.get(CT_BASE, params={
                "query.cond": condition,
                "filter.overallStatus": "RECRUITING",
                "pageSize": max_results,
                "fields": "NCTId,BriefTitle,Phase,EligibilityCriteria,LocationCity"
            }, timeout=15, headers={"User-Agent": "CareGapScout/1.0"})
            r.raise_for_status()
        studies = r.json().get("studies", [])
        _cache[key] = (now, studies)
        return studies
    except Exception:
        return []
