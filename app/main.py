from dotenv import load_dotenv
load_dotenv()

import os
# print("OPENAI KEY:", os.getenv("OPENAI_API_KEY"))


from fastapi import FastAPI
from app.api.routes.device import router as device_router
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Device RAG API",
    version="1.0.0"
)

origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,   # or ["*"] for quick testing
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ THIS LINE WAS MISSING
app.include_router(device_router)


@app.get("/")
def health_check():
    return {"status": "running"}