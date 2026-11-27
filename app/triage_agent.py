EMERGENCY_KEYWORDS = [
    "gas leak", "fire", "smoke", "electric shock", "danger", 
    "explosion", "sparking", "short circuit", "bleeding", "collapse"
]

def triage_complaint(text: str) -> dict:
    text_lower = text.lower()
    
    # 1. Zero-Latency Emergency Safety Bypass Check
    is_emergency = any(keyword in text_lower for keyword in EMERGENCY_KEYWORDS)
    if is_emergency:
        return {
            "category": "EMERGENCY HAZARD",
            "urgency": "CRITICAL",
            "is_emergency": True,
            "routed_to": "Campus Security & Safety Desk",
            "suggested_action": "🚨 Immediate Security Alert dispatched. Evacuate radius if needed."
        }

    # 2. Rule-based NLP Categorization & Urgency Parsing
    if any(k in text_lower for k in ["wifi", "internet", "network", "server", "portal", "login", "pc", "computer"]):
        category = "IT & Systems"
    elif any(k in text_lower for k in ["fan", "light", "ac", "power", "wiring", "socket", "switch"]):
        category = "Electrical"
    elif any(k in text_lower for k in ["water", "pipe", "tap", "sink", "toilet", "leak", "flush"]):
        category = "Plumbing"
    elif any(k in text_lower for k in ["bench", "door", "window", "chair", "table", "wall", "projector"]):
        category = "Civil & Infrastructure"
    else:
        category = "General Maintenance"

    if any(k in text_lower for k in ["urgent", "broken", "overflowing", "damaged", "heavy"]):
        urgency = "High"
    elif any(k in text_lower for k in ["slow", "noise", "not working", "flickering"]):
        urgency = "Medium"
    else:
        urgency = "Low"

    return {
        "category": category,
        "urgency": urgency,
        "is_emergency": False,
        "routed_to": f"{category} Maintenance Department",
        "suggested_action": f"Schedule technician inspection for {category} issue."
    }