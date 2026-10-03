from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager

from app.config import settings
from app.db import init_db
from app.routes.notes import router as notes_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize PostgreSQL DB tables on startup
    init_db()
    yield

app = FastAPI(
    title="Gnani Audio Notes API",
    description="FastAPI Backend for Gnani Audio Notes Take-home Platform",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve local media files for playback
app.mount("/media", StaticFiles(directory=str(settings.STORAGE_DIR)), name="media")

# Include notes API routes
app.include_router(notes_router)

@app.get("/api/health")
def health_check():
    return {"status": "ok", "service": "Gnani Audio Notes API"}
