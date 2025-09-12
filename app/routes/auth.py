from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import Optional
import re
from datetime import datetime
import secrets
import httpx
from ..models.database import get_db
from ..models.user import User
from ..models.api_key import APIKey
from ..models.session import Session
from ..utils.jwt import create_access_token, create_refresh_token, verify_token
from ..utils.email import email_service
from ..config import settings
from ..middleware.supabase_auth import get_current_user, SupabaseUser
from ..utils.session_manager import create_user_session, get_user_session, validate_user_session, delete_user_session

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

class OAuthCallbackRequest(BaseModel):
    code: str
    state: Optional[str] = None

class OAuthURLResponse(BaseModel):
    auth_url: str
    state: str

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

class RegistrationResponse(BaseModel):
    success: bool
    message: str
    email_sent: bool = False

@router.post("/register", response_model=RegistrationResponse)
async def register(user_data: UserRegister, db: Session = Depends(get_db)):
    """Register a new user"""
    try:
        print(f"Registration attempt for email: {user_data.email}")

        # Check if database is available - fix SQLAlchemy text usage
        from sqlalchemy import text
        db.execute(text("SELECT 1"))
        print("Database connection OK")
    except Exception as db_error:
        print(f"Database connection error: {db_error}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Registration service temporarily unavailable. Please try again later."
        )

    try:
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == user_data.email).first()
        if existing_user:
            print(f"Email already registered: {user_data.email}")
            print(f"User auth_provider: {existing_user.auth_provider}")
            print(f"User has password_hash: {existing_user.password_hash is not None}")
            
            # If user exists and has OAuth provider but no password, allow setting password
            if existing_user.auth_provider and not existing_user.password_hash:
                print(f"OAuth user found, setting password for: {user_data.email}")
                
                # Validate password
                if not validate_password(user_data.password):
                    print(f"Invalid password for OAuth user: {user_data.email}")
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Password must be at least 8 characters with uppercase, lowercase, and number"
                    )
                
                # Set password for existing OAuth user
                existing_user.set_password(user_data.password)
                existing_user.email_verified = True  # Mark as verified since they completed registration
                db.commit()
                
                print(f"Password set successfully for OAuth user: {user_data.email}")
                return RegistrationResponse(
                    success=True,
                    message="Password set successfully! You can now log in with your email and password.",
                    email_sent=False  # No email needed since they already verified via OAuth
                )
            else:
                # Regular duplicate email error
                print(f"Regular duplicate email for: {user_data.email}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered"
                )

        # Validate password
        if not validate_password(user_data.password):
            print(f"Invalid password for email: {user_data.email}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password must be at least 8 characters with uppercase, lowercase, and number"
            )

        print(f"Creating user for email: {user_data.email}")

        # Create new user
        user = User(
            email=user_data.email,
            name=user_data.name,
            company=user_data.company,
            job_title=user_data.job_title
        )
        user.set_password(user_data.password)

        # Generate verification token
        user.generate_verification_token()

        db.add(user)
        db.commit()
        db.refresh(user)

        print(f"User created successfully: {user.email}")

        # Send verification email instead of welcome email
        email_sent = False
        try:
            email_result = email_service.send_verification_email(user.email, user.email_verification_token)
            if email_result:
                print(f"Verification email sent successfully to {user.email}")
                email_sent = True
            else:
                print(f"Failed to send verification email to {user.email}")
        except Exception as e:
            # Don't fail registration if email fails
            print(f"Verification email error: {e}")

        print(f"Registration completed for: {user.email}")
        return RegistrationResponse(
            success=True,
            message="Registration successful. Please check your email to verify your account.",
            email_sent=email_sent
        )

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        print(f"Unexpected error during registration for {user_data.email}: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during registration. Please try again."
        )

# Pydantic models for password operations
class SetPasswordRequest(BaseModel):
    email: EmailStr
    password: str

class SetPasswordResponse(BaseModel):
    success: bool
    message: str

