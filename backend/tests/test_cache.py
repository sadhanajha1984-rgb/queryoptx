"""
Unit tests for Plan Cache and Query Normalizer
"""
from app.cache.normalizer import QueryNormalizer
from app.cache.plan_cache import PlanCache

def test_query_normalization():
    q1 = "SELECT * FROM students WHERE student_id = 10 AND department = 'CS';"
    q2 = "SELECT * FROM students WHERE student_id = 500 AND department = 'MATH';"

    t1, fp1 = QueryNormalizer.normalize_and_fingerprint(q1)
    t2, fp2 = QueryNormalizer.normalize_and_fingerprint(q2)

    assert fp1 == fp2
    assert "?" in t1

def test_plan_cache_lru():
    cache = PlanCache(max_size=2)
    cache.clear()

    cache.put("fp1", "SELECT ? FROM t1", {"plan": "p1"})
    cache.put("fp2", "SELECT ? FROM t2", {"plan": "p2"})

    assert cache.get("fp1") is not None
    assert cache.hits == 1

    # Adding 3rd should evict fp2 since fp1 was just accessed
    cache.put("fp3", "SELECT ? FROM t3", {"plan": "p3"})
    assert cache.get("fp2") is None
    assert cache.misses == 1
    assert cache.get("fp1") is not None
