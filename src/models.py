from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field


class Card(BaseModel):
    player_name: str
    rating: int
    card_type: str
    promo: str
    position: str | None = None
    definition_id: str
    resource_id: str | None = None
    source_id: str | None = None
    tradeable: bool = True
    platform: Literal["pc"] = "pc"
    sanity_reference_price: int | None = None
    sanity_tolerance_percent: float = 20.0


class PriceObservation(BaseModel):
    player_name: str
    rating: int
    card_type: str
    promo: str
    position: str | None = None
    definition_id: str
    resource_id: str | None = None
    source_id: str | None = None
    tradeable: bool
    platform: str
    price: int | None = None
    source: str
    source_updated_at: datetime | None = None
    collected_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    price_valid: bool = False
    confidence: int = 0
    source_status: str = "unknown"
    reason: str | None = None
    raw_meta: dict[str, Any] = Field(default_factory=dict, exclude=True)
    price_age_minutes: float | None = None
    freshness: str = "unknown"
    outlier: bool = False
    anomaly: bool = False


class ProviderStatus(BaseModel):
    status: str
    detail: str | None = None
