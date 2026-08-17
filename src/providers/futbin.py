from src.models import Card, PriceObservation
from src.providers.base import BaseProvider


class FutbinProvider(BaseProvider):
    name = "futbin"

    def get_price(self, card: Card, platform: str = "pc") -> PriceObservation:
        return self.invalid(card, "unavailable", "no public structured FC26 PC endpoint confirmed; HTML/snippets are not used")

