"""Settings schemas."""

from datetime import datetime
from pydantic import BaseModel, Field


class LLMProviderResponse(BaseModel):
    """Schema for LLM provider response."""

    id: str
    name: str
    display_name: str
    base_url: str
    has_api_key: bool = Field(description="Whether an API key is configured")
    api_key_masked: str | None = Field(description="Masked API key (e.g., sk-ant-***...***abc)")
    active: bool
    description: str | None
    max_requests_per_minute: int | None
    max_tokens_per_minute: int | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class LLMProviderUpdate(BaseModel):
    """Schema for updating an LLM provider."""

    api_key: str | None = Field(default=None, description="API key (leave empty to keep existing)")
    active: bool | None = None
    max_requests_per_minute: int | None = None
    max_tokens_per_minute: int | None = None


class LLMModelResponse(BaseModel):
    """Schema for LLM model response."""

    id: str
    provider_id: str
    name: str
    display_name: str
    description: str | None
    context_window: int | None
    max_output_tokens: int | None
    input_cost_per_1k: float | None
    output_cost_per_1k: float | None
    supports_vision: bool
    supports_function_calling: bool
    active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class IntegrationResponse(BaseModel):
    """Schema for integration response."""

    id: str
    purpose: str
    provider_id: str
    provider_name: str
    model_id: str
    model_name: str
    active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class IntegrationUpdate(BaseModel):
    """Schema for updating an integration."""

    model_id: str | None = None
    active: bool | None = None


class ProvidersListResponse(BaseModel):
    """Schema for providers list response."""

    providers: list[LLMProviderResponse]
    total: int


class ModelsListResponse(BaseModel):
    """Schema for models list response."""

    models: list[LLMModelResponse]
    total: int


class IntegrationsListResponse(BaseModel):
    """Schema for integrations list response."""

    integrations: list[IntegrationResponse]
    total: int
