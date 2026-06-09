"""
ai_handler.py — Multi-provider AI handler with automatic fallback
Providers: Groq → Together AI → OpenRouter → Local fallback
"""

import os
import json
import random
import logging
import asyncio
import aiohttp
from typing import Optional

logger = logging.getLogger(__name__)

# ─── Provider Configs ──────────────────────────────────────────────────────────
PROVIDERS = [
    {
        "name": "Groq",
        "url": "https://api.groq.com/openai/v1/chat/completions",
        "api_key_env": "GROQ_API_KEY",
        "model": "llama3-8b-8192",
        "headers_extra": {},
    },
    {
        "name": "Together AI",
        "url": "https://api.together.xyz/v1/chat/completions",
        "api_key_env": "TOGETHER_API_KEY",
        "model": "mistralai/Mixtral-8x7B-Instruct-v0.1",
        "headers_extra": {},
    },
    {
        "name": "OpenRouter",
        "url": "https://openrouter.ai/api/v1/chat/completions",
        "api_key_env": "OPENROUTER_API_KEY",
        "model": "mistralai/mistral-7b-instruct:free",
        "headers_extra": {
            "HTTP-Referer": "https://github.com/panel-rename-bot",
            "X-Title": "Panel Rename Bot",
        },
    },
]

# Fallback name variations (offline, no API needed)
FALLBACK_SUFFIXES = [
    "Pro", "Plus", "X", "Elite", "Nova", "Prime", "Max", "Ultra",
    "Hub", "Zone", "Base", "Core", "Cloud", "Net", "Tech",
]

class AIHandler:
    def __init__(self):
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=30)
            self._session = aiohttp.ClientSession(timeout=timeout)
        return self._session

    async def _call_provider(self, provider: dict, prompt: str) -> Optional[str]:
        api_key = os.environ.get(provider["api_key_env"], "")
        if not api_key:
            logger.debug(f"{provider['name']}: API key not set, skipping.")
            return None

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            **provider.get("headers_extra", {}),
        }
        payload = {
            "model": provider["model"],
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 60,
            "temperature": 0.8,
        }

        try:
            session = await self._get_session()
            async with session.post(provider["url"], headers=headers, json=payload) as resp:
                if resp.status != 200:
                    body = await resp.text()
                    logger.warning(f"{provider['name']} error {resp.status}: {body[:200]}")
                    return None
                data = await resp.json()
                content = data["choices"][0]["message"]["content"].strip()
                # Clean up
                content = content.strip('"\'`').split("\n")[0].strip()
                return content if content else None
        except asyncio.TimeoutError:
            logger.warning(f"{provider['name']}: Request timed out.")
            return None
        except Exception as e:
            logger.warning(f"{provider['name']}: {e}")
            return None

    async def generate_panel_name(self, base_name: str) -> str:
        """
        Generate a creative panel name based on the base_name.
        Tries each provider in order; falls back to local variation if all fail.
        """
        prompt = (
            f"Generate ONE creative, short admin panel or dashboard name based on: '{base_name}'. "
            "Output ONLY the name itself, no explanation, no quotes, max 4 words. "
            "Make it professional and unique. Examples: 'NexusPanel', 'CloudAdmin Pro', 'PixelDash'."
        )

        # Shuffle providers to distribute load
        providers = PROVIDERS.copy()
        random.shuffle(providers)

        for provider in providers:
            result = await self._call_provider(provider, prompt)
            if result and 2 <= len(result) <= 50:
                logger.info(f"✅ AI name from {provider['name']}: {result}")
                return result

        # Local fallback
        suffix = random.choice(FALLBACK_SUFFIXES)
        fallback = f"{base_name} {suffix}"
        logger.info(f"🔄 Using local fallback name: {fallback}")
        return fallback

    async def suggest_replacements(self, old_name: str, new_name: str, context: str) -> list[str]:
        """
        Use AI to suggest what strings to replace in the file.
        Returns a list of old→new pairs as JSON.
        """
        prompt = (
            f"I need to rename an admin panel from '{old_name}' to '{new_name}'. "
            f"Context snippet:\n{context[:300]}\n\n"
            "List up to 5 exact string replacements needed (old→new) as JSON array: "
            '[{"old": "...", "new": "..."}]. Only JSON, no explanation.'
        )

        providers = PROVIDERS.copy()
        for provider in providers:
            result = await self._call_provider(provider, prompt)
            if result:
                try:
                    # Extract JSON from response
                    start = result.find("[")
                    end = result.rfind("]") + 1
                    if start != -1 and end > start:
                        pairs = json.loads(result[start:end])
                        return pairs
                except Exception:
                    continue
        return []

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()
