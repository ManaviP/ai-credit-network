from supabase import create_client, Client
from app.core.config import settings

# Initialize the Supabase client
def _normalize_supabase_key(key: str) -> str:
    """
    Accept both legacy JWT-shaped anon keys and new sb_* keys.
    Some environments accidentally concatenate them (JWT + ".sb_publishable_*").
    """
    if not key:
        return key
    key = key.strip().strip('"').strip("'")
    # If it looks like "...<jwt>.<sb_publishable_...>", keep only the sb_* part.
    if "sb_" in key and "." in key:
        tail = key.split(".")[-1]
        if tail.startswith("sb_"):
            return tail
    return key


supabase: Client = create_client(settings.SUPABASE_URL, _normalize_supabase_key(settings.SUPABASE_KEY))
