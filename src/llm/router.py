import json
import os

class SemanticRouter:
    """
    Keyword-based query routing. Zero resource cost.
    Loads keywords from configuration to adhere to the Open/Closed Principle.
    """
    def __init__(self, config_path: str = None):
        if not config_path:
            config_path = os.path.abspath(
                os.path.join(os.path.dirname(__file__), "..", "..", "config", "keywords.json")
            )
        self.keywords = self._load_keywords(config_path)

    def _load_keywords(self, config_path: str) -> list[str]:
        if os.path.exists(config_path):
            with open(config_path, "r") as f:
                data = json.load(f)
                return data.get("telecom_keywords", [])
        print("⚠️  Warning: keywords.json not found. Router using default empty list.")
        return []

    def classify(self, query: str, has_memory: bool = False) -> str:
        """
        Returns:
            'telecom'  — query is about telecom alarms/SOPs/equipment
            'general'  — query is out-of-scope
        """
        query_lower = query.lower()

        # Conversational fallback: If this is a follow-up, treat it as telecom
        if has_memory:
            return "telecom"

        # Check if any telecom keyword appears in the query
        for keyword in self.keywords:
            if keyword in query_lower:
                return "telecom"

        # Also match ALARM_CODE_XXX patterns
        if "alarm" in query_lower or "code" in query_lower:
            return "telecom"

        return "general"
