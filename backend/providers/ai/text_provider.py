"""Claude Text Provider — implements TextProvider interface."""
import litellm
import logging
from .base import TextProvider
from core.config import ANTHROPIC_API_KEY, CLAUDE_MODEL

logger = logging.getLogger(__name__)


class ClaudeProvider(TextProvider):
    """Anthropic Claude via litellm."""

    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or ANTHROPIC_API_KEY
        self.model = model or CLAUDE_MODEL

    async def complete(self, system: str, user: str, max_tokens: int = 4000) -> str:
        response = await litellm.acompletion(
            model=self.model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            api_key=self.api_key,
            max_tokens=max_tokens,
            timeout=120,
        )
        return response.choices[0].message.content

    def complete_sync(self, system: str, user: str, max_tokens: int = 4000) -> str:
        for attempt in range(3):
            try:
                response = litellm.completion(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                    api_key=self.api_key,
                    max_tokens=max_tokens,
                    timeout=120,
                )
                return response.choices[0].message.content
            except Exception as e:
                err_str = str(e).lower()
                retryable = any(k in err_str for k in ["502", "503", "529", "timeout", "overloaded", "connection"])
                if attempt < 2 and retryable:
                    import time
                    time.sleep(3 * (attempt + 1))
                    continue
                raise

    async def complete_with_images(self, system: str, user: str, images_b64: list, max_tokens: int = 4000) -> str:
        content = [{"type": "text", "text": user}]
        for img_b64 in images_b64:
            content.append({"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_b64}"}})

        response = await litellm.acompletion(
            model=self.model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": content},
            ],
            api_key=self.api_key,
            max_tokens=max_tokens,
            timeout=120,
        )
        return response.choices[0].message.content


class GeminiTextProvider(TextProvider):
    """Google Gemini text via litellm (fallback for Claude)."""

    def __init__(self, api_key: str = None, model: str = None):
        from core.config import GEMINI_API_KEY, GEMINI_TEXT_MODEL
        self.api_key = api_key or GEMINI_API_KEY
        self.model = model or GEMINI_TEXT_MODEL

    async def complete(self, system: str, user: str, max_tokens: int = 4000) -> str:
        response = await litellm.acompletion(
            model=self.model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            api_key=self.api_key,
            max_tokens=max_tokens,
            timeout=120,
        )
        return response.choices[0].message.content

    def complete_sync(self, system: str, user: str, max_tokens: int = 4000) -> str:
        response = litellm.completion(
            model=self.model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            api_key=self.api_key,
            max_tokens=max_tokens,
            timeout=120,
        )
        return response.choices[0].message.content

    async def complete_with_images(self, system: str, user: str, images_b64: list, max_tokens: int = 4000) -> str:
        content = [{"type": "text", "text": user}]
        for img_b64 in images_b64:
            content.append({"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_b64}"}})

        response = await litellm.acompletion(
            model=self.model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": content},
            ],
            api_key=self.api_key,
            max_tokens=max_tokens,
            timeout=120,
        )
        return response.choices[0].message.content
