"""
Seed script to generate sample data for testing.

Generates:
- 3 communities (SHG, Merchant, Neighborhood)
- 10 members per community
- Trust relationships (vouches)
- Realistic loan and repayment histories
"""
import asyncio
import random
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.core.config import settings
from app.core.security import hash_aadhaar
from app.models import (
    User, Community, CommunityMembership, VouchRelationship,
    LoanApplication, Repayment, TrustScore
)
from app.services import TrustScoreCalculator
from app.core.neo4j import neo4j_service


# Sample data
FIRST_NAMES = ["Priya", "Rajesh", "Anjali", "Amit", "Sunita", "Vikram", "Lakshmi", "Arjun", "Deepa", "Kiran"]
LAST_NAMES = ["Kumar", "Sharma", "Patel", "Singh", "Reddy", "Verma", "Nair", "Gupta", "Rao", "Joshi"]
LOCATIONS = ["Mumbai", "Delhi", "Bangalore", "Chennai", "Kolkata", "Pune", "Hyderabad"]
LOAN_PURPOSES = [
    "Small business expansion",
    "Equipment purchase",
    "Inventory stock",
    "Shop renovation",
    "Working capital",
    "Agricultural needs"
]


async def create_sample_user(session: AsyncSession, index: int) -> User:
    """Create a sample user."""
    first_name = random.choice(FIRST_NAMES)
    last_name = random.choice(LAST_NAMES)
    name = f"{first_name} {last_name}"
    phone = f"98{random.randint(10000000, 99999999)}"
    aadhaar = f"{random.randint(100000000000, 999999999999)}"
    
    user = User(
        name=name,
        phone=phone,
        aadhaar_hash=hash_aadhaar(aadhaar),
        location=random.choice(LOCATIONS),
        gender=random.choice(["male", "female"]),
        state=random.choice(["Maharashtra", "Delhi", "Karnataka", "Tamil Nadu"]),
        urban_rural=random.choice(["urban", "rural"]),
        consent_given=True,
        consent_timestamp=datetime.utcnow(),
        is_verified=True,
        joined_at=datetime.utcnow() - timedelta(days=random.randint(30, 730))
    )
    
    session.add(user)
    await session.commit()
    await session.refresh(user)
    
    # Create Neo4j node
    await neo4j_service.create_user_node(user.id, user.name, settings.COLD_START_SCORE)
    
    return user


async def create_sample_community(session: AsyncSession, name: str, cluster_type: str, anchor_user: User) -> Community:
    """Create a sample community."""
    community = Community(
        name=name,
        cluster_type=cluster_type,
        anchor_user_id=anchor_user.id,
        location=anchor_user.location
    )
    
    session.add(community)
    await session.commit()
    await session.refresh(community)
    
    # Add anchor as member
    membership = CommunityMembership(
        user_id=anchor_user.id,
        community_id=community.id,
        role="anchor",
        joined_at=community.created_at,
        is_active=1
    )
    session.add(membership)
    await session.commit()
    
    # Create Neo4j membership
    await neo4j_service.create_community_membership(anchor_user.id, community.id, "anchor")
    
    return community


async def add_member_to_community(
    session: AsyncSession,
    user: User,
    community: Community,
    vouched_by: User = None
):
    """Add a user to a community."""
    membership = CommunityMembership(
        user_id=user.id,
        community_id=community.id,
        role="member",
        vouched_by_user_id=vouched_by.id if vouched_by else None,
        joined_at=datetime.utcnow() - timedelta(days=random.randint(7, 365)),
        is_active=1
    )
    
    session.add(membership)
    await session.commit()
    
    # Create Neo4j membership
    await neo4j_service.create_community_membership(user.id, community.id, "member")


async def create_vouch(session: AsyncSession, voucher: User, vouchee: User):
    """Create a vouch relationship."""
    vouch = VouchRelationship(
        voucher_id=voucher.id,
        vouchee_id=vouchee.id,
        weight=random.uniform(0.5, 1.5),
        active=True,
        repayment_count=random.randint(0, 5),
        default_count=random.randint(0, 1)
    )
    
    session.add(vouch)
    await session.commit()
    
    # Create Neo4j relationship
    await neo4j_service.create_vouch_relationship(voucher.id, vouchee.id, vouch.weight)


