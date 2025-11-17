"""
FastAPI backend for Audish scheduling web UI.
"""
import os
import tempfile
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from routes import router

# Create temp directory for file uploads and outputs
TEMP_DIR = tempfile.mkdtemp(prefix="audish_")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle."""
    # Startup
    print(f"Temporary directory: {TEMP_DIR}")
    yield
    # Shutdown - cleanup temp files
    import shutil
    if os.path.exists(TEMP_DIR):
        shutil.rmtree(TEMP_DIR)
        print(f"Cleaned up temporary directory: {TEMP_DIR}")


app = FastAPI(
    title="Audish Scheduling API",
    description="API for scheduling music auditions",
    version="0.1.0",
    lifespan=lifespan,
)

# Configure CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router, prefix="/api")

# Store temp directory in app state
app.state.temp_dir = TEMP_DIR


@app.get("/")
async def root():
    """Health check endpoint."""
    return {"status": "ok", "message": "Audish API is running"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
