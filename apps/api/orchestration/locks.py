import uuid
from contextlib import contextmanager
import redis


class LeadLock:
    """
    Fencing token pattern for lead locking.
    Prevents race conditions where multiple agents try to contact the same lead.
    """
    
    def __init__(self, org_id: str, lead_id: str, redis_client):
        self.org_id = org_id
        self.lead_id = lead_id
        self._r = redis_client
        self.token = str(uuid.uuid4())
        self.redis_key = f"sos:{org_id}:lock:lead:{lead_id}"
    
    def acquire(self, ttl: int = 60):
        """
        Acquire lock with fencing token.
        Returns True if acquired, False if already held.
        """
        return self._r.set(self.redis_key, self.token, nx=True, ex=ttl)
    
    def release(self):
        """
        Release lock only if we still hold it (fencing token check).
        Uses Lua script for atomicity.
        """
        lua = """
        if redis.call("GET", KEYS[1]) == ARGV[1] then
            return redis.call("DEL", KEYS[1])
        end
        return 0
        """
        return self._r.eval(lua, 1, self.redis_key, self.token)


@contextmanager
def lead_lock_context(org_id: str, lead_id: str, redis_client):
    """Context manager for lead locking"""
    lock = LeadLock(org_id, lead_id, redis_client)
    acquired = lock.acquire()
    if not acquired:
        raise RuntimeError(f"Could not acquire lock for lead {lead_id}")
    try:
        yield lock
    finally:
        lock.release()
