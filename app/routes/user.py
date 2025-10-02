from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
import os
import uuid
from datetime import datetime, UTC, timedelta

from ..models.database import get_db
from ..models.user import User
from ..models.api_key import APIKey
from ..models.session import Session
from ..services.redis_service import redis_service
from ..middleware.supabase_auth import (
    get_current_user as get_supabase_user,
    SupabaseUser,
)

router = APIRouter()


# Pydantic models for request/response
class UserProfileResponse(BaseModel):
    class Config:
        extra = "allow"


class UserProfileUpdate(BaseModel):
    name: Optional[str] = None
    company: Optional[str] = None
    job_title: Optional[str] = None
    timezone: Optional[str] = None


class APIKeyResponse(BaseModel):
    class Config:
        extra = "allow"


class APIKeyListResponse(BaseModel):
    api_keys: List[APIKeyResponse]


class APIKeyCreate(BaseModel):
    name: str
    permissions: List[str] = []


class APIKeyCreateResponse(BaseModel):
    id: str
    name: str
    key: str  # Only shown once during creation
    prefix: str
    permissions: List[str]


class APITokenInfoResponse(BaseModel):
    exists: bool
    id: Optional[str] = None
    prefix: Optional[str] = None
    created_at: Optional[str] = None
    last_used: Optional[str] = None
    usage_count: int = 0


class APITokenCreateResponse(BaseModel):
    id: str
    prefix: str
    key: str  # Only shown once


class SessionResponse(BaseModel):
    class Config:
        extra = "allow"


class SessionListResponse(BaseModel):
    sessions: List[SessionResponse]


class UserStatsResponse(BaseModel):
    total_calls: int
    monthly_calls: int
    quota: int
    active_keys: int
    last_activity: Optional[str]


# New models for missing endpoints
class CalculationResponse(BaseModel):
    id: str
    company: str
    calculation_data: dict
    result: dict
    version: str
    created_at: str


class CalculationListResponse(BaseModel):
    calculations: List[CalculationResponse]
    total: int
    page: int
    limit: int


class PackageResponse(BaseModel):
    id: str
    company: str
    package_data: dict
    file_url: Optional[str]
    file_size: Optional[int]
    created_at: str


class PackageListResponse(BaseModel):
    packages: List[PackageResponse]
    total: int
    page: int
    limit: int


class NotificationResponse(BaseModel):
    id: str
    title: str
    message: str
    type: str
    read: bool
    created_at: str


class NotificationListResponse(BaseModel):
    notifications: List[NotificationResponse]
    unread_count: int


class UserPreferencesResponse(BaseModel):
    units: str = "metric"
    timezone: str = "UTC"
    email_notifications: bool = True
    default_company: Optional[str] = None
    default_grid_region: str = "US_default"


class UserPreferencesUpdate(BaseModel):
    units: Optional[str] = None
    timezone: Optional[str] = None
    email_notifications: Optional[bool] = None
    default_company: Optional[str] = None
    default_grid_region: Optional[str] = None


class ActivityResponse(BaseModel):
    id: str
    action: str
    description: str
    metadata: Optional[dict]
    created_at: str


class ActivityListResponse(BaseModel):
    activities: List[ActivityResponse]
    total: int


