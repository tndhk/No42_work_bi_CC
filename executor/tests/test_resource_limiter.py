"""ResourceLimiter テスト"""
import pytest
import time


class TestResourceLimiter:
    """ResourceLimiter のテスト"""

    def _make_limiter(self, **kwargs):
        from app.resource_limiter import ResourceLimiter
        return ResourceLimiter(**kwargs)

    def test_normal_execution_completes(self):
        """制限内の処理は正常に完了する"""
        limiter = self._make_limiter(timeout_seconds=5)
        with limiter.limit():
            result = sum(range(1000))
        assert result == 499500

    def test_timeout_raises_error(self):
        """タイムアウト超過でTimeoutErrorが発生する"""
        limiter = self._make_limiter(timeout_seconds=1)
        with pytest.raises(TimeoutError, match="1秒を超えました"):
            with limiter.limit():
                time.sleep(3)

    def test_timeout_cleanup(self):
        """タイムアウト後にアラームがクリアされる"""
        import signal
        limiter = self._make_limiter(timeout_seconds=1)

        try:
            with limiter.limit():
                time.sleep(3)
        except TimeoutError:
            pass

        # アラームがクリアされていることを確認
        # (SIGALRMハンドラが元に戻っている)
        remaining = signal.alarm(0)
        assert remaining == 0

    def test_nested_context_managers(self):
        """複数のリミッターがネストできる"""
        limiter1 = self._make_limiter(timeout_seconds=5)
        limiter2 = self._make_limiter(timeout_seconds=3)

        with limiter1.limit():
            with limiter2.limit():
                result = 42
        assert result == 42

    def test_short_timeout_values(self):
        """短いタイムアウト値が正しく動作する"""
        limiter = self._make_limiter(timeout_seconds=2)
        with limiter.limit():
            # 2秒以内に完了する処理
            result = [i * 2 for i in range(100)]
        assert len(result) == 100
