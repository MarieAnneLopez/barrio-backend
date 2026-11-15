"""Contexto público del chat con IA (H36): solo datos de la plataforma, cacheado."""

from app.providers.analytic_model import AnalyticModel
from app.providers.generative_model import GenerativeModel
from app.providers.model_provider import ChatQuery
from app.providers.site_context import TTL_S, clear_cache, site_context
from tests.unit.chat_fakes import FakeTools


class Counting(FakeTools):
    builds: int = 0

    def milestones(self):  # type: ignore[no-untyped-def]
        self.builds += 1
        return super().milestones()


def test_trae_definicion_modulos_nombres_e_historia_sin_datos_personales() -> None:
    clear_cache()
    text = site_context(FakeTools(), "es", now=0)
    assert "UPZ 78 Tintal Norte (343 ha) y 79 Calandaima (319 ha)" in text
    assert ("- Centros Educativos [centros-educativos]: 4 (1 verificado, 2 por verificar, 1 dato de ejemplo): "
            "Colegio Alfa; Cancha de fútbol (por verificar) ×2; Librería de ejemplo 1 (dato de ejemplo)") in text
    assert "- Datos Catastrales [datos-catastrales]: 5 (2 verificado)" in text
    assert "- 1959: Cierra el aeropuerto de Techo (por verificar)" in text
    assert "+57" not in text and "Funza" not in text  # el perfil de la creadora no se envía


def test_cache_de_cinco_minutos_por_idioma() -> None:
    clear_cache()
    tools = Counting()
    site_context(tools, "en", now=0)
    site_context(tools, "en", now=TTL_S - 1)
    assert tools.builds == 1
    english = site_context(tools, "en", now=TTL_S + 1)
    assert "Menu sections" in english and "(sample data)" in english and tools.builds == 2


def test_el_modelo_generativo_envia_el_contexto_con_los_datos() -> None:
    seen: list[str] = []

    class Writer:
        def generate(self, system: str, prompt: str) -> str:
            seen.append(prompt)
            return "Hay cinco colegios."

    model = GenerativeModel(AnalyticModel(FakeTools()), Writer(), lambda idioma: f"CTX-{idioma}")
    model.answer(ChatQuery("colegios"))
    assert seen[0].startswith("CONTEXTO:\nCTX-es\n\nDATOS:")
    model.answer(ChatQuery("schools", "en"))
    assert seen[1].startswith("CONTEXT:\nCTX-en\n\nDATA:")