async def get_db_user(
    supa_user: SupabaseUser = Depends(get_supabase_user),
    db: Session = Depends(get_db)
):
    """Get or create DB user based on Supabase-authenticated user"""
    user = db.query(User).filter(User.email == supa_user.email).first()
    if not user:
        user = User(
            email=supa_user.email,
            name=supa_user.name or supa_user.email.split("@")[0],
            avatar_url=supa_user.avatar_url,
            email_verified=supa_user.email_verified,
            auth_provider="supabase",
            auth_provider_id=supa_user.id,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    else:
        updated = False
        if user.auth_provider != "supabase":
            user.auth_provider = "supabase"
            updated = True
        if user.auth_provider_id != supa_user.id:
            user.auth_provider_id = supa_user.id
            updated = True
        if supa_user.name and user.name != supa_user.name:
            user.name = supa_user.name
            updated = True
        if user.avatar_url != supa_user.avatar_url:
            user.avatar_url = supa_user.avatar_url
            updated = True
        if user.email_verified != supa_user.email_verified:
            user.email_verified = supa_user.email_verified
            updated = True
        if updated:
            db.commit()

    user.update_last_login()
    db.commit()
    return user

@router.get("/profile", response_model=UserProfileResponse)
async def get_user_profile(current_user: User = Depends(get_db_user)):
    """Get current user profile with Redis caching"""
    user_id = current_user.id

    # Try to get from cache first
    try:
        cached_profile = redis_service.get_cached_user_profile(user_id)
        if cached_profile:
            return UserProfileResponse(**cached_profile)
    except Exception as e:
        # If Redis fails, continue without caching
        print(f"Redis cache failed: {e}")

    # If not in cache, get from database
    profile_data = current_user.to_dict()
    
    # Ensure all required fields are present
    profile_data.update({
        'plan': profile_data.get('plan') or 'FREE',
        'email_verified': profile_data.get('email_verified', False),
        'created_at': profile_data.get('created_at') or datetime.now(UTC).isoformat(),
        'updated_at': profile_data.get('updated_at') or datetime.now(UTC).isoformat()
    })

    # Cache the profile for 10 minutes (600 seconds)
    try:
        redis_service.cache_user_profile(user_id, profile_data, ttl_seconds=600)
    except Exception as e:
        # If Redis fails, continue without caching
        print(f"Redis cache write failed: {e}")

    return UserProfileResponse(**profile_data)

@router.get("/stats", response_model=UserStatsResponse)
async def get_user_stats(current_user: User = Depends(get_db_user), db: Session = Depends(get_db)):
    """Get user usage statistics"""
    from sqlalchemy import func

    # Get all active API keys for the user
    api_keys = db.query(APIKey).filter(
        APIKey.user_id == current_user.id,
        APIKey.is_active == True
    ).all()

    # Calculate total calls across all API keys
    total_calls = sum(key.usage_count for key in api_keys if key.usage_count)

    # Calculate monthly calls (last 30 days)
    # For now, we'll use total calls as monthly calls since we don't have detailed usage logs
    monthly_calls = total_calls

    # Get quota based on user plan
    plan_quotas = {
        'FREE': 1000,
        'BASIC': 5000,
        'PREMIUM': 25000,
        'ENTERPRISE': 100000
    }
    quota = plan_quotas.get(current_user.plan or 'FREE', 1000)

    # Count active keys
    active_keys = len(api_keys)

    # Get last activity (most recent last_used across all keys or last_login)
    last_activity = None
    if api_keys:
        recent_keys_with_usage = [k for k in api_keys if k.last_used]
        if recent_keys_with_usage:
            recent_key = max(recent_keys_with_usage, key=lambda k: k.last_used)
            last_activity = recent_key.last_used.isoformat()
    
    # Fallback to last login if no API key usage
    if not last_activity and current_user.last_login:
        last_activity = current_user.last_login.isoformat()

    return UserStatsResponse(
        total_calls=total_calls,
        monthly_calls=monthly_calls,
        quota=quota,
        active_keys=active_keys,
        last_activity=last_activity
    )

@router.put("/profile", response_model=UserProfileResponse)
async def update_user_profile(
    profile_data: UserProfileUpdate,
    current_user: User = Depends(get_db_user),
    db: Session = Depends(get_db)
):
    """Update user profile"""
    # Update fields if provided
    if profile_data.name is not None:
        current_user.name = profile_data.name
    if profile_data.company is not None:
        current_user.company = profile_data.company
    if profile_data.job_title is not None:
        current_user.job_title = profile_data.job_title
    if profile_data.timezone is not None:
        current_user.timezone = profile_data.timezone

    db.commit()
    db.refresh(current_user)

    # Invalidate cache after profile update
    redis_service.invalidate_user_profile_cache(current_user.id)

    return UserProfileResponse(**current_user.to_dict())

@router.post("/avatar")
async def upload_avatar(
    file: UploadFile = File(...),
    current_user: User = Depends(get_db_user),
    db: Session = Depends(get_db)
):
    """Upload user avatar"""
    # Validate file type
    allowed_types = ["image/jpeg", "image/png", "image/gif", "image/webp"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only image files (JPEG, PNG, GIF, WebP) are allowed"
        )
    
    # Validate file size (max 5MB)
    file_size = 0
    content = await file.read()
    file_size = len(content)
    
    if file_size > 5 * 1024 * 1024:  # 5MB
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File size must be less than 5MB"
        )
    
    # Generate unique filename
    file_extension = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    
    # Create uploads directory if it doesn't exist
    upload_dir = "uploads/avatars"
    os.makedirs(upload_dir, exist_ok=True)
    
    # Save file
    file_path = os.path.join(upload_dir, unique_filename)
    with open(file_path, "wb") as f:
        f.write(content)
    
    # Update user avatar URL
    avatar_url = f"https://api.envoyou.com/{upload_dir}/{unique_filename}"
    current_user.avatar_url = avatar_url
    
    db.commit()
    
    return {
        "message": "Avatar uploaded successfully",
        "avatar_url": avatar_url
    }

