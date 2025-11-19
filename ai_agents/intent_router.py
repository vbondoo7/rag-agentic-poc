# ai_agents/intent_router.py
class RequirementsAnalyzer:
    """Detects user intent from query text."""

    @staticmethod
    def get_intent(query: str) -> str:
        q = query.lower()
        if any(kw in q for kw in ["impact", "change", "affected", "influence", "dependency", "impacted"]):
            return "impact"
        if any(kw in q for kw in ["blueprint", "solution", "design", "architecture", "approach", "pattern"]):
            return "blueprint"
        if any(kw in q for kw in ["understand", "explain", "challenge", "gotcha", "clarify", "why"]):
            return "understanding"
        return "generic"
