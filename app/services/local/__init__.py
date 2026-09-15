"""Local video analysis services using open-source AI models."""

__all__ = [
    "CLIPAnalyzer",
]


def __getattr__(name: str):
    if name == "CLIPAnalyzer":
        from app.services.local.clip_analyzer import CLIPAnalyzer
        return CLIPAnalyzer
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
