import json

SYSTEM = """
You are a CRM qualification assistant.
Never invent facts. Use only the supplied prospect and event context.
Return JSON with:
fit_score (0-100),
buying_signal (high|medium|low|unknown),
facts (array),
inferences (array),
unknowns (array),
reason (string).
"""

def build_prompt(prospect: dict, event: dict) -> str:
    return SYSTEM + "\nPROSPECT:\n" + json.dumps(prospect, default=str) + "\nEVENT:\n" + json.dumps(event, default=str)
