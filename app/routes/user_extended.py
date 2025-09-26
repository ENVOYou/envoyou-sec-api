from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
import os
from datetime import datetime, UTC

from ..models.database import get_db
from ..models.user import User
from ..middleware.supabase_auth import get_current_user as get_supabase_user, SupabaseUser

router = APIRouter()

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

async def get_db_user(supa_user: SupabaseUser = Depends(get_supabase_user), db: Session = Depends(get_db)):
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
    return user

@router.get("/calculations", response_model=CalculationListResponse)
async def get_user_calculations(
    page: int = 1,
    limit: int = 20,
    current_user: User = Depends(get_db_user),
    db: Session = Depends(get_db)
):
    """Get user's emission calculations history"""
    from sqlalchemy import text
    
    try:
        count_result = db.execute(text("SELECT COUNT(*) FROM emissions_calculations WHERE user_id = :user_id"), {"user_id": current_user.auth_provider_id})
        total = count_result.scalar() or 0
        
        offset = (page - 1) * limit
        results = db.execute(
            text("SELECT * FROM emissions_calculations WHERE user_id = :user_id ORDER BY created_at DESC LIMIT :limit OFFSET :offset"),
            {"user_id": current_user.auth_provider_id, "limit": limit, "offset": offset}
        ).fetchall()
        
        calculations = []
        for row in results:
            calculations.append(CalculationResponse(
                id=str(row.id),
                company=row.company,
                calculation_data=row.calculation_data,
                result=row.result,
                version=row.version,
                created_at=row.created_at.isoformat()
            ))
            
    except Exception:
        calculations = []
        total = 0
    
    return CalculationListResponse(calculations=calculations, total=total, page=page, limit=limit)

@router.get("/calculations/{calculation_id}")
async def get_user_calculation(
    calculation_id: str,
    current_user: User = Depends(get_db_user),
    db: Session = Depends(get_db)
):
    """Get specific calculation"""
    from sqlalchemy import text
    
    try:
        result = db.execute(
            text("SELECT * FROM emissions_calculations WHERE id = :id AND user_id = :user_id"),
            {"id": calculation_id, "user_id": current_user.auth_provider_id}
        ).fetchone()
        
        if not result:
            raise HTTPException(status_code=404, detail="Calculation not found")
            
        return CalculationResponse(
            id=str(result.id),
            company=result.company,
            calculation_data=result.calculation_data,
            result=result.result,
            version=result.version,
            created_at=result.created_at.isoformat()
        )
    except Exception as e:
        if "not found" in str(e):
            raise e
        raise HTTPException(status_code=500, detail="Database error")

@router.delete("/calculations/{calculation_id}")
async def delete_user_calculation(
    calculation_id: str,
    current_user: User = Depends(get_db_user),
    db: Session = Depends(get_db)
):
    """Delete calculation"""
    from sqlalchemy import text
    
    try:
        result = db.execute(
            text("DELETE FROM emissions_calculations WHERE id = :id AND user_id = :user_id"),
            {"id": calculation_id, "user_id": current_user.auth_provider_id}
        )
        db.commit()
        
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Calculation not found")
            
        return {"message": "Calculation deleted successfully"}
    except Exception as e:
        if "not found" in str(e):
            raise e
        raise HTTPException(status_code=500, detail="Database error")

@router.get("/packages", response_model=PackageListResponse)
async def get_user_packages(
    page: int = 1,
    limit: int = 20,
    current_user: User = Depends(get_db_user),
    db: Session = Depends(get_db)
):
    """Get user's SEC packages"""
    from sqlalchemy import text
    
    try:
        count_result = db.execute(text("SELECT COUNT(*) FROM sec_export_packages WHERE user_id = :user_id"), {"user_id": current_user.auth_provider_id})
        total = count_result.scalar() or 0
        
        offset = (page - 1) * limit
        results = db.execute(
            text("SELECT * FROM sec_export_packages WHERE user_id = :user_id ORDER BY created_at DESC LIMIT :limit OFFSET :offset"),
            {"user_id": current_user.auth_provider_id, "limit": limit, "offset": offset}
        ).fetchall()
        
        packages = []
        for row in results:
            packages.append(PackageResponse(
                id=str(row.id),
                company=row.company,
                package_data=row.package_data,
                file_url=row.file_url,
                file_size=row.file_size,
                created_at=row.created_at.isoformat()
            ))
            
    except Exception:
        packages = []
        total = 0
    
    return PackageListResponse(packages=packages, total=total, page=page, limit=limit)

@router.get("/packages/{package_id}")
async def download_user_package(
    package_id: str,
    current_user: User = Depends(get_db_user),
    db: Session = Depends(get_db)
):
    """Download specific package"""
    from sqlalchemy import text
    from fastapi.responses import FileResponse
    
    try:
        result = db.execute(
            text("SELECT * FROM sec_export_packages WHERE id = :id AND user_id = :user_id"),
            {"id": package_id, "user_id": current_user.auth_provider_id}
        ).fetchone()
        
        if not result:
            raise HTTPException(status_code=404, detail="Package not found")
            
        if not result.file_url or not os.path.exists(result.file_url):
            raise HTTPException(status_code=404, detail="Package file not found")
            
        return FileResponse(
            path=result.file_url,
            filename=f"{result.company}_sec_package.zip",
            media_type="application/zip"
        )
    except Exception as e:
        if "not found" in str(e):
            raise e
        raise HTTPException(status_code=500, detail="Database error")

