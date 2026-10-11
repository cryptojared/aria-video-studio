"""
AriaVideo - Webhooks Router
Handles Stripe webhooks and Aria UGC membership webhooks
"""
from fastapi import APIRouter, Request, HTTPException, status
from pydantic import BaseModel
from pathlib import Path
import json
import hmac
import hashlib

router = APIRouter()

BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BACKEND_DIR / "data"
USERS_FILE = DATA_DIR / "users.json"

# For demo - in production, use environment variable
STRIPE_WEBHOOK_SECRET = "whsec_demo_secret"

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

# ============== Stripe Webhooks ==============

class StripeWebhookEvent(BaseModel):
    type: str
    data: dict

@router.post("/stripe")
async def handle_stripe_webhook(request: Request):
    """
    Handle Stripe webhook events
    
    Supported events:
    - checkout.session.completed
    - customer.subscription.created
    - customer.subscription.updated
    - customer.subscription.deleted
    - invoice.payment_succeeded
    - invoice.payment_failed
    """
    # Get raw body for signature verification
    body = await request.body()
    
    # TODO: Verify Stripe signature in production
    # signature = request.headers.get("stripe-signature")
    # verify_stripe_signature(body, signature, STRIPE_WEBHOOK_SECRET)
    
    try:
        event = await request.json()
    except:
        raise HTTPException(status_code=400, detail="Invalid JSON")
    
    event_type = event.get("type")
    event_data = event.get("data", {}).get("object", {})
    
    users = load_users()
    
    # Handle different event types
    if event_type == "checkout.session.completed":
        # New subscription created via Stripe Checkout
        customer_id = event_data.get("customer")
        subscription_id = event_data.get("subscription")
        
        # Find user by Stripe customer ID and update
        for uid, user_data in users.items():
            if user_data.get("stripe_customer_id") == customer_id:
                users[uid]["subscription_id"] = subscription_id
                users[uid]["subscription_status"] = "active"
                # Determine tier from price
                # In production, look up price_id
                break
        
    elif event_type == "customer.subscription.updated":
        subscription_id = event_data.get("id")
        status_str = event_data.get("status")  # active, past_due, canceled, etc.
        
        # Update user subscription
        for uid, user_data in users.items():
            if user_data.get("subscription_id") == subscription_id:
                users[uid]["subscription_status"] = status_str
                break
                
    elif event_type == "customer.subscription.deleted":
        subscription_id = event_data.get("id")
        
        # Downgrade to free
        for uid, user_data in users.items():
            if user_data.get("subscription_id") == subscription_id:
                users[uid]["subscription_id"] = None
                users[uid]["subscription_tier"] = "free"
                users[uid]["subscription_status"] = "inactive"
                break
                
    elif event_type == "invoice.payment_failed":
        subscription_id = event_data.get("subscription")
        
        # Mark as past_due
        for uid, user_data in users.items():
            if user_data.get("subscription_id") == subscription_id:
                users[uid]["subscription_status"] = "past_due"
                break
    
    save_users(users)
    
    return {"received": True, "event_type": event_type}

# ============== Aria UGC Webhooks ==============

class AriaUGCEvent(BaseModel):
    event: str  # member_added, member_removed, subscription_created, subscription_cancelled
    aria_ugc_user_id: str
    user_email: str = None
    user_name: str = None

@router.post("/aria-ugc")
async def handle_aria_ugc_webhook(event: AriaUGCEvent):
    """
    Handle Aria UGC membership events
    
    This allows Aria UGC to tell AriaVideo when a user becomes
    a member (so they get free access)
    """
    users = load_users()
    
    if event.event == "member_added":
        # Find user by email and link to Aria UGC
        found = False
        for uid, user_data in users.items():
            if user_data.get("email") == event.user_email:
                users[uid]["aria_ugc_member"] = True
                users[uid]["aria_ugc_user_id"] = event.aria_ugc_user_id
                users[uid]["subscription_tier"] = "pro"  # Free with Aria UGC!
                users[uid]["subscription_status"] = "active"
                found = True
                break
        
        if not found:
            # Could create new user or return error
            return {"message": "User not found", "linked": False}
        
        save_users(users)
        return {"message": "Aria UGC membership linked", "linked": True}
    
    elif event.event == "member_removed":
        # Remove Aria UGC benefits
        for uid, user_data in users.items():
            if user_data.get("aria_ugc_user_id") == event.aria_ugc_user_id:
                users[uid]["aria_ugc_member"] = False
                users[uid]["aria_ugc_user_id"] = None
                # Downgrade to free (or keep their paid tier if they have one)
                if not users[uid].get("subscription_id"):
                    users[uid]["subscription_tier"] = "free"
                    users[uid]["subscription_status"] = "inactive"
                break
        
        save_users(users)
        return {"message": "Aria UGC membership removed", "linked": False}
    
    return {"message": "Event received"}

# ============== Health Check ==============

@router.get("/health")
async def webhook_health():
    """Health check for webhook endpoints"""
    return {"status": "ok", "service": "AriaVideo Webhooks"}
