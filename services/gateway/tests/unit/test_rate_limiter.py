"""Tests for the sliding window rate limiter."""

from __future__ import annotations

from gateway.storage.rate_limiter import (
    SlidingWindowLimiter,
)


def test_first_request_is_allowed(
    rate_limiter: SlidingWindowLimiter,
) -> None:
    """First request should always pass."""
    decision = rate_limiter.check("client_a")
    assert decision.allowed is True
    assert decision.remaining >= 0


def test_requests_within_limit_pass(
    rate_limiter: SlidingWindowLimiter,
) -> None:
    """All requests within RPM pass."""
    for _ in range(3):
        d = rate_limiter.check("client_b")
        assert d.allowed is True


def test_exceeding_limit_is_denied(
    rate_limiter: SlidingWindowLimiter,
) -> None:
    """Request beyond RPM is denied."""
    for _ in range(3):
        rate_limiter.check("client_c")
    decision = rate_limiter.check("client_c")
    assert decision.allowed is False
    assert decision.remaining == 0


def test_retry_after_is_positive_on_deny(
    rate_limiter: SlidingWindowLimiter,
) -> None:
    """Denied request has positive retry_after."""
    for _ in range(3):
        rate_limiter.check("client_d")
    decision = rate_limiter.check("client_d")
    assert decision.retry_after_seconds >= 0


def test_different_clients_are_independent(
    rate_limiter: SlidingWindowLimiter,
) -> None:
    """Each client has its own window."""
    for _ in range(3):
        rate_limiter.check("client_e")
    d = rate_limiter.check("client_f")
    assert d.allowed is True


def test_remaining_decrements(
    rate_limiter: SlidingWindowLimiter,
) -> None:
    """Remaining count decreases."""
    d1 = rate_limiter.check("client_g")
    d2 = rate_limiter.check("client_g")
    assert d2.remaining < d1.remaining


def test_default_rpm_is_sixty() -> None:
    """Default limiter allows 60 RPM."""
    limiter = SlidingWindowLimiter()
    d = limiter.check("client_h")
    assert d.allowed is True
    assert d.remaining == 59


def test_zero_rpm_is_coerced() -> None:
    """Zero RPM is coerced to one."""
    limiter = SlidingWindowLimiter(
        requests_per_minute=0,
    )
    d = limiter.check("client_i")
    assert d.allowed is True
