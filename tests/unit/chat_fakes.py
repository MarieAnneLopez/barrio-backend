"""Doble de BarrioTools con datos fijos: las pruebas de los modelos no tocan la base."""

from dataclasses import dataclass, field

from app.providers.tools import Locality, Milestone, ModuleSummary, NearPlace, RankedPlace


@dataclass
class FakeTools:
    empty: bool = False
    calls: list[tuple[object, ...]] = field(default_factory=list)

    def summary(self, slug: str) -> ModuleSummary:
        if self.empty:
            return ModuleSummary(slug, 0, 0, ())
        return ModuleSummary(slug, 5, 2, ("Colegio Alfa", "Jardín Beta", "IED Gamma"))

    def place_names(self, slug: str) -> list[tuple[str, str]]:
        if self.empty:
            return []
        return [("Colegio Alfa", "verificado"), ("Cancha de fútbol", "por_verificar"),
                ("Cancha de fútbol", "por_verificar"), ("Librería de ejemplo 1", "ejemplo")]

    def totals(self) -> dict[str, int]:
        return {"datos-catastrales": 3706, "estado-calles": 341, "robos": 132, "barberias": 4}

    def ratings_count(self) -> int:
        return 12

    def best(self, slug: str | None) -> RankedPlace | None:
        self.calls.append(("best", slug))
        return None if self.empty else RankedPlace(slug or "barberias", 3, "Barbería Kings", 4.25, 8)

    def nearest(self, lon: float, lat: float, slug: str | None, limit: int = 3) -> list[NearPlace]:
        self.calls.append(("nearest", lon, lat, slug))
        if self.empty:
            return []
        return [NearPlace("zonas-verdes", 1, "Parque El Tintal", 73.4),
                NearPlace("escenarios-deportivos", 2, "Cancha de fútbol", 1093.0)]

    def milestones(self) -> list[Milestone]:
        if self.empty:
            return []
        return [Milestone(1959, "Cierra el aeropuerto de Techo", False),
                Milestone(1963, "De Techo a Ciudad Kennedy", True),
                Milestone(1967, "El Concejo ratifica el nombre", True)]

    def locality(self) -> Locality | None:
        return None if self.empty else Locality("Kennedy", 1104934, 38.21)

    def center(self) -> tuple[float, float]:
        return (-74.16, 4.64)
