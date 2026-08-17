from __future__ import annotations

from src.models import Card, PriceObservation
from src.providers.base import BaseProvider, ProviderError


class FutGGProvider(BaseProvider):
    name = "futgg"
    structured = True
    url = "https://www.fut.gg/api/fut/player-prices/26/"

    def get_price(self, card: Card, platform: str = "pc") -> PriceObservation:
        if platform.lower() != "pc":
            return self.invalid(card, "invalid_platform", "only PC is allowed")
        try:
            payload = self.request_json(self.url, params={"ids": card.definition_id, "platform": "pc"})
        except ProviderError as exc:
            return self.invalid(card, exc.status, exc.detail)
        rows = payload.get("data", payload) if isinstance(payload, dict) else payload
        if isinstance(rows, dict) and card.definition_id in rows:
            row = rows[card.definition_id]
        elif isinstance(rows, list):
            row = next((x for x in rows if str(x.get("definitionId") or x.get("id")) == card.definition_id), None)
        else:
            row = None
        if not isinstance(row, dict):
            return self.invalid(card, "not_found", "exact definition_id absent")
        returned_id = str(row.get("definitionId") or row.get("definition_id") or row.get("id") or card.definition_id)
        pc = row.get("pc") or row.get("pcPrice") or row.get("pc_price")
        if isinstance(pc, dict):
            updated = self.parse_time(pc.get("updatedAt") or pc.get("updated_at"))
            pc = pc.get("price") or pc.get("value")
        else:
            updated = self.parse_time(row.get("updatedAt") or row.get("updated_at"))
        if returned_id != card.definition_id or not pc:
            return self.invalid(card, "unverified_identity", "exact card/PC price not proven")
        return PriceObservation(**card.model_dump(), price=int(pc), source=self.name, source_updated_at=updated,
            source_status="ok", price_valid=True, confidence=78)

