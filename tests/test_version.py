from bot.version import __version__


def test_version_format():
    assert __version__
    parts = __version__.split(".")
    assert len(parts) == 3
