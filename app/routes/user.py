from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
import os
import uuid
from datetime import datetime

from ..models.database import get_db
from ..models.user import User
from ..utils.jwt import verify_token

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
    created_at: Optional[str]
    last_login: Optional[str]

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
    """Get current user profile"""
    return UserProfileResponse(**current_user.to_dict())

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
