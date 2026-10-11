"""
AriaVideo - Subscription Router
Handles subscription management and Stripe integration
"""
from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer
from app.models.schemas import User, SubscriptionTier
from pathlib import Path
import json
from datetime import datetime

router = APIRouter()

BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BACKEND_DIR / "data"
USERS_FILE = DATA_DIR / "users.json"

def load_users() -> dict:
    if not USERS_FILE.exists():
        return {}
    try:
        with open(USERS_FILE, 'r') as f:
            return json.load(f)
    except:
        return {}

def save_users(users: dict):
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=2, default=str)

def get_current_user(token: str) -> User:
    user_id = token.split("_")[0] if "_" in token else None
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    users = load_users()
    if user_id in users:
        return User(**users[user_id])
    raise HTTPException(status_code=401, detail="User not found")

# ============== Subscription Routes ==============

@router.get("/")
async def get_subscription(credentials: HTTPBearer = Depends(HTTPBearer())):
    """Get current subscription info"""
    user = get_current_user(credentials.credentials)
    
    # Pricing tiers
    tiers = {
        "free": {"name": "Free", "price": 0, "videos": 2, "minutes": 5},
        "starter": {"name": "Starter", "price": 19.99, "videos": 10, "minutes": 15},
        "pro": {"name": "Pro", "price": 29.99, "videos": "unlimited", "minutes": 60}
    }
    
    current_tier = tiers.get(user.subscription_tier, tiers["free"])
    
    return {
        "tier": user.subscription_tier,
        "status": user.subscription_status,
        "aria_ugc_member": user.aria_ugc_member,
        "details": current_tier
    }

@router.post("/upgrade")
async def upgrade_subscription(
    tier: str,
    credentials: HTTPBearer = Depends(HTTPBearer())
):
    """
    Upgrade subscription tier
    Returns Stripe checkout URL (mock for now)
    """
    user = get_current_user(credentials.credentials)
    
    valid_tiers = ["starter", "pro"]
    if tier not in valid_tiers:
        raise HTTPException(status_code=400, detail="Invalid tier")
    
    # TODO: Integrate with Stripe
    # For now, return mock checkout URL
    
    prices = {
        "starter": "price_starter_xxx",
        "pro": "price_pro_xxx"
    }
    
    return {
        "checkout_url": f"https://checkout.stripe.com/mock/{prices[tier]}",
        "tier": tier,
        "message": "Stripe integration coming soon - this would redirect to Stripe checkout"
    }

@router.post("/cancel")
async def cancel_subscription(credentials: HTTPBearer = Depends(HTTPBearer())):
    """Cancel subscription at end of billing period"""
    user = get_current_user(credentials.credentials)
    
    users = load_users()
    
    if user.id in users:
        # Mark for cancellation at end of period
        users[user.id]["subscription_status"] = "canceled"
        users[user.id]["updated_at"] = datetime.now().isoformat()
        save_users(users)
    
    return {
        "message": "Subscription will be canceled at end of billing period",
        "tier": user.subscription_tier
    }

@router.get("/check-aria-ugc")
async def check_aria_ugc(aria_ugc_user_id: str):
    """
    Check if user is an Aria UGC member (called from Aria UGC)
    Returns subscription tier if member
    """
    users = load_users()
    
    for uid, user_data in users.items():
        if user_data.get("aria_ugc_user_id") == aria_ugc_user_id:
            return {
                "linked": True,
                "user_id": uid,
                "tier": user_data.get("subscription_tier", "pro"),
                "status": user_data.get("subscription_status", "active")
            }
    
    return {"linked": False}
