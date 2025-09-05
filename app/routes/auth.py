from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import Optional
import re
from datetime import datetime

from ..models.database import get_db
from ..models.user import User
from ..models.api_key import APIKey
from ..models.session import Session
from ..utils.jwt import create_access_token, create_refresh_token, verify_token
from ..utils.email import email_service
from ..utils.email import email_service

router = APIRouter()
security = HTTPBearer()

# Pydantic models for request/response
class UserRegister(BaseModel):
    email: EmailStr
    password: str
    name: str
    company: Optional[str] = None
    job_title: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: dict

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class MessageResponse(BaseModel):
    message: str

class TwoFASetupResponse(BaseModel):
    secret: str
    qr_code_url: str

class TwoFAVerifyRequest(BaseModel):
    code: str

class FreeAPIKeyRequest(BaseModel):
    email: EmailStr
    name: Optional[str] = None
    company: Optional[str] = None

class FreeAPIKeyResponse(BaseModel):
    success: bool
    message: str
    api_key: Optional[str] = None
    key_prefix: Optional[str] = None
    user_id: Optional[str] = None

def validate_password(password: str) -> bool:
    """Validate password strength"""
    if len(password) < 8:
        return False
    if not re.search(r"[A-Z]", password):
        return False
    if not re.search(r"[a-z]", password):
        return False
    if not re.search(r"\d", password):
        return False
    return True

@router.post("/register", response_model=TokenResponse)
async def register(user_data: UserRegister, db: Session = Depends(get_db)):
    """Register a new user"""
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Validate password
    if not validate_password(user_data.password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters with uppercase, lowercase, and number"
        )
    
    # Create new user
    user = User(
        email=user_data.email,
        name=user_data.name,
        company=user_data.company,
        job_title=user_data.job_title
    )
    user.set_password(user_data.password)
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Send welcome email
    try:
        email_service.send_welcome_email(user.email, user.name)
    except Exception as e:
        # Don't fail registration if email fails
        print(f"Welcome email failed: {e}")
    
    # Create tokens
    access_token = create_access_token(data={"sub": user.email})
    refresh_token = create_refresh_token(data={"sub": user.email})
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=user.to_dict()
    )

@router.post("/login", response_model=TokenResponse)
async def login(
    user_data: UserLogin,
    db: Session = Depends(get_db),
    request: Request = None
):
    """Login user"""
    user = db.query(User).filter(User.email == user_data.email).first()
    if not user or not user.verify_password(user_data.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Create tokens
    access_token = create_access_token(data={"sub": user.email})
    refresh_token = create_refresh_token(data={"sub": user.email})
    
    # Create session tracking
    try:
        # Get device info from request headers
        user_agent = request.headers.get("User-Agent", "Unknown")
        ip_address = request.client.host if request.client else "Unknown"
        
        # Parse device info
        device_info = {
            "device": user_agent,
            "browser": "Unknown",
            "os": "Unknown"
        }
        
        # Create session
        session = Session(
            user_id=user.id,
            token=access_token,
            device_info=device_info,
            ip_address=ip_address
        )
        
        db.add(session)
        db.commit()
        
        # Send login notification email
        try:
            from datetime import datetime
            login_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            email_service.send_login_notification(
                user.email, user.name, login_time, ip_address, user_agent
            )
        except Exception as e:
            # Don't fail login if email fails
            print(f"Login notification email failed: {e}")
        
    except Exception as e:
        # Don't fail login if session creation fails
        print(f"Session creation failed: {e}")
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=user.to_dict()
    )

@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(request: RefreshTokenRequest, db: Session = Depends(get_db)):
    """Refresh access token using refresh token"""
    token_data = verify_token(request.refresh_token, "refresh")
    if not token_data or not token_data.email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    user = db.query(User).filter(User.email == token_data.email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    # Create new tokens
    access_token = create_access_token(data={"sub": user.email})
    refresh_token = create_refresh_token(data={"sub": user.email})
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=user.to_dict()
    )