@router.post("/set-password", response_model=SetPasswordResponse)
async def set_password_for_oauth_user(request_data: SetPasswordRequest, db: Session = Depends(get_db)):
    """Set password for existing OAuth user who wants to enable password login"""
    try:
        print(f"Set password request for email: {request_data.email}")

        # Find user by email
        user = db.query(User).filter(User.email == request_data.email).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Check if user has OAuth provider
        if not user.auth_provider:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This account was not created with social login. Use password reset instead."
            )

        # Validate password
        if not validate_password(request_data.password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password must be at least 8 characters with uppercase, lowercase, and number"
            )

        # Set password
        user.set_password(request_data.password)
        user.email_verified = True  # Ensure email is marked as verified
        db.commit()

        print(f"Password set successfully for OAuth user: {request_data.email}")
        return SetPasswordResponse(
            success=True,
            message="Password set successfully! You can now log in with your email and password."
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error setting password for {request_data.email}: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to set password. Please try again."
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
    
    # Check if email is verified
    if not user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Please verify your email address before logging in"
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
        
        # Create Redis session if enabled
        redis_session_id = None
        if os.getenv("USE_REDIS_SESSIONS", "false").lower() == "true":
            try:
                redis_session_id = create_user_session(
                    user_id=user.id,
                    user_data=user.to_dict(),
                    device_info=device_info,
                    ip_address=ip_address
                )
                if redis_session_id:
                    print(f"Redis session created: {redis_session_id}")
            except Exception as e:
                print(f"Redis session creation failed: {e}")
        
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
    
    response_data = TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=user.to_dict()
    )
    
    # Add Redis session ID to response if available
    if redis_session_id:
        response_data.user["redis_session_id"] = redis_session_id
    
    return response_data

@router.get("/sessions/redis/{session_id}")
async def get_redis_session(session_id: str):
    """Get Redis session information (for debugging/admin purposes)"""
    if os.getenv("USE_REDIS_SESSIONS", "false").lower() != "true":
        raise HTTPException(status_code=404, detail="Redis sessions not enabled")
    
    session_data = get_user_session(session_id)
    if not session_data:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Return session info without sensitive data
    safe_data = {
        "session_id": session_data.get("session_id"),
        "user_id": session_data.get("user_id"),
        "created_at": session_data.get("created_at"),
        "last_active": session_data.get("last_active"),
        "expires_at": session_data.get("expires_at"),
        "device_info": session_data.get("device_info", {}),
        "ip_address": session_data.get("ip_address")
    }
    
    return {"status": "success", "session": safe_data}

@router.delete("/sessions/redis/{session_id}")
async def delete_redis_session(session_id: str):
    """Delete Redis session"""
    if os.getenv("USE_REDIS_SESSIONS", "false").lower() != "true":
        raise HTTPException(status_code=404, detail="Redis sessions not enabled")
    
    success = delete_user_session(session_id)
    if not success:
        raise HTTPException(status_code=404, detail="Session not found or could not be deleted")
    
    return {"status": "success", "message": "Session deleted"}

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

class EmailRequest(BaseModel):
    email: EmailStr

# Email Verification Endpoints
@router.post("/send-verification", response_model=MessageResponse)
async def send_verification_email(email_data: EmailRequest, db: Session = Depends(get_db)):
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

@router.get("/verify-email", response_class=HTMLResponse)
async def verify_email_get(token: str, db: Session = Depends(get_db)):
    """Verify email with token via GET request (for email links)"""
    if not token:
        return """
        <html>
        <head>
            <title>Email Verification - Envoyou</title>
            <style>
                body { font-family: Arial, sans-serif; text-align: center; padding: 50px; }
                .error { color: #dc3545; }
                .container { max-width: 600px; margin: 0 auto; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1 class="error">Verification Failed</h1>
                <p>No verification token provided.</p>
                <p>Please check your email for the correct verification link.</p>
            </div>
        </body>
        </html>
        """
    
    user = db.query(User).filter(User.email_verification_token == token).first()
    if not user:
        return """
        <html>
        <head>
            <title>Email Verification - Envoyou</title>
            <style>
                body { font-family: Arial, sans-serif; text-align: center; padding: 50px; }
                .error { color: #dc3545; }
                .container { max-width: 600px; margin: 0 auto; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1 class="error">Verification Failed</h1>
                <p>This verification link is invalid or has expired.</p>
                <p>Please request a new verification email or contact support.</p>
            </div>
        </body>
        </html>
        """
    
    if user.verify_verification_token(token):
        db.commit()
        return f"""
        <html>
        <head>
            <title>Email Verification - Envoyou</title>
            <style>
                body {{ font-family: Arial, sans-serif; text-align: center; padding: 50px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; }}
                .success {{ color: #28a745; }}
                .container {{ max-width: 600px; margin: 0 auto; background: white; padding: 40px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); color: #333; }}
                .btn {{ background-color: #4CAF50; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; display: inline-block; margin-top: 20px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1 class="success">✅ Email Verified Successfully!</h1>
                <p>Welcome to Envoyou, <strong>{user.name}</strong>!</p>
                <p>Your email address <strong>{user.email}</strong> has been verified.</p>
                <p>You can now log in to your account and start using our services.</p>
                <a href="/" class="btn">Go to Login</a>
            </div>
        </body>
        </html>
        """
    else:
        return """
        <html>
        <head>
            <title>Email Verification - Envoyou</title>
            <style>
                body { font-family: Arial, sans-serif; text-align: center; padding: 50px; }
                .error { color: #dc3545; }
                .container { max-width: 600px; margin: 0 auto; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1 class="error">Verification Failed</h1>
                <p>This verification link is invalid or has expired.</p>
                <p>Please request a new verification email or contact support.</p>
            </div>
        </body>
        </html>
        """

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
                email_verified=True  # Auto-verify for free users
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


