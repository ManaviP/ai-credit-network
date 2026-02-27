"""
Unit tests for TrustScoreCalculator.
"""
import pytest
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.models import User, Community, CommunityMembership, LoanApplication, Repayment, TrustScore
from app.services import TrustScoreCalculator
from app.core.config import settings


# Test database setup
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

@pytest.fixture
async def db_session():
    """Create a test database session."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        yield session
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest.mark.asyncio
async def test_cold_start_score(db_session):
    """Test score calculation for new user with no history."""
    # Create new user
    user = User(
        name="New User",
        phone="1234567890",
        aadhaar_hash="hash123",
        is_verified=True
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    
    # Calculate score
    calculator = TrustScoreCalculator(db_session)
    score, breakdown, explanation = await calculator.calculate_score(user.id)
    
    # Assertions
    assert score == settings.COLD_START_SCORE
    assert breakdown["is_cold_start"] is True
    assert "building their credit profile" in explanation.lower()


@pytest.mark.asyncio
async def test_repayment_score_component(db_session):
    """Test repayment history scoring."""
    # Create user and community
    user = User(name="Test User", phone="1234567890", aadhaar_hash="hash123", is_verified=True)
    community = Community(name="Test Community", cluster_type="shg", anchor_user_id=1)
    db_session.add_all([user, community])
    await db_session.commit()
    await db_session.refresh(user)
    await db_session.refresh(community)
    
    # Create loan with repayments
    loan = LoanApplication(
        borrower_id=user.id,
        community_id=community.id,
        amount_requested=10000,
        amount_approved=10000,
        purpose="Business",
        status="disbursed",
        tenure_months=6
    )
    db_session.add(loan)
    await db_session.commit()
    await db_session.refresh(loan)
    
    # Add repayments (8 on-time, 2 late)
    for i in range(10):
        repayment = Repayment(
            loan_id=loan.id,
            amount=1000,
            due_date=datetime.utcnow() - timedelta(days=(10-i)*30),
            paid_date=datetime.utcnow() - timedelta(days=(10-i)*30),
            on_time=1 if i < 8 else 0
        )
        db_session.add(repayment)
    
    await db_session.commit()
    
    # Calculate score
    calculator = TrustScoreCalculator(db_session)
    score, breakdown, explanation = await calculator.calculate_score(user.id)
    
    # Repayment component should be 800 (80% on-time rate)
    repayment_component = breakdown["components"]["repayment_history"]
    assert repayment_component["score"] == 800.0
    assert repayment_component["data"]["on_time_rate"] == 0.8


@pytest.mark.asyncio
async def test_community_tenure_score(db_session):
    """Test community tenure scoring."""
    # Create user and community
    user = User(name="Test User", phone="1234567890", aadhaar_hash="hash123", is_verified=True)
    community = Community(name="Test Community", cluster_type="shg", anchor_user_id=1)
    db_session.add_all([user, community])
    await db_session.commit()
    await db_session.refresh(user)
    await db_session.refresh(community)
    
    # Create membership from 12 months ago
    membership = CommunityMembership(
        user_id=user.id,
        community_id=community.id,
        role="member",
        joined_at=datetime.utcnow() - timedelta(days=365),
        is_active=1
    )
    db_session.add(membership)
    await db_session.commit()
    
    # Calculate score
    calculator = TrustScoreCalculator(db_session)
    score, breakdown, explanation = await calculator.calculate_score(user.id)
    
    # Tenure component should be ~500 (12 months / 24 months max * 1000)
    tenure_component = breakdown["components"]["community_tenure"]
    assert 450 <= tenure_component["score"] <= 550  # Allow some variance
    assert tenure_component["data"]["months_active"] >= 11.5


@pytest.mark.asyncio
async def test_full_profile_score(db_session):
    """Test score calculation for user with complete history."""
    # Create anchor user first
    anchor = User(name="Anchor", phone="0000000000", aadhaar_hash="anchor_hash", is_verified=True)
    db_session.add(anchor)
    await db_session.commit()
    await db_session.refresh(anchor)
    
    # Create user and community
    user = User(name="Active User", phone="1234567890", aadhaar_hash="hash123", is_verified=True)
    community = Community(name="Strong Community", cluster_type="shg", anchor_user_id=anchor.id)
    db_session.add_all([user, community])
    await db_session.commit()
    await db_session.refresh(user)
    await db_session.refresh(community)
    
    # Membership (12 months ago)
    membership = CommunityMembership(
        user_id=user.id,
        community_id=community.id,
        role="member",
        joined_at=datetime.utcnow() - timedelta(days=365),
        is_active=1
    )
    db_session.add(membership)
    
    # Loan with perfect repayment
    loan = LoanApplication(
        borrower_id=user.id,
        community_id=community.id,
        amount_requested=50000,
        amount_approved=50000,
        purpose="Business expansion",
        status="repaid",
        tenure_months=12
    )
    db_session.add(loan)
    await db_session.commit()
    await db_session.refresh(loan)
    
    # Perfect repayments
    for i in range(12):
        repayment = Repayment(
            loan_id=loan.id,
            amount=4500,
            due_date=datetime.utcnow() - timedelta(days=(12-i)*30),
            paid_date=datetime.utcnow() - timedelta(days=(12-i)*30),
            on_time=1
        )
        db_session.add(repayment)
    
    await db_session.commit()
    
    # Calculate score
    calculator = TrustScoreCalculator(db_session)
    score, breakdown, explanation = await calculator.calculate_score(user.id)
    
    # Should have good score from repayment (1000) and tenure (~500)
    assert score > 500
    assert breakdown["is_cold_start"] is False
    assert breakdown["components"]["repayment_history"]["score"] == 1000.0
