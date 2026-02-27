"""
Rule-based Trust Score Calculator.

Calculates trust scores based on weighted components:
1. Repayment History (40%) - on-time payment rate
2. Community Tenure (20%) - months active in community
3. Vouch Count Received (15%) - active vouches
4. Voucher Reliability (15%) - avg score of vouchers
5. Loan Volume History (10%) - total repaid successfully
"""
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
import hashlib
import json

from app.models import User, Repayment, LoanApplication, TrustScore, VouchRelationship, CommunityMembership
from app.core.config import settings
from app.core.neo4j import neo4j_service


class TrustScoreCalculator:
    """Calculate rule-based trust scores for users."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.weights = {
            "repayment_history": settings.WEIGHT_REPAYMENT,
            "community_tenure": settings.WEIGHT_TENURE,
            "vouch_count": settings.WEIGHT_VOUCH_COUNT,
            "voucher_reliability": settings.WEIGHT_VOUCHER_RELIABILITY,
            "loan_volume": settings.WEIGHT_LOAN_VOLUME,
        }
    
    async def calculate_score(self, user_id: int) -> Tuple[float, Dict, str]:
        """
        Calculate trust score for a user.
        
        Returns:
            tuple: (score, breakdown_dict, explanation_text)
        """
        # Check if user exists
        result = await self.db.execute(select(User).filter(User.id == user_id))
        user = result.scalar_one_or_none()
        
        if not user:
            raise ValueError(f"User {user_id} not found")
        
        # Calculate each component
        repayment_score, repayment_data = await self._calculate_repayment_history(user_id)
        tenure_score, tenure_data = await self._calculate_community_tenure(user_id)
        vouch_score, vouch_data = await self._calculate_vouch_count(user_id)
        voucher_rel_score, voucher_rel_data = await self._calculate_voucher_reliability(user_id)
        loan_volume_score, loan_volume_data = await self._calculate_loan_volume(user_id)
        
        # Check if cold start (new user with no history)
        is_cold_start = (
            repayment_data["total_repayments"] == 0 and
            tenure_data["months_active"] == 0 and
            vouch_data["vouch_count"] == 0
        )
        
        if is_cold_start:
            final_score = settings.COLD_START_SCORE
            explanation = self._generate_cold_start_explanation(user.name)
        else:
            # Weighted sum
            final_score = (
                repayment_score * self.weights["repayment_history"] +
                tenure_score * self.weights["community_tenure"] +
                vouch_score * self.weights["vouch_count"] +
                voucher_rel_score * self.weights["voucher_reliability"] +
                loan_volume_score * self.weights["loan_volume"]
            )
            
            explanation = self._generate_explanation(
                user.name,
                repayment_score, repayment_data,
                tenure_score, tenure_data,
                vouch_score, vouch_data,
                voucher_rel_score, voucher_rel_data,
                loan_volume_score, loan_volume_data
            )
        
        # Build breakdown
        breakdown = {
            "final_score": round(final_score, 2),
            "is_cold_start": is_cold_start,
            "components": {
                "repayment_history": {
                    "score": round(repayment_score, 2),
                    "weight": self.weights["repayment_history"],
                    "weighted_contribution": round(repayment_score * self.weights["repayment_history"], 2),
                    "data": repayment_data
                },
                "community_tenure": {
                    "score": round(tenure_score, 2),
                    "weight": self.weights["community_tenure"],
                    "weighted_contribution": round(tenure_score * self.weights["community_tenure"], 2),
                    "data": tenure_data
                },
                "vouch_count": {
                    "score": round(vouch_score, 2),
                    "weight": self.weights["vouch_count"],
                    "weighted_contribution": round(vouch_score * self.weights["vouch_count"], 2),
                    "data": vouch_data
                },
                "voucher_reliability": {
                    "score": round(voucher_rel_score, 2),
                    "weight": self.weights["voucher_reliability"],
                    "weighted_contribution": round(voucher_rel_score * self.weights["voucher_reliability"], 2),
                    "data": voucher_rel_data
                },
                "loan_volume": {
                    "score": round(loan_volume_score, 2),
                    "weight": self.weights["loan_volume"],
                    "weighted_contribution": round(loan_volume_score * self.weights["loan_volume"], 2),
                    "data": loan_volume_data
                }
            },
            "computed_at": datetime.utcnow().isoformat()
        }
        
        return round(final_score, 2), breakdown, explanation
    
    async def _calculate_repayment_history(self, user_id: int) -> Tuple[float, Dict]:
        """Calculate repayment history score (40% weight)."""
        # Get all loans for user
        loan_result = await self.db.execute(
            select(LoanApplication)
            .filter(LoanApplication.borrower_id == user_id)
        )
        loans = loan_result.scalars().all()
        
        if not loans:
            return 0.0, {
                "total_repayments": 0,
                "on_time_repayments": 0,
                "on_time_rate": 0.0,
                "late_repayments": 0
            }
        
        loan_ids = [loan.id for loan in loans]
        
        # Get all repayments
        repayment_result = await self.db.execute(
            select(Repayment)
            .filter(Repayment.loan_id.in_(loan_ids))
            .filter(Repayment.paid_date.isnot(None))
        )
        repayments = repayment_result.scalars().all()
        
        if not repayments:
            return 0.0, {
                "total_repayments": 0,
                "on_time_repayments": 0,
                "on_time_rate": 0.0,
                "late_repayments": 0
            }
        
        total_repayments = len(repayments)
        on_time_repayments = sum(1 for r in repayments if r.on_time == 1)
        late_repayments = total_repayments - on_time_repayments
        
        on_time_rate = on_time_repayments / total_repayments if total_repayments > 0 else 0.0
        
        # Score: 0-1000 based on on-time rate
        score = on_time_rate * 1000
        
        return score, {
            "total_repayments": total_repayments,
            "on_time_repayments": on_time_repayments,
            "on_time_rate": round(on_time_rate, 3),
            "late_repayments": late_repayments
        }
    
    async def _calculate_community_tenure(self, user_id: int) -> Tuple[float, Dict]:
        """Calculate community tenure score (20% weight)."""
        # Get earliest community membership
        result = await self.db.execute(
            select(func.min(CommunityMembership.joined_at))
            .filter(CommunityMembership.user_id == user_id)
            .filter(CommunityMembership.is_active == 1)
        )
        earliest_join = result.scalar()
        
        if not earliest_join:
            return 0.0, {
                "months_active": 0,
                "joined_date": None
            }
        
        # Calculate months active
        months_active = (datetime.utcnow() - earliest_join).days / 30.0
        
        # Score: 0-1000, capping at 24 months for max score
        score = min(months_active / 24.0, 1.0) * 1000
        
        return score, {
            "months_active": round(months_active, 1),
            "joined_date": earliest_join.isoformat()
        }
    
    async def _calculate_vouch_count(self, user_id: int) -> Tuple[float, Dict]:
        """Calculate vouch count score (15% weight)."""
        # Get active vouches from Neo4j
        vouch_count = await neo4j_service.get_user_vouch_count(user_id)
        
        # Score: 0-1000, capping at 10 vouches for max score
        score = min(vouch_count / 10.0, 1.0) * 1000
        
        return score, {
            "vouch_count": vouch_count
        }
    
    async def _calculate_voucher_reliability(self, user_id: int) -> Tuple[float, Dict]:
        """Calculate voucher reliability score (15% weight)."""
        # Get average trust score of vouchers from Neo4j
        avg_voucher_score = await neo4j_service.get_voucher_avg_score(user_id)
        
        # Score is directly the average (already 0-1000)
        score = avg_voucher_score if avg_voucher_score else 0.0
        
        return score, {
            "avg_voucher_score": round(avg_voucher_score, 2) if avg_voucher_score else 0.0
        }
    
    async def _calculate_loan_volume(self, user_id: int) -> Tuple[float, Dict]:
        """Calculate loan volume score (10% weight)."""
        # Get successfully repaid loans
        result = await self.db.execute(
            select(func.sum(LoanApplication.amount_approved))
            .filter(LoanApplication.borrower_id == user_id)
            .filter(LoanApplication.status == "repaid")
        )
        total_repaid = result.scalar() or 0.0
        
        # Score: 0-1000, capping at ₹100,000 for max score
        score = min(total_repaid / 100000.0, 1.0) * 1000
        
        return score, {
            "total_amount_repaid": round(total_repaid, 2),
            "currency": "INR"
        }
    
    def _generate_explanation(
        self,
        name: str,
        repayment_score: float, repayment_data: Dict,
        tenure_score: float, tenure_data: Dict,
        vouch_score: float, vouch_data: Dict,
        voucher_rel_score: float, voucher_rel_data: Dict,
        loan_volume_score: float, loan_volume_data: Dict
    ) -> str:
        """Generate plain-language explanation of score."""
        parts = [f"{name}'s trust score breakdown:"]
        
        # Repayment
        if repayment_data["total_repayments"] > 0:
            rate_pct = repayment_data["on_time_rate"] * 100
            parts.append(
                f"- Repayment: {rate_pct:.0f}% on-time rate "
                f"({repayment_data['on_time_repayments']}/{repayment_data['total_repayments']} payments)"
            )
        else:
            parts.append("- Repayment: No history yet")
        
        # Tenure
        if tenure_data["months_active"] > 0:
            parts.append(f"- Community: Active for {tenure_data['months_active']:.1f} months")
        else:
            parts.append("- Community: Just joined")
        
        # Vouches
        if vouch_data["vouch_count"] > 0:
            parts.append(f"- Vouches: {vouch_data['vouch_count']} community members vouch for them")
        else:
            parts.append("- Vouches: No vouches yet")
        
        # Voucher quality
        if voucher_rel_data["avg_voucher_score"] > 0:
            parts.append(f"- Voucher Quality: Vouchers have avg score of {voucher_rel_data['avg_voucher_score']:.0f}")
        
        # Loan volume
        if loan_volume_data["total_amount_repaid"] > 0:
            parts.append(f"- Loan History: ₹{loan_volume_data['total_amount_repaid']:,.0f} successfully repaid")
        
        return "\n".join(parts)
    
    def _generate_cold_start_explanation(self, name: str) -> str:
        """Generate explanation for new users."""
        return (
            f"{name} is building their credit profile. "
            f"Starting with a base score of {settings.COLD_START_SCORE}. "
            f"Score will improve with community participation, vouches, and successful repayments."
        )
    
    def generate_content_hash(self, breakdown: Dict) -> str:
        """Generate SHA-256 hash of breakdown for blockchain anchoring."""
        json_str = json.dumps(breakdown, sort_keys=True)
        return hashlib.sha256(json_str.encode()).hexdigest()
    
    async def save_score(
        self,
        user_id: int,
        score: float,
        breakdown: Dict,
        explanation: str
    ) -> TrustScore:
        """Save trust score to database."""
        content_hash = self.generate_content_hash(breakdown)
        
        trust_score = TrustScore(
            user_id=user_id,
            score=score,
            breakdown_json=breakdown,
            explanation=explanation,
            content_hash=content_hash
        )
        
        self.db.add(trust_score)
        await self.db.commit()
        await self.db.refresh(trust_score)
        
        # Update Neo4j user node
        result = await self.db.execute(select(User).filter(User.id == user_id))
        user = result.scalar_one()
        await neo4j_service.create_user_node(user_id, user.name, score)
        
        return trust_score
