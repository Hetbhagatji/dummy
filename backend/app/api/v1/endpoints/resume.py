from fastapi import APIRouter,UploadFile,File
from app.services.resume_service import ResumeService
from app.llm_models.grok_llm import GroqLLM
from app.llm_models.ollama_lllm import OllamaLLM
import yaml
from pathlib import Path
from app.llm_models.llm_factory import get_llm
router = APIRouter()

BASE_DIR = Path(__file__).resolve().parents[4]
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

@router.post("/parse")
def parse(resume_text:str):
    return resume_service.parse(resume_text=resume_text)
@router.post("/parse-skills")
def parse_skills(resume_text:str):
    return resume_service.parse_skills(resume_text=resume_text)
