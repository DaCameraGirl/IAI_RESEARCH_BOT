"""
Rate Limiter - Prevents HTTP 503 errors from external APIs
Implements exponential backoff and request throttling
"""

import time
from typing import Callable, Any, Optional
from functools import wraps
from datetime import datetime, timedelta
import threading


class RateLimiter:
    """
    Rate limiter with exponential backoff for API calls
    Prevents HTTP 503 (Service Unavailable) errors
    """
    
    def __init__(
        self,
        calls_per_second: float = 1.0,
        max_retries: int = 3,
        initial_backoff: float = 1.0,
        max_backoff: float = 60.0
    ):
        """
        Initialize rate limiter
        
        Args:
            calls_per_second: Maximum calls per second
            max_retries: Maximum retry attempts on failure
            initial_backoff: Initial backoff delay in seconds
            max_backoff: Maximum backoff delay in seconds
        """
        self.calls_per_second = calls_per_second
        self.min_interval = 1.0 / calls_per_second
        self.max_retries = max_retries
        self.initial_backoff = initial_backoff
        self.max_backoff = max_backoff
        
        self.last_call_time = {}
        self.lock = threading.Lock()
    
    def wait_if_needed(self, key: str = "default"):
        """Wait if necessary to respect rate limit"""
        with self.lock:
            now = time.time()
            
            if key in self.last_call_time:
                elapsed = now - self.last_call_time[key]
                if elapsed < self.min_interval:
                    sleep_time = self.min_interval - elapsed
                    time.sleep(sleep_time)
            
            self.last_call_time[key] = time.time()
    
    def __call__(self, func: Callable) -> Callable:
        """Decorator for rate-limited functions"""
        @wraps(func)
        def wrapper(*args, **kwargs):
            key = kwargs.get('rate_limit_key', 'default')
            
            for attempt in range(self.max_retries + 1):
                try:
                    # Wait for rate limit
                    self.wait_if_needed(key)
                    
                    # Execute function
                    return func(*args, **kwargs)
                
                except Exception as e:
                    error_str = str(e).lower()
                    
                    # Check if it's a rate limit error
                    is_rate_limit = any(code in error_str for code in [
                        '503', '429', 'rate limit', 'too many requests',
                        'service unavailable', 'quota exceeded'
                    ])
                    
                    if not is_rate_limit or attempt == self.max_retries:
                        # Not a rate limit error or max retries reached
                        raise
                    
                    # Calculate backoff
                    backoff = min(
                        self.initial_backoff * (2 ** attempt),
                        self.max_backoff
                    )
                    
                    print(f"Rate limit hit, retrying in {backoff:.1f}s (attempt {attempt + 1}/{self.max_retries})")
                    time.sleep(backoff)
            
            raise Exception(f"Max retries ({self.max_retries}) exceeded")
        
        return wrapper


class APIThrottler:
    """
    API-specific throttler with per-endpoint limits
    Prevents overwhelming external services
    """
    
    def __init__(self):
        """Initialize API throttler with default limits"""
        self.limiters = {
            'wayback': RateLimiter(calls_per_second=0.5, max_retries=3),  # 1 call per 2 seconds
            'fcc': RateLimiter(calls_per_second=0.33, max_retries=3),     # 1 call per 3 seconds
            'ptab': RateLimiter(calls_per_second=0.5, max_retries=3),
            'google_groups': RateLimiter(calls_per_second=0.25, max_retries=3),  # 1 call per 4 seconds
            'github': RateLimiter(calls_per_second=1.0, max_retries=3),
            'semantic_scholar': RateLimiter(calls_per_second=1.0, max_retries=3),
            'crossref': RateLimiter(calls_per_second=1.0, max_retries=3),
            'unpaywall': RateLimiter(calls_per_second=1.0, max_retries=3),
            'default': RateLimiter(calls_per_second=0.5, max_retries=3)
        }
    
    def get_limiter(self, api_name: str) -> RateLimiter:
        """Get rate limiter for specific API"""
        return self.limiters.get(api_name, self.limiters['default'])
    
    def throttle(self, api_name: str):
        """Decorator for API-specific throttling"""
        limiter = self.get_limiter(api_name)
        return limiter


# Global throttler instance
throttler = APIThrottler()


# Convenience decorators for common APIs
def wayback_throttle(func):
    """Throttle Wayback Machine API calls"""
    return throttler.throttle('wayback')(func)


def fcc_throttle(func):
    """Throttle FCC API calls"""
    return throttler.throttle('fcc')(func)


def ptab_throttle(func):
    """Throttle USPTO PTAB API calls"""
    return throttler.throttle('ptab')(func)


def github_throttle(func):
    """Throttle GitHub API calls"""
    return throttler.throttle('github')(func)


# Example usage
if __name__ == "__main__":
    import requests
    
    @wayback_throttle
    def fetch_wayback_snapshot(url: str):
        """Fetch Wayback Machine snapshot"""
        api_url = f"http://archive.org/wayback/available?url={url}"
        response = requests.get(api_url, timeout=10)
        response.raise_for_status()
        return response.json()
    
    # Test with multiple calls
    urls = [
        "semiconductors.philips.com",
        "nxp.com",
        "philips.com"
    ]
    
    for url in urls:
        try:
            result = fetch_wayback_snapshot(url)
            print(f"✓ {url}: {len(result)} snapshots")
        except Exception as e:
            print(f"✗ {url}: {e}")
