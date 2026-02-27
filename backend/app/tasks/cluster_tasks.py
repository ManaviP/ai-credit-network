"""
Cluster health monitoring tasks.
"""
from sqlalchemy import select
import asyncio

from app.tasks.celery_app import celery_app
from app.core.database import AsyncSessionLocal
from app.services import ClusterHealthService
from app.models import Community


@celery_app.task(name="app.tasks.cluster_tasks.check_cluster_health")
def check_cluster_health_task(community_id: int):
    """
    Check health metrics for a specific community.
    
    Runs nightly for each community.
    """
    return asyncio.run(check_cluster_health_async(community_id))


async def check_cluster_health_async(community_id: int):
    """Async implementation of cluster health check."""
    async with AsyncSessionLocal() as db:
        try:
            health_service = ClusterHealthService(db)
            health_data = await health_service.calculate_cluster_health(community_id)
            
            # TODO: Send alerts if cluster is fragile or has at-risk members
            if health_data["cluster_status"] == "Fragile":
                print(f"⚠️ Alert: Community {community_id} ({health_data['community_name']}) is FRAGILE")
            
            if health_data["at_risk_members"]:
                print(f"⚠️ Alert: {len(health_data['at_risk_members'])} at-risk members in {health_data['community_name']}")
            
            return health_data
        
        except Exception as e:
            return {"error": str(e), "community_id": community_id}


@celery_app.task(name="app.tasks.cluster_tasks.check_all_cluster_health")
def check_all_cluster_health():
    """
    Check health for all communities.
    
    Scheduled to run nightly at 2 AM.
    """
    return asyncio.run(check_all_cluster_health_async())


async def check_all_cluster_health_async():
    """Async implementation of all cluster health check."""
    async with AsyncSessionLocal() as db:
        try:
            # Get all communities
            result = await db.execute(select(Community))
            communities = result.scalars().all()
            
            results = []
            for community in communities:
                health_data = await check_cluster_health_async(community.id)
                results.append(health_data)
            
            return {
                "total_communities": len(communities),
                "results": results
            }
        
        except Exception as e:
            return {"error": str(e)}
