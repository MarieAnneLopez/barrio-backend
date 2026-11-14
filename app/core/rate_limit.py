"""Límite de intentos de inicio de sesión y registro (H21, D58).

Ventana fija en memoria: sirve para un solo proceso de uvicorn, que es como
corre el proyecto. Con varios procesos habría que llevarlo a un almacén común.
"""

import time
from collections.abc import Callable

from app.core.exceptions import AppError


class TooManyAttemptsError(AppError):
    def __init__(self, retry_after: int) -> None:
        super().__init__("TOO_MANY_ATTEMPTS", "Demasiados intentos; espera unos minutos",
                         429, {"retry_after_s": retry_after})


class AttemptLimiter:
    def __init__(self, max_attempts: int = 10, window_s: int = 900,
                 clock: Callable[[], float] = time.monotonic) -> None:
        self._max = max_attempts
        self._window = window_s
        self._clock = clock
        self._hits: dict[str, tuple[float, int]] = {}

    def check(self, key: str) -> None:
        start, count = self._hits.get(key, (0.0, 0))
        elapsed = self._clock() - start
        if elapsed >= self._window:
            self._hits.pop(key, None)
        elif count >= self._max:
            raise TooManyAttemptsError(int(self._window - elapsed) + 1)

    def hit(self, key: str) -> None:
        start, count = self._hits.get(key, (self._clock(), 0))
        self._hits[key] = (start, count + 1)

    def reset(self, key: str) -> None:
        self._hits.pop(key, None)
