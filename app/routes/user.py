from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
import os
import uuid
from datetime import datetime, UTC

from ..models.database import get_db
from ..models.user import User
from ..models.api_key import APIKey
from ..models.session import Session
from ..utils.jwt import verify_token
from ..services.redis_service import redis_service

router = APIRouter()
security = HTTPBearer()

# Pydantic models for request/response
class UserProfileUpdate(BaseModel):
    name: Optional[str] = None
    company: Optional[str] = None
    job_title: Optional[str] = None
    timezone: Optional[str] = None

class UserProfileResponse(BaseModel):
    id: str
    email: str
    name: str
    company: Optional[str]
    job_title: Optional[str]
    avatar_url: Optional[str]
    timezone: str
    email_verified: bool
    two_factor_enabled: bool
    created_at: Optional[str]
    last_login: Optional[str]

class APIKeyCreate(BaseModel):
    name: str
    permissions: list = ["read"]

class APIKeyResponse(BaseModel):
    id: str
    name: str
    prefix: str
    created_at: Optional[str]
    last_used: Optional[str]
    usage_count: int
    permissions: list

class APIKeyListResponse(BaseModel):
    api_keys: list[APIKeyResponse]

class APIKeyCreateResponse(BaseModel):
    id: str
    name: str
    key: str  # Only shown once during creation
    prefix: str
    permissions: list

class SessionResponse(BaseModel):
    id: str
    device: str
    ip: str
    location: str
    last_active: Optional[str]
    current: bool

class SessionListResponse(BaseModel):
    sessions: list[SessionResponse]

class UserStatsResponse(BaseModel):
    total_calls: int
    monthly_calls: int
    quota: int
    active_keys: int
    last_activity: Optional[str]

# Dependency to get current user
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Get current authenticated user"""
    token_data = verify_token(credentials.credentials, "access")
    if not token_data or not token_data.email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token"
        )
    
    user = db.query(User).filter(User.email == token_data.email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    # Update last login
    user.update_last_login()
    db.commit()
    
    return user

@router.get("/profile", response_model=UserProfileResponse)
async def get_user_profile(current_user: User = Depends(get_current_user)):
    """Get current user profile with Redis caching"""
    user_id = current_user.id

    # Try to get from cache first
    cached_profile = redis_service.get_cached_user_profile(user_id)
    if cached_profile:
        return UserProfileResponse(**cached_profile)

    # If not in cache, get from database
    profile_data = current_user.to_dict()

    # Cache the profile for 10 minutes (600 seconds)
    redis_service.cache_user_profile(user_id, profile_data, ttl_seconds=600)

    return UserProfileResponse(**profile_data)

@router.get("/stats", response_model=UserStatsResponse)
async def get_user_stats(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get user usage statistics"""
    from sqlalchemy import func
    from datetime import datetime, timedelta

    # Get all active API keys for the user
    api_keys = db.query(APIKey).filter(
        APIKey.user_id == current_user.id,
        APIKey.is_active == True
    ).all()

    # Calculate total calls across all API keys
    total_calls = sum(key.usage_count for key in api_keys)

    # Calculate monthly calls (last 30 days)
    thirty_days_ago = datetime.now(UTC) - timedelta(days=30)
    monthly_calls = 0
    # For now, we'll use total calls as monthly calls since we don't have detailed usage logs
    # In a real implementation, you'd have a usage_logs table to track this properly
    monthly_calls = total_calls

    # Get quota (this could be based on user plan, for now using a default)
    quota = 5000  # Default quota

    # Count active keys
    active_keys = len(api_keys)

    # Get last activity (most recent last_used across all keys)
    last_activity = None
    if api_keys:
        recent_key = max(api_keys, key=lambda k: k.last_used or datetime.min)
        if recent_key.last_used:
            last_activity = recent_key.last_used.isoformat()

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
    current_user: User = Depends(get_current_user),
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
    current_user: User = Depends(get_current_user),
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
async def get_api_keys(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get all API keys for current user"""
    api_keys = db.query(APIKey).filter(
        APIKey.user_id == current_user.id,
        APIKey.is_active == True
    ).all()
    
    return APIKeyListResponse(api_keys=[APIKeyResponse(**key.to_dict()) for key in api_keys])

@router.post("/api-keys", response_model=APIKeyCreateResponse)
async def create_api_key(
    key_data: APIKeyCreate,
    current_user: User = Depends(get_current_user),
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
        api_key_preview = f"{actual_key[:8]}...{actual_key[-4:]}"
        email_service.send_api_key_created_notification(
            current_user.email, current_user.name, key_data.name, api_key_preview
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
    current_user: User = Depends(get_current_user),
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

@router.get("/sessions", response_model=SessionListResponse)
async def get_user_sessions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all active sessions for current user"""
    sessions = db.query(Session).filter(
        Session.user_id == current_user.id,
        Session.expires_at > datetime.now(UTC)
    ).order_by(Session.last_active.desc()).all()
    
    session_responses = []
    for session in sessions:
        session_dict = session.to_dict()
        # Mark current session (this would need to be determined from request context)
        # For now, we'll mark the most recent one as current
        session_dict["current"] = False
        session_responses.append(SessionResponse(**session_dict))
    
    # Mark the first (most recent) session as current
    if session_responses:
        session_responses[0].current = True
    
    return SessionListResponse(sessions=session_responses)

@router.delete("/sessions/{session_id}")
async def delete_user_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
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
async def get_user_plan(current_user: User = Depends(get_current_user)):
    """Get current user's plan"""
    return {"plan": current_user.plan or "FREE"}
