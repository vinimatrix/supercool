# Multi-Provider AI Abstraction Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create a multi-provider AI abstraction layer that allows the application to use Google Gemini, OpenAI GPT-4o, or NVIDIA NIM for LLM operations with automatic fallback.

**Architecture:** Abstract base class `LLMProvider` defines the interface for entity extraction and prompt generation. Concrete implementations use httpx for HTTP calls. A `ProviderRegistry` manages provider instances with fallback logic based on available API keys.

**Tech Stack:** Python 3.12, httpx (async HTTP), pydantic-settings (config), pytest-asyncio (tests)

## Global Constraints

- Python >= 3.12
- httpx >= 0.27.0 (already in dependencies)
- pytest-asyncio for async tests
- asyncio_mode = "auto" (configured in pyproject.toml)

---

## File Structure

| File | Responsibility |
|------|----------------|
| `app/providers/__init__.py` | Package exports |
| `app/providers/base.py` | `Entity` dataclass + `LLMProvider` ABC |
| `app/providers/google.py` | Google Gemini provider implementation |
| `app/providers/openai.py` | OpenAI GPT-4o provider implementation |
| `app/providers/nvidia.py` | NVIDIA NIM provider implementation |
| `app/providers/registry.py` | `ProviderRegistry` with fallback logic |
| `tests/test_providers/__init__.py` | Test package |
| `tests/test_providers/test_registry.py` | Registry and provider interface tests |

---

## Task 1: Write Tests for Provider Interface and Registry

**Files:**
- Create: `tests/test_providers/__init__.py`
- Create: `tests/test_providers/test_registry.py`

**Interfaces:**
- Consumes: `app.providers.base.LLMProvider`, `app.providers.base.Entity`, `app.providers.registry.ProviderRegistry`
- Produces: Test cases that validate registry creation, provider interface, and fallback behavior

- [ ] **Step 1: Create test package init**

```python
# tests/test_providers/__init__.py
```

- [ ] **Step 2: Write registry and interface tests**

```python
# tests/test_providers/test_registry.py
import pytest
from unittest.mock import AsyncMock, MagicMock

from app.providers.base import LLMProvider, Entity
from app.providers.registry import ProviderRegistry


def test_entity_dataclass():
    entity = Entity(name="John", entity_type="character", traits=["brave"], confidence=0.95)
    assert entity.name == "John"
    assert entity.entity_type == "character"
    assert entity.traits == ["brave"]
    assert entity.confidence == 0.95


def test_provider_registry_creation():
    registry = ProviderRegistry(providers={})
    assert registry is not None
    assert registry.get_provider() is None


def test_provider_interface():
    assert hasattr(LLMProvider, "extract_entities")
    assert hasattr(LLMProvider, "generate_prompt")
    assert hasattr(LLMProvider, "health_check")


def test_provider_registry_with_mock():
    mock_provider = MagicMock(spec=LLMProvider)
    registry = ProviderRegistry(providers={"test": mock_provider})
    assert registry.get_provider("test") is mock_provider


def test_provider_registry_primary():
    mock_provider = MagicMock(spec=LLMProvider)
    registry = ProviderRegistry(providers={"google": mock_provider}, primary="google")
    assert registry.get_provider() is mock_provider


def test_provider_registry_fallback_chain():
    mock_google = MagicMock(spec=LLMProvider)
    mock_openai = MagicMock(spec=LLMProvider)
    registry = ProviderRegistry(
        providers={"google": mock_google, "openai": mock_openai},
        primary="google",
        fallback=["google", "openai"]
    )
    assert registry.get_fallback_provider("google") is mock_openai
    assert registry.get_fallback_provider("nonexistent") is None
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `pytest tests/test_providers/test_registry.py -v`
Expected: FAIL with import errors (modules don't exist yet)

---

## Task 2: Create Base Provider Module

**Files:**
- Create: `app/providers/__init__.py`
- Create: `app/providers/base.py`

**Interfaces:**
- Consumes: Nothing (foundational module)
- Produces: `Entity` dataclass, `LLMProvider` ABC

- [ ] **Step 1: Create base module with Entity and LLMProvider**

```python
# app/providers/base.py
from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class Entity:
    name: str
    entity_type: str
    traits: list[str] = field(default_factory=list)
    confidence: float = 0.0


