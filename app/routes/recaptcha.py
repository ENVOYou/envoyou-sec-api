from fastapi import APIRouter, HTTPException, status, Request
from pydantic import BaseModel
import httpx
from typing import Any, Dict
from app.config import settings

router = APIRouter()


class RecaptchaRequest(BaseModel):
    recaptchaToken: str


@router.post("/verify")
async def verify_recaptcha(payload: RecaptchaRequest, request: Request) -> Dict[str, Any]:
    """Verify reCAPTCHA token with Google and return verification result.

    Expects JSON { recaptchaToken: "..." } and returns { success: bool, score: float?, action: str? }
    """

    # Read recaptcha secret from settings (Pydantic settings object should load env vars)
    recaptcha_key = getattr(settings, 'RECAPTCHA_SECRET_KEY', None)
    if not recaptcha_key:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="reCAPTCHA secret not configured")

    token = payload.recaptchaToken
    if not token:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing recaptchaToken")

    verify_url = "https://recaptcha.google.com/recaptcha/api/siteverify"
    # Determine client IP (respect X-Forwarded-For when behind proxies)
    xff = request.headers.get('x-forwarded-for')
    if xff:
        remote_ip = xff.split(',')[0].strip()
    else:
        remote_ip = request.client.host if request.client else ''

    # Use async HTTP client to avoid blocking the event loop
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.post(verify_url, data={
                'secret': recaptcha_key,
                'response': token,
                'remoteip': remote_ip
            })
    except httpx.RequestError as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Failed to reach reCAPTCHA service: {e}")

    if resp.status_code != 200:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"reCAPTCHA service error: {resp.status_code}")

    data = resp.json()

    # Basic policy: require success true and score >= threshold (if provided)
    success = bool(data.get('success'))
    score = data.get('score')
    action = data.get('action')

    threshold = float(getattr(settings, 'RECAPTCHA_SCORE_THRESHOLD', 0.5))

    passed = success and (score is None or float(score) >= threshold)

    # Only return the minimal fields the frontend needs
    result: Dict[str, Any] = {
        'success': passed,
        'score': score,
        'action': action,
    }

    return result
