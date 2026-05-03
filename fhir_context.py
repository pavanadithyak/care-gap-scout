# Extracts Prompt Opinion's official FHIR context headers.
# Reference: https://docs.promptopinion.ai/fhir-context/mcp-fhir-context
#
# PO sends these exact headers when a tool is called:
#   X-FHIR-Server-URL     — base URL of FHIR server
#   X-FHIR-Access-Token   — bearer token (empty = public sandbox)
#   X-Patient-ID          — FHIR patient resource ID
#
# DO NOT use old SHARP headers (x-sharp-patient-id etc.) — those are wrong.

from fastmcp import Context

def get_fhir_context(ctx: Context) -> dict:
    """
    Extract Prompt Opinion FHIR context from MCP request headers.
    Returns defaults when headers absent (direct testing without PO platform).
    """
    try:
        request = ctx.get_http_request()
        headers = request.headers
    except (ValueError, AttributeError):
        headers = {}

    return {
        "patient_id": headers.get("x-patient-id", ""),
        "fhir_url": headers.get("x-fhir-server-url", "https://r4.smarthealthit.org"),
        "token": headers.get("x-fhir-access-token", ""),
        "refresh_token": headers.get("x-fhir-refresh-token", ""),
    }
