from squirrel_app import WELCOME_BLOCK, ensure_squirrel_md
from pathlib import Path

def test_welcome_block_has_commands():
    assert "@squirrel:" in WELCOME_BLOCK
    assert "mode" in WELCOME_BLOCK.lower()

def test_ensure_squirrel_md_creates_file(tmp_path):
    md = tmp_path / "Squirrel.md"
    ensure_squirrel_md(md)
    assert md.exists()
    assert "@squirrel:" in md.read_text()

def test_ensure_squirrel_md_idempotent(tmp_path):
    md = tmp_path / "Squirrel.md"
    ensure_squirrel_md(md)
    original = md.read_text()
    ensure_squirrel_md(md)
    assert md.read_text() == original
