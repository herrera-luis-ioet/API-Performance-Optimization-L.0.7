"""Rate limiting middleware implementation using Redis."""
from typing import Callable
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from redis.exceptions import RedisError
from app.core.cache import redis_client
from app.config import settings

class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware using Redis for tracking request counts.
    
    Implements a sliding window rate limit using Redis sorted sets.
    """
    
    def __init__(self, app):
        """Initialize the middleware with the FastAPI app."""
        super().__init__(app)
        self.rate_limit_requests = settings.RATE_LIMIT_REQUESTS
        self.rate_limit_window = settings.RATE_LIMIT_WINDOW

    async def get_client_identifier(self, request: Request) -> str:
        """
        Get a unique identifier for the client making the request.
        
        Args:
            request: The incoming request
            
        Returns:
            str: A unique identifier (IP address or API key)
        """
        # Use X-Forwarded-For header if behind a proxy, fallback to client host
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            client_ip = forwarded_for.split(",")[0].strip()
        else:
            client_ip = request.client.host
            
        return f"rate_limit:{client_ip}"

    async def check_rate_limit(self, client_id: str) -> tuple[bool, int]:
        """
        Check if the client has exceeded their rate limit.
        
        Args:
            client_id: The client's unique identifier
            
        Returns:
            tuple[bool, int]: (is_allowed, remaining_requests)
            
        Raises:
            RedisError: If Redis operations fail
        """
        try:
            current_time = await redis_client.time()
            window_start = current_time[0] - self.rate_limit_window
            
            # Remove old requests outside the window
            await redis_client.zremrangebyscore(client_id, 0, window_start)
            
            # Count requests in current window
            request_count = await redis_client.zcard(client_id)
            
            if request_count >= self.rate_limit_requests:
                return False, 0
                
            # Add current request
            await redis_client.zadd(client_id, {str(current_time[0]): current_time[0]})
            await redis_client.expire(client_id, self.rate_limit_window)
            
            remaining = self.rate_limit_requests - request_count - 1
            return True, remaining
            
        except RedisError as e:
            # Log the error in production
            print(f"Redis error in rate limiter: {str(e)}")
            # Allow request to proceed if Redis fails
            return True, self.rate_limit_requests

    async def set_rate_limit_headers(self, response: Response, remaining: int) -> None:
        """
        Set rate limit headers on the response.
        
        Args:
            response: The response object
            remaining: Number of remaining requests
        """
        response.headers["X-RateLimit-Limit"] = str(self.rate_limit_requests)
        response.headers["X-RateLimit-Remaining"] = str(max(0, remaining))
        response.headers["X-RateLimit-Reset"] = str(self.rate_limit_window)

    async def __call__(self, request: Request, call_next: Callable) -> Response:
        """
        Process the request and apply rate limiting.
        
        Args:
            request: The incoming request
            call_next: The next middleware/route handler
            
        Returns:
            Response: The response object
        """
        if not settings.RATE_LIMIT_ENABLED:
            return await call_next(request)

        client_id = await self.get_client_identifier(request)
        is_allowed, remaining = await self.check_rate_limit(client_id)

        if not is_allowed:
            response = JSONResponse(
                status_code=429,
                content={
                    "detail": "Too many requests. Please try again later."
                }
            )
            await self.set_rate_limit_headers(response, remaining)
            return response

        response = await call_next(request)
        await self.set_rate_limit_headers(response, remaining)
        return response