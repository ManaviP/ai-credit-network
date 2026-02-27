"""
Authentication router - handles registration, OTP verification, and JWT tokens.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timedelta
import random
import string

from app.core import get_db, hash_aadhaar, create_access_token, create_refresh_token, decode_token
from app.models import User
from app.schemas import (
    RegisterRequest, OAuthLoginRequest, TokenResponse, RefreshTokenRequest, VerifyOTPRequest
)
from app.core.neo4j import neo4j_service
from app.core.config import settings

router = APIRouter(prefix="/auth", tags=["Authentication"])


def generate_otp() -> str:
    """Generate 6-digit OTP."""
    return ''.join(random.choices(string.digits, k=6))


async def send_otp_sms(phone: str, otp: str):
    """
    Send OTP via SMS.
    
    In production, integrate with SMS provider (Twilio, AWS SNS, etc.)
    For MVP, just log it.
    """
    print(f"📱 SMS to {phone}: Your OTP is {otp}")
    # TODO: Integrate actual SMS service
    # if settings.SMS_API_KEY:
    #     async with httpx.AsyncClient() as client:
    #         await client.post(settings.SMS_API_URL, json={
    #             "to": phone,
    #             "message": f"Your OTP is {otp}",
    #             "sender_id": settings.SMS_SENDER_ID
    #         })


@router.post("/register", response_model=dict, status_code=status.HTTP_200_OK)
async def register(
    request: RegisterRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Register a new user and send OTP for verification.
    
    - Hashes Aadhaar for privacy compliance
    - Generates and sends OTP
    - Creates user record with unverified status
    """
    # Check if phone already exists
    result = await db.execute(
        select(User).filter(User.phone == request.phone)
    )
    existing_user = result.scalar_one_or_none()
    
    if existing_user and existing_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Phone number already registered"
        )
    
    # Hash Aadhaar for privacy
    aadhaar_hash = hash_aadhaar(request.aadhaar)
    
    # Generate OTP
    otp = generate_otp()
    otp_expires = datetime.utcnow() + timedelta(minutes=10)
    
    if existing_user:
        # Update existing unverified user
        existing_user.name = request.name
        existing_user.aadhaar_hash = aadhaar_hash
        existing_user.location = request.location
        existing_user.gender = request.gender
        existing_user.state = request.state
        existing_user.urban_rural = request.urban_rural
        existing_user.consent_given = request.consent_given
        existing_user.consent_timestamp = datetime.utcnow() if request.consent_given else None
        existing_user.otp_code = otp
        existing_user.otp_expires_at = otp_expires
        user = existing_user
    else:
        # Create new user
        user = User(
            name=request.name,
            phone=request.phone,
            aadhaar_hash=aadhaar_hash,
            location=request.location,
            gender=request.gender,
            state=request.state,
            urban_rural=request.urban_rural,
            consent_given=request.consent_given,
            consent_timestamp=datetime.utcnow() if request.consent_given else None,
            otp_code=otp,
            otp_expires_at=otp_expires,
            is_verified=False
        )
        db.add(user)
    
    await db.commit()
    await db.refresh(user)
    
    # Send OTP
    await send_otp_sms(user.phone, otp)
    
    return {
        "message": "OTP sent successfully",
        "phone": user.phone,
        "expires_in_minutes": 10
    }


@router.post("/verify-otp", response_model=TokenResponse)
async def verify_otp(
    request: VerifyOTPRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Verify OTP and return JWT tokens.
    
    - Validates OTP code and expiration
    - Marks user as verified
    - Creates Neo4j user node
    - Returns access and refresh tokens
    """
    # Get user
    result = await db.execute(
        select(User).filter(User.phone == request.phone)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check OTP
    if user.otp_code != request.otp:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid OTP"
        )
    
    # Check expiration
    if user.otp_expires_at < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OTP expired"
        )
    
    # Mark as verified
    user.is_verified = True
    user.otp_code = None
    user.otp_expires_at = None
    await db.commit()
    
    # Create Neo4j user node with cold start score
    await neo4j_service.create_user_node(
        user.id,
        user.name,
        settings.COLD_START_SCORE
    )
    
    # Generate tokens
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user_id=user.id
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    request: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Refresh access token using refresh token.
    """
    try:
        payload = decode_token(request.refresh_token)
        
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type"
            )
        
        user_id = payload.get("sub")
        
        # Verify user exists
        result = await db.execute(
            select(User).filter(User.id == int(user_id))
        )
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Generate new tokens
        access_token = create_access_token(data={"sub": str(user.id)})
        new_refresh_token = create_refresh_token(data={"sub": str(user.id)})
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=new_refresh_token,
            user_id=user.id
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
