from groq import Groq
import os
from dotenv import load_dotenv

load_dotenv()
# It's better to keep the key in env variable
# export GROQ_API_KEY="your-key"
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def call_llm(prompt: str) -> str:
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",  # or llama3-8b / mixtral
        messages=[
            {"role": "system", "content": "You are a resume parser that only outputs pure JSON."},
            {"role": "user", "content": prompt}
        ],
        temperature=0
    )

    return response.choices[0].message.content