@router.get("/api-keys", response_model=APIKeyListResponse)
async def get_api_keys(current_user: User = Depends(get_db_user), db: Session = Depends(get_db)):
    """Get all API keys for current user"""
    api_keys = db.query(APIKey).filter(
        APIKey.user_id == current_user.id,
        APIKey.is_active == True
    ).all()
    
    # Convert to dict and ensure all required fields are present
    api_key_responses = []
    for key in api_keys:
        key_dict = key.to_dict()
        # Ensure all required fields are present with defaults
        api_key_responses.append(APIKeyResponse(
            id=key_dict.get('id', ''),
            name=key_dict.get('name', 'Unnamed Key'),
            prefix=key_dict.get('prefix', 'sk-xxxxxxxxxx'),
            permissions=key_dict.get('permissions', []),
            is_active=key_dict.get('is_active', True),
            last_used=key_dict.get('last_used'),
            usage_count=key_dict.get('usage_count', 0),
            created_at=key_dict.get('created_at', '')
        ))
    
    return APIKeyListResponse(api_keys=api_key_responses)

@router.post("/api-keys", response_model=APIKeyCreateResponse)
async def create_api_key(
    key_data: APIKeyCreate,
    current_user: User = Depends(get_db_user),
    db: Session = Depends(get_db)
):
    """Create a new API key"""
    # Create new API key
    api_key = APIKey(
        user_id=current_user.id,
        name=key_data.name,
        permissions=key_data.permissions
    )
    
    # Generate the actual key (this is the only time we see the full key)
    actual_key = api_key._generate_key()
    
    db.add(api_key)
    db.commit()
    db.refresh(api_key)
    
    # Send API key creation notification
    try:
        from app.utils.email import email_service
        key_preview = f"{actual_key[:8]}...{actual_key[-4:]}"
        email_service.send_api_key_created_notification(
            current_user.email, current_user.name, key_data.name, key_preview
        )
    except Exception as e:
        # Don't fail API key creation if email fails
        print(f"API key creation email failed: {e}")
    
    return APIKeyCreateResponse(
        id=api_key.id,
        name=api_key.name,
        key=actual_key,  # Only shown once
        prefix=api_key.prefix,
        permissions=key_data.permissions
    )

@router.delete("/api-keys/{key_id}")
async def delete_api_key(
    key_id: str,
    current_user: User = Depends(get_db_user),
    db: Session = Depends(get_db)
):
    """Delete an API key"""
    api_key = db.query(APIKey).filter(
        APIKey.id == key_id,
        APIKey.user_id == current_user.id
    ).first()
    
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )
    
    # Soft delete by marking as inactive
    api_key.is_active = False
    db.commit()
    
    return {
        "message": "API key deleted successfully"
    }

@router.get("/api-token", response_model=APITokenInfoResponse)
async def get_api_token_info(current_user: User = Depends(get_db_user), db: Session = Depends(get_db)):
    """Get the user's personal API token info (no full key returned)."""
    personal_key = db.query(APIKey).filter(
        APIKey.user_id == current_user.id,
        APIKey.is_active == True,
        APIKey.name == "Personal Token"
    ).first()

    if not personal_key:
        return APITokenInfoResponse(exists=False, usage_count=0)

    key_dict = personal_key.to_dict()
    return APITokenInfoResponse(
        exists=True,
        id=key_dict["id"],
        prefix=key_dict["prefix"],
        created_at=key_dict["created_at"],
        last_used=key_dict["last_used"],
        usage_count=key_dict["usage_count"],
    )

