"""
Rate Limiting Middleware for SBN ChatAgent
Protects against abuse and ensures fair usage
"""
import time
import logging
from typing import Dict, Optional
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    Simple in-memory rate limiter using sliding window algorithm.
    """

    def __init__(self, requests_per_window: int = 10, window_seconds: int = 60):
        """
        Initialize rate limiter.
        
        Args:
            requests_per_window: Maximum requests allowed per window
            window_seconds: Time window in seconds
        """
        self.requests_per_window = requests_per_window
        self.window_seconds = window_seconds
        self.requests: Dict[str, list] = {}  # key -> list of timestamps
        logger.info(f"RateLimiter initialized: {requests_per_window} requests per {window_seconds}s")

    def _cleanup_old_requests(self, key: str, current_time: float) -> None:
        """Remove requests outside the current window"""
        if key in self.requests:
            cutoff = current_time - self.window_seconds
            self.requests[key] = [ts for ts in self.requests[key] if ts > cutoff]

    def is_allowed(self, key: str) -> bool:
        """
        Check if a request is allowed for the given key.
        
        Args:
            key: Identifier (e.g., IP address, user ID)
            
        Returns:
            True if request is allowed, False if rate limited
        """
        current_time = time.time()
        self._cleanup_old_requests(key, current_time)

        if key not in self.requests:
            self.requests[key] = []

        if len(self.requests[key]) >= self.requests_per_window:
            return False

        self.requests[key].append(current_time)
        return True

    def get_remaining_requests(self, key: str) -> int:
        """Get remaining requests for the current window"""
        current_time = time.time()
        self._cleanup_old_requests(key, current_time)
        
        if key not in self.requests:
            return self.requests_per_window
        
        return max(0, self.requests_per_window - len(self.requests[key]))

    def get_retry_after(self, key: str) -> int:
        """Get seconds until the next request is allowed"""
        if key not in self.requests or not self.requests[key]:
            return 0
        
        oldest_request = min(self.requests[key])
        retry_after = int(oldest_request + self.window_seconds - time.time()) + 1
        return max(0, retry_after)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware for rate limiting.
    """

    def __init__(
        self,
        app,
        requests_per_window: int = 10,
        window_seconds: int = 60,
        exclude_paths: Optional[list] = None
    ):
        """
        Initialize rate limit middleware.
        
        Args:
            app: FastAPI application
            requests_per_window: Maximum requests per window
            window_seconds: Time window in seconds
            exclude_paths: List of paths to exclude from rate limiting
        """
        super().__init__(app)
        self.limiter = RateLimiter(requests_per_window, window_seconds)
        self.exclude_paths = exclude_paths or ["/health", "/docs", "/openapi.json"]
        logger.info(f"RateLimitMiddleware initialized, excluded paths: {self.exclude_paths}")

    def _get_client_identifier(self, request: Request) -> str:
        """
        Get client identifier for rate limiting.
        Uses X-Forwarded-For header if available, otherwise client host.
        """
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # Take the first IP in the chain
            return forwarded_for.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

    async def dispatch(self, request: Request, call_next):
        """Process request with rate limiting"""
        # Skip rate limiting for excluded paths
        if any(request.url.path.startswith(path) for path in self.exclude_paths):
            return await call_next(request)

        client_id = self._get_client_identifier(request)
        
        if not self.limiter.is_allowed(client_id):
            retry_after = self.limiter.get_retry_after(client_id)
            remaining = self.limiter.get_remaining_requests(client_id)
            
            logger.warning(
                f"Rate limit exceeded for {client_id} on {request.url.path}. "
                f"Retry after: {retry_after}s"
            )
            
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Too many requests",
                    "message": f"Rate limit exceeded. Please try again in {retry_after} seconds.",
                    "retry_after": retry_after
                },
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit": str(self.limiter.requests_per_window),
                    "X-RateLimit-Remaining": str(remaining),
                    "X-RateLimit-Reset": str(retry_after)
                }
            )

        # Process request
        response = await call_next(request)
        
        # Add rate limit headers to response
        remaining = self.limiter.get_remaining_requests(client_id)
        response.headers["X-RateLimit-Limit"] = str(self.limiter.requests_per_window)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        
        return response


def create_rate_limit_middleware(
    requests_per_window: int = 10,
    window_seconds: int = 60,
    exclude_paths: Optional[list] = None
) -> RateLimitMiddleware:
    """
    Factory function to create rate limit middleware.
    
    Args:
        requests_per_window: Maximum requests per window (default: 10)
        window_seconds: Time window in seconds (default: 60)
        exclude_paths: Paths to exclude from rate limiting
        
    Returns:
        RateLimitMiddleware instance
    """
    def middleware_factory(app):
        return RateLimitMiddleware(
            app,
            requests_per_window=requests_per_window,
            window_seconds=window_seconds,
            exclude_paths=exclude_paths
        )
    return middleware_factory
