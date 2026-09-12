from app.providers.base import LLMProvider, Entity
from app.providers.registry import ProviderRegistry


def test_provider_registry_creation():
    registry = ProviderRegistry(providers={})
    assert registry is not None


def test_provider_interface():
    assert hasattr(LLMProvider, "extract_entities")
    assert hasattr(LLMProvider, "generate_prompt")
    assert hasattr(LLMProvider, "health_check")


def test_entity_dataclass():
    e = Entity(name="Boruto", entity_type="character", traits=["scar"], confidence=0.9)
    assert e.name == "Boruto"
    assert e.entity_type == "character"
    assert e.confidence == 0.9


def test_registry_with_empty_providers():
    registry = ProviderRegistry(providers={})
    assert registry.get_provider() is None
    assert registry.get_fallback_provider() is None


def test_registry_get_named_provider():
    from app.providers.google import GoogleProvider
    registry = ProviderRegistry(providers={"google": GoogleProvider()})
    provider = registry.get_provider("google")
    assert provider is not None
    assert isinstance(provider, GoogleProvider)
