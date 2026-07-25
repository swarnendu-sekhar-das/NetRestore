"""Check that the configured Groq client can return a response."""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.llm.generator import get_llm_generator


def test_llm_smoke():
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        print("Warning: GROQ_API_KEY is not set. Skipping the LLM smoke test.")
        return

    print("Testing Groq LLM connectivity.")
    llm = get_llm_generator()
    response = llm.complete("Reply with exactly one word: OK")
    assert response.text.strip(), "LLM returned empty response — check API key"
    print(f"LLM smoke test passed. Response: '{response.text.strip()}'")


if __name__ == "__main__":
    test_llm_smoke()
