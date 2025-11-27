"""
Keepa Service - Data Models and Constants
==========================================
Data classes, enums, and constants for Keepa API integration.

Separated from keepa_service.py for SRP compliance.
"""

from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field
from typing import Any, Optional


# Keepa API endpoint costs (in tokens)
ENDPOINT_COSTS = {
    "product": 1,        # 1 token per ASIN (batch up to 100)
    "bestsellers": 50,   # 50 tokens flat (returns up to 500k ASINs)
    "deals": 5,          # 5 tokens per 150 deals
    "search": 10,        # 10 tokens per result page
    "category": 1,       # 1 token per category
    "seller": 1,         # 1 token per seller
}

# Safety thresholds
MIN_BALANCE_THRESHOLD = 10  # Refuse requests if balance < 10 tokens
SAFETY_BUFFER = 20          # Warn if balance < 20 tokens


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass
class CacheEntry:
    """Cache entry with TTL."""
    data: Any
    expires_at: datetime
    cache_type: str  # 'meta', 'pricing', 'bsr'

    def is_expired(self) -> bool:
        return datetime.now() > self.expires_at


@dataclass
class TokenMetrics:
    """Token usage tracking."""
    tokens_used: int = 0
    tokens_remaining: Optional[int] = None
    requests_count: int = 0
    last_reset: datetime = field(default_factory=datetime.now)

    def add_usage(self, tokens: int, remaining: Optional[int] = None):
        self.tokens_used += tokens
        self.tokens_remaining = remaining
        self.requests_count += 1


@dataclass
class CircuitBreaker:
    """Circuit breaker for API resilience."""
    failure_threshold: int = 5
    timeout_duration: int = 60  # seconds
    half_open_max_calls: int = 3

    failure_count: int = 0
    state: CircuitState = CircuitState.CLOSED
    last_failure_time: Optional[datetime] = None
    half_open_calls: int = 0

    def can_proceed(self) -> bool:
        if self.state == CircuitState.CLOSED:
            return True
        elif self.state == CircuitState.OPEN:
            if self.last_failure_time and \
               datetime.now() - self.last_failure_time > timedelta(seconds=self.timeout_duration):
                self.state = CircuitState.HALF_OPEN
                self.half_open_calls = 0
                return True
            return False
        elif self.state == CircuitState.HALF_OPEN:
            return self.half_open_calls < self.half_open_max_calls
        return False

    def record_success(self):
        self.failure_count = 0
        if self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.CLOSED
        self.half_open_calls = 0

    def record_failure(self):
        self.failure_count += 1
        self.last_failure_time = datetime.now()

        if self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.OPEN
        elif self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN


# Backward compatibility exports
__all__ = [
    # Constants
    'ENDPOINT_COSTS',
    'MIN_BALANCE_THRESHOLD',
    'SAFETY_BUFFER',

    # Enums
    'CircuitState',

    # Data classes
    'CacheEntry',
    'TokenMetrics',
    'CircuitBreaker',
]