# OAuth Endpoints
@router.get("/google/login", response_model=OAuthURLResponse)
async def google_login():
    """Get Google OAuth login URL"""
    if not settings.ENABLE_SOCIAL_AUTH:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Social authentication is currently disabled"
        )

    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google OAuth is not configured"
        )

    # Generate state for CSRF protection
    state = secrets.token_urlsafe(32)

    # Google OAuth2 configuration
    auth_url = "https://accounts.google.com/o/oauth2/auth"
    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": settings.google_redirect_uri,
        "scope": "openid email profile",
        "response_type": "code",
        "state": state,
        "access_type": "offline",
        "prompt": "consent"
    }

    # Build the authorization URL
    query_string = "&".join([f"{k}={v}" for k, v in params.items()])
    full_auth_url = f"{auth_url}?{query_string}"

    return OAuthURLResponse(auth_url=full_auth_url, state=state)


@router.post("/google/callback", response_model=TokenResponse)
async def google_callback(
    callback_data: OAuthCallbackRequest,
    db: Session = Depends(get_db)
):
    """Handle Google OAuth callback"""
    if not settings.ENABLE_SOCIAL_AUTH:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Social authentication is currently disabled"
        )

    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google OAuth is not configured"
        )

    try:
        # Exchange authorization code for access token
        token_url = "https://oauth2.googleapis.com/token"
        token_data = {
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "code": callback_data.code,
            "grant_type": "authorization_code",
            "redirect_uri": settings.google_redirect_uri
        }

        async with httpx.AsyncClient() as client:
            token_response = await client.post(token_url, data=token_data)
            token_response.raise_for_status()
            token_info = token_response.json()

        # Get user info from Google
        user_info_url = "https://www.googleapis.com/oauth2/v2/userinfo"
        headers = {"Authorization": f"Bearer {token_info['access_token']}"}

        async with httpx.AsyncClient() as client:
            user_response = await client.get(user_info_url, headers=headers)
            user_response.raise_for_status()
            user_info = user_response.json()

        # Check if user exists
        try:
            user = db.query(User).filter(User.email == user_info["email"]).first()
            print(f"DEBUG: Database query successful, user found: {user is not None}")
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database error: {str(e)}"
            )

        if not user:
            # Create new user
            user = User(
                email=user_info["email"],
                name=user_info.get("name", ""),
                email_verified=True,  # Google accounts are pre-verified
                auth_provider="google",
                auth_provider_id=user_info["id"]
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        else:
            # Update existing user with Google info if not already set
            if not user.auth_provider:
                user.auth_provider = "google"
                user.auth_provider_id = user_info["id"]
                db.commit()

        # Create tokens
        access_token = create_access_token({"sub": str(user.id), "email": user.email})
        refresh_token = create_refresh_token({"sub": str(user.id), "email": user.email})

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            user={
                "id": user.id,
                "email": user.email,
                "name": user.name,
                "email_verified": user.email_verified,
                "auth_provider": user.auth_provider
            }
        )

    except httpx.HTTPError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"OAuth token exchange failed: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"OAuth authentication failed: {str(e)}"
        )


