"""LLM client using LiteLLM for multi-provider support."""

import asyncio
from typing import Any
import structlog

logger = structlog.get_logger()


class LiteLLMClient:
    """LLM client using LiteLLM for unified multi-provider access."""

    def __init__(
        self,
        model: str,
        api_key: str,
        provider_name: str | None = None,
        fallback_models: list[str] | None = None,
    ):
        """Initialize LiteLLM client.

        Args:
            model: Model name in LiteLLM format (e.g., "anthropic/claude-3-5-sonnet-20241022")
                   or just model name if provider is specified
            api_key: API key for the provider
            provider_name: Provider name (anthropic, openai, google)
            fallback_models: Optional list of fallback models in order of priority
        """
        import litellm

        self.litellm = litellm

        # Build model name with provider prefix if needed
        if provider_name and "/" not in model:
            # Map provider names to LiteLLM prefixes
            provider_prefix = {
                "anthropic": "anthropic",
                "openai": "openai",
                "google": "gemini",
            }.get(provider_name, provider_name)
            self.model = f"{provider_prefix}/{model}"
        else:
            self.model = model

        self.api_key = api_key
        self.provider_name = provider_name
        self.fallback_models = fallback_models or []

        # Set API key in environment for LiteLLM
        self._set_api_key(provider_name, api_key)

        logger.info(
            "LiteLLM client initialized",
            model=self.model,
            provider=provider_name,
            fallbacks=len(self.fallback_models),
        )

    def _set_api_key(self, provider_name: str | None, api_key: str) -> None:
        """Set API key in environment for LiteLLM."""
        import os

        if provider_name == "anthropic":
            os.environ["ANTHROPIC_API_KEY"] = api_key
        elif provider_name == "openai":
            os.environ["OPENAI_API_KEY"] = api_key
        elif provider_name == "google":
            os.environ["GEMINI_API_KEY"] = api_key
        else:
            # Try to infer from model name
            if "anthropic" in self.model.lower() or "claude" in self.model.lower():
                os.environ["ANTHROPIC_API_KEY"] = api_key
            elif "openai" in self.model.lower() or "gpt" in self.model.lower():
                os.environ["OPENAI_API_KEY"] = api_key
            elif "gemini" in self.model.lower():
                os.environ["GEMINI_API_KEY"] = api_key

    async def create_message(
        self,
        messages: list[dict[str, Any]],
        system: str,
        model: str | None = None,
        max_tokens: int = 1024,
        temperature: float = 0.0,
    ) -> tuple[str, int]:
        """Create a message completion using LiteLLM.

        Args:
            messages: List of message dicts with role and content
            system: System prompt
            model: Optional model override
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature

        Returns:
            Tuple of (response_text, total_tokens_used)
        """
        loop = asyncio.get_event_loop()

        # Use provided model or default
        use_model = model or self.model

        # Build LiteLLM messages (prepend system as a message)
        litellm_messages = [{"role": "system", "content": system}]

        for msg in messages:
            role = msg["role"]
            content = msg["content"]

            if isinstance(content, str):
                litellm_messages.append({"role": role, "content": content})
            elif isinstance(content, list):
                # Handle multimodal content
                litellm_content = []
                for item in content:
                    if item.get("type") == "text":
                        litellm_content.append({
                            "type": "text",
                            "text": item.get("text", "")
                        })
                    elif item.get("type") == "image":
                        source = item.get("source", {})
                        if source.get("type") == "base64":
                            media_type = source.get("media_type", "image/png")
                            data = source.get("data", "")
                            litellm_content.append({
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{media_type};base64,{data}"
                                }
                            })
                litellm_messages.append({"role": role, "content": litellm_content})

        try:
            logger.debug("Calling LiteLLM", model=use_model)

            response = await loop.run_in_executor(
                None,
                lambda: self.litellm.completion(
                    model=use_model,
                    messages=litellm_messages,
                    max_tokens=max_tokens,
                    temperature=temperature,
                ),
            )

            logger.debug("LiteLLM call successful")

            response_text = response.choices[0].message.content or ""
            total_tokens = response.usage.total_tokens if response.usage else 0

            return response_text, total_tokens

        except Exception as e:
            logger.error("LiteLLM call failed", model=use_model, error=str(e))
            raise


def create_llm_client(
    provider_name: str,
    api_key: str,
    model: str | None = None,
    fallback_models: list[str] | None = None,
) -> LiteLLMClient:
    """Factory function to create LiteLLM client.

    Args:
        provider_name: Name of the provider (anthropic, openai, google)
        api_key: API key for the provider
        model: Optional model name (defaults based on provider)
        fallback_models: Optional list of fallback models

    Returns:
        LiteLLMClient instance
    """
    # Default models for each provider
    default_models = {
        "anthropic": "claude-sonnet-4-5-20250929",
        "openai": "gpt-4o",
        "google": "gemini-2.0-flash",
    }

    use_model = model or default_models.get(provider_name, "gpt-4o")

    return LiteLLMClient(
        model=use_model,
        api_key=api_key,
        provider_name=provider_name,
        fallback_models=fallback_models,
    )
