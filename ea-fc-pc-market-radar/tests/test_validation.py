from datetime import datetime, timedelta, timezone

from src.models import Card, PriceObservation
from src.validation import validate_observation

NOW=datetime(2026,8,17,12,0,tzinfo=timezone.utc)
CARD=Card(player_name="Test",rating=98,card_type="special",promo="FUTTIES",definition_id="123",tradeable=True)

def obs(**kw):
    base=dict(**CARD.model_dump(),price=88000,source="test",source_updated_at=NOW,price_valid=True,confidence=90,source_status="ok")
    base.update(kw); return PriceObservation(**base)

def test_wrong_platform(): assert not validate_observation(obs(platform="ps"),CARD,NOW).price_valid
def test_expired(): assert not validate_observation(obs(source_updated_at=NOW-timedelta(minutes=61)),CARD,NOW).price_valid
def test_zero(): assert not validate_observation(obs(price=0),CARD,NOW).price_valid
def test_wrong_id(): assert not validate_observation(obs(definition_id="999"),CARD,NOW).price_valid
def test_evolution(): assert not validate_observation(obs(card_type="Evolution"),CARD,NOW).price_valid

