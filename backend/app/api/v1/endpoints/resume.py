from fastapi import APIRouter,UploadFile,File
from app.services.resume_service import ResumeService
from app.llm_models.grok_llm import GroqLLM
from app.llm_models.ollama_lllm import OllamaLLM
import yaml
from pathlib import Path
from app.llm_models.llm_factory import get_llm
from typing import List
router = APIRouter()
import tempfile
import os
from app.services.s3_service import S3Service
import tempfile
import os
from fastapi import APIRouter
from app.services.s3_service import S3Service
# from app.services.docling_service import extract_text_from_pdf  # your existing util

router = APIRouter()
s3_service = S3Service()

router = APIRouter()
s3_service = S3Service()
BASE_DIR = Path(__file__).resolve().parents[4]


from docling.document_converter import DocumentConverter

_converter = DocumentConverter()  # ← initialize once

def extract_text_from_pdf(file_path: str) -> str:
    doc = _converter.convert(file_path).document
    text = doc.export_to_markdown()
    return text

# resume.py -> endpoints -> v1 -> api -> app -> backend

CONFIG_PATH = BASE_DIR / "app" / "config" / "llm_config.yml"

with open(CONFIG_PATH, "r") as f:
    config = yaml.safe_load(f)  

llm_instance=get_llm(config["llm_model"])
resume_service=ResumeService(llm=llm_instance)

@router.post("/extract-text")
async def extract_text(file: UploadFile = File(...)):
    response=resume_service.extract_text(file)
    return response

@router.post("/parse-resume")
def parse_resume(file: UploadFile = File(...)):
    return resume_service.parse_resume(file)

# ── New API: upload resumes for a specific job ───────────────────────────────
@router.post("/upload-resumes/{job_id}")
def upload_resumes(
    job_id: str
):
    return resume_service.upload_resumes_for_job(job_id=job_id)


@router.post("/extract-resumes/{job_id}")
def extract_resumes(job_id: str):
    prefix = f"{job_id}/resumes/"
    pdf_keys = [obj["Key"] for obj in s3_service.list_files(prefix) if obj["Key"].endswith(".pdf")]

    results = []

    for pdf_key in pdf_keys:
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp_path = tmp.name

        s3_service.download_file(pdf_key, tmp_path)

        text = extract_text_from_pdf(tmp_path)  # ← your docling extractor

        os.remove(tmp_path)

        txt_key = pdf_key.replace(".pdf", ".txt")
        s3_service.upload_text(text, txt_key)

        results.append({"pdf": pdf_key, "txt": txt_key})

    return {"job_id": job_id, "processed": results}