"""
AriaVideo - Render Router
Handles video rendering and integration with aria-video-studio scripts
"""
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from fastapi.security import HTTPBearer
from app.models.schemas import User, RenderJob, RenderJobResponse, RenderStatus, RenderType
from pathlib import Path
import json
import os
import subprocess
import uuid
import asyncio
from datetime import datetime

router = APIRouter()

BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BACKEND_DIR / "data"
RENDER_DIR = DATA_DIR / "renders"
RENDER_JOBS_FILE = DATA_DIR / "render_jobs.json"
PROJECTS_FILE = DATA_DIR / "projects.json"
CLIPS_FILE = DATA_DIR / "clips.json"

# Path to existing aria-video-studio scripts
ARIA_STUDIO_SCRIPTS = Path(os.path.expanduser("~/aria-video-studio/scripts"))

def ensure_data_dir():
    """Ensure data directories exist"""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    RENDER_DIR.mkdir(parents=True, exist_ok=True)

def load_render_jobs() -> dict:
    ensure_data_dir()
    if not RENDER_JOBS_FILE.exists():
        return {}
    try:
        with open(RENDER_JOBS_FILE, 'r') as f:
            return json.load(f)
    except:
        return {}

def save_render_jobs(jobs: dict):
    ensure_data_dir()
    with open(RENDER_JOBS_FILE, 'w') as f:
        json.dump(jobs, f, indent=2, default=str)

def load_projects() -> dict:
    if not PROJECTS_FILE.exists():
        return {}
    try:
        with open(PROJECTS_FILE, 'r') as f:
            return json.load(f)
    except:
        return {}

def save_projects(projects: dict):
    with open(PROJECTS_FILE, 'w') as f:
        json.dump(projects, f, indent=2, default=str)

def load_clips() -> dict:
    if not CLIPS_FILE.exists():
        return {}
    try:
        with open(CLIPS_FILE, 'r') as f:
            return json.load(f)
    except:
        return {}

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

# ============== Video Processing Functions ==============

async def run_aria_edit_script(video_path: str, output_dir: str, taste: str = "cinematic") -> dict:
    """
    Run the aria-video-studio edit.py script
    
    This integrates with the existing scripts from ~/aria-video-studio/scripts/
    """
    script_path = ARIA_STUDIO_SCRIPTS / "edit.py"
    
    if not script_path.exists():
        return {"success": False, "error": f"Script not found: {script_path}"}
    
    # Run the edit script
    cmd = [
        "python3", str(script_path),
        video_path,
        "--out-dir", output_dir,
        "--taste", taste
    ]
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=600  # 10 min timeout
        )
        
        if result.returncode == 0:
            return {
                "success": True,
                "output": result.stdout,
                "output_dir": output_dir
            }
        else:
            return {
                "success": False,
                "error": result.stderr,
                "output": result.stdout
            }
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Timeout - video processing took too long"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def find_output_files(output_dir: str) -> dict:
    """Find the output files from the edit script"""
    output_files = {
        "edited_video": None,
        "shorts": [],
        "review_html": None
    }
    
    output_path = Path(output_dir)
    if not output_path.exists():
        return output_files
    
    # Find edited video
    for f in output_path.glob("*.edited.mp4"):
        output_files["edited_video"] = str(f)
        break
    
    # Find shorts
    for f in output_path.glob("*.short*.mp4"):
        output_files["shorts"].append(str(f))
    
    # Find review HTML
    for f in output_path.glob("review.html"):
        output_files["review_html"] = str(f)
        break
    
    return output_files

# ============== Render Routes ==============

