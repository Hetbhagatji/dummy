from fastapi import FastAPI
from app.api.v1.api import api_router
from app.events.register_handlers import register_all_handlers
app = FastAPI()

@app.on_event("startup")
async def startup_event():
    register_all_handlers()   # runs only once when app starts

app.include_router(api_router, prefix="/api/v1")
