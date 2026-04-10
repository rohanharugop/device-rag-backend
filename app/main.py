from dotenv import load_dotenv
load_dotenv()

import os
print("OPENAI KEY:", os.getenv("OPENAI_API_KEY"))

from fastapi import FastAPI
from app.api.routes.device import router as device_router

app = FastAPI(
    title="Device RAG API",
    version="1.0.0"
)

# ✅ THIS LINE WAS MISSING
app.include_router(device_router)


@app.get("/")
def health_check():
    return {"status": "running"}