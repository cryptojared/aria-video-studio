"""
AriaVideo Backend — AI-Powered Video Editing Platform
FastAPI backend for the Aria Video Studio

Monetization:
- Standalone subscription: $19.99/mo (or $9.99/mo early bird)
- Free with Aria UGC membership (linked via user_id)

API Base: http://localhost:8080
Docs: http://localhost:8080/docs
"""
from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timedelta
from enum import Enum
import os
import uuid
import json
import shutil
import subprocess
import asyncio
from pathlib import Path

# Import our modules
from app.models.schemas import (
    User, UserCreate, UserResponse, Subscription, SubscriptionTier,
    Project, ProjectCreate, ProjectUpdate, ProjectStatus,
    Clip, ClipType, VideoGenerateRequest, VideoGenerateResponse,
    RenderJob, RenderStatus, RenderType
)
from app.routers import auth, projects, clips, render, subscription, webhooks

app = FastAPI(
    title="AriaVideo API",
    description="AI-Powered Video Editing Platform — Edit videos by just talking to it",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# ============== Configuration ==============
# Path to the existing aria-video-studio scripts
ARIA_STUDIO_PATH = os.path.expanduser("~/aria-video-studio/scripts")
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
UPLOAD_DIR = os.path.join(DATA_DIR, "uploads")
RENDER_DIR = os.path.join(DATA_DIR, "renders")

# Ensure directories exist
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(RENDER_DIR, exist_ok=True)

# ============== CORS ==============
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Restrict to specific domains in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============== Include Routers ==============
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(projects.router, prefix="/api/projects", tags=["Projects"])
app.include_router(clips.router, prefix="/api/clips", tags=["Clips"])
app.include_router(render.router, prefix="/api/render", tags=["Render"])
app.include_router(subscription.router, prefix="/api/subscription", tags=["Subscription"])
app.include_router(webhooks.router, prefix="/api/webhooks", tags=["Webhooks"])

# ============== Health & Status ==============
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "ok",
        "service": "AriaVideo",
        "version": "0.1.0",
        "aria_studio_path": ARIA_STUDIO_PATH,
        "scripts_available": os.path.exists(ARIA_STUDIO_PATH)
    }

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to AriaVideo API",
        "docs": "/docs",
        "features": [
            "Zero-click video editing",
            "AI-powered B-roll placement",
            "Auto captions with highlight words",
            "Shorts generation",
            "Taste-driven editing (taste.yaml)"
        ],
        "pricing": {
            "standalone": "$19.99/mo",
            "aria_ugc_member": "Free (included)"
        }
    }

# ============== File Serving ==============
@app.get("/download/{path:path}")
async def download_file(path: str):
    """Serve generated files"""
    file_path = os.path.join(RENDER_DIR, path)
    if os.path.exists(file_path):
        return FileResponse(file_path)
    raise HTTPException(status_code=404, detail="File not found")

# ============== Pricing Info (Public) ==============
@app.get("/api/pricing")
async def get_pricing():
    """Public pricing information"""
    return {
        "tiers": [
            {
                "name": "Free",
                "price": 0,
                "interval": "month",
                "videos_per_month": 2,
                "max_duration_minutes": 5,
                "features": [
                    "2 videos/month",
                    "Up to 5 min each",
                    "Basic captions",
                    "Standard quality"
                ]
            },
            {
                "name": "Starter",
                "price": 19.99,
                "interval": "month",
                "videos_per_month": 10,
                "max_duration_minutes": 15,
                "features": [
                    "10 videos/month",
                    "Up to 15 min each",
                    "Basic captions",
                    "HD quality"
                ]
            },
            {
                "name": "Pro",
                "price": 29.99,
                "interval": "month",
                "videos_per_month": "unlimited",
                "max_duration_minutes": 60,
                "features": [
                    "Unlimited videos",
                    "Up to 60 min each",
                    "AI B-roll",
                    "Highlight captions",
                    "Shorts generation",
                    "Priority rendering",
                    "Custom LUTs",
                    "Everything included!"
                ]
            }
        ],
        "aria_ugc_included": True,
        "aria_ugc_discount": "100%"
    }

# ============== Initialize Default Data ==============
def init_default_data():
    """Initialize default subscription tiers and settings"""
    config_path = os.path.join(DATA_DIR, "config.json")
    if not os.path.exists(config_path):
        config = {
            "subscription_tiers": {
                "starter": {"price": 9.99, "videos": 5, "max_duration": 10},
                "pro": {"price": 19.99, "videos": "unlimited", "max_duration": 30},
                "enterprise": {"price": 49.99, "videos": "unlimited", "max_duration": 60}
            },
            "aria_ugc_linked": True,
            "default_taste": "cinematic"
        }
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)

# Run initialization on startup
@app.on_event("startup")
async def startup_event():
    init_default_data()
    print("🎬 AriaVideo API started!")
    print(f"📁 Scripts path: {ARIA_STUDIO_PATH}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
