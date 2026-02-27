"""
Loan and repayment reminder tasks.
"""
from sqlalchemy import select
from datetime import datetime, timedelta
import asyncio

from app.tasks.celery_app import celery_app
from app.core.database import AsyncSessionLocal
from app.models import Repayment, LoanApplication, User


@celery_app.task(name="app.tasks.loan_tasks.send_repayment_reminder")
def send_repayment_reminder_task(loan_id: int):
    """
    Send repayment reminder for a specific loan.
    
    Triggered 3 days before due date.
    """
    return asyncio.run(send_repayment_reminder_async(loan_id))


async def send_repayment_reminder_async(loan_id: int):
    """Async implementation of repayment reminder."""
    async with AsyncSessionLocal() as db:
        try:
            # Get loan and borrower
            result = await db.execute(
                select(LoanApplication, User)
                .join(User, LoanApplication.borrower_id == User.id)
                .filter(LoanApplication.id == loan_id)
            )
            row = result.one_or_none()
            
            if not row:
                return {"error": f"Loan {loan_id} not found"}
            
            loan, borrower = row
            
            # Get next pending repayment
            repayment_result = await db.execute(
                select(Repayment)
                .filter(Repayment.loan_id == loan_id)
                .filter(Repayment.paid_date.is_(None))
                .order_by(Repayment.due_date)
                .limit(1)
            )
            repayment = repayment_result.scalar_one_or_none()
            
            if not repayment:
                return {"message": "No pending repayments"}
            
            # TODO: Send SMS reminder
            print(f"📱 SMS to {borrower.phone}: Repayment of ₹{repayment.amount} due on {repayment.due_date.date()}")
            
            return {
                "loan_id": loan_id,
                "borrower_id": borrower.id,
                "borrower_phone": borrower.phone,
                "amount": repayment.amount,
                "due_date": repayment.due_date.isoformat()
            }
        
        except Exception as e:
            return {"error": str(e), "loan_id": loan_id}


@celery_app.task(name="app.tasks.loan_tasks.send_upcoming_repayment_reminders")
def send_upcoming_repayment_reminders():
    """
    Send reminders for all repayments due in next 3 days.
    
    Scheduled to run daily at 9 AM.
    """
    return asyncio.run(send_upcoming_repayment_reminders_async())


async def send_upcoming_repayment_reminders_async():
    """Async implementation of bulk reminders."""
    async with AsyncSessionLocal() as db:
        try:
            # Get repayments due in next 3 days
            today = datetime.utcnow()
            three_days_later = today + timedelta(days=3)
            
            result = await db.execute(
                select(Repayment)
                .filter(Repayment.paid_date.is_(None))
                .filter(Repayment.due_date >= today)
                .filter(Repayment.due_date <= three_days_later)
            )
            upcoming_repayments = result.scalars().all()
            
            reminders_sent = []
            for repayment in upcoming_repayments:
                reminder_result = await send_repayment_reminder_async(repayment.loan_id)
                reminders_sent.append(reminder_result)
            
            return {
                "total_reminders": len(reminders_sent),
                "results": reminders_sent
            }
        
        except Exception as e:
            return {"error": str(e)}
