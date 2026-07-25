import os
from llama_index.llms.groq import Groq
from dotenv import load_dotenv

def get_llm_generator():
    """Create the Groq client used to generate responses."""
    # Load variables from a local .env file when it is present.
    load_dotenv()
    
    if "GROQ_API_KEY" not in os.environ:
        print("Warning: GROQ_API_KEY is not set. LLM generation may fail.")
        
    llm = Groq(
        model="llama-3.1-8b-instant",
        temperature=0.0,  # Use repeatable output for procedural answers.
    )
    return llm
