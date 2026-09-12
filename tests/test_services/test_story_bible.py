from app.services.context_injector import ContextInjector


def test_context_injector_locked_traits():
    injector = ContextInjector()
    result = injector.inject_locked_traits("Boruto stands", ["scar", "cape"])
    assert "scar" in result
    assert "cape" in result


def test_context_injector_negative_prompt():
    injector = ContextInjector()
    result = injector.get_negative_prompt()
    assert "2d anime" in result


def test_context_injector_engine_routing():
    injector = ContextInjector()
    assert injector.detect_engine("dash forward and strike") == "SEEDANCE"
    assert injector.detect_engine("stare at the sunset") == "FLOW"