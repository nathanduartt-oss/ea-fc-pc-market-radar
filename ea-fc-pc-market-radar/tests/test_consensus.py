from datetime import datetime, timezone
from src.consensus import build_consensus
from src.models import PriceObservation

def o(price):
    return PriceObservation(player_name="x",rating=98,card_type="special",promo="FUTTIES",definition_id="1",tradeable=True,
      platform="pc",price=price,source=str(price),source_updated_at=datetime.now(timezone.utc),price_valid=True,confidence=90,source_status="ok",freshness="fresh")

def test_agreement():
    c=build_consensus([o(88000),o(88500)])
    assert c["price_valid"] and c["confidence"] >= 95

def test_divergence_over_ten_invalidates_outlier_not_median_pair():
    observations=[o(88000),o(88500),o(40000)]
    c=build_consensus(observations)
    assert c["price_valid"] and observations[2].outlier

def test_two_sources_over_ten_conflict_invalid():
    assert not build_consensus([o(88000),o(60000)])["price_valid"]

