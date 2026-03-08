
from pathlib import Path

OUTPUT_BASE_DIR = "output"

def _flag_path(drive_id: str) -> Path:
    return Path(OUTPUT_BASE_DIR) / drive_id / "status.txt"

def set_job_flag(drive_id: str, value: int) -> None:
    """Write 0 (running) or 1 (done) to the flag file."""
    path = _flag_path(drive_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(str(value))

def get_job_flag(drive_id: str) -> int | None:
    """Returns 0, 1, or None if file doesn't exist yet."""
    path = _flag_path(drive_id)
    if not path.exists():
        return None
    return int(path.read_text().strip())