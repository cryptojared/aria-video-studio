"""
AriaVideo - Clips Router
Additional clip operations (analysis, tagging)
"""
from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer
from app.models.schemas import User, Clip, ClipResponse
from pathlib import Path
import json
import os

router = APIRouter()

BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BACKEND_DIR / "data"
CLIPS_FILE = DATA_DIR / "clips.json"

def load_clips() -> dict:
    if not CLIPS_FILE.exists():
        return {}
    try:
        with open(CLIPS_FILE, 'r') as f:
            return json.load(f)
    except:
        return {}

def save_clips(clips: dict):
    with open(CLIPS_FILE, 'w') as f:
        json.dump(clips, f, indent=2, default=str)

def get_current_user(token: str) -> User:
    user_id = token.split("_")[0] if "_" in token else None
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    users_file = DATA_DIR / "users.json"
    if users_file.exists():
        with open(users_file, 'r') as f:
            users = json.load(f)
            if user_id in users:
                return User(**users[user_id])
    raise HTTPException(status_code=401, detail="User not found")

# ============== Clip Analysis Routes ==============

@router.post("/{clip_id}/analyze")
async def analyze_clip(
    clip_id: str,
    credentials: HTTPBearer = Depends(HTTPBearer())
):
    """
    Analyze a B-roll clip using GPT-4o Vision
    Returns: description, tags, mood, best_for
    """
    user = get_current_user(credentials.credentials)
    
    clips = load_clips()
    
    if clip_id not in clips:
        raise HTTPException(status_code=404, detail="Clip not found")
    
    if clips[clip_id].get("user_id") != user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    clip = clips[clip_id]
    
    # For B-roll clips, run analysis
    if clip.get("type") != "broll":
        return {"message": "Analysis only needed for B-roll clips", "clip_id": clip_id}
    
    # TODO: Integrate with GPT-4o Vision
    # For now, return a placeholder
    analysis = {
        "description": "AI analysis pending - integrate OpenAI GPT-4o Vision",
        "tags": ["pending"],
        "mood": "neutral",
        "best_for": ["general"]
    }
    
    clips[clip_id]["analysis"] = analysis
    save_clips(clips)
    
    return {
        "message": "Clip analysis complete",
        "clip_id": clip_id,
        "analysis": analysis
    }

@router.put("/{clip_id}/tags")
async def update_clip_tags(
    clip_id: str,
    tags: list[str],
    credentials: HTTPBearer = Depends(HTTPBearer())
):
    """Update clip tags manually"""
    user = get_current_user(credentials.credentials)
    
    clips = load_clips()
    
    if clip_id not in clips:
        raise HTTPException(status_code=404, detail="Clip not found")
    
    if clips[clip_id].get("user_id") != user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    clips[clip_id]["tags"] = tags
    save_clips(clips)
    
    return {"message": "Tags updated", "clip_id": clip_id, "tags": tags}
