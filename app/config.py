"""Explicit settings override OS-protected saved provider credentials."""

import os
from dataclasses import dataclass, field
from pathlib import Path

from .provider_options import DEFAULT_MODELS
from .credentials import load_saved

PROVIDERS = {"openai": "OPENAI", "anthropic": "ANTHROPIC"}


@dataclass(frozen=True)
class ProviderConfig:
    api_key: str = field(repr=False)
    model: str
    provider: str = "openai"
    timeout_seconds: int = 45

    def __post_init__(self):
        if self.provider not in PROVIDERS:
            raise ValueError("provider must be openai or anthropic")
        if not self.api_key.strip() or self.api_key == "your-api-key":
            raise ValueError("a provider API key is required; offline mode needs no key")
        if not self.model.strip() or self.model == "your-model-id":
            raise ValueError("an accessible model ID is required")
        if any(c in self.api_key for c in "\r\n"):
            raise ValueError("API key cannot contain line breaks")


def read_settings(env_file: Path = Path(".env")) -> dict:
    allowed = {"LLM_PROVIDER", "OPENAI_API_KEY", "OPENAI_MODEL", "ANTHROPIC_API_KEY", "ANTHROPIC_MODEL"}
    values = {}
    if env_file.is_file():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            key, separator, value = line.partition("=")
            if not separator:
                raise ValueError(".env must use KEY=value lines (no shell statements)")
            if key.strip() in allowed:
                value = value.strip()
                if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
                    value = value[1:-1]
                values[key.strip()] = value
    values.update({key: os.environ[key] for key in allowed if key in os.environ})
    return values


def load_config(env_file: Path = Path(".env"), provider: str | None = None) -> ProviderConfig:
    values = read_settings(env_file)
    provider = provider or values.get("LLM_PROVIDER", "openai")
    if provider not in PROVIDERS:
        raise ValueError("LLM_PROVIDER must be openai or anthropic")
    prefix = PROVIDERS[provider]
    key = values.get(f"{prefix}_API_KEY", "").strip()
    saved = load_saved(provider) if not key or key == "your-api-key" else None
    if saved:
        key = saved['api_key']
    model = values.get(f"{prefix}_MODEL", "").strip() or (saved or {}).get('model') or DEFAULT_MODELS[provider]
    return ProviderConfig(key, model, provider)
