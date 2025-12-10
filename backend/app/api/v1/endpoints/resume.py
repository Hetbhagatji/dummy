from fastapi import APIRouter,UploadFile,File
from app.services.resume_service import ResumeService
from app.llm_models.grok_llm import GroqLLM
from app.llm_models.ollama_lllm import OllamaLLM

router = APIRouter()

llm_instance=GroqLLM()
resume_service=ResumeService(llm=llm_instance)


@router.post("/extract-text")
async def extract_text(file: UploadFile = File(...)):
    response=resume_service.extract_text(file)
    print(response)
    return response

@router.post("/parse-resume")
def parse_resume(file: UploadFile = File(...)):
    return resume_service.parse_resume(file)

@router.post("/parse")
def parse(resume_text:str):
    return resume_service.parse(resume_text=resume_text)


    


