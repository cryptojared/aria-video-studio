"""
AriaVideo Data Models
Pydantic schemas for all data structures
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
import uuid

# ============== Enums ==============
class SubscriptionTier(str, Enum):
    FREE = "free"
    STARTER = "starter"
    PRO = "pro"

class ProjectStatus(str, Enum):
    DRAFT = "draft"
    UPLOADING = "uploading"
    PROCESSING = "processing"
    RENDERING = "rendering"
    COMPLETED = "completed"
    ERROR = "error"

class ClipType(str, Enum):
    TALKING_HEAD = "talking_head"
    BROLL = "broll"

class RenderStatus(str, Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class RenderType(str, Enum):
    FULL_VIDEO = "full_video"
    SHORT = "short"
    ADJUSTMENT = "adjustment"

class VideoStyle(str, Enum):
    CINEMATIC = "cinematic"
    WARM = "warm"
    CORPORATE = "corporate"
    CUSTOM = "custom"

class AspectRatio(str, Enum):
    LANDSCAPE = "16:9"
    PORTRAIT = "9:16"
    SQUARE = "1:1"

# ============== User Models ==============
class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: str
    name: str
    avatar_url: Optional[str] = None
    subscription_tier: SubscriptionTier = SubscriptionTier.FREE
    subscription_id: Optional[str] = None  # Stripe subscription ID
    subscription_status: str = "inactive"  # active, past_due, canceled
    aria_ugc_member: bool = False  # Linked from Aria UGC
    aria_ugc_user_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

class UserCreate(BaseModel):
    email: str
    password: str
    name: str
    referral_code: Optional[str] = None  # For Aria UGC linking

class UserLogin(BaseModel):
    email: str
    password: str

class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    avatar_url: Optional[str]
    subscription_tier: str
    subscription_status: str
    aria_ugc_member: bool
    created_at: datetime

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

# ============== Subscription Models ==============
class Subscription(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    tier: SubscriptionTier
    stripe_subscription_id: Optional[str] = None
    stripe_customer_id: Optional[str] = None
    status: str = "active"  # active, past_due, canceled, trialing
    current_period_start: Optional[datetime] = None
    current_period_end: Optional[datetime] = None
    cancel_at_period_end: bool = False
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

class SubscriptionCreate(BaseModel):
    tier: SubscriptionTier
    payment_method_id: Optional[str] = None

class SubscriptionResponse(BaseModel):
    tier: str
    status: str
    current_period_end: Optional[str]
    cancel_at_period_end: bool

# ============== Project Models ==============
class Project(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    name: str
    description: Optional[str] = None
    status: ProjectStatus = ProjectStatus.DRAFT
    
    # Style settings
    style_preset: VideoStyle = VideoStyle.CINEMATIC
    custom_lut: Optional[str] = None
    instructions: Optional[str] = None
    
    # Output
    aspect_ratio: AspectRatio = AspectRatio.LANDSCAPE
    rendered_video_url: Optional[str] = None
    shorts: List[str] = Field(default_factory=list)
    
    # Metadata
    duration_seconds: Optional[float] = None
    clip_count: int = 0
    
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None
    style_preset: VideoStyle = VideoStyle.CINEMATIC
    aspect_ratio: AspectRatio = AspectRatio.LANDSCAPE
    instructions: Optional[str] = None

class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    style_preset: Optional[VideoStyle] = None
    aspect_ratio: Optional[AspectRatio] = None
    instructions: Optional[str] = None
    status: Optional[ProjectStatus] = None

class ProjectResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    status: str
    style_preset: str
    aspect_ratio: str
    clip_count: int
    rendered_video_url: Optional[str]
    shorts: List[str]
    created_at: datetime
    updated_at: datetime

# ============== Clip Models ==============
class Clip(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    project_id: str
    user_id: str
    type: ClipType
    file_name: str
    file_path: str
    file_url: Optional[str] = None
    duration: Optional[float] = None
    thumbnail_url: Optional[str] = None
    
    # AI Analysis (for B-roll)
    analysis: Optional[Dict[str, Any]] = None
    tags: List[str] = Field(default_factory=list)
    
    created_at: datetime = Field(default_factory=datetime.now)

class ClipResponse(BaseModel):
    id: str
    project_id: str
    type: str
    file_name: str
    duration: Optional[float]
    thumbnail_url: Optional[str]
    tags: List[str]
    created_at: datetime

# ============== Render Models ==============
class RenderJob(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    project_id: str
    user_id: str
    type: RenderType
    status: RenderStatus = RenderStatus.QUEUED
    progress: float = 0.0  # 0.0 - 1.0
    
    # Adjustment details (for re-renders)
    adjustment_type: Optional[str] = None
    adjustment_params: Optional[Dict[str, Any]] = None
    
    # Output
    output_url: Optional[str] = None
    error_message: Optional[str] = None
    
    # Timing
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.now)

class RenderJobResponse(BaseModel):
    id: str
    project_id: str
    type: str
    status: str
    progress: float
    output_url: Optional[str]
    error_message: Optional[str]
    created_at: datetime
    completed_at: Optional[str]

# ============== Video Generation Request ==============
class VideoGenerateRequest(BaseModel):
    prompt: str
    style: VideoStyle = VideoStyle.CINEMATIC
    duration: int = 30
    aspect_ratio: str = "16:9"
    project_id: Optional[str] = None

class VideoGenerateResponse(BaseModel):
    video_id: str
    project_id: str
    status: str
    message: str
    estimated_time_minutes: int = 5

# ============== Webhook Models ==============
class StripeWebhook(BaseModel):
    type: str
    data: Dict[str, Any]

class AriaUGCWebhook(BaseModel):
    event: str  # subscription_created, subscription_cancelled, member_added, member_removed
    user_id: str
    aria_ugc_user_id: str
    data: Dict[str, Any]

# ============== Usage & Limits ==============
class UsageStats(BaseModel):
    user_id: str
    videos_this_month: int = 0
    minutes_this_month: float = 0.0
    subscription_tier: str
    limit_videos: int = 0
    limit_minutes: float = 0.0
    
    @property
    def videos_remaining(self) -> int:
        if self.limit_videos == 0:  # unlimited
            return -1
        return max(0, self.limit_videos - self.videos_this_month)
    
    @property
    def minutes_remaining(self) -> float:
        if self.limit_minutes == 0:  # unlimited
            return -1
        return max(0, self.limit_minutes - self.minutes_this_month)
