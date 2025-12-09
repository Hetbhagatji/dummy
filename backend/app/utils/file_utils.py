import os
import shutil

def save_upload_file(upload_file, upload_dir: str) -> str:
    os.makedirs(upload_dir, exist_ok=True)

    file_path = os.path.join(upload_dir, upload_file.filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(upload_file.file, buffer)

    return file_path
