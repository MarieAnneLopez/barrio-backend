"""Factory del ModelProvider: CHAT_MODEL en .env elige el ambiente sin tocar la lógica.

- analitico (Local, por defecto): AnalyticModel, sin internet ni claves.
- generativo (Nube): GenerativeModel con Claude si hay ANTHROPIC_API_KEY; si no, respaldo analítico.
- moe (Híbrido): MoERouter con expertos espacial y documental locales y conversacional generativo.
"""

from app.core.config import Settings
from app.providers.analytic_model import AnalyticModel
from app.providers.generative_model import GenerativeModel, TextGenerator
from app.providers.model_provider import ModelProvider
from app.providers.moe_router import MoERouter
from app.providers.tools import BarrioTools


def text_generator(settings: Settings) -> TextGenerator | None:
    key = settings.anthropic_api_key.get_secret_value()
    if not key:
        return None
    from app.providers.claude_generator import ClaudeTextGenerator  # solo si hay credencial

    return ClaudeTextGenerator(key, settings.chat_llm_model)


def build_provider(settings: Settings, tools: BarrioTools) -> ModelProvider:
    analytic = AnalyticModel(tools)
    if settings.chat_model == "analitico":
        return analytic
    generative = GenerativeModel(analytic, text_generator(settings))
    if settings.chat_model == "generativo":
        return generative
    return MoERouter({
        "espacial": AnalyticModel(tools, experto="espacial"),
        "documental": AnalyticModel(tools, experto="documental"),
        "conversacional": generative,
    })
