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
        
    llm = Groq(
        model="llama-3.1-8b-instant",
        temperature=0.0,  # Use repeatable output for procedural answers.
        api_key=key_to_use,
    )
    return llm