class LLMProvider(ABC):
    @abstractmethod
    async def extract_entities(self, text: str) -> list[Entity]:
        """Extract named entities from text."""
        ...

    @abstractmethod
    async def generate_prompt(self, scene_description: str, characters: list[dict]) -> str:
        """Generate an image generation prompt from scene description."""
        ...

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the provider is available."""
        ...
```

- [ ] **Step 2: Create package init**

```python
# app/providers/__init__.py
from app.providers.base import Entity, LLMProvider
from app.providers.registry import ProviderRegistry

__all__ = ["Entity", "LLMProvider", "ProviderRegistry"]
```

- [ ] **Step 3: Run tests to verify Entity tests pass**

Run: `pytest tests/test_providers/test_registry.py::test_entity_dataclass tests/test_providers/test_registry.py::test_provider_interface -v`
Expected: PASS

---

## Task 3: Create Google Gemini Provider

**Files:**
- Create: `app/providers/google.py`

**Interfaces:**
- Consumes: `app.providers.base.LLMProvider`, `app.providers.base.Entity`, `app.config.settings`
- Produces: `GoogleProvider` class

- [ ] **Step 1: Implement Google Gemini provider**

```python
# app/providers/google.py
import json
from typing import Any

import httpx

from app.config import settings
from app.providers.base import Entity, LLMProvider


class GoogleProvider(LLMProvider):
    BASE_URL = "https://generativelanguage.googleapis.com/v1beta"

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or settings.google_api_key
        self.client = httpx.AsyncClient(timeout=30.0)

    async def extract_entities(self, text: str) -> list[Entity]:
        prompt = f"""Extract named entities from the following text.
Return a JSON array where each entity has:
- name: the entity name
- entity_type: character, location, or object
- traits: list of descriptive traits
- confidence: float 0-1

Text: {text}

Return ONLY the JSON array, no other text."""

        response = await self._generate(prompt)
        try:
            data = json.loads(response)
            return [Entity(**item) for item in data]
        except (json.JSONDecodeError, KeyError):
            return []

    async def generate_prompt(self, scene_description: str, characters: list[dict]) -> str:
        chars_text = json.dumps(characters, indent=2) if characters else "None"
        prompt = f"""Generate a detailed image generation prompt for this cinematic scene.
Include visual details, lighting, mood, and composition.

Scene: {scene_description}
Characters: {chars_text}

Return ONLY the prompt text, no quotes or explanation."""

        return await self._generate(prompt)

    async def health_check(self) -> bool:
        try:
            response = await self.client.get(
                f"{self.BASE_URL}/models",
                params={"key": self.api_key}
            )
            return response.status_code == 200
        except Exception:
            return False

    async def _generate(self, prompt: str) -> str:
        response = await self.client.post(
            f"{self.BASE_URL}/models/gemini-2.0-flash:generateContent",
            params={"key": self.api_key},
            json={
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": 0.7}
            }
        )
        response.raise_for_status()
        data = response.json()
        return data["candidates"][0]["content"]["parts"][0]["text"]

    async def close(self):
        await self.client.aclose()
```

- [ ] **Step 2: Run tests to verify import works**

Run: `pytest tests/test_providers/test_registry.py -v`
Expected: PASS (registry tests still pass, Google not tested yet)

---

## Task 4: Create OpenAI Provider

**Files:**
- Create: `app/providers/openai.py`

**Interfaces:**
- Consumes: `app.providers.base.LLMProvider`, `app.providers.base.Entity`, `app.config.settings`
- Produces: `OpenAIProvider` class

- [ ] **Step 1: Implement OpenAI GPT-4o provider**

```python
# app/providers/openai.py
import json

import httpx

from app.config import settings
from app.providers.base import Entity, LLMProvider


class OpenAIProvider(LLMProvider):
    BASE_URL = "https://api.openai.com/v1"

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or settings.openai_api_key
        self.client = httpx.AsyncClient(
            timeout=30.0,
            headers={"Authorization": f"Bearer {self.api_key}"}
        )

    async def extract_entities(self, text: str) -> list[Entity]:
        prompt = f"""Extract named entities from the following text.
Return a JSON array where each entity has:
- name: the entity name
- entity_type: character, location, or object
- traits: list of descriptive traits
- confidence: float 0-1

Text: {text}

Return ONLY the JSON array, no other text."""

        response = await self._chat(prompt)
        try:
            data = json.loads(response)
            return [Entity(**item) for item in data]
        except (json.JSONDecodeError, KeyError):
            return []

    async def generate_prompt(self, scene_description: str, characters: list[dict]) -> str:
        chars_text = json.dumps(characters, indent=2) if characters else "None"
        prompt = f"""Generate a detailed image generation prompt for this cinematic scene.
Include visual details, lighting, mood, and composition.

Scene: {scene_description}
Characters: {chars_text}

