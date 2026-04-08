"""
Midnight Core — Template Registry
Takeoff LLC

Routes doc_type → template pack directory.
Add new template packs here as they are built.
"""

TEMPLATE_REGISTRY = {
    "POLICY":    "generic_policy",
    "SOP":       "generic_sop",
    "PLAYBOOK":  "generic_playbook",
    "PLAN":      "generic_plan",
    "STANDARD":  "generic_policy",   # reuses policy structure
    "PROCEDURE": "generic_sop",      # reuses SOP structure
}

def get_template_path(doc_type: str) -> str:
    name = TEMPLATE_REGISTRY.get(doc_type.upper(), "generic_policy")
    return f"backend/templates/{name}"
