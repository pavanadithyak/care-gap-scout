# Generates clinician-ready plain-text care gap report.

from datetime import date

def generate_report(
    patient_demographics: dict,
    patient_id: str,
    gaps: list,
    trials: dict = None`
) -> str:
    """
    Format care gap findings into a structured clinical report.
    Readable in under 30 seconds. Includes CPT codes for direct ordering.
    """
    today = date.today().strftime("%B %d, %Y")
    name = patient_demographics.get("name", "Unknown").strip() or "Unknown"
    dob = patient_demographics.get("birth_date", "")
    gender = patient_demographics.get("gender", "").capitalize()
    city = patient_demographics.get("city", "")

    lines = [
        "═════════════════════════════════",
        "       CARE GAP REPORT — CareGapScout",
        "═════════════════════════════════",
        f"Patient:    {name}",
        f"DOB:        {dob}  |  Sex: {gender}  |  {city}",
        f"Patient ID: {patient_id}",
        f"Report Date: {today}",
        f"Gaps Found: {len(gaps)} actionable gap(s)",
        "───────────────────────────────────",
    ]

    if not gaps:
        lines.append("✓ No care gaps identified. Patient is current on all")
        lines.append("  applicable screenings and preventive measures.")
    else:
        lines.append("PRIORITY ACTION LIST:")
        lines.append("")
        for i, gap in enumerate(gaps[:5], 1):
            status_icon = "⚠️" if gap["status"] == "OVERDUE" else "❌"
            name_val = gap["name"]
            status_val = gap["status"]
            overdue_val = gap.get("overdue_note", "")
            action_val = gap["description"]
            cpt_val = gap.get("cpt_hint", "")
            evidence_val = gap["evidence"]
            lines.append(f"{i}. {status_icon} {name_val}")
            lines.append(f"   Status:   {status_val} — {overdue_val}")
            lines.append(f"   Action:   {action_val}")
            lines.append(f"   Order:    {cpt_val}")
            lines.append(f"   Evidence: {evidence_val}")
            if trials and gap["id"] in trials and trials[gap["id"]]:
                trial_list = trials[gap["id"]][:2]
                lines.append(f"   Trials:   {len(trial_list)} matching clinical trial(s) available")
                for t in trial_list:
                    proto = t.get("protocolSection", {})
                    title = proto.get("identificationModule", {}).get("briefTitle", "")[:60]
                    nct = proto.get("identificationModule", {}).get("nctId", "")
                    lines.append(f"             • {title} ({nct})")
            lines.append("")

    if len(gaps) > 5:
        lines.append(f"[+{len(gaps)-5} additional gap(s) — use get_gap_details for full list]")

    lines.append("───────────────────────────────────")
    lines.append("⚠️ AI-generated preliminary report.")
    lines.append("  Verify all recommendations with clinical judgment.")
    lines.append("═════════════════════════════════")
    return "\n".join(lines)
