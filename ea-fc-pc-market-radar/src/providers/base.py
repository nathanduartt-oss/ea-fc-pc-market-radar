from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any

import httpx

from src.models import Card, PriceObservation


class ProviderError(Exception):
    def __init__(self, status: str, detail: str):
        super().__init__(detail)
        self.status = status
        self.detail = detail


class BaseProvider(ABC):
    name = "base"
    structured = False

    def __init__(self, timeout: float = 12.0, client: httpx.Client | None = None):
        self.client = client or httpx.Client(
            timeout=timeout,
            follow_redirects=True,
            headers={"User-Agent": "ea-fc-pc-market-radar/0.1 (+public price research)"},
        )

    @abstractmethod
    def get_price(self, card: Card, platform: str = "pc") -> PriceObservation:
        raise NotImplementedError

    def invalid(self, card: Card, status: str, reason: str) -> PriceObservation:
        return PriceObservation(**card.model_dump(), source=self.name, source_status=status, reason=reason)

    def request_json(self, url: str, *, params: dict[str, Any]) -> Any:
        try:
            response = self.client.get(url, params=params)
        except httpx.TimeoutException as exc:
            raise ProviderError("timeout", str(exc)) from exc
        except httpx.HTTPError as exc:
            raise ProviderError("unavailable", str(exc)) from exc
        if response.status_code in (403, 429):
            raise ProviderError("blocked", str(response.status_code))
        if response.status_code >= 400:
            raise ProviderError(str(response.status_code), f"HTTP {response.status_code}")
        try:
            return response.json()
        except ValueError as exc:
            raise ProviderError("invalid_response", "response is not JSON") from exc

    @staticmethod
    def parse_time(value: Any) -> datetime | None:
        if value is None:
            return None
        if isinstance(value, (int, float)):
            if value > 10_000_000_000:
                value /= 1000
            return datetime.fromtimestamp(value, tz=timezone.utc)
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)
            except ValueError:
                return None
        return None

