import json

SYSTEM = """
Create a concise personalized business outreach draft.
Use only provided facts. Do not invent relationships, achievements, budgets, or intent.
Return JSON:
subject,
message,
personalization_points,
unknowns.
"""

def build_prompt(prospect: dict, event: dict) -> str:
    return SYSTEM + "\nPROSPECT:\n" + json.dumps(prospect, default=str) + "\nEVENT:\n" + json.dumps(event, default=str)
