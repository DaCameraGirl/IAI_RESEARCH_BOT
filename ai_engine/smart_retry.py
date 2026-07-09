"""
Smart Retry - Intelligent retry logic with exponential backoff and strategy adaptation
Automatically retries failed searches with different approaches
"""

import time
from typing import Callable, Any, Optional, Dict, List
from functools import wraps
from datetime import datetime
import random


class RetryStrategy:
    """
    Smart retry strategy that adapts based on failure type
    """
    
    def __init__(
        self,
        max_retries: int = 3,
        initial_backoff: float = 1.0,
        max_backoff: float = 60.0,
        backoff_multiplier: float = 2.0,
        jitter: bool = True
    ):
        """
        Initialize retry strategy
        
        Args:
            max_retries: Maximum retry attempts
            initial_backoff: Initial backoff delay in seconds
            max_backoff: Maximum backoff delay in seconds
            backoff_multiplier: Backoff multiplier for exponential backoff
            jitter: Add random jitter to backoff to avoid thundering herd
        """
        self.max_retries = max_retries
        self.initial_backoff = initial_backoff
        self.max_backoff = max_backoff
        self.backoff_multiplier = backoff_multiplier
        self.jitter = jitter
        
        # Track retry statistics
        self.stats = {
            'total_attempts': 0,
            'total_retries': 0,
            'successful_retries': 0,
            'failed_retries': 0,
            'retry_reasons': {}
        }
    
    def calculate_backoff(self, attempt: int) -> float:
        """Calculate backoff delay for attempt"""
        backoff = min(
            self.initial_backoff * (self.backoff_multiplier ** attempt),
            self.max_backoff
        )
        
        if self.jitter:
            # Add random jitter (±25%)
            jitter_amount = backoff * 0.25
            backoff += random.uniform(-jitter_amount, jitter_amount)
        
        return max(0, backoff)
    
    def should_retry(self, error: Exception, attempt: int) -> bool:
        """Determine if error should be retried"""
        if attempt >= self.max_retries:
            return False
        
        error_str = str(error).lower()
        
        # Retryable errors
        retryable_patterns = [
            '503',  # Service unavailable
            '429',  # Too many requests
            '502',  # Bad gateway
            '504',  # Gateway timeout
            'rate limit',
            'timeout',
            'connection',
            'temporary',
            'unavailable'
        ]
        
        # Non-retryable errors
        non_retryable_patterns = [
            '404',  # Not found
            '401',  # Unauthorized
            '403',  # Forbidden
            '400',  # Bad request
            'invalid',
            'not found',
            'does not exist'
        ]
        
        # Check non-retryable first
        for pattern in non_retryable_patterns:
            if pattern in error_str:
                return False
        
        # Check retryable
        for pattern in retryable_patterns:
            if pattern in error_str:
                return True
        
        # Default: retry unknown errors
        return True
    
    def get_retry_reason(self, error: Exception) -> str:
        """Get human-readable retry reason"""
        error_str = str(error).lower()
        
        if '503' in error_str or 'unavailable' in error_str:
            return 'Service unavailable'
        elif '429' in error_str or 'rate limit' in error_str:
            return 'Rate limit exceeded'
        elif 'timeout' in error_str:
            return 'Request timeout'
        elif 'connection' in error_str:
            return 'Connection error'
        else:
            return 'Unknown error'
    
    def retry_with_backoff(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function with retry and exponential backoff
        
        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
            
        Raises:
            Last exception if all retries fail
        """
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            self.stats['total_attempts'] += 1
            
            try:
                result = func(*args, **kwargs)
                
                if attempt > 0:
                    self.stats['successful_retries'] += 1
                    print(f"✓ Retry successful after {attempt} attempts")
                
                return result
            
            except Exception as e:
                last_exception = e
                
                if attempt < self.max_retries:
                    if self.should_retry(e, attempt):
                        self.stats['total_retries'] += 1
                        
                        reason = self.get_retry_reason(e)
                        self.stats['retry_reasons'][reason] = self.stats['retry_reasons'].get(reason, 0) + 1
                        
                        backoff = self.calculate_backoff(attempt)
                        
                        print(f"⚠ {reason}, retrying in {backoff:.1f}s (attempt {attempt + 1}/{self.max_retries})")
                        time.sleep(backoff)
                    else:
                        print(f"✗ Non-retryable error: {e}")
                        break
                else:
                    self.stats['failed_retries'] += 1
                    print(f"✗ Max retries ({self.max_retries}) exceeded")
        
        raise last_exception
    
    def __call__(self, func: Callable) -> Callable:
        """Decorator for automatic retry"""
        @wraps(func)
        def wrapper(*args, **kwargs):
            return self.retry_with_backoff(func, *args, **kwargs)
        
        return wrapper


class AdaptiveRetryStrategy(RetryStrategy):
    """
    Adaptive retry strategy that changes approach based on failure patterns
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Track failure patterns
        self.failure_patterns = {
            'rate_limit': 0,
            'timeout': 0,
            'connection': 0,
            'service_unavailable': 0
        }
        
        # Adaptation thresholds
        self.adaptation_threshold = 3
    
    def adapt_strategy(self, error: Exception):
        """Adapt retry strategy based on error patterns"""
        error_str = str(error).lower()
        
        # Track failure pattern
        if 'rate limit' in error_str or '429' in error_str:
            self.failure_patterns['rate_limit'] += 1
            
            # If rate limiting is frequent, increase backoff
            if self.failure_patterns['rate_limit'] >= self.adaptation_threshold:
                self.initial_backoff *= 1.5
                self.max_backoff *= 1.5
                print(f"⚙ Adapted: Increased backoff due to rate limiting")
        
        elif 'timeout' in error_str:
            self.failure_patterns['timeout'] += 1
            
            # If timeouts are frequent, increase max retries
            if self.failure_patterns['timeout'] >= self.adaptation_threshold:
                self.max_retries = min(self.max_retries + 1, 5)
                print(f"⚙ Adapted: Increased max retries to {self.max_retries}")
        
        elif 'connection' in error_str:
            self.failure_patterns['connection'] += 1
            
            # If connection errors are frequent, add more jitter
            if self.failure_patterns['connection'] >= self.adaptation_threshold:
                self.jitter = True
                print(f"⚙ Adapted: Enabled jitter for connection stability")
        
        elif '503' in error_str or 'unavailable' in error_str:
            self.failure_patterns['service_unavailable'] += 1
            
            # If service is frequently unavailable, increase backoff significantly
            if self.failure_patterns['service_unavailable'] >= self.adaptation_threshold:
                self.initial_backoff *= 2.0
                self.max_backoff = min(self.max_backoff * 2.0, 300.0)
                print(f"⚙ Adapted: Significantly increased backoff for service stability")
    
    def retry_with_backoff(self, func: Callable, *args, **kwargs) -> Any:
        """Execute with adaptive retry"""
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                result = func(*args, **kwargs)
                
                if attempt > 0:
                    self.stats['successful_retries'] += 1
                    print(f"✓ Retry successful after {attempt} attempts")
                
                return result
            
            except Exception as e:
                last_exception = e
                
                # Adapt strategy based on error
                self.adapt_strategy(e)
                
                if attempt < self.max_retries and self.should_retry(e, attempt):
                    backoff = self.calculate_backoff(attempt)
                    
                    reason = self.get_retry_reason(e)
                    print(f"⚠ {reason}, retrying in {backoff:.1f}s (attempt {attempt + 1}/{self.max_retries})")
                    
                    time.sleep(backoff)
                else:
                    break
        
        raise last_exception


# Global retry strategies
default_retry = RetryStrategy(max_retries=3, initial_backoff=1.0)
adaptive_retry = AdaptiveRetryStrategy(max_retries=3, initial_backoff=1.0)


# Convenience decorators
def retry(max_retries: int = 3):
    """Simple retry decorator"""
    return RetryStrategy(max_retries=max_retries)


def adaptive_retry_decorator(max_retries: int = 3):
    """Adaptive retry decorator"""
    return AdaptiveRetryStrategy(max_retries=max_retries)


# Example usage
if __name__ == "__main__":
    import requests
    
    # Example 1: Simple retry
    @retry(max_retries=3)
    def fetch_url(url: str):
        """Fetch URL with retry"""
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        return response.text
    
    # Example 2: Adaptive retry
    @adaptive_retry_decorator(max_retries=5)
    def fetch_api(endpoint: str):
        """Fetch API with adaptive retry"""
        response = requests.get(f"https://api.example.com/{endpoint}", timeout=10)
        response.raise_for_status()
        return response.json()
    
    # Test
    try:
        result = fetch_url("https://httpstat.us/503")
        print(f"Success: {len(result)} bytes")
    except Exception as e:
        print(f"Failed: {e}")
    
    # Print statistics
    print(f"\nRetry Statistics:")
    print(f"  Total attempts: {default_retry.stats['total_attempts']}")
    print(f"  Total retries: {default_retry.stats['total_retries']}")
    print(f"  Successful retries: {default_retry.stats['successful_retries']}")
    print(f"  Failed retries: {default_retry.stats['failed_retries']}")
