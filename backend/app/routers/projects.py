"""
AriaVideo - Projects Router
Handles video project management
"""
from fastapi import APIRouter, HTTPException, status, Depends, UploadFile, File
from fastapi.security import HTTPBearer
from app.models.schemas import (
    Project, ProjectCreate, ProjectUpdate, ProjectResponse,
    User, Clip, ClipResponse, ClipType
)
from pathlib import Path
import json
import uuid
import os
import shutil
import subprocess
from datetime import datetime

router = APIRouter()
security = HTTPBearer()

# Data paths
BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BACKEND_DIR / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
PROJECTS_FILE = DATA_DIR / "projects.json"
CLIPS_FILE = DATA_DIR / "clips.json"

def ensure_data_dir():
    """Ensure data directories exist"""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

def load_projects() -> dict:
    """Load projects from file"""
    ensure_data_dir()
    if not PROJECTS_FILE.exists():
        return {}
    try:
        with open(PROJECTS_FILE, 'r') as f:
            return json.load(f)
    except:
        return {}

def save_projects(projects: dict):
    """Save projects to file"""
    ensure_data_dir()
    with open(PROJECTS_FILE, 'w') as f:
        json.dump(projects, f, indent=2, default=str)

def load_clips() -> dict:
    """Load clips from file"""
    ensure_data_dir()
    if not CLIPS_FILE.exists():
        return {}
    try:
        with open(CLIPS_FILE, 'r') as f:
            return json.load(f)
    except:
        return {}

def save_clips(clips: dict):
    """Save clips to file"""
    ensure_data_dir()
    with open(CLIPS_FILE, 'w') as f:
        json.dump(clips, f, indent=2, default=str)

def get_video_duration(file_path: str) -> float:
    """Get video duration using ffprobe"""
    try:
        cmd = [
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", file_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        return float(result.stdout.strip()) if result.stdout.strip() else 0.0
    except Exception as e:
        print(f"Error getting duration: {e}")
        return 0.0

def get_current_user(token: str) -> User:
    """Get user from token (simplified)"""
    user_id = token.split("_")[0] if "_" in token else None
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    # Load users
    users_file = DATA_DIR / "users.json"
    if users_file.exists():
        with open(users_file, 'r') as f:
            users = json.load(f)
            if user_id in users:
                return User(**users[user_id])
    
    raise HTTPException(status_code=401, detail="User not found")

# ============== Project Routes ==============

@router.post("/", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    project: ProjectCreate,
    credentials: HTTPBearer = Depends(security)
):
    """Create a new video project"""
    user = get_current_user(credentials.credentials)
    
    project_id = str(uuid.uuid4())
    now = datetime.now().isoformat()
    
    project_data = {
        "id": project_id,
        "user_id": user.id,
        "name": project.name,
        "description": project.description,
        "status": "draft",
        "style_preset": project.style_preset.value,
        "custom_lut": None,
        "instructions": project.instructions,
        "aspect_ratio": project.aspect_ratio.value,
        "rendered_video_url": None,
        "shorts": [],
        "duration_seconds": None,
        "clip_count": 0,
        "created_at": now,
        "updated_at": now
    }
    
    projects = load_projects()
    projects[project_id] = project_data
    save_projects(projects)
    
    return ProjectResponse(**project_data)

@router.get("/", response_model=list[ProjectResponse])
async def list_projects(
    status: str = None,
    credentials: HTTPBearer = Depends(security)
):
    """List all projects for current user"""
    user = get_current_user(credentials.credentials)
    
    projects = load_projects()
    result = []
    
    for pid, pdata in projects.items():
        if pdata.get("user_id") == user.id:
            if status is None or pdata.get("status") == status:
                result.append(ProjectResponse(**pdata))
    
    # Sort by updated_at descending
    result.sort(key=lambda x: x.updated_at, reverse=True)
    return result

@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: str,
    credentials: HTTPBearer = Depends(security)
):
    """Get a specific project"""
    user = get_current_user(credentials.credentials)
    
    projects = load_projects()
    project_data = projects.get(project_id)
    
    if not project_data:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if project_data.get("user_id") != user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    return ProjectResponse(**project_data)

