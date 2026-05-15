from pathlib import Path

from s2_mod_manager.utils.hashing import clear_hash_cache, hash_file


def test_hash_file_cache_reuses_unchanged_file(tmp_path: Path, monkeypatch) -> None:
    clear_hash_cache()
    source = tmp_path / "mod.pak"
    source.write_bytes(b"abc")
    first = hash_file(source, chunk_size=2)

    def fail_open(*_args, **_kwargs):
        raise AssertionError("cached hash should not reopen unchanged file")

    monkeypatch.setattr(Path, "open", fail_open)
    assert hash_file(source, chunk_size=2) == first


def test_hash_file_cache_invalidates_when_file_changes(tmp_path: Path) -> None:
    clear_hash_cache()
    source = tmp_path / "mod.pak"
    source.write_bytes(b"abc")
    first = hash_file(source, chunk_size=2)
    source.write_bytes(b"abcd")

    assert hash_file(source, chunk_size=2) != first
