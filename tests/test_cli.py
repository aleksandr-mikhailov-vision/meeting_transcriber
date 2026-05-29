from pathlib import Path

from meeting_transcribator.cli import _disambiguate, discover, output_path_for


def test_output_path_mirrors_recordings_relative(tmp_path):
    rec = tmp_path / "recordings"
    out = tmp_path / "outputs"
    src = rec / "team" / "standup.m4a"
    src.parent.mkdir(parents=True)
    src.write_bytes(b"x")
    assert output_path_for(src, rec, out) == out / "team" / "standup.md"


def test_output_path_for_external_file_uses_name(tmp_path):
    rec = tmp_path / "recordings"
    out = tmp_path / "outputs"
    rec.mkdir()
    src = tmp_path / "elsewhere" / "call.m4a"
    src.parent.mkdir(parents=True)
    src.write_bytes(b"x")
    assert output_path_for(src, rec, out) == out / "call.md"


def _touch(p: Path) -> Path:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(b"x")
    return p


def test_discover_skips_existing_transcripts(tmp_path):
    rec = tmp_path / "recordings"
    out = tmp_path / "outputs"
    a = _touch(rec / "a.m4a")
    _touch(rec / "b.m4a")
    _touch(rec / "notes.txt")  # non-audio, ignored
    _touch(out / "a.md")  # a already transcribed

    pending = discover(rec, out, overwrite=False)
    assert pending == [rec / "b.m4a"]

    all_targets = discover(rec, out, overwrite=True)
    assert all_targets == [rec / "a.m4a", rec / "b.m4a"]
    assert a in all_targets


def test_disambiguate_avoids_in_run_collisions(tmp_path):
    used: set = set()
    d = tmp_path / "call.md"
    first = _disambiguate(d, used)
    used.add(first)
    second = _disambiguate(d, used)
    used.add(second)
    third = _disambiguate(d, used)
    assert first == tmp_path / "call.md"
    assert second == tmp_path / "call-2.md"
    assert third == tmp_path / "call-3.md"
