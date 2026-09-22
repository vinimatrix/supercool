# Multi-Provider AI Abstraction Design

## Overview

This design describes the multi-provider AI abstraction layer for SuperCool AI Cinematic Studio. It allows the application to use different LLM providers (Google Gemini, OpenAI GPT-4o, NVIDIA NIM) with a unified interface and configurable fallback.

## Core Components

### 1. Entity Dataclass
- **Purpose:** Represent extracted entities from text.
- **Fields:** `name`, `entity_type` (character/location/prop), `traits` (list[str]), `confidence` (float).
- **Location:** `app/providers/base.py`.

### 2. LLMProvider Abstract Base Class
- **Purpose:** Define a common interface for all LLM providers.
- **Methods:**
  - `async extract_entities(text: str) -> list[Entity]`
  - `async generate_prompt(scene_description: str, characters: list[dict]) -> str`
  - `async health_check() -> bool`
- **Location:** `app/providers/base.py`.

### 3. Provider Implementations
- **GoogleProvider:** Uses Google Gemini API (gemini-2.0-flash).
- **OpenAIProvider:** Uses OpenAI API (gpt-4o).
- **NVIDIAProvider:** Uses NVIDIA NIM API (meta/llama-3.1-8b-instruct).
- **Common Pattern:** Each provider reads its API key from `settings`, uses `httpx` for HTTP requests, and implements the `LLMProvider` interface.
- **Health Check:** Returns `True` if the API key is non-empty (simple check).

### 4. ProviderRegistry
- **Purpose:** Manage available providers and provide fallback logic.
- **Constructor:** Accepts optional `providers` dict; if `None`, auto-discovers based on `settings` API keys.
- **Primary Provider:** `get_provider(name=None)` returns the provider matching `settings.llm_provider` if available, otherwise `None`.
- **Fallback Provider:** `get_fallback_provider()` returns the next available provider in the fallback chain (`google → openai → nvidia`), starting from the primary.
- **No Automatic Retry:** Callers are responsible for handling fallback when a provider fails.
- **Location:** `app/providers/registry.py`.

## Configuration

The `Settings` class in `app/config.py` includes:
- `google_api_key`, `openai_api_key`, `nvidia_api_key` for provider authentication.
- `llm_provider` (default `"google"`) for primary provider selection.
- `llm_fallback_enabled` (default `True`) for enabling/disabling fallback (currently unused in registry but available for future use).

## Data Flow

1. Caller requests a provider via `registry.get_provider()` (for primary) or `registry.get_fallback_provider()` (for fallback).
2. Registry returns a provider instance (or `None` if unavailable).
3. Caller uses provider's `extract_entities`, `generate_prompt`, or `health_check` methods.
4. If a provider call fails, caller can request the next fallback provider.

## Error Handling

- Providers raise exceptions on API errors (e.g., `httpx.HTTPStatusError`).
- Registry does not catch exceptions; callers must handle them.
- Health checks are simple API key presence checks; actual API connectivity is not verified.

## Testing Strategy

- **Unit Tests:** Mock HTTP calls to test provider logic without real API calls.
- **Registry Tests:** Verify provider discovery, primary selection, and fallback order.
- **Interface Tests:** Ensure all providers implement the `LLMProvider` interface correctly.

## Files to Create

1. `app/providers/__init__.py` - Package marker.
2. `app/providers/base.py` - `Entity` dataclass and `LLMProvider` ABC.
3. `app/providers/google.py` - `GoogleProvider` implementation.
4. `app/providers/openai.py` - `OpenAIProvider` implementation.
5. `app/providers/nvidia.py` - `NVIDIAProvider` implementation.
6. `app/providers/registry.py` - `ProviderRegistry` class.
7. `tests/test_providers/__init__.py` - Test package marker.
8. `tests/test_providers/test_registry.py` - Tests for registry and interface.

## Dependencies

- `httpx` for HTTP requests (already in project dependencies).
- `app.config.settings` for API keys and provider configuration.

## Future Considerations

- Implement actual API error handling and retries.
- Add provider-specific rate limiting.
- Include provider health checks that verify API connectivity.
- Support for additional providers (e.g., Anthropic, Cohere).
- Dynamic provider registration and removal.