from app.ratelimit import SlidingWindowRateLimiter


def test_allows_up_to_limit():
    limiter = SlidingWindowRateLimiter(max_requests=3, window_seconds=60)
    for _ in range(3):
        limiter.check("key-a")  # should not raise


def test_blocks_once_over_limit():
    limiter = SlidingWindowRateLimiter(max_requests=2, window_seconds=60)
    limiter.check("key-b")
    limiter.check("key-b")
    try:
        limiter.check("key-b")
        raised = False
    except Exception:
        raised = True
    assert raised


def test_keys_are_independent():
    limiter = SlidingWindowRateLimiter(max_requests=1, window_seconds=60)
    limiter.check("key-c")
    limiter.check("key-d")  # different key, independent budget — should not raise
