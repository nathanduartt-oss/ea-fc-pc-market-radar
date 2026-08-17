from __future__ import annotations

from datetime import datetime, timezone
from statistics import median

from src.models import Card, PriceObservation


def freshness(age_minutes: float | None) -> str:
    if age_minutes is None:
        return "unknown"
    if age_minutes <= 15:
        return "fresh"
    if age_minutes <= 30:
        return "valid"
    if age_minutes <= 60:
        return "aging"
    return "expired"


def validate_observation(obs: PriceObservation, card: Card, now: datetime | None = None) -> PriceObservation:
    now = now or datetime.now(timezone.utc)
    reasons: list[str] = []
    if obs.platform.lower() != "pc": reasons.append("platform_not_pc")
    if obs.definition_id != card.definition_id: reasons.append("definition_id_mismatch")
    if obs.rating != card.rating or obs.promo.casefold() != card.promo.casefold(): reasons.append("card_version_mismatch")
    if "evolution" in obs.card_type.casefold() or "evolution" in obs.promo.casefold(): reasons.append("evolution_not_tradeable_quote")
    if not obs.tradeable: reasons.append("untradeable")
    if obs.price is None or obs.price <= 0: reasons.append("non_positive_price")
    if obs.source_updated_at:
        updated = obs.source_updated_at
        if updated.tzinfo is None: updated = updated.replace(tzinfo=timezone.utc)
        obs.price_age_minutes = max(0.0, (now - updated).total_seconds() / 60)
        obs.freshness = freshness(obs.price_age_minutes)
        if obs.price_age_minutes > 60: reasons.append("expired")
    else:
        obs.freshness = "unknown"
        obs.confidence = min(obs.confidence, 60)
    if reasons:
        obs.price_valid = False
        obs.reason = ",".join(reasons)
        obs.confidence = min(obs.confidence, 30)
    return obs


def mark_historical_anomaly(obs: PriceObservation, recent_prices: list[int], threshold: float = 0.10) -> PriceObservation:
    if not obs.price or len(recent_prices) < 2:
        return obs
    baseline = median(recent_prices[-12:])
    delta = abs(obs.price - baseline) / baseline if baseline else 1
    if delta > threshold:
        obs.anomaly = True
        obs.price_valid = False
        obs.reason = "historical_anomaly"
        obs.confidence = min(obs.confidence, 35)
    return obs


def mark_reference_anomaly(obs: PriceObservation, card: Card) -> PriceObservation:
    """Use a user-supplied sanity hint only to reject, never to manufacture a quote."""
    if not obs.price or not card.sanity_reference_price:
        return obs
    delta = abs(obs.price - card.sanity_reference_price) / card.sanity_reference_price * 100
    if delta > card.sanity_tolerance_percent:
        obs.anomaly = True
        obs.price_valid = False
        obs.reason = "sanity_reference_anomaly_requires_independent_confirmation"
        obs.confidence = min(obs.confidence, 35)
    return obs
