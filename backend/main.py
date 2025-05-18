from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
from pathlib import Path

# import your routers here
from api import data, status
from core.config import settings

app = FastAPI()

# Include your routers here
app.include_router(data.router, prefix="/data", tags=["data"])
app.include_router(status.router, prefix="/status", tags=["status"])

# CORS middleware configuration
# This allows your frontend to communicate with the backend
# without CORS issues. Adjust the allowed origins as necessary.
# For example, you can set it to ["http://localhost:5173"] if you're using Vite.
# You can also use ["*"] to allow all origins, but this is not recommended for production.
# Be cautious with CORS settings in production environments.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # or ["http://localhost:5173"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
# Create directories if they don't exist
thumbnails_dir = settings.DOWNLOAD_DIR / "thumbnails"
knobs_dir = settings.DOWNLOAD_DIR / "knobs"
os.makedirs(thumbnails_dir, exist_ok=True)
os.makedirs(knobs_dir, exist_ok=True)

# Mount static directories
app.mount("/static/thumbnails", StaticFiles(directory=thumbnails_dir), name="thumbnails")
app.mount("/static/knobs", StaticFiles(directory=knobs_dir), name="knobs")

# Example route for testing
# This is a simple root endpoint that returns a JSON response.
@app.get("/")
def read_root():
    return {"Hello": "World", "name": "KnobGallery++", "version": "1.0.0"}
