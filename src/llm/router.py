import json
import os

class SemanticRouter:
    """Route obvious telecom queries with keywords from a configuration file."""
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
        print("Warning: keywords.json was not found. The router has no configured keywords.")
        return []

    def classify(self, query: str, has_memory: bool = False) -> str:
        """Return ``telecom`` for supported queries and ``general`` otherwise."""
        query_lower = query.lower()

        # Treat follow-up questions as telecom questions.
        if has_memory:
            return "telecom"

        # Check the configured telecom keywords.
        for keyword in self.keywords:
            if keyword in query_lower:
                return "telecom"

        # Keep alarm-related questions in scope.
        if "alarm" in query_lower or "code" in query_lower:
            return "telecom"

        return "general"