Return ONLY the prompt text, no quotes or explanation."""

        return await self._chat(prompt)

    async def health_check(self) -> bool:
        try:
            response = await self.client.get(f"{self.BASE_URL}/models")
            return response.status_code == 200
        except Exception:
            return False

    async def _chat(self, prompt: str) -> str:
        response = await self.client.post(
            f"{self.BASE_URL}/chat/completions",
            json={
                "model": "gpt-4o",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.7
            }
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]

    async def close(self):
        await self.client.aclose()
```

- [ ] **Step 2: Run tests to verify import works**

Run: `pytest tests/test_providers/test_registry.py -v`
Expected: PASS

---

## Task 5: Create NVIDIA NIM Provider

**Files:**
- Create: `app/providers/nvidia.py`

**Interfaces:**
- Consumes: `app.providers.base.LLMProvider`, `app.providers.base.Entity`, `app.config.settings`
- Produces: `NvidiaProvider` class

- [ ] **Step 1: Implement NVIDIA NIM provider**

```python
# app/providers/nvidia.py
import json

import httpx

from app.config import settings
from app.providers.base import Entity, LLMProvider


class NvidiaProvider(LLMProvider):
    BASE_URL = "https://integrate.api.nvidia.com/v1"

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or settings.nvidia_api_key
        self.client = httpx.AsyncClient(
            timeout=30.0,
            headers={"Authorization": f"Bearer {self.api_key}"}
        )

    async def extract_entities(self, text: str) -> list[Entity]:
        prompt = f"""Extract named entities from the following text.
Return a JSON array where each entity has:
- name: the entity name
- entity_type: character, location, or object
- traits: list of descriptive traits
- confidence: float 0-1

Text: {text}

Return ONLY the JSON array, no other text."""

        response = await self._chat(prompt)
        try:
            data = json.loads(response)
            return [Entity(**item) for item in data]
        except (json.JSONDecodeError, KeyError):
            return []

    async def generate_prompt(self, scene_description: str, characters: list[dict]) -> str:
        chars_text = json.dumps(characters, indent=2) if characters else "None"
        prompt = f"""Generate a detailed image generation prompt for this cinematic scene.
Include visual details, lighting, mood, and composition.

Scene: {scene_description}
Characters: {chars_text}

Return ONLY the prompt text, no quotes or explanation."""

        return await self._chat(prompt)

    async def health_check(self) -> bool:
        try:
            response = await self.client.get(f"{self.BASE_URL}/models")
            return response.status_code == 200
        except Exception:
            return False

    async def _chat(self, prompt: str) -> str:
        response = await self.client.post(
            f"{self.BASE_URL}/chat/completions",
            json={
                "model": "meta/llama-3.1-70b-instruct",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.7,
                "max_tokens": 1024
            }
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]

    async def close(self):
        await self.client.aclose()
```

- [ ] **Step 2: Run tests to verify import works**

Run: `pytest tests/test_providers/test_registry.py -v`
Expected: PASS

---

## Task 6: Create Provider Registry with Fallback

**Files:**
- Create: `app/providers/registry.py`

**Interfaces:**
- Consumes: `app.providers.base.LLMProvider`, `app.config.settings`
- Produces: `ProviderRegistry` class with `get_provider()`, `get_fallback_provider()`

- [ ] **Step 1: Implement ProviderRegistry**

```python
# app/providers/registry.py
from typing import Any

from app.config import settings
from app.providers.base import LLMProvider


class ProviderRegistry:
    FALLBACK_CHAIN = ["google", "openai", "nvidia"]

    def __init__(
        self,
        providers: dict[str, LLMProvider] | None = None,
        primary: str | None = None,
        fallback: list[str] | None = None,
    ):
        self._providers = providers or {}
        self._primary = primary or settings.llm_provider
        self._fallback = fallback or self.FALLBACK_CHAIN

    def get_provider(self, name: str | None = None) -> LLMProvider | None:
        target = name or self._primary
        return self._providers.get(target)

    def get_fallback_provider(self, current: str) -> LLMProvider | None:
        try:
            idx = self._fallback.index(current)
        except ValueError:
            return None
        for name in self._fallback[idx + 1:]:
            provider = self._providers.get(name)
            if provider is not None:
                return provider
        return None

    def register(self, name: str, provider: LLMProvider) -> None:
        self._providers[name] = provider

    @classmethod
    def from_settings(cls) -> "ProviderRegistry":
        from app.providers.google import GoogleProvider
        from app.providers.openai import OpenAIProvider
        from app.providers.nvidia import NvidiaProvider

        providers = {}
        if settings.google_api_key:
            providers["google"] = GoogleProvider()
        if settings.openai_api_key:
            providers["openai"] = OpenAIProvider()
        if settings.nvidia_api_key:
            providers["nvidia"] = NvidiaProvider()
        return cls(providers=providers)
```

- [ ] **Step 2: Run all tests**

Run: `pytest tests/test_providers/test_registry.py -v`
Expected: PASS

---

## Task 7: Final Verification and Commit

**Files:**
- No new files

**Interfaces:**
- Consumes: All provider modules
- Produces: Passing test suite

- [ ] **Step 1: Run full test suite**

Run: `pytest tests/test_providers/ -v`
Expected: All tests PASS

- [ ] **Step 2: Run linter**

Run: `ruff check app/providers/ tests/test_providers/`
Expected: No errors

- [ ] **Step 3: Commit**

```bash
git add app/providers/ tests/test_providers/
git commit -m "feat: multi-provider AI abstraction (Google/OpenAI/NVIDIA)"
```
