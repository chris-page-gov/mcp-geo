from server.dataset_cache import DatasetCache


def test_dataset_cache_read_write(tmp_path):
    cache = DatasetCache(tmp_path)
    assert cache.read("missing") is None
    cache.write("ons:dimensions", {"dimensions": ["time"], "source_url": "https://example"})
    stored = cache.read("ons:dimensions")
    assert stored is not None
    assert stored["dimensions"] == ["time"]
    assert "cached_at" in stored
