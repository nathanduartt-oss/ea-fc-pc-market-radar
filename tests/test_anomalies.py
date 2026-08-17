from datetime import datetime, timezone
import httpx
from src.history import trend_flags
from src.models import Card, PriceObservation
from src.providers.futnext import FutnextProvider
from src.validation import mark_historical_anomaly, mark_reference_anomaly

CARD=Card(player_name="Sadio Mane",rating=98,card_type="special",promo="FUTTIES",definition_id="100872018")

def test_historical_outlier():
    o=PriceObservation(**CARD.model_dump(),price=40000,source="x",price_valid=True,confidence=90)
    assert mark_historical_anomaly(o,[87500,88000,88500]).anomaly and not o.price_valid

def test_user_reference_only_rejects_suspicious_quote():
    card=CARD.model_copy(update={"sanity_reference_price":88000})
    o=PriceObservation(**card.model_dump(),price=40000,source="x",price_valid=True,confidence=72)
    assert not mark_reference_anomaly(o,card).price_valid

def test_false_recovery_requires_broader_negative_history():
    assert trend_flags({"change_1h":2,"change_3h":-1,"change_6h":-8})["false_recovery"]
    assert not trend_flags({"change_1h":2,"change_3h":3,"change_6h":-8})["false_recovery"]

def test_429_and_403_are_blocked():
    for status in (429,403):
        client=httpx.Client(transport=httpx.MockTransport(lambda request: httpx.Response(status)))
        assert FutnextProvider(client=client).get_price(CARD).source_status == "blocked"

def test_unavailable_source_does_not_raise():
    def fail(request): raise httpx.ConnectError("offline",request=request)
    client=httpx.Client(transport=httpx.MockTransport(fail))
    assert FutnextProvider(client=client).get_price(CARD).source_status == "unavailable"