@router.post("/google/token", response_model=TokenResponse)
async def google_token_exchange(
    callback_data: OAuthCallbackRequest,
    db: Session = Depends(get_db)
):
    """Exchange Google OAuth authorization code for tokens (called by frontend)"""
    if not settings.ENABLE_SOCIAL_AUTH:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Social authentication is currently disabled"
        )

    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google OAuth is not configured"
        )

    try:
        # Exchange authorization code for access token
        token_url = "https://oauth2.googleapis.com/token"
        token_data = {
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "code": callback_data.code,
            "grant_type": "authorization_code",
            "redirect_uri": settings.google_redirect_uri
        }

        async with httpx.AsyncClient() as client:
            token_response = await client.post(token_url, data=token_data)
            token_response.raise_for_status()
            token_info = token_response.json()

        # Get user info from Google
        user_info_url = "https://www.googleapis.com/oauth2/v2/userinfo"
        headers = {"Authorization": f"Bearer {token_info['access_token']}"}

        async with httpx.AsyncClient() as client:
            user_response = await client.get(user_info_url, headers=headers)
            user_response.raise_for_status()
            user_info = user_response.json()

        # Check if user exists
        try:
            user = db.query(User).filter(User.email == user_info["email"]).first()
            print(f"DEBUG: Database query successful, user found: {user is not None}")
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database error: {str(e)}"
            )

        if not user:
            # Create new user
            user = User(
                email=user_info["email"],
                name=user_info.get("name", ""),
                email_verified=True,  # Google accounts are pre-verified
                auth_provider="google",
                auth_provider_id=user_info["id"]
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        else:
            # Update existing user with Google info if not already set
            if not user.auth_provider:
                user.auth_provider = "google"
                user.auth_provider_id = user_info["id"]
                db.commit()

        # Create tokens
        access_token = create_access_token({"sub": str(user.id), "email": user.email})
        refresh_token = create_refresh_token({"sub": str(user.id), "email": user.email})

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            user={
                "id": user.id,
                "email": user.email,
                "name": user.name,
                "email_verified": user.email_verified,
                "auth_provider": user.auth_provider
            }
        )

    except httpx.HTTPError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"OAuth token exchange failed: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"OAuth authentication failed: {str(e)}"
        )


@router.post("/github/token", response_model=TokenResponse)
async def github_token_exchange(
    callback_data: OAuthCallbackRequest,
    db: Session = Depends(get_db)
):
    """Exchange GitHub OAuth authorization code for tokens (called by frontend)"""
    if not settings.ENABLE_SOCIAL_AUTH:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Social authentication is currently disabled"
        )

    if not settings.GITHUB_CLIENT_ID or not settings.GITHUB_CLIENT_SECRET:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="GitHub OAuth is not configured"
        )

    try:
        # Exchange authorization code for access token
        token_url = "https://github.com/login/oauth/access_token"
        token_data = {
            "client_id": settings.GITHUB_CLIENT_ID,
            "client_secret": settings.GITHUB_CLIENT_SECRET,
            "code": callback_data.code,
            "redirect_uri": settings.github_redirect_uri
        }

        async with httpx.AsyncClient() as client:
            token_response = await client.post(
                token_url,
                data=token_data,
                headers={"Accept": "application/json"}
            )
            token_response.raise_for_status()
            token_info = token_response.json()

        if "error" in token_info:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"GitHub OAuth error: {token_info['error_description']}"
            )

        # Get user info from GitHub
        user_info_url = "https://api.github.com/user"
        headers = {"Authorization": f"Bearer {token_info['access_token']}"}

        async with httpx.AsyncClient() as client:
            user_response = await client.get(user_info_url, headers=headers)
            user_response.raise_for_status()
            user_info = user_response.json()

        # Get user email from GitHub
        email_url = "https://api.github.com/user/emails"
        async with httpx.AsyncClient() as client:
            email_response = await client.get(email_url, headers=headers)
            email_response.raise_for_status()
            emails = email_response.json()

        # Find primary email
        primary_email = None
        for email_data in emails:
            if email_data.get("primary"):
                primary_email = email_data["email"]
                break
        if not primary_email:
            primary_email = emails[0]["email"] if emails else user_info.get("email")

        if not primary_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unable to retrieve email from GitHub"
            )

        # Check if user exists
        user = db.query(User).filter(User.email == primary_email).first()

        if not user:
            # Create new user
            user = User(
                email=primary_email,
                name=user_info.get("name", user_info.get("login", "")),
                email_verified=True,  # GitHub accounts are pre-verified
                auth_provider="github",
                auth_provider_id=str(user_info["id"])
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        else:
            # Update existing user with GitHub info if not already set
            if not user.auth_provider:
                user.auth_provider = "github"
                user.auth_provider_id = str(user_info["id"])
                db.commit()

        # Create tokens
        access_token = create_access_token({"sub": str(user.id), "email": user.email})
        refresh_token = create_refresh_token({"sub": str(user.id), "email": user.email})

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            user={
                "id": user.id,
                "email": user.email,
                "name": user.name,
                "email_verified": user.email_verified,
                "auth_provider": user.auth_provider
            }
        )

    except httpx.HTTPError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"OAuth token exchange failed: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"OAuth authentication failed: {str(e)}"
        )


