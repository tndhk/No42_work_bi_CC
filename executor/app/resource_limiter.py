"""ResourceLimiter - リソース使用量を制限"""
import platform
import signal
import threading
from contextlib import contextmanager
from typing import Generator


class ResourceLimiter:
    """リソース使用量を制限"""

    def __init__(
        self,
        timeout_seconds: int = 10,
        max_memory_mb: int = 2048,
    ) -> None:
        self.timeout = timeout_seconds
        self.max_memory = max_memory_mb * 1024 * 1024
        self._is_linux = platform.system() == 'Linux'

    @contextmanager
    def limit(self) -> Generator[None, None, None]:
        """リソース制限を適用"""
        old_handler = None
        old_mem_limit = None
        is_main_thread = threading.current_thread() is threading.main_thread()

        try:
            # タイムアウト設定 (SIGALRM - メインスレッドでのみ動作)
            if is_main_thread:
                def timeout_handler(signum: int, frame: object) -> None:
                    raise TimeoutError(f"実行が{self.timeout}秒を超えました")

                old_handler = signal.signal(signal.SIGALRM, timeout_handler)
                signal.alarm(self.timeout)

            # メモリ制限 (Linux only - macOSでは RLIMIT_AS が動作しない)
            if self._is_linux:
                import resource
                old_mem_limit = resource.getrlimit(resource.RLIMIT_AS)
                resource.setrlimit(
                    resource.RLIMIT_AS,
                    (self.max_memory, self.max_memory),
                )

            yield

        finally:
            # タイムアウト解除
            if is_main_thread:
                signal.alarm(0)
                if old_handler is not None:
                    signal.signal(signal.SIGALRM, old_handler)

            # メモリ制限を元に戻す
            if self._is_linux and old_mem_limit is not None:
                import resource
                resource.setrlimit(resource.RLIMIT_AS, old_mem_limit)
