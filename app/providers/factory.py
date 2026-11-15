"""Factory del ModelProvider: CHAT_MODEL en .env elige el ambiente sin tocar la lógica.

- analitico (Local, por defecto): AnalyticModel, sin internet ni claves.
- generativo (Nube): GenerativeModel con Gemini si hay GEMINI_API_KEY (H36), si no con
  Claude si hay ANTHROPIC_API_KEY; sin ninguna, respaldo analítico. Redacta con el
  contexto público de la plataforma (site_context).
- moe (Híbrido): MoERouter con expertos espacial y documental locales y conversacional generativo.
"""

from typing import Literal

from app.core.config import Settings
from app.providers.analytic_model import AnalyticModel
from app.providers.generative_model import GenerativeModel, TextGenerator
from app.providers.model_provider import Language, ModelProvider
from app.providers.moe_router import MoERouter
from app.providers.site_context import site_context
from app.providers.tools import BarrioTools


def text_generator(settings: Settings) -> TextGenerator | None:
    gemini = settings.gemini_api_key.get_secret_value()
    if gemini:
        from app.providers.gemini_generator import GeminiTextGenerator

        return GeminiTextGenerator(gemini, settings.gemini_model)
    key = settings.anthropic_api_key.get_secret_value()
    if not key:
        return None
    from app.providers.claude_generator import ClaudeTextGenerator  # solo si hay credencial

    return ClaudeTextGenerator(key, settings.chat_llm_model)


def provider_name(settings: Settings) -> Literal["gemini", "claude"] | None:
    """Proveedor externo que recibe los mensajes (para el aviso del chat), o None."""
    if settings.chat_model == "analitico":
        return None
    if settings.gemini_api_key.get_secret_value():
        return "gemini"
    return "claude" if settings.anthropic_api_key.get_secret_value() else None


def build_provider(settings: Settings, tools: BarrioTools) -> ModelProvider:
    analytic = AnalyticModel(tools)
    if settings.chat_model == "analitico":
        return analytic

    def context(idioma: Language) -> str:
        return site_context(tools, idioma)

    generative = GenerativeModel(analytic, text_generator(settings), context)
    if settings.chat_model == "generativo":
        return generative
    return MoERouter({
        "espacial": AnalyticModel(tools, experto="espacial"),
        "documental": AnalyticModel(tools, experto="documental"),
        "conversacional": generative,
    })
