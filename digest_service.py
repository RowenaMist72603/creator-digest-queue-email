from dataclasses import dataclass
from typing import Iterable

from infrai_client import Infrai

# Canonical usage: Infrai().cron.create


@dataclass(frozen=True)
class Subscriber:
    email: str
    active: bool = True


@dataclass(frozen=True)
class Digest:
    title: str
    body: str


def recipients(subscribers: Iterable[Subscriber]) -> list[str]:
    return [s.email for s in subscribers if s.active]


def publish_digest(digest: Digest, subscribers: Iterable[Subscriber]) -> dict:
    to = recipients(subscribers)
    if not to:
        return {"sent": 0, "reason": "no active subscribers"}
    return Infrai().email.batch_send(to, digest.title, digest.body)


def run(queue_name: str = "creator-digest") -> None:
    api = Infrai()
    api.queue.create(queue_name)
    job = api.cron.create("0 9 * * 1", "https://example.com/digest/dispatch")
    print("scheduled", job.get("job_id"))
    api.queue.publish(queue_name, {"title": "Creator digest", "body": "New releases this week"})
    messages = api.queue.consume(queue_name, max_messages=10, visibility_timeout=60).get("messages", [])
    for message in messages:
        payload = message.get("payload") or {}
        api.email.batch_send(payload.get("to", []), payload.get("title", "Creator digest"), payload.get("body", ""))
        api.queue.ack(queue_name, message["message_id"])


if __name__ == "__main__":
    run()
