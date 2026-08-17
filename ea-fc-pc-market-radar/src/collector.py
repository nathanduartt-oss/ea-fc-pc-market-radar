from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from pydantic import TypeAdapter

from src.consensus import build_consensus
from src.history import append_history, read_history, recent_prices, time_series, trend_flags
from src.models import Card
from src.providers import FutbinProvider, FutGGProvider, FutnextProvider, FutwizProvider
from src.validation import mark_historical_anomaly, mark_reference_anomaly, validate_observation

ROOT = Path(__file__).resolve().parents[1]


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")
    temp.replace(path)


def collect(root: Path = ROOT) -> list[dict]:
    now = datetime.now(timezone.utc)
    cards = TypeAdapter(list[Card]).validate_json((root / "config/watchlist.json").read_text(encoding="utf-8"))
    history_path = root / "data/history.csv"
    old_rows = read_history(history_path)
    providers = [FutnextProvider(), FutGGProvider(), FutbinProvider(), FutwizProvider()]
    latest=[]; radar=[]; statuses={p.name:"not_run" for p in providers}; valid_to_append=[]
    for card in cards:
        observations=[]
        baseline = recent_prices(old_rows, card.definition_id)
        for provider in providers:
            obs = provider.get_price(card, platform="pc")
            obs = validate_observation(obs, card, now)
            obs = mark_historical_anomaly(obs, baseline)
            obs = mark_reference_anomaly(obs, card)
            observations.append(obs)
            if obs.source_status == "ok": statuses[provider.name] = "ok"
            elif statuses[provider.name] != "ok": statuses[provider.name] = obs.source_status
        consensus=build_consensus(observations)
        valid_to_append.extend(o for o in observations if o.price_valid)
        latest.append({"card":card.model_dump(),"observations":[o.model_dump(exclude={"raw_meta"}, mode="json") for o in observations],"consensus":consensus})
        series=time_series(old_rows, card.definition_id, consensus["price"], now)
        flags=trend_flags(series)
        source_times=[o.source_updated_at for o in observations if o.price_valid and o.source_updated_at]
        updated=max(source_times).isoformat() if source_times else None
        ages=[o.price_age_minutes for o in observations if o.price_valid and o.price_age_minutes is not None]
        radar.append({"name":card.player_name,"rating":card.rating,"promo":card.promo,"id":card.definition_id,
            "pc_price":consensus["price"],"updated_at":updated,"age_minutes":round(min(ages),2) if ages else None,
            "price_valid":consensus["price_valid"],"quote_quality":consensus["confidence"],**series,**flags,
            "sources":{o.source:o.price if o.price_valid else None for o in observations},
            "source_disagreement_percent":consensus["disagreement"],
            "anomaly":any(o.anomaly for o in observations)})
    append_history(history_path, valid_to_append)
    run_stamp=now.strftime("%Y%m%dT%H%M%SZ")
    write_json(root / "data/latest.json", {"collected_at":now.isoformat(),"platform":"pc","cards":latest})
    write_json(root / f"data/history/{run_stamp}.json", {"collected_at":now.isoformat(),"platform":"pc","observations":[o.model_dump(mode="json") for o in valid_to_append]})
    write_json(root / "data/radar.json", {"generated_at":now.isoformat(),"platform":"pc","cards":radar})
    write_json(root / "data/status.json", {"collected_at":now.isoformat(),**statuses})
    return radar


if __name__ == "__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    args=parser.parse_args()
    result=collect(args.root)
    print(json.dumps(result, ensure_ascii=False, indent=2))
