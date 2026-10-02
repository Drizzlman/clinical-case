"""Toolchain smoke test: proves pytest is wired for the backend project."""


def test_smoke() -> None:
    assert 1 + 1 == 2
