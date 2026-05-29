from bot.services.reminders_ui import LIST_PAGE_SIZE, _paginate


def test_paginate_single_page():
    items = list(range(5))
    page_items, page, total = _paginate(items, 0)
    assert len(page_items) == 5
    assert total == 1


def test_paginate_second_page():
    items = list(range(LIST_PAGE_SIZE + 3))
    page_items, page, total = _paginate(items, 1)
    assert page == 1
    assert total == 2
    assert len(page_items) == 3
