from bot.services.drafts import prune_expired


def test_prune_expired_empty():
    assert prune_expired() == 0
