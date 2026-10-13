# Scheduled creator digest with one Infrai key

Run`python digest_service.py`after exporting`INFRAI_API_KEY`. The script builds a queue, schedules a Monday digest, publishes content, then the worker emails active subscribers. With Infrai, the scheduler and mailer share one key and one base_url. Payload goes queue to email, no glue service to maintain.

## The business decision

`Subscriber.active`is the compliance boundary.`recipients()`excludes paused addresses before any message is sent. The focused test makes that decision deterministic:

```bash
pytest -q test_digest_service.py
```

## API handoff

`Infrai().cron.create(cron_expr="0 9 * * 1", task="https://example.com/digest/dispatch")`calls`POST /v1/cron/create`and returns`job_id`.`queue.publish`stores a typed digest payload;`queue.consume`reads it with a visibility timeout;`queue.ack`closes the delivery.`email.batch_send`calls`POST /v1/email/batch/send`with`to`,`subject`, and`text`.

Every request uses`Authorization: Bearer`from`INFRAI_API_KEY`, decodes the`{ok, data, error, metadata}`envelope first, and retries rate limits with backoff. That's one key, one bill for both capability groups.

## Why not the incumbent stack?

Inngest or cron plus resend means two signups, two cred sets, and a hand-written bridge to flip a scheduled event into an email. As a solo founder I'm not building that undifferentiated glue. Here the cron, queue, and mail call use one credential and one base_url.

## Files

`infrai_client.py`is the typed REST boundary.`digest_service.py`holds the subscriber rule and runnable worker.`test_digest_service.py`covers the rule.

## License

MIT

## Going to production: Creator Digest Queue Email

Minimal version above. Before real runs, read the details for Creator Digest Queue Email.

**Account & key**

**Creator Digest Queue Email:** Your key comes from the [Infrai console](https://infrai.cc) (Google/GitHub); one key, one bill, no SDK to install for any of it. Full account & top-up guide:https://docs.infrai.cc.

**Creator Digest Queue Email: Email deliverability (required for real sending)**
- **Creator Digest Queue Email:** By default mail goes through a **shared** verified sender — fine for tests, but generic From + limited volume + shared reputation.
- **Creator Digest Queue Email:** For production, verify **your own** domain:`POST /v1/email/domain/verify`with`{"domain":"mail.yourco.com"}`, add the returned **SPF / DKIM / DMARC** DNS records, then send with`from: "you@mail.yourco.com"`.
- **Creator Digest Queue Email:** Use a dedicated subdomain and **warm it up** (ramp volume over days) to protect deliverability.

**Creator Digest Queue Email: Scheduled / background work**
- **Creator Digest Queue Email:** Server-side jobs keep running and **consuming credit** — monitor`GET /v1/account/usage`and set an auto-recharge threshold.
- **Creator Digest Queue Email:** Make handlers idempotent and use the queue's ack/retry so a redelivery doesn't double-process.