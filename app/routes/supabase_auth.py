from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from ..models.database import get_db
from ..models.user import User
from ..middleware.supabase_auth import get_current_user, SupabaseUser, supabase_auth
from ..utils.jwt import create_access_token, create_refresh_token

router = APIRouter()

# Supabase JWT Authentication Endpoints
class SupabaseAuthRequest(BaseModel):
    supabase_token: Optional[str] = None

class SupabaseAuthResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: dict
    message: str = "Successfully authenticated with Supabase"

@router.post("/supabase/verify", response_model=SupabaseAuthResponse)
async def verify_supabase_token(
    auth_request: SupabaseAuthRequest,
    db: Session = Depends(get_db),
    authorization: Optional[str] = None
):
    """
    Verify Supabase JWT token and create/update user in database.
    This endpoint replaces manual OAuth handling by verifying Supabase tokens.
    """
    try:
        token = auth_request.supabase_token
        # Fallback: read from Authorization header
        if (not token or token.strip() == "") and authorization:
            try:
                scheme, bearer = authorization.split(" ", 1)
                if scheme.lower() == "bearer":
                    token = bearer
            except Exception:
                pass
        if not token:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing Supabase token")

    print(f"[SUPABASE VERIFY ENDPOINT] token_length={len(token)}")
    # Verify the Supabase JWT token
        supabase_user = supabase_auth.verify_token(token)

        # Check if user exists in our database
        user = db.query(User).filter(User.email == supabase_user.email).first()

        if not user:
            # Create new user from Supabase data
            user = User(
                email=supabase_user.email,
                name=supabase_user.name or "",
                email_verified=supabase_user.email_verified,
                auth_provider="supabase",
                auth_provider_id=supabase_user.id
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            print(f"✅ Created new user from Supabase: {user.email}")
        else:
            # Update existing user with Supabase info if needed
            if not user.auth_provider or user.auth_provider != "supabase":
                user.auth_provider = "supabase"
                user.auth_provider_id = supabase_user.id
                if supabase_user.name and not user.name:
                    user.name = supabase_user.name
                user.email_verified = supabase_user.email_verified
                db.commit()
                print(f"✅ Updated existing user with Supabase info: {user.email}")

        # Create our own JWT tokens for the user
        access_token = create_access_token({"sub": str(user.id), "email": user.email})
        refresh_token = create_refresh_token({"sub": str(user.id), "email": user.email})

        return SupabaseAuthResponse(
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

    except HTTPException:
        # Re-raise HTTP exceptions from token verification
        raise
    except Exception as e:
        print(f"❌ Supabase token verification failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Supabase authentication failed: {str(e)}"
        )

@router.get("/supabase/me", response_model=dict)
async def get_supabase_user_info(current_user: SupabaseUser = Depends(get_current_user)):
    """
    Get current user information from Supabase JWT token.
    This endpoint can be used to verify token validity and get user data.
    """
    return {
        "id": current_user.id,
        "email": current_user.email,
        "name": current_user.name,
        "avatar_url": current_user.avatar_url,
        "email_verified": current_user.email_verified
    }
