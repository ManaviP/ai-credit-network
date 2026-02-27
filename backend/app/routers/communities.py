"""
Communities router - create, join, vouch, and view community health.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.core import get_db, get_current_user
from app.models import User, Community, CommunityMembership, VouchRelationship
from app.schemas import (
    CreateCommunityRequest, CommunityResponse, JoinCommunityRequest,
    VouchRequest, ClusterHealthResponse
)
from app.core.neo4j import neo4j_service
from app.services import ClusterHealthService

router = APIRouter(prefix="/communities", tags=["Communities"])


@router.post("", response_model=CommunityResponse, status_code=status.HTTP_201_CREATED)
async def create_community(
    request: CreateCommunityRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new community with current user as anchor.
    """
    # Create community
    community = Community(
        name=request.name,
        cluster_type=request.cluster_type,
        description=request.description,
        location=request.location,
        anchor_user_id=current_user.id
    )
    db.add(community)
    await db.commit()
    await db.refresh(community)
    
    # Add creator as anchor member
    membership = CommunityMembership(
        user_id=current_user.id,
        community_id=community.id,
        role="anchor"
    )
    db.add(membership)
    await db.commit()
    
    # Create in Neo4j
    await neo4j_service.create_community_membership(
        current_user.id,
        community.id,
        "anchor"
    )
    
    return CommunityResponse(
        id=community.id,
        name=community.name,
        cluster_type=community.cluster_type,
        created_at=community.created_at,
        anchor_user_id=community.anchor_user_id,
        total_members=1
    )


@router.post("/{community_id}/join", response_model=dict)
async def join_community(
    community_id: int,
    request: JoinCommunityRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Join a community, optionally with a vouch from existing member.
    """
    # Check if community exists
    result = await db.execute(
        select(Community).filter(Community.id == community_id)
    )
    community = result.scalar_one_or_none()
    
    if not community:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Community not found"
        )
    
    # Check if already a member
    existing = await db.execute(
        select(CommunityMembership)
        .filter(CommunityMembership.user_id == current_user.id)
        .filter(CommunityMembership.community_id == community_id)
        .filter(CommunityMembership.is_active == 1)
    )
    
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Already a member of this community"
        )
    
    # If vouched_by provided, validate
    if request.vouched_by_user_id:
        voucher_result = await db.execute(
            select(CommunityMembership)
            .filter(CommunityMembership.user_id == request.vouched_by_user_id)
            .filter(CommunityMembership.community_id == community_id)
            .filter(CommunityMembership.is_active == 1)
        )
        voucher_membership = voucher_result.scalar_one_or_none()
        
        if not voucher_membership:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Voucher is not a member of this community"
            )
    
    # Create membership
    membership = CommunityMembership(
        user_id=current_user.id,
        community_id=community_id,
        role="member",
        vouched_by_user_id=request.vouched_by_user_id
    )
    db.add(membership)
    await db.commit()
    
    # Create in Neo4j
    await neo4j_service.create_community_membership(
        current_user.id,
        community_id,
        "member"
    )
    
    return {
        "message": "Successfully joined community",
        "community_id": community_id,
        "community_name": community.name,
        "vouched_by": request.vouched_by_user_id
    }


@router.post("/{community_id}/vouch", response_model=dict)
async def vouch_for_member(
    community_id: int,
    request: VouchRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Vouch for another community member.
    
    Creates a trust relationship in both PostgreSQL and Neo4j.
    """
    # Verify both users are in the community
    voucher_membership = await db.execute(
        select(CommunityMembership)
        .filter(CommunityMembership.user_id == current_user.id)
        .filter(CommunityMembership.community_id == community_id)
        .filter(CommunityMembership.is_active == 1)
    )
    
    if not voucher_membership.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this community"
        )
    
    vouchee_membership = await db.execute(
        select(CommunityMembership)
        .filter(CommunityMembership.user_id == request.vouchee_user_id)
        .filter(CommunityMembership.community_id == community_id)
        .filter(CommunityMembership.is_active == 1)
    )
    
    if not vouchee_membership.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Vouchee is not a member of this community"
        )
    
    # Can't vouch for yourself
    if current_user.id == request.vouchee_user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot vouch for yourself"
        )
    
    # Check if vouch already exists
    existing_vouch = await db.execute(
        select(VouchRelationship)
        .filter(VouchRelationship.voucher_id == current_user.id)
        .filter(VouchRelationship.vouchee_id == request.vouchee_user_id)
        .filter(VouchRelationship.active == True)
    )
    
    if existing_vouch.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You have already vouched for this user"
        )
    
    # Create vouch relationship
    vouch = VouchRelationship(
        voucher_id=current_user.id,
        vouchee_id=request.vouchee_user_id,
        weight=request.weight
    )
    db.add(vouch)
    await db.commit()
    
    # Create in Neo4j
    await neo4j_service.create_vouch_relationship(
        current_user.id,
        request.vouchee_user_id,
        request.weight
    )
    
    # Get vouchee name
    vouchee_result = await db.execute(
        select(User).filter(User.id == request.vouchee_user_id)
    )
    vouchee = vouchee_result.scalar_one()
    
    return {
        "message": f"Successfully vouched for {vouchee.name}",
        "voucher_id": current_user.id,
        "vouchee_id": request.vouchee_user_id,
        "weight": request.weight
    }


@router.get("/{community_id}/dashboard", response_model=dict)
async def get_community_dashboard(
    community_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get comprehensive health metrics for a community.
    
    Includes:
    - Average trust score
    - On-time repayment rate
    - Financial summary
    - At-risk members
    - Cluster status
    """
    # Verify user is a member
    membership = await db.execute(
        select(CommunityMembership)
        .filter(CommunityMembership.user_id == current_user.id)
        .filter(CommunityMembership.community_id == community_id)
        .filter(CommunityMembership.is_active == 1)
    )
    
    if not membership.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this community"
        )
    
    # Calculate health metrics
    health_service = ClusterHealthService(db)
    health_data = await health_service.calculate_cluster_health(community_id)
    
    return health_data


@router.get("", response_model=List[CommunityResponse])
async def list_my_communities(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List all communities the current user is a member of.
    """
    result = await db.execute(
        select(Community)
        .join(CommunityMembership)
        .filter(CommunityMembership.user_id == current_user.id)
        .filter(CommunityMembership.is_active == 1)
    )
    communities = result.scalars().all()
    
    return [
        CommunityResponse(
            id=c.id,
            name=c.name,
            cluster_type=c.cluster_type,
            created_at=c.created_at,
            anchor_user_id=c.anchor_user_id,
            total_members=len(c.memberships)
        )
        for c in communities
    ]
