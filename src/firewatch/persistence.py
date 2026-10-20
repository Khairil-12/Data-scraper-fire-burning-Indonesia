"""Cluster repeated nearby fire detections into persistence episodes."""

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from hashlib import sha256
from typing import Sequence

from .geography import haversine_km
from .models import Hotspot


@dataclass(frozen=True, slots=True)
class PersistenceEpisode:
    episode_id: str
    latitude: float
    longitude: float
    province: str | None
    detection_count: int
    first_detected_at_utc: datetime
    last_detected_at_utc: datetime
    active_duration_hours: float
    max_frp_mw: float | None
    member_ids: tuple[str, ...]


def build_persistence_episodes(
    observations: Sequence[Hotspot],
    distance_km: float = 1.0,
) -> list[PersistenceEpisode]:
    """Group observations within distance_km into persistence episodes."""
    n = len(observations)
    if not n:
        return []

    adj: dict[int, list[int]] = defaultdict(list)
    for i in range(n):
        h1 = observations[i]
        for j in range(i + 1, n):
            h2 = observations[j]
            dist = haversine_km(h1.latitude, h1.longitude, h2.latitude, h2.longitude)
            if dist <= distance_km:
                adj[i].append(j)
                adj[j].append(i)

    visited: set[int] = set()
    episodes: list[PersistenceEpisode] = []

    for i in range(n):
        if i not in visited:
            cluster_indices = []
            queue = [i]
            visited.add(i)
            while queue:
                curr = queue.pop(0)
                cluster_indices.append(curr)
                for neighbor in adj[curr]:
                    if neighbor not in visited:
                        visited.add(neighbor)
                        queue.append(neighbor)

            cluster = [observations[idx] for idx in cluster_indices]
            first_time = min(item.observed_at_utc for item in cluster)
            last_time = max(item.observed_at_utc for item in cluster)
            duration_hours = (last_time - first_time).total_seconds() / 3600.0
            avg_lat = sum(item.latitude for item in cluster) / len(cluster)
            avg_lon = sum(item.longitude for item in cluster) / len(cluster)
            max_frp = max((item.frp_mw for item in cluster if item.frp_mw is not None), default=None)
            member_ids = tuple(sorted(item.id for item in cluster))
            ep_id = f"ep_{sha256('|'.join(member_ids).encode()).hexdigest()[:20]}"
            province = cluster[0].province if any(item.province for item in cluster) else None

            episodes.append(
                PersistenceEpisode(
                    episode_id=ep_id,
                    latitude=round(avg_lat, 4),
                    longitude=round(avg_lon, 4),
                    province=province,
                    detection_count=len(cluster),
                    first_detected_at_utc=first_time,
                    last_detected_at_utc=last_time,
                    active_duration_hours=round(duration_hours, 2),
                    max_frp_mw=max_frp,
                    member_ids=member_ids,
                )
            )

    return episodes
