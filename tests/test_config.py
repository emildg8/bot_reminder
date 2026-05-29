from bot.config import _parse_admin_ids


def test_admin_ids_single_int():
    assert _parse_admin_ids(250891839) == [250891839]


def test_admin_ids_csv_string():
    assert _parse_admin_ids("1, 2, 3") == [1, 2, 3]


def test_admin_ids_empty():
    assert _parse_admin_ids("") == []
    assert _parse_admin_ids(None) == []
