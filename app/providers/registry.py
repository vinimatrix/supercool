from app.providers.base import LLMProvider
from app.providers.google import GoogleProvider
from app.providers.openai import OpenAIProvider
from app.providers.nvidia import NVIDIAProvider
from app.config import settings


class ProviderRegistry:
    def __init__(self, providers: dict[str, LLMProvider] | None = None):
        if providers is None:
            providers = {}
            if settings.google_api_key:
                providers["google"] = GoogleProvider()
            if settings.openai_api_key:
                providers["openai"] = OpenAIProvider()
            if settings.nvidia_api_key:
                providers["nvidia"] = NVIDIAProvider()
        self._providers = providers
        self._fallback_order = ["google", "openai", "nvidia"]

    def get_provider(self, name: str | None = None) -> LLMProvider | None:
        if name and name in self._providers:
            return self._providers[name]
        # Return primary provider from settings
        primary = settings.llm_provider
        if primary in self._providers:
            return self._providers[primary]
        return None

    def get_fallback_provider(self) -> LLMProvider | None:
        for name in self._fallback_order:
            if name in self._providers:
                return self._providers[name]
        return None
