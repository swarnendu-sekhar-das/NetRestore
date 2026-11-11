import os
import logging
from llama_index.llms.groq import Groq
from dotenv import load_dotenv

logger = logging.getLogger("netrestore")

def get_llm_generator(api_key: str = None):
    """Create the Groq client used to generate responses."""
    # Load variables from a local .env file when it is present.
    load_dotenv()
    
    # If no key passed explicitly, fallback to os.environ just in case, but prefer explicitly passed key
    key_to_use = api_key or os.environ.get("GROQ_API_KEY")
    
    if not key_to_use:
        logger.warning("Warning: GROQ_API_KEY is not set. LLM generation may fail.")

    # Keep the deployment configurable, while defaulting to a model that is
    # available to this project's Groq account.
    model_name = os.environ.get("GROQ_MODEL", "qwen/qwen3.8-27b")
    context_window = int(os.environ.get("GROQ_CONTEXT_WINDOW", "32768"))
    logger.info("Initializing Groq model: %s (context_window: %d)", model_name, context_window)
        
    llm = Groq(
        model=model_name,
        temperature=0.0,  # Use repeatable output for procedural answers.
        max_tokens=512,
        context_window=context_window,
        api_key=key_to_use,
    )
    return llm
