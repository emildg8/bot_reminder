from bot.config import _merge_admin_ids, _parse_admin_ids, BUILTIN_ADMIN_TELEGRAM_IDS


def test_admin_ids_single_int():
    assert _parse_admin_ids(250891839) == [250891839]


def test_admin_ids_csv_string():
    assert _parse_admin_ids("1, 2, 3") == [1, 2, 3]


def test_admin_ids_empty():
    assert _parse_admin_ids("") == []
    assert _parse_admin_ids(None) == []


def test_builtin_admin_always_merged():
    assert 292396648 in BUILTIN_ADMIN_TELEGRAM_IDS
    assert _merge_admin_ids([]) == [292396648]
    assert _merge_admin_ids([111]) == [292396648, 111]
    assert _merge_admin_ids([292396648, 111]) == [292396648, 111]
