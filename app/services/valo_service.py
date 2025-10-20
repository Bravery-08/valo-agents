import logging
import threading
import time
from typing import Dict, List, Tuple

from bs4 import BeautifulSoup
from curl_cffi import requests

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class ValoService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self._lock = threading.RLock()
        # cache: timestamp, value
        self._maps_cache: Tuple[float, List[str]] | None = None
        self._agents_cache: Dict[str, Tuple[float, Dict[int | str, str | float]]] = {}

    def _request_with_retries(self, url: str, impersonate: str | None = None) -> str:
        retries = max(0, self.settings.http_max_retries)
        last_exc: Exception | None = None
        for attempt in range(retries + 1):
            try:
                if impersonate:
                    response = requests.get(url, impersonate=impersonate, timeout=self.settings.http_timeout_seconds)
                else:
                    response = requests.get(url, timeout=self.settings.http_timeout_seconds)
                response.raise_for_status()
                return response.text
            except Exception as exc:  # noqa: BLE001
                last_exc = exc
                logger.warning("HTTP GET failed (attempt %s/%s) for %s: %s", attempt + 1, retries + 1, url, exc)
                if attempt < retries:
                    time.sleep(0.5 * (attempt + 1))
        assert last_exc is not None
        raise last_exc

    def get_map_pool(self) -> List[str]:
        with self._lock:
            now = time.time()
            if self._maps_cache:
                ts, val = self._maps_cache
                if now - ts < self.settings.map_pool_ttl_seconds:
                    return list(val)

        html_text = self._request_with_retries(self.settings.map_pool_url)
        soup = BeautifulSoup(html_text, "html.parser")
        all_a = soup.find_all("a")

        # Fallback: search for elements that look like map names if structure changes
        map_pool: List[str] = []
        start_index = 14
        for index in range(start_index, start_index + 7):
            if index < len(all_a):
                text = all_a[index].get_text().strip()
                if text:
                    map_pool.append(text.split()[0])

        # Deduplicate and keep order
        unique_maps: List[str] = []
        for m in map_pool:
            if m not in unique_maps:
                unique_maps.append(m)
        with self._lock:
            self._maps_cache = (time.time(), unique_maps)
        return list(unique_maps)

    def get_agents_for_map(self, map_name: str) -> Dict[str, str | float | int]:
        normalized = (map_name or "").strip()
        if not normalized:
            raise ValueError("map_name must be provided")
        normalized = normalized.lower()

        with self._lock:
            now = time.time()
            cached = self._agents_cache.get(normalized)
            if cached:
                ts, val = cached
                if now - ts < self.settings.agents_ttl_seconds:
                    return dict(val)

        url = self.settings.agents_api_url.format(map=normalized)
        json_text = self._request_with_retries(url, impersonate="chrome110")
        # curl_cffi returns .text; we can re-fetch as JSON by calling again, or parse via requests.json()
        # Safer to use requests.get(...).json(), but our retry helper returns text. Call API once more to get JSON.
        result = requests.get(url, impersonate="chrome110", timeout=self.settings.http_timeout_seconds).json()

        insights = result.get("data", {}).get("insights", [])
        agents: Dict[str, Dict[str, float | str]] = {
            item["metadata"]["name"]: {
                "role": item["metadata"].get("className", ""),
                "winrate": float(item["stats"]["wlPercentage"].get("value", 0) or 0),
                "played": float(item["stats"].get("playedPct", {}).get("value", 0) or 0),
            }
            for item in insights
            if isinstance(item, dict)
        }

        sorted_agents = sorted(
            agents.items(), key=lambda kv: (kv[1]["winrate"], kv[1]["played"]), reverse=True
        )

        target_roles = {"Duelist", "Initiator", "Controller", "Sentinel"}
        best_agents: Dict[int | str, str | float] = {"Map": normalized}
        extra_candidate_added = False
        index_counter = 1

        for name, stats in sorted_agents:
            if stats["played"] < 1:
                continue
            if stats["role"] in target_roles:
                best_agents[index_counter] = name
                index_counter += 1
                target_roles.remove(stats["role"])
            elif not extra_candidate_added:
                best_agents[index_counter] = name
                index_counter += 1
                extra_candidate_added = True

            if not target_roles and extra_candidate_added:
                break

        with self._lock:
            # enforce maxsize; drop oldest
            if len(self._agents_cache) >= max(1, self.settings.agents_cache_maxsize):
                oldest_key = min(self._agents_cache.items(), key=lambda kv: kv[1][0])[0]
                self._agents_cache.pop(oldest_key, None)
            self._agents_cache[normalized] = (time.time(), dict(best_agents))

        return dict(best_agents)