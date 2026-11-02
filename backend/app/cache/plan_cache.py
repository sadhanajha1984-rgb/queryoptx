"""
Plan Cache Module with LRU Eviction & Hit/Miss Tracking
"""
from collections import OrderedDict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from app.config import settings

class PlanCache:
    _instance: Optional["PlanCache"] = None

    def __init__(self, max_size: int = settings.PLAN_CACHE_MAX_SIZE):
        self.max_size = max_size
        self._cache: OrderedDict[str, Dict[str, Any]] = OrderedDict()
        self.hits: int = 0
        self.misses: int = 0

    @classmethod
    def get_instance(cls) -> "PlanCache":
        if cls._instance is None:
            cls._instance = PlanCache()
        return cls._instance

    def get(self, fingerprint: str) -> Optional[Dict[str, Any]]:
        if fingerprint in self._cache:
            self.hits += 1
            # Move to most-recently-used end
            self._cache.move_to_end(fingerprint)
            entry = self._cache[fingerprint]
            entry["hits"] += 1
            return entry
        else:
            self.misses += 1
            return None

    def put(self, fingerprint: str, sql_template: str, result_data: Dict[str, Any]):
        if fingerprint in self._cache:
            self._cache.move_to_end(fingerprint)
            self._cache[fingerprint]["result"] = result_data
        else:
            if len(self._cache) >= self.max_size:
                # Evict LRU (first item)
                self._cache.popitem(last=False)

            self._cache[fingerprint] = {
                "fingerprint": fingerprint,
                "sql_template": sql_template,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "hits": 1,
                "result": result_data
            }

    def clear(self):
        self._cache.clear()
        self.hits = 0
        self.misses = 0

    def get_status(self) -> Dict[str, Any]:
        total_requests = self.hits + self.misses
        hit_rate = (self.hits / total_requests * 100.0) if total_requests > 0 else 0.0

        entries_list = []
        for fp, entry in reversed(self._cache.items()):
            res = entry.get("result", {})
            best_algo = res.get("best_algorithm", "DP")
            algos = res.get("algorithms", {})
            best_algo_data = algos.get(best_algo, {})
            cost = best_algo_data.get("estimated_cost", 0.0)

            entries_list.append({
                "fingerprint": fp,
                "sql_template": entry.get("sql_template", ""),
                "created_at": entry.get("created_at", ""),
                "hits": entry.get("hits", 0),
                "cost": cost,
                "best_algorithm": best_algo
            })

        return {
            "total_entries": len(self._cache),
            "max_size": self.max_size,
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate_percent": round(hit_rate, 2),
            "entries": entries_list
        }
