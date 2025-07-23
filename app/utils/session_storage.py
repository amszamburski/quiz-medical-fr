"""
Server-side session storage using Redis/KV for persistence across serverless requests.
"""

import json
import os
from typing import Optional, Dict, Any
from datetime import datetime, timedelta


class SessionStorage:
    """Handle server-side session storage using Redis/KV backend."""
    
    def __init__(self):
        self.redis_client = None
        self._init_redis()
    
    def _init_redis(self):
        """Initialize Redis connection for session storage."""
        try:
            redis_url = os.getenv("KV_REST_API_URL") or os.getenv("UPSTASH_REDIS_REST_URL") or os.getenv("UPSTASH_REDIS_URL") or os.getenv("REDIS_URL")
            if redis_url:
                if "upstash" in redis_url:
                    token = os.getenv("KV_REST_API_TOKEN") or os.getenv("UPSTASH_REDIS_REST_TOKEN") or os.getenv("UPSTASH_REDIS_TOKEN")
                    if token:
                        from upstash_redis import Redis
                        self.redis_client = Redis(url=redis_url, token=token)
                        print("Session storage: Redis connection established")
                else:
                    import redis
                    self.redis_client = redis.from_url(redis_url)
                    print("Session storage: Redis connection established")
        except Exception as e:
            print(f"Session storage: Redis connection failed: {e}")
            self.redis_client = None
    
    def store_quiz_data(self, session_id: str, data: Dict[Any, Any], ttl_hours: int = 2) -> bool:
        """Store quiz data for a session with TTL."""
        if not self.redis_client:
            print("Session storage: No Redis connection available")
            return False
        
        try:
            key = f"quiz_session:{session_id}"
            serialized_data = json.dumps(data, default=str)
            ttl_seconds = ttl_hours * 3600
            
            result = self.redis_client.setex(key, ttl_seconds, serialized_data)
            print(f"Session storage: Stored quiz data for {session_id} (TTL: {ttl_hours}h)")
            return bool(result)
        except Exception as e:
            print(f"Session storage: Failed to store quiz data: {e}")
            return False
    
    def get_quiz_data(self, session_id: str) -> Optional[Dict[Any, Any]]:
        """Retrieve quiz data for a session."""
        if not self.redis_client:
            print("Session storage: No Redis connection available")
            return None
        
        try:
            key = f"quiz_session:{session_id}"
            data = self.redis_client.get(key)
            
            if data:
                if isinstance(data, bytes):
                    data = data.decode('utf-8')
                parsed_data = json.loads(data)
                print(f"Session storage: Retrieved quiz data for {session_id}")
                return parsed_data
            else:
                print(f"Session storage: No data found for {session_id}")
                return None
        except Exception as e:
            print(f"Session storage: Failed to retrieve quiz data: {e}")
            return None
    
    def update_quiz_data(self, session_id: str, data: Dict[Any, Any], ttl_hours: int = 2) -> bool:
        """Update existing quiz data for a session."""
        return self.store_quiz_data(session_id, data, ttl_hours)
    
    def delete_quiz_data(self, session_id: str) -> bool:
        """Delete quiz data for a session."""
        if not self.redis_client:
            return False
        
        try:
            key = f"quiz_session:{session_id}"
            result = self.redis_client.delete(key)
            print(f"Session storage: Deleted quiz data for {session_id}")
            return bool(result)
        except Exception as e:
            print(f"Session storage: Failed to delete quiz data: {e}")
            return False
    
    def session_exists(self, session_id: str) -> bool:
        """Check if session data exists."""
        if not self.redis_client:
            return False
        
        try:
            key = f"quiz_session:{session_id}"
            exists = self.redis_client.exists(key)
            return bool(exists)
        except Exception as e:
            print(f"Session storage: Failed to check session existence: {e}")
            return False


# Global session storage instance
session_storage = SessionStorage()