@router.post("/api-token", response_model=APITokenCreateResponse)
async def create_api_token(current_user: User = Depends(get_db_user), db: Session = Depends(get_db)):
    """Create a new personal API token. If exists, return 409 to force explicit regeneration."""
    existing = db.query(APIKey).filter(
        APIKey.user_id == current_user.id,
        APIKey.is_active == True,
        APIKey.name == "Personal Token",
    ).first()

    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="API token already exists. Use regenerate to rotate token.")

    new_key = APIKey(user_id=current_user.id, name="Personal Token", permissions=["read"])
    full_token = new_key._generate_key()
    db.add(new_key)
    db.commit()
    db.refresh(new_key)

    return APITokenCreateResponse(id=new_key.id, prefix=new_key.prefix, key=full_token)

@router.post("/api-token/regenerate", response_model=APITokenCreateResponse)
async def regenerate_api_token(current_user: User = Depends(get_db_user), db: Session = Depends(get_db)):
    """Regenerate (rotate) the user's personal API token, returning the new token."""
    personal_key = db.query(APIKey).filter(
        APIKey.user_id == current_user.id,
        APIKey.is_active == True,
        APIKey.name == "Personal Token"
    ).first()

    if not personal_key:
        # If none exists, create one
        personal_key = APIKey(user_id=current_user.id, name="Personal Token", permissions=["read"])
        full_token = personal_key._generate_key()
        db.add(personal_key)
    else:
        # Rotate existing key in place
        full_token = personal_key._generate_key()

    db.commit()
    db.refresh(personal_key)

    return APITokenCreateResponse(id=personal_key.id, prefix=personal_key.prefix, key=full_token)

@router.get("/sessions", response_model=SessionListResponse)
async def get_user_sessions(
    current_user: User = Depends(get_db_user),
    db: Session = Depends(get_db)
):
    """Get all active sessions for current user"""
    # For now, return mock session data since Session model might not be fully implemented
    mock_sessions = [
        SessionResponse(
            id="current_session",
            device_info="Web Browser",
            ip_address="127.0.0.1",
            location="Local",
            last_active=datetime.now(UTC).isoformat(),
            created_at=current_user.last_login.isoformat() if current_user.last_login else current_user.created_at.isoformat(),
            current=True
        )
    ]
    
    return SessionListResponse(sessions=mock_sessions)

@router.delete("/sessions/{session_id}")
async def delete_user_session(
    session_id: str,
    current_user: User = Depends(get_db_user),
    db: Session = Depends(get_db)
):
    """Delete a specific session"""
    session = db.query(Session).filter(
        Session.id == session_id,
        Session.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    db.delete(session)
    db.commit()
    
    return {"message": "Session deleted successfully"}

# Plan endpoint
@router.get("/plan")
async def get_user_plan(current_user: User = Depends(get_db_user)):
    """Get current user's plan"""
    return {"plan": current_user.plan or "FREE"}

@router.get("/activity", response_model=ActivityListResponse)
async def get_user_activity(
    limit: int = 20,
    current_user: User = Depends(get_db_user),
    db: Session = Depends(get_db)
):
    """Get user activity log"""
    # For now, we'll generate activity from API key usage and profile updates
    activities = []
    
    # Get API key activities
    api_keys = db.query(APIKey).filter(
        APIKey.user_id == current_user.id
    ).order_by(APIKey.created_at.desc()).limit(limit // 2).all()
    
    for key in api_keys:
        activities.append(ActivityResponse(
            id=f"api_key_{key.id}",
            action="api_key_created",
            description=f"Created API key '{key.name}'",
            metadata={"key_name": key.name, "key_id": key.id},
            created_at=key.created_at.isoformat()
        ))
        
        if key.last_used:
            activities.append(ActivityResponse(
                id=f"api_key_used_{key.id}",
                action="api_key_used",
                description=f"Used API key '{key.name}' ({key.usage_count} total uses)",
                metadata={"key_name": key.name, "usage_count": key.usage_count},
                created_at=key.last_used.isoformat()
            ))
    
    # Add profile activity
    activities.append(ActivityResponse(
        id=f"profile_login_{current_user.id}",
        action="user_login",
        description="Logged into dashboard",
        metadata={"email": current_user.email},
        created_at=current_user.last_login.isoformat() if current_user.last_login else current_user.created_at.isoformat()
    ))
    
    # Sort by created_at descending and limit
    activities.sort(key=lambda x: x.created_at, reverse=True)
    activities = activities[:limit]
    
    return ActivityListResponse(
        activities=activities,
        total=len(activities)
    )
