import json
from pathlib import Path
def write_json(path: Path, data: dict) -> None: 
    print(f"[write_json] Writing to: {path}")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, default=str)