async def create_loan_with_repayments(
    session: AsyncSession,
    borrower: User,
    community: Community,
    months_ago: int
):
    """Create a loan with repayment history."""
    amount = random.randint(5000, 50000)
    tenure = random.randint(3, 12)
    on_time_rate = random.uniform(0.7, 1.0)  # 70-100% on-time
    
    loan = LoanApplication(
        borrower_id=borrower.id,
        community_id=community.id,
        amount_requested=amount,
        amount_approved=amount,
        purpose=random.choice(LOAN_PURPOSES),
        status="repaid" if random.random() > 0.1 else "disbursed",
        interest_rate=12.0,
        tenure_months=tenure,
        applied_at=datetime.utcnow() - timedelta(days=months_ago * 30),
        approved_at=datetime.utcnow() - timedelta(days=months_ago * 30 - 3),
        disbursed_at=datetime.utcnow() - timedelta(days=months_ago * 30 - 5)
    )
    
    session.add(loan)
    await session.commit()
    await session.refresh(loan)
    
    # Create repayments
    monthly_payment = amount / tenure
    
    for i in range(tenure):
        due_date = loan.disbursed_at + timedelta(days=(i + 1) * 30)
        
        # Determine if paid and if on time
        is_paid = due_date < datetime.utcnow()
        is_on_time = random.random() < on_time_rate
        
        if is_paid:
            paid_date = due_date + timedelta(days=0 if is_on_time else random.randint(1, 10))
        else:
            paid_date = None
        
        repayment = Repayment(
            loan_id=loan.id,
            amount=monthly_payment,
            due_date=due_date,
            paid_date=paid_date,
            on_time=1 if is_on_time else 0 if paid_date else None,
            payment_method="upi" if paid_date else None
        )
        
        session.add(repayment)
    
    await session.commit()


async def seed_database():
    """Main seed function."""
    print("🌱 Starting database seed...")
    
    # Create async engine
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Create session
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        print("📝 Creating communities and users...")
        
        communities = []
        all_users = []
        
        # Create 3 communities
        community_configs = [
            ("Women's SHG - Mumbai", "shg"),
            ("Street Vendors Association", "merchant"),
            ("Neighborhood Credit Circle", "neighborhood")
        ]
        
        for i, (comm_name, comm_type) in enumerate(community_configs):
            print(f"\n🏘️  Creating community: {comm_name}")
            
            # Create anchor user
            anchor = await create_sample_user(session, i * 100)
            all_users.append(anchor)
            
            # Create community
            community = await create_sample_community(session, comm_name, comm_type, anchor)
            communities.append(community)
            
            # Create 9 more members
            community_members = [anchor]
            for j in range(1, 10):
                member = await create_sample_user(session, i * 100 + j)
                all_users.append(member)
                
                # Add to community (possibly vouched by existing member)
                vouched_by = random.choice(community_members) if len(community_members) > 1 else None
                await add_member_to_community(session, member, community, vouched_by)
                community_members.append(member)
            
            print(f"✅ Created {len(community_members)} members in {comm_name}")
            
            # Create vouch relationships (network effect)
            print(f"🤝 Creating vouch relationships...")
            for _ in range(random.randint(15, 25)):
                voucher = random.choice(community_members)
                vouchee = random.choice(community_members)
                
                if voucher.id != vouchee.id:
                    await create_vouch(session, voucher, vouchee)
            
            # Create loans for some members
            print(f"💰 Creating loan histories...")
            for member in random.sample(community_members, min(7, len(community_members))):
                # Create 1-3 loans per borrower
                for _ in range(random.randint(1, 3)):
                    months_ago = random.randint(2, 24)
                    await create_loan_with_repayments(session, member, community, months_ago)
        
        print("\n🧮 Computing trust scores for all users...")
        for user in all_users:
            calculator = TrustScoreCalculator(session)
            try:
                score, breakdown, explanation = await calculator.calculate_score(user.id)
                trust_score = await calculator.save_score(user.id, score, breakdown, explanation)
                print(f"   User {user.name}: {score:.0f}")
            except Exception as e:
                print(f"   ⚠️  Failed to compute score for {user.name}: {e}")
    
    await engine.dispose()
    
    print("\n✅ Database seeded successfully!")
    print(f"📊 Summary:")
    print(f"   - Communities: {len(communities)}")
    print(f"   - Users: {len(all_users)}")
    print(f"   - Check http://localhost:8000/docs to test the API")


if __name__ == "__main__":
    asyncio.run(seed_database())
