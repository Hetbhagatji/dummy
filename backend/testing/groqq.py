from groq import Groq
from dotenv import load_dotenv
import os
import json

# Load environment variables
load_dotenv()

# Initialize Groq client
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

def call_groq(prompt: str, model: str = "llama-3.3-70b-versatile") -> str:
    """Call Groq API and return the response content."""
    chat_completion = client.chat.completions.create(
        messages=[
            {"role": "user", "content": prompt}
        ],
        model=model,
        response_format={"type": "json_object"}  # Ensure JSON output
    )
    return chat_completion.choices[0].message.content
