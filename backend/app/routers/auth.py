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
from sqlalchemy.exc import IntegrityError
from app.models import User
from app.schemas import (
    RegisterRequest, OAuthLoginRequest, TokenResponse, RefreshTokenRequest
)
from app.core.neo4j import neo4j_service
from app.core.config import settings

router = APIRouter(prefix="/auth", tags=["Authentication"])


from app.core.supabase import supabase

@router.post("/register", response_model=dict, status_code=status.HTTP_200_OK)
async def register(
    request: RegisterRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Register a new user after they have authenticated with Google OAuth via Supabase on the frontend.
    
    - Validates the provided Supabase access token.
    - Hashes Aadhaar for privacy compliance.
    - Creates user record with verified status.
    """
    # Verify the Supabase token
    try:
        user_response = supabase.auth.get_user(request.access_token)
        if not user_response.user:
            raise ValueError("No user found for token")
        
        supabase_user = user_response.user
        email = supabase_user.email
        provider_id = supabase_user.id
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Invalid OAuth token: {str(e)}")

    # Check if user already exists
    result = await db.execute(
        select(User).filter(User.provider_id == provider_id)
    )
    existing_user = result.scalar_one_or_none()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already registered with this Google account"
        )
    
    # Check if Aadhaar already exists
    aadhaar = request.aadhaar.replace(' ', '')
    aadhaar_hash = hash_aadhaar(aadhaar)
    
    result_aadhaar = await db.execute(select(User).filter(User.aadhaar_hash == aadhaar_hash))
    if result_aadhaar.scalar_one_or_none():
         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Aadhaar already registered")

    # Create new user
    user = User(
        name=request.name,
        email=request.email or email,
        phone=request.phone,
        auth_provider=request.provider,
        provider_id=provider_id,
        aadhaar_hash=aadhaar_hash,
        location=request.location,
        gender=request.gender,
        state=request.state,
        urban_rural=request.urban_rural,
        consent_given=request.consent_given,
        consent_timestamp=datetime.utcnow() if request.consent_given else None,
        is_verified=True # OAuth users are pre-verified
    )
    db.add(user)
    
    try:
        await db.commit()
        await db.refresh(user)
    except IntegrityError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Phone or Aadhaar already registered")
    
    # Create Neo4j user node with cold start score
    try:
        await neo4j_service.create_user_node(
            user.id,
            user.name,
            settings.COLD_START_SCORE
        )
    except Exception as e:
        print(f"Warning: Failed to create neo4j node: {str(e)}")

    # Generate tokens for our own backend access
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})
    
    return {
        "message": "Registration successful",
        "access_token": access_token,
        "refresh_token": refresh_token,
        "user_id": user.id
    }


@router.post("/oauth-login", response_model=TokenResponse)
async def oauth_login(
    request: OAuthLoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Login with Supabase Google OAuth token.
    
    - Validates token via Supabase.
    - Retrieves local user record.
    - Returns local access and refresh tokens.
    """
    # Verify token via Supabase
    try:
        user_response = supabase.auth.get_user(request.access_token)
        if not user_response.user:
            raise ValueError("No user found for token")
        
        provider_id = user_response.user.id
    except Exception as e:
        print(f"OAuth Verification Failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired OAuth token"
        )
        
    # Get local User
    result = await db.execute(
        select(User).filter(User.provider_id == provider_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found in local database. Please complete registration first."
        )
    
    # Generate tokens for our own backend access
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
