from digest_service import Subscriber, recipients


def test_only_active_subscribers_receive_digest():
    subscribers = [Subscriber("a@example.com"), Subscriber("paused@example.com", active=False)]
    assert recipients(subscribers) == ["a@example.com"]
