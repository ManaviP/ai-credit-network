"""
Trust score computation tasks.
"""
from celery import Task
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import asyncio

from app.tasks.celery_app import celery_app
from app.core.database import AsyncSessionLocal
from app.services import TrustScoreCalculator
from app.models import User, AuditLog


class AsyncTask(Task):
    """Base task with async support."""
    
    def __call__(self, *args, **kwargs):
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(self.run_async(*args, **kwargs))
    
    async def run_async(self, *args, **kwargs):
        raise NotImplementedError()


@celery_app.task(bind=True, base=AsyncTask, name="app.tasks.scoring_tasks.compute_trust_score")
def compute_trust_score_task(self, user_id: int):
    """
    Asynchronously compute trust score for a user.
    
    Triggered after:
    - Loan repayment
    - New vouch received
    - Manual trigger
    """
    return asyncio.run(compute_trust_score_async(user_id))


async def compute_trust_score_async(user_id: int):
    """Async implementation of trust score computation."""
    async with AsyncSessionLocal() as db:
        try:
            # Get user
            result = await db.execute(select(User).filter(User.id == user_id))
            user = result.scalar_one_or_none()
            
            if not user:
                return {"error": f"User {user_id} not found"}
            
            # Calculate score
            calculator = TrustScoreCalculator(db)
            score, breakdown, explanation = await calculator.calculate_score(user_id)
            
            # Save score
            trust_score = await calculator.save_score(
                user_id=user_id,
                score=score,
                breakdown=breakdown,
                explanation=explanation
            )
            
            # Log to audit
            audit_log = AuditLog(
                user_id=user_id,
                event_type="score_computed",
                entity_id=trust_score.id,
                payload_json={
                    "score": score,
                    "breakdown": breakdown,
                    "explanation": explanation
                }
            )
            db.add(audit_log)
            await db.commit()
            
            return {
                "user_id": user_id,
                "score": score,
                "computed_at": trust_score.computed_at.isoformat()
            }
        
        except Exception as e:
            await db.rollback()
            return {"error": str(e), "user_id": user_id}
