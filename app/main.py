from dotenv import load_dotenv
load_dotenv()

from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.api.routes.device import router as device_router
from fastapi.middleware.cors import CORSMiddleware
from app.db.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()          # startup
    yield
    # shutdown (nothing to clean up for SQLite)


app = FastAPI(
    title="Device RAG API",
    version="1.0.0",
    lifespan=lifespan
)

origins = [
    "https://device-repurposing-assistant.vercel.app",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(device_router)

@app.get("/")
def health_check():
    return {"status": "running"}