@router.get("/github/login", response_model=OAuthURLResponse)
async def github_login():
    """Get GitHub OAuth login URL"""
    if not settings.ENABLE_SOCIAL_AUTH:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Social authentication is currently disabled"
        )

    if not settings.GITHUB_CLIENT_ID or not settings.GITHUB_CLIENT_SECRET:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="GitHub OAuth is not configured"
        )

    # Generate state for CSRF protection
    state = secrets.token_urlsafe(32)

    # GitHub OAuth2 configuration
    auth_url = "https://github.com/login/oauth/authorize"
    params = {
        "client_id": settings.GITHUB_CLIENT_ID,
        "redirect_uri": settings.github_redirect_uri,
        "scope": "user:email",
        "state": state
    }

    # Build the authorization URL
    query_string = "&".join([f"{k}={v}" for k, v in params.items()])
    full_auth_url = f"{auth_url}?{query_string}"

    return OAuthURLResponse(auth_url=full_auth_url, state=state)


@router.post("/github/callback", response_model=TokenResponse)
async def github_callback(
    callback_data: OAuthCallbackRequest,
    db: Session = Depends(get_db)
):
    """Handle GitHub OAuth callback"""
    if not settings.ENABLE_SOCIAL_AUTH:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Social authentication is currently disabled"
        )

    if not settings.GITHUB_CLIENT_ID or not settings.GITHUB_CLIENT_SECRET:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="GitHub OAuth is not configured"
        )

    try:
        # Exchange authorization code for access token
        token_url = "https://github.com/login/oauth/access_token"
        token_data = {
            "client_id": settings.GITHUB_CLIENT_ID,
            "client_secret": settings.GITHUB_CLIENT_SECRET,
            "code": callback_data.code,
            "redirect_uri": settings.github_redirect_uri
        }

        async with httpx.AsyncClient() as client:
            token_response = await client.post(
                token_url,
                data=token_data,
                headers={"Accept": "application/json"}
            )
            token_response.raise_for_status()
            token_info = token_response.json()

        if "error" in token_info:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"GitHub OAuth error: {token_info['error_description']}"
            )

        # Get user info from GitHub
        user_info_url = "https://api.github.com/user"
        headers = {"Authorization": f"Bearer {token_info['access_token']}"}

        async with httpx.AsyncClient() as client:
            user_response = await client.get(user_info_url, headers=headers)
            user_response.raise_for_status()
            user_info = user_response.json()

        # Get user email from GitHub
        email_url = "https://api.github.com/user/emails"
        async with httpx.AsyncClient() as client:
            email_response = await client.get(email_url, headers=headers)
            email_response.raise_for_status()
            emails = email_response.json()

        # Find primary email
        primary_email = None
        for email_data in emails:
            if email_data.get("primary"):
                primary_email = email_data["email"]
                break
        if not primary_email:
            primary_email = emails[0]["email"] if emails else user_info.get("email")

        if not primary_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unable to retrieve email from GitHub"
            )

        # Check if user exists
        user = db.query(User).filter(User.email == primary_email).first()

        if not user:
            # Create new user
            user = User(
                email=primary_email,
                name=user_info.get("name", user_info.get("login", "")),
                email_verified=True,  # GitHub accounts are pre-verified
                auth_provider="github",
                auth_provider_id=str(user_info["id"])
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        else:
            # Update existing user with GitHub info if not already set
            if not user.auth_provider:
                user.auth_provider = "github"
                user.auth_provider_id = str(user_info["id"])
                db.commit()

        # Create tokens
        access_token = create_access_token({"sub": str(user.id), "email": user.email})
        refresh_token = create_refresh_token({"sub": str(user.id), "email": user.email})

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            user={
                "id": user.id,
                "email": user.email,
                "name": user.name,
                "email_verified": user.email_verified,
                "auth_provider": user.auth_provider
            }
        )

    except httpx.HTTPError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"OAuth token exchange failed: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"OAuth authentication failed: {str(e)}"
        )
