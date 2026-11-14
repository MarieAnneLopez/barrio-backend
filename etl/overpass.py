"""Cliente de Overpass API con reintentos, backoff y timeouts.

La respuesta es dato externo no confiable: se valida su forma antes de usarla.
"""

import time
from typing import Any

import httpx

OVERPASS_URL = "https://overpass-api.de/api/interpreter"
USER_AGENT = "barrio-etl/0.1 (Reconoce tu Barrio: El Tintal, proyecto academico)"
RETRY_STATUS = {429, 500, 502, 503, 504}


class OverpassError(RuntimeError):
    """La consulta no se pudo completar o la respuesta no es válida."""


class OverpassClient:
    def __init__(
        self,
        http: httpx.Client | None = None,
        url: str = OVERPASS_URL,
        retries: int = 3,
        backoff_s: float = 5.0,
        timeout_s: float = 180.0,
    ) -> None:
        self._http = http or httpx.Client(timeout=timeout_s)
        self._url = url
        self._retries = retries
        self._backoff_s = backoff_s

    def query(self, ql: str) -> dict[str, Any]:
        last_error = "sin respuesta"
        for attempt in range(1, self._retries + 1):
            try:
                response = self._http.post(
                    self._url, data={"data": ql}, headers={"User-Agent": USER_AGENT}
                )
            except httpx.TransportError as exc:
                last_error = f"{type(exc).__name__}: {exc}"
            else:
                if response.status_code == 200:
                    return _validated(response)
                if response.status_code not in RETRY_STATUS:
                    raise OverpassError(f"Overpass respondió {response.status_code}")
                last_error = f"HTTP {response.status_code}"
            if attempt < self._retries:
                time.sleep(self._backoff_s * 2 ** (attempt - 1))
        raise OverpassError(f"Overpass falló tras {self._retries} intentos ({last_error})")


def _validated(response: httpx.Response) -> dict[str, Any]:
    try:
        body = response.json()
    except ValueError as exc:
        raise OverpassError("Overpass no devolvió JSON") from exc
    if not isinstance(body, dict) or not isinstance(body.get("elements"), list):
        raise OverpassError("Respuesta de Overpass sin lista 'elements'")
    return body