@router.post("/start", response_model=RenderJobResponse)
async def start_render(
    project_id: str,
    background_tasks: BackgroundTasks,
    render_type: RenderType = RenderType.FULL_VIDEO,
    credentials: HTTPBearer = Depends(HTTPBearer())
):
    """
    Start rendering a video project
    
    This will:
    1. Gather all clips from the project
    2. Run the aria-video-studio edit pipeline
    3. Return the rendered video(s)
    """
    user = get_current_user(credentials.credentials)
    
    # Verify project exists and belongs to user
    projects = load_projects()
    if project_id not in projects:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if projects[project_id].get("user_id") != user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    project = projects[project_id]
    
    # Get clips for this project
    clips = load_clips()
    project_clips = [c for cid, c in clips.items() if c.get("project_id") == project_id]
    
    if not project_clips:
        raise HTTPException(status_code=400, detail="No clips in project")
    
    # Create render job
    job_id = str(uuid.uuid4())
    now = datetime.now().isoformat()
    
    job_data = {
        "id": job_id,
        "project_id": project_id,
        "user_id": user.id,
        "type": render_type.value,
        "status": "queued",
        "progress": 0.0,
        "adjustment_type": None,
        "adjustment_params": None,
        "output_url": None,
        "error_message": None,
        "started_at": None,
        "completed_at": None,
        "created_at": now
    }
    
    # Save job
    jobs = load_render_jobs()
    jobs[job_id] = job_data
    save_render_jobs(jobs)
    
    # Update project status
    project["status"] = "rendering"
    projects[project_id] = project
    save_projects(projects)
    
    # Schedule background processing
    background_tasks.add_task(process_render_job, job_id)
    
    return RenderJobResponse(**job_data)

@router.get("/{job_id}", response_model=RenderJobResponse)
async def get_render_job(
    job_id: str,
    credentials: HTTPBearer = Depends(HTTPBearer())
):
    """Get render job status"""
    user = get_current_user(credentials.credentials)
    
    jobs = load_render_jobs()
    
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = jobs[job_id]
    
    if job.get("user_id") != user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    return RenderJobResponse(**job)

@router.get("/project/{project_id}", response_model=list[RenderJobResponse])
async def get_project_renders(
    project_id: str,
    credentials: HTTPBearer = Depends(HTTPBearer())
):
    """Get all render jobs for a project"""
    user = get_current_user(credentials.credentials)
    
    jobs = load_render_jobs()
    result = []
    
    for jid, jdata in jobs.items():
        if jdata.get("project_id") == project_id and jdata.get("user_id") == user.id:
            result.append(RenderJobResponse(**jdata))
    
    result.sort(key=lambda x: x.created_at, reverse=True)
    return result

async def process_render_job(job_id: str):
    """Background task to process a render job"""
    jobs = load_render_jobs()
    projects = load_projects()
    clips = load_clips()
    
    if job_id not in jobs:
        return
    
    job = jobs[job_id]
    project_id = job.get("project_id")
    
    try:
        # Update status to processing
        job["status"] = "processing"
        job["started_at"] = datetime.now().isoformat()
        jobs[job_id] = job
        save_render_jobs(jobs)
        
        # Get project clips
        project_clips = [c for cid, c in clips.items() if c.get("project_id") == project_id]
        
        if not project_clips:
            raise Exception("No clips found")
        
        # Get the main talking head (first one)
        talking_heads = [c for c in project_clips if c.get("type") == "talking_head"]
        if not talking_heads:
            talking_heads = project_clips  # Use any clip if no talking head specified
        
        main_video = talking_heads[0].get("file_path")
        
        # Create output directory
        output_dir = RENDER_DIR / project_id
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Get taste preset from project
        taste = projects[project_id].get("style_preset", "cinematic")
        
        # Run the edit script
        result = await run_aria_edit_script(main_video, str(output_dir), taste)
        
        if result.get("success"):
            # Find output files
            output_files = find_output_files(str(output_dir))
            
            # Update job
            job["status"] = "completed"
            job["progress"] = 1.0
            job["output_url"] = output_files.get("edited_video")
            job["completed_at"] = datetime.now().isoformat()
            
            # Update project
            if project_id in projects:
                projects[project_id]["status"] = "completed"
                projects[project_id]["rendered_video_url"] = output_files.get("edited_video")
                projects[project_id]["shorts"] = output_files.get("shorts", [])
                projects[project_id]["updated_at"] = datetime.now().isoformat()
        else:
            # Job failed
            job["status"] = "failed"
            job["error_message"] = result.get("error", "Unknown error")
            job["completed_at"] = datetime.now().isoformat()
            
            # Update project status
            if project_id in projects:
                projects[project_id]["status"] = "error"
                projects[project_id]["updated_at"] = datetime.now().isoformat()
        
    except Exception as e:
        job["status"] = "failed"
        job["error_message"] = str(e)
        job["completed_at"] = datetime.now().isoformat()
        
        if project_id in projects:
            projects[project_id]["status"] = "error"
            save_projects(projects)
    
    jobs[job_id] = job
    save_render_jobs(jobs)
    save_projects(projects)
