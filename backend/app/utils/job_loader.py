import json

from pathlib import Path
BASE_DIR = Path(__file__).resolve().parents[1]
CONFIG_PATH = BASE_DIR / "extractors" / "jobs.json"
def get_job_text(job_id: str, file_path: str = CONFIG_PATH):
    try:
        with open(file_path, "r") as f:
            data = json.load(f)

        return data.get(job_id)

    except FileNotFoundError:
        return None