@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: str,
    update: ProjectUpdate,
    credentials: HTTPBearer = Depends(security)
):
    """Update a project"""
    user = get_current_user(credentials.credentials)
    
    projects = load_projects()
    
    if project_id not in projects:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if projects[project_id].get("user_id") != user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Update fields
    if update.name is not None:
        projects[project_id]["name"] = update.name
    if update.description is not None:
        projects[project_id]["description"] = update.description
    if update.style_preset is not None:
        projects[project_id]["style_preset"] = update.style_preset.value
    if update.aspect_ratio is not None:
        projects[project_id]["aspect_ratio"] = update.aspect_ratio.value
    if update.instructions is not None:
        projects[project_id]["instructions"] = update.instructions
    if update.status is not None:
        projects[project_id]["status"] = update.status.value
    
    projects[project_id]["updated_at"] = datetime.now().isoformat()
    save_projects(projects)
    
    return ProjectResponse(**projects[project_id])

@router.delete("/{project_id}")
async def delete_project(
    project_id: str,
    credentials: HTTPBearer = Depends(security)
):
    """Delete a project and all its clips"""
    user = get_current_user(credentials.credentials)
    
    projects = load_projects()
    
    if project_id not in projects:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if projects[project_id].get("user_id") != user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Delete associated clips
    clips = load_clips()
    clips_to_delete = [cid for cid, cdata in clips.items() 
                      if cdata.get("project_id") == project_id]
    for cid in clips_to_delete:
        del clips[cid]
    save_clips(clips)
    
    # Delete project
    del projects[project_id]
    save_projects(projects)
    
    return {"message": "Project deleted"}

# ============== Clip Routes ==============

@router.post("/{project_id}/clips", response_model=ClipResponse)
async def upload_clip(
    project_id: str,
    file: UploadFile = File(...),
    clip_type: ClipType = ClipType.TALKING_HEAD,
    credentials: HTTPBearer = Depends(security)
):
    """Upload a video clip to a project"""
    user = get_current_user(credentials.credentials)
    
    # Verify project exists and belongs to user
    projects = load_projects()
    if project_id not in projects:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if projects[project_id].get("user_id") != user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Save file
    clip_id = str(uuid.uuid4())
    file_ext = os.path.splitext(file.filename)[1] or ".mp4"
    file_name = f"{clip_id}{file_ext}"
    file_path = UPLOAD_DIR / file_name
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Get duration
    duration = get_video_duration(str(file_path))
    
    clip_data = {
        "id": clip_id,
        "project_id": project_id,
        "user_id": user.id,
        "type": clip_type.value,
        "file_name": file.filename,
        "file_path": str(file_path),
        "file_url": f"/uploads/{file_name}",
        "duration": duration,
        "thumbnail_url": None,
        "analysis": None,
        "tags": [],
        "created_at": datetime.now().isoformat()
    }
    
    # Save clip
    clips = load_clips()
    clips[clip_id] = clip_data
    save_clips(clips)
    
    # Update project clip count
    projects[project_id]["clip_count"] = projects[project_id].get("clip_count", 0) + 1
    projects[project_id]["updated_at"] = datetime.now().isoformat()
    save_projects(projects)
    
    return ClipResponse(**clip_data)

@router.get("/{project_id}/clips", response_model=list[ClipResponse])
async def list_clips(
    project_id: str,
    credentials: HTTPBearer = Depends(security)
):
    """List all clips in a project"""
    user = get_current_user(credentials.credentials)
    
    # Verify project
    projects = load_projects()
    if project_id not in projects:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if projects[project_id].get("user_id") != user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    clips = load_clips()
    result = []
    
    for cid, cdata in clips.items():
        if cdata.get("project_id") == project_id:
            result.append(ClipResponse(**cdata))
    
    return result

@router.delete("/clips/{clip_id}")
async def delete_clip(
    clip_id: str,
    credentials: HTTPBearer = Depends(security)
):
    """Delete a clip"""
    user = get_current_user(credentials.credentials)
    
    clips = load_clips()
    
    if clip_id not in clips:
        raise HTTPException(status_code=404, detail="Clip not found")
    
    if clips[clip_id].get("user_id") != user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Delete file
    file_path = clips[clip_id].get("file_path")
    if file_path and os.path.exists(file_path):
        os.remove(file_path)
    
    # Update project clip count
    project_id = clips[clip_id].get("project_id")
    projects = load_projects()
    if project_id in projects:
        projects[project_id]["clip_count"] = max(0, projects[project_id].get("clip_count", 1) - 1)
        projects[project_id]["updated_at"] = datetime.now().isoformat()
        save_projects(projects)
    
    # Delete clip
    del clips[clip_id]
    save_clips(clips)
    
    return {"message": "Clip deleted"}
