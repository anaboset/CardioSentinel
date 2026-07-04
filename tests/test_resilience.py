import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from utils.resilience import retry_with_backoff, LoopLimitExceeded, check_loop_limit


class TestRetryWithBackoff:
    def test_succeeds_on_first_attempt(self):
        result = retry_with_backoff(lambda: 42, operation_name="test")
        assert result == 42

    def test_retries_on_failure(self):
        attempts = {"count": 0}

        def flaky():
            attempts["count"] += 1
            if attempts["count"] < 2:
                raise ValueError("temporary")
            return "ok"

        result = retry_with_backoff(flaky, max_retries=3, backoff=0.01, operation_name="flaky")
        assert result == "ok"
        assert attempts["count"] == 2

    def test_raises_after_max_retries(self):
        with pytest.raises(RuntimeError):
            retry_with_backoff(
                lambda: (_ for _ in ()).throw(RuntimeError("permanent")),
                max_retries=2,
                backoff=0.01,
                operation_name="fail",
            )


class TestLoopLimit:
    def test_check_loop_limit_raises(self):
        with pytest.raises(LoopLimitExceeded):
            check_loop_limit(100, "test_loop")

    def test_check_loop_limit_ok(self):
        check_loop_limit(5, "test_loop")
