from __future__ import annotations

from statistics import median

from src.models import PriceObservation


def disagreement_percent(observations: list[PriceObservation]) -> float | None:
    prices = [o.price for o in observations if o.price_valid and o.price]
    if len(prices) < 2:
        return None
    center = median(prices)
    return round((max(prices) - min(prices)) / center * 100, 2)


def build_consensus(observations: list[PriceObservation]) -> dict:
    valid = [o for o in observations if o.price_valid and o.price and o.platform == "pc"]
    disagreement = disagreement_percent(valid)
    if not valid:
        return {"price": None, "price_valid": False, "confidence": 0, "disagreement": disagreement}
    center = int(median([o.price for o in valid]))
    for obs in valid:
        if abs(obs.price - center) / center > 0.10:
            obs.outlier = True
            obs.price_valid = False
    valid = [o for o in valid if o.price_valid]
    disagreement = disagreement_percent(valid)
    if not valid or (disagreement is not None and disagreement > 10):
        return {"price": None, "price_valid": False, "confidence": 25, "disagreement": disagreement}
    center = int(median([o.price for o in valid]))
    if len(valid) == 1:
        quality = min(69, valid[0].confidence)
    elif disagreement is not None and disagreement <= 5:
        quality = 96 if all(o.freshness == "fresh" for o in valid) else 90
    elif disagreement is not None and disagreement <= 8:
        quality = 85
    else:
        quality = 65
    if any(o.freshness == "unknown" for o in valid): quality = min(quality, 69)
    return {"price": center, "price_valid": True, "confidence": quality, "disagreement": disagreement}

