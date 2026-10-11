"""
AriaVideo - Authentication Router
Handles user registration, login, and token management
"""
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.models.schemas import UserCreate, UserLogin, UserResponse, Token, User, SubscriptionTier
from typing import Optional
import json
import os
import uuid
from datetime import datetime
from pathlib import Path
import hashlib

router = APIRouter()
security = HTTPBearer()

# Data paths
BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BACKEND_DIR / "data"
USERS_FILE = DATA_DIR / "users.json"

def ensure_data_dir():
    """Ensure data directory exists"""
    DATA_DIR.mkdir(parents=True, exist_ok=True)

def load_users() -> dict:
    """Load users from file"""
    ensure_data_dir()
    if not USERS_FILE.exists():
        return {}
    try:
        with open(USERS_FILE, 'r') as f:
            return json.load(f)
    except:
        return {}

def save_users(users: dict):
    """Save users to file"""
    ensure_data_dir()
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=2, default=str)

def hash_password(password: str) -> str:
    """Simple password hashing"""
    return hashlib.sha256(password.encode()).hexdigest()

def create_token(user_id: str) -> str:
    """Create a simple token"""
    return f"{user_id}_{uuid.uuid4().hex}"

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    """Get current user from token"""
    token = credentials.credentials
    user_id = token.split("_")[0] if "_" in token else None
    
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    
    users = load_users()
    user_data = users.get(user_id)
    
    if not user_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return User(**user_data)

# ============== Routes ==============

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(user: UserCreate):
    """Register a new user"""
    users = load_users()
    
    # Check if email exists
    for uid, user_data in users.items():
        if user_data.get("email") == user.email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
    
    # Create user
    user_id = str(uuid.uuid4())
    now = datetime.now().isoformat()
    
    new_user = {
        "id": user_id,
        "email": user.email,
        "name": user.name,
        "password_hash": hash_password(user.password),
        "subscription_tier": "free",
        "subscription_id": None,
        "subscription_status": "inactive",
        "aria_ugc_member": False,
        "aria_ugc_user_id": None,
        "created_at": now,
        "updated_at": now
    }
    
    users[user_id] = new_user
    save_users(users)
    
    token = create_token(user_id)
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": UserResponse(
            id=new_user["id"],
            email=new_user["email"],
            name=new_user["name"],
            avatar_url=new_user.get("avatar_url"),
            subscription_tier=new_user["subscription_tier"],
            subscription_status=new_user["subscription_status"],
            aria_ugc_member=new_user["aria_ugc_member"],
            created_at=datetime.fromisoformat(new_user["created_at"])
        )
    }

@router.post("/login", response_model=Token)
async def login(user: UserLogin):
    """Login and get access token"""
    users = load_users()
    
    # Find user by email
    user_id = None
    for uid, ud in users.items():
        if ud.get("email") == user.email:
            user_id = uid
            break
    
    if not user_id or users[user_id].get("password_hash") != hash_password(user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Create token
    token = create_token(user_id)
    
    return Token(access_token=token)

@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """Get current user info"""
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        name=current_user.name,
        avatar_url=current_user.avatar_url,
        subscription_tier=current_user.subscription_tier,
        subscription_status=current_user.subscription_status,
        aria_ugc_member=current_user.aria_ugc_member,
        created_at=current_user.created_at
    )

@router.put("/me", response_model=UserResponse)
async def update_me(
    name: str = None,
    avatar_url: str = None,
    current_user: User = Depends(get_current_user)
):
    """Update current user info"""
    users = load_users()
    
    if current_user.id not in users:
        raise HTTPException(status_code=404, detail="User not found")
    
    if name:
        users[current_user.id]["name"] = name
    if avatar_url:
        users[current_user.id]["avatar_url"] = avatar_url
    
    users[current_user.id]["updated_at"] = datetime.now().isoformat()
    save_users(users)
    
    return UserResponse(**users[current_user.id])

@router.post("/link-aria-ugc")
async def link_aria_ugc(
    aria_ugc_user_id: str,
    current_user: User = Depends(get_current_user)
):
    """Link Aria UGC membership to this account"""
    users = load_users()
    
    # Update user to link Aria UGC
    users[current_user.id]["aria_ugc_member"] = True
    users[current_user.id]["aria_ugc_user_id"] = aria_ugc_user_id
    users[current_user.id]["subscription_tier"] = "pro"  # Free with Aria UGC!
    users[current_user.id]["subscription_status"] = "active"
    users[current_user.id]["updated_at"] = datetime.now().isoformat()
    
    save_users(users)
    
    return {"message": "Aria UGC membership linked successfully!", "tier": "pro"}

@router.get("/usage", response_model=dict)
async def get_usage(current_user: User = Depends(get_current_user)):
    """Get current user's usage stats"""
    # Load projects to count videos
    projects_file = DATA_DIR / "projects.json"
    videos_count = 0
    minutes_count = 0.0
    
    if projects_file.exists():
        with open(projects_file, 'r') as f:
            projects = json.load(f)
            for p in projects.values():
                if p.get("user_id") == current_user.id and p.get("status") == "completed":
                    videos_count += 1
                    minutes_count += p.get("duration_seconds", 0) / 60
    
    # Get limits based on tier
    tier_limits = {
        "free": {"videos": 2, "minutes": 5},
        "starter": {"videos": 10, "minutes": 15},
        "pro": {"videos": 0, "minutes": 0}
    }
    
    limits = tier_limits.get(current_user.subscription_tier, tier_limits["free"])
    
    return {
        "videos_this_month": videos_count,
        "minutes_this_month": round(minutes_count, 1),
        "subscription_tier": current_user.subscription_tier,
        "limit_videos": limits["videos"],
        "limit_minutes": limits["minutes"],
        "videos_remaining": -1 if limits["videos"] == 0 else max(0, limits["videos"] - videos_count),
        "minutes_remaining": -1 if limits["minutes"] == 0 else max(0, limits["minutes"] - minutes_count)
    }
