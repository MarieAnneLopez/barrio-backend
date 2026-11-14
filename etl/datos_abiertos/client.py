"""Descarga de archivos de datos abiertos con lista blanca de hosts, caché y reintentos.

Solo se descargan archivos publicados en los portales autorizados (D4). Los
archivos de toda la ciudad se filtran en memoria y solo se persiste lo que cae
dentro de El Tintal. Caché en etl/.cache/ (fuera de Git): repetir el ETL no
vuelve a descargar.
"""

import hashlib
import time
from pathlib import Path
from urllib.parse import urlparse

import httpx

from etl.overpass import USER_AGENT

ALLOWED_HOSTS = frozenset({"datosabiertos.bogota.gov.co", "www.datos.gov.co"})
CACHE = Path(__file__).resolve().parent.parent / ".cache"
RETRY_STATUS = {429, 500, 502, 503, 504}


class OpenDataError(RuntimeError):
    """Host no autorizado o descarga fallida."""


class OpenDataClient:
    def __init__(self, http: httpx.Client | None = None, cache_dir: Path = CACHE,
                 retries: int = 3, backoff_s: float = 5.0) -> None:
        self._http = http or httpx.Client(timeout=600.0, follow_redirects=True)
        self._cache = cache_dir
        self._retries = retries
        self._backoff_s = backoff_s

    def fetch(self, url: str) -> Path:
        """Ruta local del archivo; lo descarga una sola vez."""
        host = urlparse(url).hostname or ""
        if urlparse(url).scheme != "https" or host not in ALLOWED_HOSTS:
            raise OpenDataError(f"Host no autorizado por D4: {host or url}")
        target = self._cache / hashlib.sha256(url.encode()).hexdigest()[:24]
        if target.exists():
            return target
        self._cache.mkdir(parents=True, exist_ok=True)
        last = "sin respuesta"
        for attempt in range(1, self._retries + 1):
            try:
                with self._http.stream("GET", url, headers={"User-Agent": USER_AGENT}) as r:
                    if r.status_code == 200:
                        partial = target.with_suffix(".part")
                        with partial.open("wb") as fh:
                            for chunk in r.iter_bytes(1 << 20):
                                fh.write(chunk)
                        partial.replace(target)
                        return target
                    if r.status_code not in RETRY_STATUS:
                        raise OpenDataError(f"{host} respondió {r.status_code}")
                    last = f"HTTP {r.status_code}"
            except httpx.TransportError as exc:
                last = f"{type(exc).__name__}: {exc}"
            if attempt < self._retries:
                time.sleep(self._backoff_s * 2 ** (attempt - 1))
        raise OpenDataError(f"Descarga fallida tras {self._retries} intentos ({last})")


def read_text(path: Path) -> str:
    """UTF-8 si el archivo lo es; si no, Windows-1252 (varios recursos del portal)."""
    raw = path.read_bytes()
    try:
        return raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        return raw.decode("cp1252", errors="replace")
