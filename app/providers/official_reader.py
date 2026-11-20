"""Lee únicamente fichas oficiales registradas, con límites de tiempo y tamaño."""

from functools import lru_cache
from html.parser import HTMLParser
from time import monotonic

import httpx

LIBRARY_URL = "https://biblored.gov.co/bibliotecas/biblioteca-tintal"
TRANSIT_URL = (
    "https://www.transmilenio.gov.co/comunicaciones/noticias-de-transmilenio/"
    "especiales-transmilenio/transmiapp-aplicacion-oficial-transmilenio"
)
_transport: httpx.BaseTransport | None = None
_LIMIT = 512_000
_SECONDS = 2.5


def read_page(url: str) -> str | None:
    if url not in (LIBRARY_URL, TRANSIT_URL):
        return None
    return _read(url, _transport, int(monotonic() // 300))


@lru_cache(maxsize=8)
def _read(url: str, transport: httpx.BaseTransport | None, window: int) -> str | None:
    deadline = monotonic() + _SECONDS
    try:
        with httpx.Client(timeout=_SECONDS, transport=transport, follow_redirects=False) as client:
            with client.stream("GET", url, headers={"Accept": "text/html"}) as response:
                if response.status_code != 200 or "text/html" not in response.headers.get("content-type", ""):
                    return None
                body = bytearray()
                for chunk in response.iter_bytes(chunk_size=4096):
                    if monotonic() > deadline or len(body) + len(chunk) > _LIMIT:
                        return None
                    body.extend(chunk)
                return body.decode("utf-8")
    except (httpx.HTTPError, UnicodeError):
        return None


class LibraryField(HTMLParser):
    """Examina un solo campo de la ficha de BibloRed."""

    def __init__(self, field: str) -> None:
        super().__init__()
        self.field = field
        self.depth = 0
        self.done = False
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if self.done:
            return
        if self.depth and tag == "br":
            self.parts.append("\n")
        values = dict(attrs)
        if tag == "div" and (self.depth or self.field in (values.get("class") or "").split()):
            self.depth += 1

    def handle_endtag(self, tag: str) -> None:
        if self.depth and tag == "div":
            self.depth -= 1
            self.done = self.depth == 0
        if self.depth and tag in {"div", "p", "br"}:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if self.depth >= 2:
            self.parts.append(data)

    def values(self, html: str) -> tuple[str, ...]:
        self.feed(html)
        parts = (" ".join(line.split()).strip("- ") for line in "".join(self.parts).split("\n"))
        return tuple(value for value in parts if value)[1:] if self.done else ()
