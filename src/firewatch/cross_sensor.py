"""Link overlapping satellite detections across different sensors."""

import dataclasses
from collections import defaultdict
from hashlib import sha256
from typing import Sequence

from .geography import haversine_km
from .models import Hotspot

CROSS_SENSOR_METHOD = "cross_sensor_500m_30m_v1"


def link_cross_sensor_observations(
    observations: Sequence[Hotspot],
    distance_m: float = 500.0,
    window_minutes: float = 30.0,
) -> list[Hotspot]:
    """Link overlapping observations from different sensors into dedupe groups."""
    n = len(observations)
    if n <= 1:
        return [
            dataclasses.replace(item, dedupe_group_id=item.id) if item.dedupe_group_id is None else item
            for item in observations
        ]

    adj: dict[int, list[int]] = defaultdict(list)
    max_seconds = window_minutes * 60.0

    for i in range(n):
        h1 = observations[i]
        t1 = h1.observed_at_utc
        for j in range(i + 1, n):
            h2 = observations[j]
            if h1.sensor == h2.sensor:
                continue
            t2 = h2.observed_at_utc
            if abs((t1 - t2).total_seconds()) > max_seconds:
                continue
            dist_m = haversine_km(h1.latitude, h1.longitude, h2.latitude, h2.longitude) * 1000.0
            if dist_m <= distance_m:
                adj[i].append(j)
                adj[j].append(i)

    visited: set[int] = set()
    components: list[list[int]] = []

    for i in range(n):
        if i not in visited:
            component = []
            queue = [i]
            visited.add(i)
            while queue:
                curr = queue.pop(0)
                component.append(curr)
                for neighbor in adj[curr]:
                    if neighbor not in visited:
                        visited.add(neighbor)
                        queue.append(neighbor)
            components.append(component)

    result_map: dict[str, Hotspot] = {}
    for comp in components:
        if len(comp) > 1:
            member_ids = sorted(observations[idx].id for idx in comp)
            group_id = f"grp_{sha256('|'.join(member_ids).encode()).hexdigest()[:20]}"
            for idx in comp:
                orig = observations[idx]
                result_map[orig.id] = dataclasses.replace(orig, dedupe_group_id=group_id)
        else:
            idx = comp[0]
            orig = observations[idx]
            group_id = orig.id
            result_map[orig.id] = dataclasses.replace(orig, dedupe_group_id=group_id)

    return [result_map[item.id] for item in observations]
