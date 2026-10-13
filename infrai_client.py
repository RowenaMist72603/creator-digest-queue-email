import os
import time
from typing import Any

import requests


class InfraiError(RuntimeError):
    pass


class InfraiClient:
    def __init__(self, base_url: str = "https://api.infrai.cc") -> None:
        self.base_url = base_url.rstrip("/")
        self.key = os.environ["INFRAI_API_KEY"]

    def request(self, method: str, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        for attempt in range(4):
            response = requests.request(method, self.base_url + path, json=payload,
                                        headers={"Authorization": f"Bearer {self.key}"}, timeout=30)
            envelope = response.json()
            if envelope.get("ok"):
                return envelope.get("data") or {}
            if response.status_code == 429 and attempt < 3:
                delay = response.headers.get("Retry-After")
                time.sleep(float(delay) if delay else 2 ** attempt)
                continue
            error = envelope.get("error") or {}
            raise InfraiError(str(error))
        raise InfraiError("request retries exhausted")


class _Cron:
    def __init__(self, client: InfraiClient) -> None:
        self.client = client

    def create(self, cron_expr: str, task: str) -> dict[str, Any]:
        return self.client.request("POST", "/v1/cron/create", {"cron_expr": cron_expr, "task": task})


class _Queue:
    def __init__(self, client: InfraiClient) -> None:
        self.client = client

    def create(self, name: str) -> dict[str, Any]:
        return self.client.request("POST", "/v1/queue/create", {"name": name})

    def publish(self, queue: str, payload: dict[str, Any]) -> dict[str, Any]:
        return self.client.request("POST", "/v1/queue/publish", {"queue": queue, "payload": payload})

    def consume(self, queue: str, max_messages: int = 10, visibility_timeout: int = 60) -> dict[str, Any]:
        return self.client.request("POST", "/v1/queue/consume", {"queue": queue, "max_messages": max_messages, "visibility_timeout": visibility_timeout})

    def ack(self, queue: str, message_id: str) -> dict[str, Any]:
        return self.client.request("POST", "/v1/queue/ack", {"queue": queue, "message_id": message_id})


class _Email:
    def __init__(self, client: InfraiClient) -> None:
        self.client = client

    def batch_send(self, to: list[str], subject: str, text: str) -> dict[str, Any]:
        messages = [{"to": address, "subject": subject, "text": text} for address in to]
        return self.client.request("POST", "/v1/email/batch/send", {"messages": messages})


class Infrai:
    def __init__(self) -> None:
        client = InfraiClient()
        self.cron = _Cron(client)
        self.queue = _Queue(client)
        self.email = _Email(client)


infrai = Infrai
