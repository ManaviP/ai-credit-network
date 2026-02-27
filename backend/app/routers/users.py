"""
Users router - user profiles, scores, and trust graphs.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core import get_db, get_current_user
from app.models import User, TrustScore
from app.schemas import UserProfile, UserScoreSummary, TrustGraphResponse
from app.core.neo4j import neo4j_service

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserProfile)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get current authenticated user's profile with latest trust score.
    """
    # Get latest trust score
    result = await db.execute(
        select(TrustScore)
        .filter(TrustScore.user_id == current_user.id)
        .order_by(TrustScore.computed_at.desc())
        .limit(1)
    )
    latest_score = result.scalar_one_or_none()
    
    return UserProfile(
        id=current_user.id,
        name=current_user.name,
        phone=current_user.phone,
        location=current_user.location,
        tier=current_user.tier,
        joined_at=current_user.joined_at,
        current_trust_score=latest_score.score if latest_score else None
    )


@router.get("/{user_id}/score", response_model=dict)
async def get_user_score_breakdown(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get full trust score breakdown for a user.
    
    Users can view their own score or scores of community members.
    """
    # Get user
    result = await db.execute(
        select(User).filter(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Get latest trust score
    score_result = await db.execute(
        select(TrustScore)
        .filter(TrustScore.user_id == user_id)
        .order_by(TrustScore.computed_at.desc())
        .limit(1)
    )
    latest_score = score_result.scalar_one_or_none()
    
    if not latest_score:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No trust score computed yet"
        )
    
    return {
        "user_id": user.id,
        "user_name": user.name,
        "score": latest_score.score,
        "breakdown": latest_score.breakdown_json,
        "explanation": latest_score.explanation,
        "computed_at": latest_score.computed_at.isoformat(),
        "score_type": latest_score.score_type.value
    }


@router.get("/{user_id}/graph", response_model=TrustGraphResponse)
async def get_user_trust_graph(
    user_id: int,
    depth: int = 2,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get trust graph around a user for D3.js visualization.
    
    Args:
        user_id: Target user ID
        depth: Graph depth (1-3, default 2)
    
    Returns:
        Graph with nodes and edges for visualization
    """
    # Validate user exists
    result = await db.execute(
        select(User).filter(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Limit depth
    if depth < 1 or depth > 3:
        depth = 2
    
    # Get graph from Neo4j
    graph_data = await neo4j_service.get_user_trust_graph(user_id, depth)
    
    return TrustGraphResponse(
        nodes=graph_data["nodes"],
        edges=graph_data["edges"]
    )