@router.delete("/packages/{package_id}")
async def delete_user_package(
    package_id: str,
    current_user: User = Depends(get_db_user),
    db: Session = Depends(get_db)
):
    """Delete package"""
    from sqlalchemy import text
    
    try:
        result = db.execute(
            text("SELECT file_url FROM sec_export_packages WHERE id = :id AND user_id = :user_id"),
            {"id": package_id, "user_id": current_user.auth_provider_id}
        ).fetchone()
        
        if not result:
            raise HTTPException(status_code=404, detail="Package not found")
            
        if result.file_url and os.path.exists(result.file_url):
            os.remove(result.file_url)
            
        db.execute(
            text("DELETE FROM sec_export_packages WHERE id = :id AND user_id = :user_id"),
            {"id": package_id, "user_id": current_user.auth_provider_id}
        )
        db.commit()
        
        return {"message": "Package deleted successfully"}
    except Exception as e:
        if "not found" in str(e):
            raise e
        raise HTTPException(status_code=500, detail="Database error")

@router.get("/notifications", response_model=NotificationListResponse)
async def get_user_notifications(
    current_user: User = Depends(get_db_user),
    db: Session = Depends(get_db)
):
    """Get user notifications"""
    from sqlalchemy import text
    
    try:
        results = db.execute(
            text("SELECT * FROM notifications WHERE user_id = :user_id ORDER BY created_at DESC LIMIT 50"),
            {"user_id": current_user.id}
        ).fetchall()
        
        notifications = []
        unread_count = 0
        
        for row in results:
            notifications.append(NotificationResponse(
                id=str(row.id),
                title=row.title,
                message=row.message,
                type=row.type,
                read=row.read,
                created_at=row.created_at.isoformat()
            ))
            if not row.read:
                unread_count += 1
                
    except Exception:
        notifications = []
        unread_count = 0
    
    return NotificationListResponse(notifications=notifications, unread_count=unread_count)

@router.put("/notifications/{notification_id}/read")
async def mark_notification_read(
    notification_id: str,
    current_user: User = Depends(get_db_user),
    db: Session = Depends(get_db)
):
    """Mark notification as read"""
    from sqlalchemy import text
    
    try:
        result = db.execute(
            text("UPDATE notifications SET read = true WHERE id = :id AND user_id = :user_id"),
            {"id": notification_id, "user_id": current_user.id}
        )
        db.commit()
        
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Notification not found")
            
        return {"message": "Notification marked as read"}
    except Exception as e:
        if "not found" in str(e):
            raise e
        raise HTTPException(status_code=500, detail="Database error")

@router.delete("/notifications/{notification_id}")
async def delete_notification(
    notification_id: str,
    current_user: User = Depends(get_db_user),
    db: Session = Depends(get_db)
):
    """Delete notification"""
    from sqlalchemy import text
    
    try:
        result = db.execute(
            text("DELETE FROM notifications WHERE id = :id AND user_id = :user_id"),
            {"id": notification_id, "user_id": current_user.id}
        )
        db.commit()
        
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Notification not found")
            
        return {"message": "Notification deleted successfully"}
    except Exception as e:
        if "not found" in str(e):
            raise e
        raise HTTPException(status_code=500, detail="Database error")

@router.get("/preferences", response_model=UserPreferencesResponse)
async def get_user_preferences(current_user: User = Depends(get_db_user)):
    """Get user preferences"""
    return UserPreferencesResponse(
        units=getattr(current_user, 'preferred_units', 'metric'),
        timezone=getattr(current_user, 'timezone', 'UTC'),
        email_notifications=True,
        default_company=getattr(current_user, 'company', None),
        default_grid_region='US_default'
    )

@router.put("/preferences", response_model=UserPreferencesResponse)
async def update_user_preferences(
    preferences: UserPreferencesUpdate,
    current_user: User = Depends(get_db_user),
    db: Session = Depends(get_db)
):
    """Update user preferences"""
    if preferences.timezone:
        current_user.timezone = preferences.timezone
    if preferences.default_company:
        current_user.company = preferences.default_company
        
    db.commit()
    
    return UserPreferencesResponse(
        units=preferences.units or 'metric',
        timezone=current_user.timezone or 'UTC',
        email_notifications=preferences.email_notifications if preferences.email_notifications is not None else True,
        default_company=current_user.company,
        default_grid_region=preferences.default_grid_region or 'US_default'
    )

@router.get("/activity", response_model=ActivityListResponse)
async def get_user_activity(
    limit: int = 20,
    current_user: User = Depends(get_db_user),
    db: Session = Depends(get_db)
):
    """Get user activity log"""
    from sqlalchemy import text
    
    try:
        results = db.execute(
            text("SELECT * FROM audit_trail WHERE company_cik = :company ORDER BY timestamp DESC LIMIT :limit"),
            {"company": current_user.company or current_user.email, "limit": limit}
        ).fetchall()
        
        activities = []
        for row in results:
            activities.append(ActivityResponse(
                id=str(row.id),
                action=row.source_file,
                description=f"Calculation version {row.calculation_version}",
                metadata={"notes": row.notes} if row.notes else None,
                created_at=row.timestamp.isoformat()
            ))
            
    except Exception:
        activities = [
            ActivityResponse(
                id="1",
                action="profile_update",
                description="Profile updated",
                metadata=None,
                created_at=datetime.now(UTC).isoformat()
            )
        ]
    
    return ActivityListResponse(activities=activities, total=len(activities))