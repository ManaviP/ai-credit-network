"""
Cluster Health Service - Calculate community health metrics.
"""
from datetime import datetime, timedelta
from typing import Dict, List
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    Community, CommunityMembership, LoanApplication,
    Repayment, TrustScore, User
)
from app.core.config import settings


class ClusterHealthService:
    """Calculate and track community/cluster health metrics."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def calculate_cluster_health(self, community_id: int) -> Dict:
        """
        Calculate comprehensive health metrics for a community.
        
        Returns:
            dict: Health metrics and status
        """
        # Get community
        result = await self.db.execute(
            select(Community).filter(Community.id == community_id)
        )
        community = result.scalar_one_or_none()
        
        if not community:
            raise ValueError(f"Community {community_id} not found")
        
        # Get active members
        members_result = await self.db.execute(
            select(CommunityMembership)
            .filter(CommunityMembership.community_id == community_id)
            .filter(CommunityMembership.is_active == 1)
        )
        memberships = members_result.scalars().all()
        member_ids = [m.user_id for m in memberships]
        
        if not member_ids:
            return {
                "community_id": community_id,
                "community_name": community.name,
                "cluster_type": community.cluster_type.value,
                "total_members": 0,
                "status": "empty",
                "message": "No active members"
            }
        
        # Average trust score
        avg_score_result = await self.db.execute(
            select(func.avg(TrustScore.score))
            .join(User, TrustScore.user_id == User.id)
            .filter(User.id.in_(member_ids))
            .filter(
                TrustScore.id.in_(
                    select(func.max(TrustScore.id))
                    .filter(TrustScore.user_id.in_(member_ids))
                    .group_by(TrustScore.user_id)
                )
            )
        )
        avg_trust_score = avg_score_result.scalar() or 0.0
        
        # On-time repayment rate (last 90 days)
        ninety_days_ago = datetime.utcnow() - timedelta(days=90)
        
        repayments_result = await self.db.execute(
            select(Repayment)
            .join(LoanApplication, Repayment.loan_id == LoanApplication.id)
            .filter(LoanApplication.borrower_id.in_(member_ids))
            .filter(Repayment.paid_date >= ninety_days_ago)
            .filter(Repayment.paid_date.isnot(None))
        )
        recent_repayments = repayments_result.scalars().all()
        
        if recent_repayments:
            on_time_count = sum(1 for r in recent_repayments if r.on_time == 1)
            on_time_rate = on_time_count / len(recent_repayments)
        else:
            on_time_rate = 0.0
        
        # Active borrowers
        active_borrowers_result = await self.db.execute(
            select(func.count(func.distinct(LoanApplication.borrower_id)))
            .filter(LoanApplication.community_id == community_id)
            .filter(LoanApplication.status.in_(["approved", "disbursed"]))
        )
        active_borrowers = active_borrowers_result.scalar() or 0
        
        # Loan statistics
        loans_result = await self.db.execute(
            select(
                func.sum(LoanApplication.amount_approved).label("total_disbursed"),
                func.count(LoanApplication.id).label("total_loans")
            )
            .filter(LoanApplication.community_id == community_id)
            .filter(LoanApplication.status.in_(["disbursed", "repaid"]))
        )
        loan_stats = loans_result.one()
        total_disbursed = loan_stats.total_disbursed or 0.0
        
        # Total repaid
        repaid_result = await self.db.execute(
            select(func.sum(Repayment.amount))
            .join(LoanApplication, Repayment.loan_id == LoanApplication.id)
            .filter(LoanApplication.community_id == community_id)
            .filter(Repayment.paid_date.isnot(None))
        )
        total_repaid = repaid_result.scalar() or 0.0
        
        # Outstanding
        outstanding = total_disbursed - total_repaid
        
        # Determine cluster status
        if avg_trust_score >= settings.STABLE_CLUSTER_THRESHOLD:
            status = "Stable"
            status_color = "green"
        elif avg_trust_score >= settings.GROWING_CLUSTER_THRESHOLD:
            status = "Growing"
            status_color = "yellow"
        else:
            status = "Fragile"
            status_color = "red"
        
        # At-risk members (score drop > 100 in last 30 days)
        at_risk_members = await self._identify_at_risk_members(member_ids)
        
        return {
            "community_id": community_id,
            "community_name": community.name,
            "cluster_type": community.cluster_type.value,
            "total_members": len(member_ids),
            "average_trust_score": round(avg_trust_score, 2),
            "on_time_repayment_rate": round(on_time_rate, 3),
            "on_time_repayment_rate_pct": round(on_time_rate * 100, 1),
            "active_borrowers_count": active_borrowers,
            "cluster_status": status,
            "status_color": status_color,
            "financial_summary": {
                "total_disbursed": round(total_disbursed, 2),
                "total_repaid": round(total_repaid, 2),
                "outstanding": round(outstanding, 2),
                "currency": "INR"
            },
            "at_risk_members": at_risk_members,
            "computed_at": datetime.utcnow().isoformat()
        }
    
    async def _identify_at_risk_members(self, member_ids: List[int]) -> List[Dict]:
        """Identify members with significant score drops."""
        at_risk = []
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        
        for user_id in member_ids:
            # Get latest score
            latest_result = await self.db.execute(
                select(TrustScore)
                .filter(TrustScore.user_id == user_id)
                .order_by(TrustScore.computed_at.desc())
                .limit(1)
            )
            latest_score = latest_result.scalar_one_or_none()
            
            if not latest_score:
                continue
            
            # Get score from 30 days ago
            old_result = await self.db.execute(
                select(TrustScore)
                .filter(TrustScore.user_id == user_id)
                .filter(TrustScore.computed_at <= thirty_days_ago)
                .order_by(TrustScore.computed_at.desc())
                .limit(1)
            )
            old_score = old_result.scalar_one_or_none()
            
            if old_score:
                score_drop = old_score.score - latest_score.score
                
                if score_drop > 100:
                    # Get user name
                    user_result = await self.db.execute(
                        select(User).filter(User.id == user_id)
                    )
                    user = user_result.scalar_one()
                    
                    at_risk.append({
                        "user_id": user_id,
                        "name": user.name,
                        "current_score": round(latest_score.score, 2),
                        "previous_score": round(old_score.score, 2),
                        "score_drop": round(score_drop, 2),
                        "days_ago": (datetime.utcnow() - old_score.computed_at).days
                    })
        
        return at_risk
