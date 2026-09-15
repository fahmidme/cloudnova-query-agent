"""Reviewer defaults and official onboarding links, checked on 2026-09-15."""

DEFAULT_MODELS = {"openai": "gpt-5.6-luna", "anthropic": "claude-haiku-4-5-20251001"}

GUIDES = {
    "openai": {
        "name": "OpenAI GPT-5.6 Luna",
        "price": "$0.20 input / $1.20 output per 1M tokens (standard, short context)",
        "pricing_url": "https://developers.openai.com/api/docs/pricing",
        "steps": [
            "Sign in or create an account: https://platform.openai.com/",
            "Choose your organization/project; enable API billing or add credits: https://platform.openai.com/settings/organization/billing/overview",
            "Open https://platform.openai.com/api-keys and choose Create new secret key. Name it CloudNova review and select your project.",
            "Copy the new secret key, return here, and paste it at the hidden API key prompt. Press Enter to keep the selected model.",
        ],
    },
    "anthropic": {
        "name": "Claude Haiku 4.5",
        "price": "$1 input / $5 output per 1M tokens (standard)",
        "pricing_url": "https://platform.claude.com/docs/en/models/overview",
        "steps": [
            "Sign in or create an account: https://platform.claude.com/",
            "Enable API billing or add credits: https://platform.claude.com/settings/billing",
            "Open https://platform.claude.com/settings/keys and choose Create key. Name it CloudNova review, link your account, and scope it to one workspace.",
            "Copy the key shown at creation, return here, and paste it at the hidden API key prompt. Press Enter to keep the selected model.",
        ],
    },
}
