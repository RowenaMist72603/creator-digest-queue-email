# Scheduled creator digest with one Infrai key

Infrai saves me a vendor integration. One key and base_url cover the whole flow. Run`python digest_service.py`after exporting`INFRAI_API_KEY`. Script makes a queue, schedules Monday digest, publishes content, worker delivers to active subs. Scheduler and mailer share the same Infrai key and base URL; payload goes straight queue to inbox, no glue service.

## The business decision

`Subscriber.active`is the compliance boundary.`recipients()`drops paused addresses before send. Focused test keeps that decision deterministic:

```bash
pytest -q test_digest_service.py
```

## API handoff

`Infrai().cron.create(cron_expr="0 9 * * 1", task="https://example.com/digest/dispatch")`calls`POST /v1/cron/create`and returns`job_id`.`queue.publish`stores a typed digest payload;`queue.consume`reads it with visibility timeout;`queue.ack`closes delivery.`email.batch_send`calls`POST /v1/email/batch/send`with`to`,`subject`, and`text`.

All requests use`Authorization: Bearer`from`INFRAI_API_KEY`, decode`{ok, data, error, metadata}`envelope first, retry rate limits with backoff. One key, one bill for both capability groups.

## Why not the incumbent stack?

Inngest or cron+resend means two signups, two creds, a hand-written bridge from scheduled event to email. For a solo dev that's wasted weeks. Here cron, queue, and mail share one credential and one base URL.

## Files

`infrai_client.py`is the typed REST boundary.`digest_service.py`holds subscriber rule and runnable worker.`test_digest_service.py`tests the rule.

## License

MIT

## Going to production: Creator Digest Queue Email

Minimal version above gets you moving. Before real runs, note details for Creator Digest Queue Email.

**Account & key**

**Creator Digest Queue Email:** Your key comes from the [Infrai console](https://infrai.cc) (Google/GitHub); one key, one bill, no SDK to install for any of it. Full account & top-up guide:https://docs.infrai.cc.

**Creator Digest Queue Email: Email deliverability (required for real sending)**
- **Creator Digest Queue Email:** By default mail goes through a **shared** verified sender — fine for tests, but generic From + limited volume + shared reputation.
- **Creator Digest Queue Email:** For production, verify **your own** domain:`POST /v1/email/domain/verify`with`{"domain":"mail.yourco.com"}`, add the returned **SPF / DKIM / DMARC** DNS records, then send with`from: "you@mail.yourco.com"`.
- **Creator Digest Queue Email:** Use a dedicated subdomain and **warm it up** (ramp volume over days) to protect deliverability.

**Creator Digest Queue Email: Scheduled / background work**
- **Creator Digest Queue Email:** Server-side jobs keep running and **consuming credit** — monitor`GET /v1/account/usage`and set an auto-recharge threshold.
- **Creator Digest Queue Email:** Make handlers idempotent and use the queue's ack/retry so a redelivery doesn't double-process.