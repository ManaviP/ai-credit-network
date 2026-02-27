"""
Admin router - fairness reports and compliance tools.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime
from typing import Dict

from app.core import get_db, get_current_user
from app.models import User, TrustScore

router = APIRouter(prefix="/admin", tags=["Admin"])


# TODO: Add proper admin role checking
async def verify_admin(current_user: User = Depends(get_current_user)):
    """Verify user has admin permissions."""
    # In production, check user role or permissions
    # For MVP, allow all authenticated users
    return current_user


@router.get("/fairness-report", response_model=dict)
async def get_fairness_report(
    admin_user: User = Depends(verify_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Generate fairness report showing average scores by demographic groups.
    
    Ensures DPDP Act 2023 compliance by anonymizing individual data.
    Only shows aggregated statistics.
    """
    # Total users
    total_users_result = await db.execute(
        select(func.count(User.id))
    )
    total_users = total_users_result.scalar()
    
    # Get latest scores for all users
    latest_scores_subquery = (
        select(
            TrustScore.user_id,
            func.max(TrustScore.id).label("max_score_id")
        )
        .group_by(TrustScore.user_id)
        .subquery()
    )
    
    # Average score by gender
    gender_scores = {}
    gender_result = await db.execute(
        select(
            User.gender,
            func.avg(TrustScore.score).label("avg_score"),
            func.count(User.id).label("count")
        )
        .join(TrustScore, User.id == TrustScore.user_id)
        .join(
            latest_scores_subquery,
            (TrustScore.user_id == latest_scores_subquery.c.user_id) &
            (TrustScore.id == latest_scores_subquery.c.max_score_id)
        )
        .filter(User.gender.isnot(None))
        .group_by(User.gender)
    )
    
    for row in gender_result:
        if row.count >= 5:  # Only show if 5+ users for privacy
            gender_scores[row.gender or "not_specified"] = {
                "avg_score": round(row.avg_score, 2),
                "count": row.count
            }
    
    # Average score by state
    state_scores = {}
    state_result = await db.execute(
        select(
            User.state,
            func.avg(TrustScore.score).label("avg_score"),
            func.count(User.id).label("count")
        )
        .join(TrustScore, User.id == TrustScore.user_id)
        .join(
            latest_scores_subquery,
            (TrustScore.user_id == latest_scores_subquery.c.user_id) &
            (TrustScore.id == latest_scores_subquery.c.max_score_id)
        )
        .filter(User.state.isnot(None))
        .group_by(User.state)
    )
    
    for row in state_result:
        if row.count >= 5:
            state_scores[row.state or "not_specified"] = {
                "avg_score": round(row.avg_score, 2),
                "count": row.count
            }
    
    # Average score by urban/rural
    urban_rural_scores = {}
    urban_rural_result = await db.execute(
        select(
            User.urban_rural,
            func.avg(TrustScore.score).label("avg_score"),
            func.count(User.id).label("count")
        )
        .join(TrustScore, User.id == TrustScore.user_id)
        .join(
            latest_scores_subquery,
            (TrustScore.user_id == latest_scores_subquery.c.user_id) &
            (TrustScore.id == latest_scores_subquery.c.max_score_id)
        )
        .filter(User.urban_rural.isnot(None))
        .group_by(User.urban_rural)
    )
    
    for row in urban_rural_result:
        if row.count >= 5:
            urban_rural_scores[row.urban_rural or "not_specified"] = {
                "avg_score": round(row.avg_score, 2),
                "count": row.count
            }
    
    # Overall average
    overall_result = await db.execute(
        select(func.avg(TrustScore.score))
        .join(
            latest_scores_subquery,
            (TrustScore.user_id == latest_scores_subquery.c.user_id) &
            (TrustScore.id == latest_scores_subquery.c.max_score_id)
        )
    )
    overall_avg = overall_result.scalar() or 0.0
    
    return {
        "report_generated_at": datetime.utcnow().isoformat(),
        "total_users": total_users,
        "overall_average_score": round(overall_avg, 2),
        "by_gender": gender_scores if gender_scores else {"message": "Insufficient data (min 5 users per group)"},
        "by_state": state_scores if state_scores else {"message": "Insufficient data (min 5 users per group)"},
        "by_urban_rural": urban_rural_scores if urban_rural_scores else {"message": "Insufficient data (min 5 users per group)"},
        "privacy_note": "Only groups with 5+ users are shown to protect individual privacy (DPDP Act 2023 compliance)"
    }
