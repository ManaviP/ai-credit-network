"""
API routers package.
"""
from app.routers import auth, users, communities, loans, scoring, admin

__all__ = ["auth", "users", "communities", "loans", "scoring", "admin"]
