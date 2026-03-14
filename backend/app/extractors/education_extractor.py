import json
from pydantic import ValidationError

from app.llm_models.client import get_groq_client
from app.schemas.raw_schemas import RawJobData
from app.prompts.education_prompt import get_education_parsing_prompt
from app.schemas.education_schema import EDUCATION_SCHEMA
from app.utils.clean_json import clean_llm_json
import yaml
from pathlib import Path
CONFIG_PATH = Path(__file__).resolve().parent.parent / "config" / "llm_config.yml"

def load_config():
    with open(CONFIG_PATH, "r") as f:
        return yaml.safe_load(f)

config = load_config()

MODEL_NAME = config["llamma_model"]




def run_education_parser(job_description: str):
    # 1️⃣ Create RawJobData (only education is needed)
    raw_data = RawJobData(
        raw_education_requirements_text=job_description
    )

    # 2️⃣ Build prompt
    prompt = get_education_parsing_prompt(raw_data)

    # 3️⃣ Call LLM
    client = get_groq_client()
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {
                "role": "system",
                "content": "You are a precise education requirement parser."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0
    )

    # 4️⃣ Clean & print raw output
    content = response.choices[0].message.content
    content = clean_llm_json(content)
    data = json.loads(content)


  

    # 5️⃣ Validate JSON
    try:
        data = json.loads(content)
        print("\n✅ JSON is valid")
    except json.JSONDecodeError as e:
        print("\n❌ Invalid JSON")
        raise e

    return data



