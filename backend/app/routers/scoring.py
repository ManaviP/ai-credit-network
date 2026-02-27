"""
Scoring router - compute and explain trust scores.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core import get_db, get_current_user
from app.models import User
from app.services import TrustScoreCalculator
from app.tasks.celery_app import compute_trust_score_task

router = APIRouter(prefix="/scoring", tags=["Scoring"])


@router.post("/compute/{user_id}", response_model=dict)
async def trigger_score_computation(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Trigger trust score recalculation for a user.
    
    Runs asynchronously via Celery.
    Users can trigger their own score or community anchors can trigger member scores.
    """
    # Verify user exists
    result = await db.execute(
        select(User).filter(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Permission check: user can compute their own score
    # TODO: Add permission for community anchors to trigger member scores
    if user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only trigger your own score computation"
        )
    
    # Trigger async task
    task = compute_trust_score_task.delay(user_id)
    
    return {
        "message": "Trust score computation started",
        "user_id": user_id,
        "task_id": task.id,
        "status": "processing"
    }


@router.get("/explain/{user_id}", response_model=dict)
async def get_score_explanation(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get plain-language explanation of a user's trust score.
    
    Includes full breakdown of all scoring components.
    """
    # Verify user exists
    result = await db.execute(
        select(User).filter(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Calculate score (won't save, just for explanation)
    calculator = TrustScoreCalculator(db)
    
    try:
        score, breakdown, explanation = await calculator.calculate_score(user_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to calculate score: {str(e)}"
        )
    
    return {
        "user_id": user_id,
        "user_name": user.name,
        "score": score,
        "explanation": explanation,
        "breakdown": breakdown,
        "components_detail": {
            "repayment_history": {
                "description": "On-time payment rate from past loans",
                "weight": "40%",
                "score": breakdown["components"]["repayment_history"]["score"],
                "contribution": breakdown["components"]["repayment_history"]["weighted_contribution"]
            },
            "community_tenure": {
                "description": "Months active in community",
                "weight": "20%",
                "score": breakdown["components"]["community_tenure"]["score"],
                "contribution": breakdown["components"]["community_tenure"]["weighted_contribution"]
            },
            "vouch_count": {
                "description": "Number of active community vouches",
                "weight": "15%",
                "score": breakdown["components"]["vouch_count"]["score"],
                "contribution": breakdown["components"]["vouch_count"]["weighted_contribution"]
            },
            "voucher_reliability": {
                "description": "Average trust score of vouchers",
                "weight": "15%",
                "score": breakdown["components"]["voucher_reliability"]["score"],
                "contribution": breakdown["components"]["voucher_reliability"]["weighted_contribution"]
            },
            "loan_volume": {
                "description": "Total amount successfully repaid",
                "weight": "10%",
                "score": breakdown["components"]["loan_volume"]["score"],
                "contribution": breakdown["components"]["loan_volume"]["weighted_contribution"]
            }
        }
    }
