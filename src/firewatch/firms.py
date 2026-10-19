"""NASA FIRMS area CSV client."""

from datetime import date
from pathlib import Path

import httpx

INDONESIA_AREA = "94.0,-11.5,142.5,6.5"
BASE_URL = "https://firms.modaps.eosdis.nasa.gov/api/area/csv"


class FirmsClient:
    """Fetch and privately preserve FIRMS CSV responses."""

    def __init__(
        self,
        map_key: str,
        raw_dir: Path,
        *,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        if not map_key.strip():
            raise ValueError("FIRMS_MAP_KEY is required")
        self._map_key = map_key
        self._raw_dir = Path(raw_dir)
        self._transport = transport

    def fetch(self, sensor: str, days: int, *, today: str | None = None) -> bytes:
        if not 1 <= days <= 5:
            raise ValueError("days must be between 1 and 5")
        url = f"{BASE_URL}/{self._map_key}/{sensor}/{INDONESIA_AREA}/{days}"
        try:
            with httpx.Client(timeout=30, follow_redirects=True, transport=self._transport) as client:
                response = client.get(url)
                response.raise_for_status()
        except httpx.HTTPError as error:
            raise RuntimeError(f"NASA FIRMS request failed: {error.__class__.__name__}") from error
        if not response.content.strip():
            raise RuntimeError("NASA FIRMS returned an empty response")
        stamp = today or date.today().isoformat()
        self._raw_dir.mkdir(parents=True, exist_ok=True)
        (self._raw_dir / f"firms-{stamp}-{sensor}.csv").write_bytes(response.content)
        return response.content
