from __future__ import annotations

import csv
from datetime import datetime, timedelta, timezone
from pathlib import Path

from src.models import PriceObservation

FIELDS = ["timestamp","definition_id","player_name","rating","promo","platform","price","source","confidence","price_valid"]


def read_history(path: Path) -> list[dict]:
    if not path.exists(): return []
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def append_history(path: Path, observations: list[PriceObservation]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    exists = path.exists() and path.stat().st_size > 0
    with path.open("a", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDS, lineterminator="\n")
        if not exists: writer.writeheader()
        for o in observations:
            if not o.price_valid: continue
            writer.writerow({"timestamp":o.collected_at.isoformat(),"definition_id":o.definition_id,"player_name":o.player_name,
                "rating":o.rating,"promo":o.promo,"platform":o.platform,"price":o.price,"source":o.source,
                "confidence":o.confidence,"price_valid":str(o.price_valid).lower()})


def recent_prices(rows: list[dict], card_id: str, hours: int = 24) -> list[int]:
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    result=[]
    for row in rows:
        if row.get("definition_id") != card_id or row.get("platform") != "pc": continue
        try:
            if datetime.fromisoformat(row["timestamp"].replace("Z", "+00:00")) >= cutoff: result.append(int(row["price"]))
        except (ValueError, TypeError): pass
    return result


def time_series(rows: list[dict], card_id: str, current: int | None, now: datetime) -> dict:
    samples=[]
    for row in rows:
        if row.get("definition_id") != card_id or row.get("platform") != "pc": continue
        try: samples.append((datetime.fromisoformat(row["timestamp"].replace("Z", "+00:00")), int(row["price"])))
        except (ValueError, TypeError): pass
    samples.sort()
    output={}
    for hours in (1,2,3,6,12,24):
        target=now-timedelta(hours=hours)
        eligible=[x for x in samples if x[0] <= target]
        old=eligible[-1][1] if eligible else None
        output[f"price_{hours}h_ago"]=old
        if hours in (1,3,6,12,24): output[f"change_{hours}h"]=round((current-old)/old*100,2) if current and old else None
    return output


def trend_flags(series: dict) -> dict:
    c1,c3,c6=series.get("change_1h"),series.get("change_3h"),series.get("change_6h")
    prices=[v for k,v in series.items() if k.startswith("price_") and v is not None]
    new_low=bool(prices and series.get("price_1h_ago") is not None and series["price_1h_ago"] <= min(prices))
    recovering=bool(c1 is not None and c3 is not None and c1 > 0 and c3 > 0)
    stabilizing=bool(c1 is not None and c3 is not None and abs(c1) <= 1.5 and abs(c3) <= 3)
    false_recovery=bool(c1 is not None and c3 is not None and c6 is not None and c1 > 0 and c3 <= 0 and c6 < 0)
    trend="false_recovery" if false_recovery else "recovering" if recovering else "stabilizing" if stabilizing else "falling" if c3 is not None and c3 < 0 else "unknown"
    return {"new_low":new_low,"stabilizing":stabilizing,"recovering":recovering,"false_recovery":false_recovery,"trend":trend}
