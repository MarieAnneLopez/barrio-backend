"""Historia local (H20): línea de tiempo con trazabilidad y fuentes citadas."""

from collections.abc import Sequence
from typing import Any, Protocol

from app.schemas.historia import FuenteOut, HistoriaOut, HitoOut


class HistoriaSource(Protocol):
    """Lo único que el servicio necesita del almacenamiento (ISP)."""

    def hitos(self) -> Sequence[Any]: ...

    def fuentes(self) -> list[dict[str, Any]]: ...

    def consultado(self) -> str: ...


class HistoriaService:
    def __init__(self, source: HistoriaSource) -> None:
        self._source = source

    def historia(self) -> HistoriaOut:
        hitos = [HitoOut.model_validate(h) for h in self._source.hitos()]
        cited = {ref for h in hitos for ref in (h.source_ref or "").split(" | ") if ref}
        fuentes = [FuenteOut.model_validate(f) for f in self._source.fuentes()]
        # Primero las fuentes que respaldan hitos, en el orden del catálogo.
        fuentes.sort(key=lambda f: f.url not in cited)
        return HistoriaOut(consultado=self._source.consultado(), hitos=hitos, fuentes=fuentes)
