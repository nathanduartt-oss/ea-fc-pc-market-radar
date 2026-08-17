from __future__ import annotations

from typing import Any

from src.models import Card, PriceObservation
from src.providers.base import BaseProvider, ProviderError


class FutnextProvider(BaseProvider):
    name = "futnext"
    structured = True
    url = "https://enhancer-api.futnext.com/players/prices"

    def get_price(self, card: Card, platform: str = "pc") -> PriceObservation:
        if platform.lower() != "pc":
            return self.invalid(card, "invalid_platform", "only PC is allowed")
        try:
            payload = self.request_json(self.url, params={"ids": card.definition_id, "platform": "pc"})
            row = self._find(payload, card.definition_id)
            if row is None:
                return self.invalid(card, "not_found", "definition_id absent from response")
            response_platform = str(row.get("platform") or "pc").lower()
            if response_platform != "pc":
                return self.invalid(card, "unverified_platform", "response conflicts with requested PC market")
            returned_id = str(row.get("definitionId") or row.get("definition_id") or row.get("id") or "")
            if returned_id != card.definition_id:
                return self.invalid(card, "identity_mismatch", "returned card ID differs")
            price = row.get("price") or row.get("lowestPrice") or row.get("lowest_price")
            if not price and isinstance(row.get("prices"), list) and row["prices"]:
                price = row["prices"][0]
            updated = self.parse_time(row.get("updatedAt") or row.get("updated_at") or row.get("timestamp"))
            return PriceObservation(**card.model_dump(), price=int(price) if price else None, source=self.name,
                source_updated_at=updated, source_status="ok", price_valid=bool(price), confidence=72,
                raw_meta={"requested_platform":"pc","platform_confirmation":"request_parameter"})
        except ProviderError as exc:
            return self.invalid(card, exc.status, exc.detail)
        except (TypeError, ValueError) as exc:
            return self.invalid(card, "invalid_response", str(exc))

    @staticmethod
    def _find(payload: Any, definition_id: str) -> dict[str, Any] | None:
        candidates = payload.get("data", payload.get("players", payload)) if isinstance(payload, dict) else payload
        if isinstance(candidates, dict):
            direct = candidates.get(definition_id)
            if isinstance(direct, dict):
                direct.setdefault("definitionId", definition_id)
                return direct
            candidates = list(candidates.values())
        if isinstance(candidates, list):
            for row in candidates:
                if isinstance(row, dict) and str(row.get("definitionId") or row.get("definition_id") or row.get("id")) == definition_id:
                    return row
        return None
