"""
Loans router - apply, view status, repay, and track history.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from datetime import datetime, timedelta

from app.core import get_db, get_current_user
from app.models import User, LoanApplication, Repayment, TrustScore, CommunityMembership
from app.schemas import (
    LoanApplicationRequest, LoanApplicationResponse,
    RepaymentRequest, RepaymentResponse
)
from app.tasks.scoring_tasks import compute_trust_score_task

router = APIRouter(prefix="/loans", tags=["Loans"])


@router.post("/apply", response_model=LoanApplicationResponse, status_code=status.HTTP_201_CREATED)
async def apply_for_loan(
    request: LoanApplicationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Submit a loan application.
    
    Captures current trust score at application time for audit trail.
    """
    # Verify user is member of the community
    membership = await db.execute(
        select(CommunityMembership)
        .filter(CommunityMembership.user_id == current_user.id)
        .filter(CommunityMembership.community_id == request.community_id)
        .filter(CommunityMembership.is_active == 1)
    )
    
    if not membership.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You must be a member of this community to apply for a loan"
        )
    
    # Get current trust score
    score_result = await db.execute(
        select(TrustScore)
        .filter(TrustScore.user_id == current_user.id)
        .order_by(TrustScore.computed_at.desc())
        .limit(1)
    )
    current_score = score_result.scalar_one_or_none()
    
    # Create loan application
    loan = LoanApplication(
        borrower_id=current_user.id,
        community_id=request.community_id,
        amount_requested=request.amount_requested,
        purpose=request.purpose,
        tenure_months=request.tenure_months,
        status="pending",
        trust_score_at_application=current_score.score if current_score else None
    )
    
    db.add(loan)
    await db.commit()
    await db.refresh(loan)
    
    return LoanApplicationResponse(
        id=loan.id,
        borrower_id=loan.borrower_id,
        community_id=loan.community_id,
        amount_requested=loan.amount_requested,
        amount_approved=loan.amount_approved,
        purpose=loan.purpose,
        status=loan.status,
        applied_at=loan.applied_at,
        trust_score_at_application=loan.trust_score_at_application
    )


@router.get("/{loan_id}/status", response_model=dict)
async def get_loan_status(
    loan_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get detailed status of a loan application.
    """
    result = await db.execute(
        select(LoanApplication).filter(LoanApplication.id == loan_id)
    )
    loan = result.scalar_one_or_none()
    
    if not loan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Loan not found"
        )
    
    # Verify user is the borrower or community anchor
    if loan.borrower_id != current_user.id:
        # Check if user is anchor
        membership = await db.execute(
            select(CommunityMembership)
            .filter(CommunityMembership.user_id == current_user.id)
            .filter(CommunityMembership.community_id == loan.community_id)
            .filter(CommunityMembership.role == "anchor")
        )
        if not membership.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to view this loan"
            )
    
    # Get repayments
    repayments_result = await db.execute(
        select(Repayment)
        .filter(Repayment.loan_id == loan_id)
        .order_by(Repayment.due_date)
    )
    repayments = repayments_result.scalars().all()
    
    return {
        "loan_id": loan.id,
        "borrower_id": loan.borrower_id,
        "amount_requested": loan.amount_requested,
        "amount_approved": loan.amount_approved,
        "status": loan.status.value,
        "applied_at": loan.applied_at.isoformat(),
        "approved_at": loan.approved_at.isoformat() if loan.approved_at else None,
        "disbursed_at": loan.disbursed_at.isoformat() if loan.disbursed_at else None,
        "tenure_months": loan.tenure_months,
        "interest_rate": loan.interest_rate,
        "repayments": [
            {
                "id": r.id,
                "amount": r.amount,
                "due_date": r.due_date.isoformat(),
                "paid_date": r.paid_date.isoformat() if r.paid_date else None,
                "on_time": r.on_time == 1 if r.on_time is not None else None
            }
            for r in repayments
        ]
    }


@router.post("/{loan_id}/repay", response_model=dict)
async def log_repayment(
    loan_id: int,
    request: RepaymentRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Log a loan repayment.
    
    Automatically triggers trust score recalculation.
    """
    # Get loan
    result = await db.execute(
        select(LoanApplication).filter(LoanApplication.id == loan_id)
    )
    loan = result.scalar_one_or_none()
    
    if not loan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Loan not found"
        )
    
    # Verify user is the borrower
    if loan.borrower_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the borrower can log repayments"
        )
    
    # Verify loan is disbursed
    if loan.status not in ["disbursed", "approved"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Loan is not active for repayments"
        )
    
    # Get next pending repayment
    pending_result = await db.execute(
        select(Repayment)
        .filter(Repayment.loan_id == loan_id)
        .filter(Repayment.paid_date.is_(None))
        .order_by(Repayment.due_date)
        .limit(1)
    )
    pending_repayment = pending_result.scalar_one_or_none()
    
    if not pending_repayment:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No pending repayments found"
        )
    
    # Mark as paid
    paid_date = datetime.utcnow()
    pending_repayment.paid_date = paid_date
    pending_repayment.payment_method = request.payment_method
    pending_repayment.transaction_id = request.transaction_id
    
    # Check if on time (within 3 days grace period)
    grace_period = pending_repayment.due_date + timedelta(days=3)
    pending_repayment.on_time = 1 if paid_date <= grace_period else 0
    
    await db.commit()
    
    # Check if all repayments are done
    remaining_result = await db.execute(
        select(Repayment)
        .filter(Repayment.loan_id == loan_id)
        .filter(Repayment.paid_date.is_(None))
    )
    remaining = remaining_result.scalars().all()
    
    if not remaining:
        loan.status = "repaid"
        loan.repaid_at = paid_date
        await db.commit()
    
    # Trigger async trust score recalculation
    compute_trust_score_task.delay(current_user.id)
    
    return {
        "message": "Repayment logged successfully",
        "repayment_id": pending_repayment.id,
        "amount": pending_repayment.amount,
        "on_time": pending_repayment.on_time == 1,
        "loan_status": loan.status.value,
        "trust_score_update": "Computing in background"
    }


@router.get("/my-loans", response_model=List[LoanApplicationResponse])
async def get_my_loans(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all loans for the current user.
    """
    result = await db.execute(
        select(LoanApplication)
        .filter(LoanApplication.borrower_id == current_user.id)
        .order_by(LoanApplication.applied_at.desc())
    )
    loans = result.scalars().all()
    
    return [
        LoanApplicationResponse(
            id=loan.id,
            borrower_id=loan.borrower_id,
            community_id=loan.community_id,
            amount_requested=loan.amount_requested,
            amount_approved=loan.amount_approved,
            purpose=loan.purpose,
            status=loan.status,
            applied_at=loan.applied_at,
            trust_score_at_application=loan.trust_score_at_application
        )
        for loan in loans
    ]
