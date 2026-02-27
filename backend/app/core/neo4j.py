from neo4j import AsyncGraphDatabase
from typing import List, Dict, Optional
from app.core.config import settings


class Neo4jService:
    """Service for managing Neo4j graph database connections and operations."""
    
    def __init__(self):
        self.driver = AsyncGraphDatabase.driver(
            settings.NEO4J_URI,
            auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
        )
    
    async def close(self):
        """Close the driver connection."""
        await self.driver.close()
    
    async def create_user_node(self, user_id: int, name: str, trust_score: float = 300):
        """Create or update a user node in Neo4j."""
        async with self.driver.session() as session:
            query = """
            MERGE (u:User {user_id: $user_id})
            SET u.name = $name, u.trust_score = $trust_score, u.updated_at = datetime()
            RETURN u
            """
            result = await session.run(query, user_id=user_id, name=name, trust_score=trust_score)
            return await result.single()
    
    async def create_vouch_relationship(
        self,
        voucher_id: int,
        vouchee_id: int,
        weight: float = 1.0
    ):
        """Create a VOUCHES_FOR relationship between two users."""
        async with self.driver.session() as session:
            query = """
            MATCH (voucher:User {user_id: $voucher_id})
            MATCH (vouchee:User {user_id: $vouchee_id})
            MERGE (voucher)-[v:VOUCHES_FOR]->(vouchee)
            SET v.weight = $weight,
                v.created_at = CASE WHEN v.created_at IS NULL THEN datetime() ELSE v.created_at END,
                v.updated_at = datetime(),
                v.repayment_count = COALESCE(v.repayment_count, 0),
                v.default_count = COALESCE(v.default_count, 0)
            RETURN v
            """
            result = await session.run(
                query,
                voucher_id=voucher_id,
                vouchee_id=vouchee_id,
                weight=weight
            )
            return await result.single()
    
    async def create_community_membership(
        self,
        user_id: int,
        community_id: int,
        role: str = "member"
    ):
        """Create MEMBER_OF relationship between user and community."""
        async with self.driver.session() as session:
            query = """
            MATCH (u:User {user_id: $user_id})
            MERGE (c:Community {community_id: $community_id})
            MERGE (u)-[m:MEMBER_OF]->(c)
            SET m.role = $role,
                m.joined_at = CASE WHEN m.joined_at IS NULL THEN datetime() ELSE m.joined_at END
            RETURN m
            """
            result = await session.run(
                query,
                user_id=user_id,
                community_id=community_id,
                role=role
            )
            return await result.single()
    
    async def get_user_vouch_count(self, user_id: int) -> int:
        """Get count of active vouches received by a user."""
        async with self.driver.session() as session:
            query = """
            MATCH (:User)-[v:VOUCHES_FOR]->(u:User {user_id: $user_id})
            RETURN count(v) as vouch_count
            """
            result = await session.run(query, user_id=user_id)
            record = await result.single()
            return record["vouch_count"] if record else 0
    
    async def get_voucher_avg_score(self, user_id: int) -> float:
        """Get average trust score of users vouching for this user."""
        async with self.driver.session() as session:
            query = """
            MATCH (voucher:User)-[:VOUCHES_FOR]->(u:User {user_id: $user_id})
            RETURN avg(voucher.trust_score) as avg_score
            """
            result = await session.run(query, user_id=user_id)
            record = await result.single()
            return float(record["avg_score"]) if record and record["avg_score"] else 0.0
    
    async def get_user_trust_graph(self, user_id: int, depth: int = 2) -> Dict:
        """Get trust graph around a user for visualization."""
        async with self.driver.session() as session:
            query = """
            MATCH path = (u:User {user_id: $user_id})-[v:VOUCHES_FOR*1..$depth]-(other:User)
            WITH u, other, v
            RETURN u.user_id as source_id,
                   u.name as source_name,
                   u.trust_score as source_score,
                   collect({
                       user_id: other.user_id,
                       name: other.name,
                       trust_score: other.trust_score,
                       relationship: v
                   }) as connections
            """
            result = await session.run(query, user_id=user_id, depth=depth)
            record = await result.single()
            
            if not record:
                return {"nodes": [], "edges": []}
            
            # Format for D3.js
            nodes = [{"id": record["source_id"], "name": record["source_name"], "score": record["source_score"]}]
            edges = []
            
            for conn in record["connections"]:
                if conn["user_id"] not in [n["id"] for n in nodes]:
                    nodes.append({
                        "id": conn["user_id"],
                        "name": conn["name"],
                        "score": conn["trust_score"]
                    })
                edges.append({
                    "source": record["source_id"],
                    "target": conn["user_id"],
                    "weight": 1.0
                })
            
            return {"nodes": nodes, "edges": edges}
    
    async def get_community_members(self, community_id: int) -> List[int]:
        """Get all user IDs in a community."""
        async with self.driver.session() as session:
            query = """
            MATCH (u:User)-[:MEMBER_OF]->(c:Community {community_id: $community_id})
            RETURN collect(u.user_id) as member_ids
            """
            result = await session.run(query, community_id=community_id)
            record = await result.single()
            return record["member_ids"] if record else []
    
    async def update_vouch_repayment(self, voucher_id: int, vouchee_id: int, is_default: bool = False):
        """Update repayment or default count on vouch relationship."""
        async with self.driver.session() as session:
            if is_default:
                query = """
                MATCH (voucher:User {user_id: $voucher_id})-[v:VOUCHES_FOR]->(vouchee:User {user_id: $vouchee_id})
                SET v.default_count = v.default_count + 1
                RETURN v
                """
            else:
                query = """
                MATCH (voucher:User {user_id: $voucher_id})-[v:VOUCHES_FOR]->(vouchee:User {user_id: $vouchee_id})
                SET v.repayment_count = v.repayment_count + 1
                RETURN v
                """
            result = await session.run(query, voucher_id=voucher_id, vouchee_id=vouchee_id)
            return await result.single()


# Global Neo4j service instance
neo4j_service = Neo4jService()