@router.post("/logout", response_model=MessageResponse)
async def logout(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Logout user (client should discard tokens)"""
    # In a stateless JWT system, logout is handled client-side
    # Server doesn't need to do anything special
    return MessageResponse(message="Logged out successfully")

# Email Verification Endpoints
@router.post("/send-verification", response_model=MessageResponse)
async def send_verification_email(email_data: UserLogin, db: Session = Depends(get_db)):
    """Send email verification"""
    user = db.query(User).filter(User.email == email_data.email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already verified"
        )
    
    # Generate verification token
    user.generate_verification_token()
    db.commit()
    
    # Send verification email
    if email_service.send_verification_email(user.email, user.email_verification_token):
        return MessageResponse(message="Verification email sent successfully")
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send verification email"
        )

@router.post("/verify-email", response_model=MessageResponse)
async def verify_email(token_data: dict, db: Session = Depends(get_db)):
    """Verify email with token"""
    token = token_data.get("token")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token is required"
        )
    
    user = db.query(User).filter(User.email_verification_token == token).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired token"
        )
    
    if user.verify_verification_token(token):
        db.commit()
        return MessageResponse(message="Email verified successfully")
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired token"
        )

# Password Management Endpoints
@router.post("/forgot-password", response_model=MessageResponse)
async def forgot_password(email_data: UserLogin, db: Session = Depends(get_db)):
    """Send password reset email"""
    user = db.query(User).filter(User.email == email_data.email).first()
    if not user:
        # Don't reveal if email exists or not for security
        return MessageResponse(message="If the email exists, a reset link has been sent")
    
    # Generate reset token
    user.generate_reset_token()
    db.commit()
    
    # Send reset email
    if email_service.send_password_reset_email(user.email, user.password_reset_token):
        return MessageResponse(message="Password reset email sent successfully")
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send reset email"
        )

@router.post("/reset-password", response_model=MessageResponse)
async def reset_password(request: dict, db: Session = Depends(get_db)):
    """Reset password with token"""
    token = request.get("token")
    new_password = request.get("password")
    
    if not token or not new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token and new password are required"
        )
    
    # Validate password
    if not validate_password(new_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters with uppercase, lowercase, and number"
        )
    
    user = db.query(User).filter(User.password_reset_token == token).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired token"
        )
    
    if user.verify_reset_token(token):
        user.set_password(new_password)
        db.commit()
        return MessageResponse(message="Password reset successfully")
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired token"
        )

@router.post("/change-password", response_model=MessageResponse)
async def change_password(
    request: dict,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Change password for authenticated user"""
    current_password = request.get("current_password")
    new_password = request.get("new_password")
    
    if not current_password or not new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password and new password are required"
        )
    
    # Validate new password
    if not validate_password(new_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters with uppercase, lowercase, and number"
        )
    
    # Get current user
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
    
    # Verify current password
    if not user.verify_password(current_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    # Set new password
    user.set_password(new_password)
    db.commit()
    
    return MessageResponse(message="Password changed successfully")

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
    
    # Update session activity if session exists
    try:
        session = db.query(Session).filter(
            Session.user_id == user.id,
            Session.expires_at > datetime.utcnow()
        ).order_by(Session.last_active.desc()).first()
        
        if session:
            session.update_activity()
            db.commit()
    except Exception as e:
        # Don't fail if session update fails
        print(f"Session update failed: {e}")
    
    return user

# Two-Factor Authentication Endpoints
@router.post("/2fa/setup", response_model=TwoFASetupResponse)
async def setup_2fa(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Setup 2FA for user"""
    if current_user.two_factor_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="2FA is already enabled"
        )
    
    try:
        import pyotp
        import qrcode
        import io
        import base64
    except ImportError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="2FA dependencies not installed"
        )
    
    # Generate secret
    secret = pyotp.random_base32()
    
    # Setup TOTP
    totp = pyotp.TOTP(secret)
    
    # Generate QR code URL
    qr_code_url = totp.provisioning_uri(
        name=current_user.email,
        issuer_name="EnvoyOU"
    )
    
    # Store secret temporarily (don't enable yet)
    current_user.setup_2fa(secret)
    db.commit()
    
    return TwoFASetupResponse(
        secret=secret,
        qr_code_url=qr_code_url
    )

@router.post("/2fa/verify", response_model=MessageResponse)
async def verify_2fa(
    request: TwoFAVerifyRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Verify 2FA setup with code"""
    if not current_user.two_factor_secret:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="2FA setup not initiated"
        )
    
    if current_user.two_factor_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="2FA is already enabled"
        )
    
    # Verify the code
    if current_user.verify_2fa_code(request.code):
        current_user.enable_2fa()
        db.commit()
        return MessageResponse(message="2FA enabled successfully")
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid 2FA code"
        )

@router.post("/2fa/disable", response_model=MessageResponse)
async def disable_2fa(
    request: TwoFAVerifyRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Disable 2FA"""
    if not current_user.two_factor_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="2FA is not enabled"
        )
    
    # Verify current 2FA code before disabling
    if current_user.verify_2fa_code(request.code):
        current_user.disable_2fa()
        db.commit()
        return MessageResponse(message="2FA disabled successfully")
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid 2FA code"
        )

@router.post("/request-free-api-key", response_model=FreeAPIKeyResponse)
async def request_free_api_key(
    request: FreeAPIKeyRequest,
    db: Session = Depends(get_db)
):
    """Request free API key without registration (public endpoint)"""
    try:
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == request.email).first()
        
        if existing_user:
            # User exists, check if they already have an API key
            existing_api_key = db.query(APIKey).filter(
                APIKey.user_id == existing_user.id,
                APIKey.is_active == True
            ).first()
            
            if existing_api_key:
                return FreeAPIKeyResponse(
                    success=False,
                    message="You already have an active API key. Please check your email or contact support.",
                    api_key=None,
                    key_prefix=existing_api_key.prefix,
                    user_id=existing_user.id
                )
            
            # Create new API key for existing user
            user_id = existing_user.id
            user_name = existing_user.name
            user_email = existing_user.email
            
        else:
            # Create new user for free API key
            new_user = User(
                email=request.email,
                name=request.name or f"Free User - {request.email.split('@')[0]}",
                company=request.company or "Free User",
                password_hash="",  # No password for free users
                is_active=True,
                email_verified=True,  # Auto-verify for free users
                role="free"
            )
            
            db.add(new_user)
            db.commit()
            db.refresh(new_user)
            
            user_id = new_user.id
            user_name = new_user.name
            user_email = new_user.email
        
        # Create free API key
        api_key = APIKey(
            user_id=user_id,
            name="Free API Key",
            permissions=["read"]  # Limited permissions for free users
        )
        
        # Generate the actual key
        actual_key = api_key._generate_key()
        
        db.add(api_key)
        db.commit()
        db.refresh(api_key)
        
        # Send welcome email with API key
        try:
            from app.utils.email import email_service
            api_key_preview = f"{actual_key[:8]}...{actual_key[-4:]}"
            email_service.send_free_api_key_notification(
                user_email, user_name, actual_key, api_key.prefix
            )
        except Exception as e:
            # Don't fail API key creation if email fails
            print(f"Free API key email failed: {e}")
        
        return FreeAPIKeyResponse(
            success=True,
            message="Free API key created successfully! Please check your email for the complete key.",
            api_key=actual_key,  # Only shown once
            key_prefix=api_key.prefix,
            user_id=user_id
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create free API key: {str(e)}"
        )
