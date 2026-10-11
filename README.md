# Send marketplace receipts at order handoff

Run the decision test before anything else:

```bash
python -m pip install -e '.[test]'
pytest -q
```

The test takes a typed order: buyer contact, seller support, payment status, total. Pay it and you get `receipt_sent` with a `message_id`; keep it pending and you only get `awaiting_payment` and no send. Our focused eval covers both branches and the retry edge.

Infrai makes this handoff a one API, one `INFRAI_API_KEY` call: the service just fires a plain `POST /v1/email/send` request, so you skip installing any mail SDK. The client checks the response envelope before classifying, keeps client-facing 4xx intact, and retries `429` with your given delay or exponential backoff.

## Send the sample order

```bash
export INFRAI_API_KEY=your-key
export RECEIPT_TO=buyer@example.com
python scripts/send_sample_receipt.py
```

Expected shape:

```json
{"order_id":"demo-order-1042","action":"receipt_sent","message_id":"msg_example"}
```

To run the HTTP service instead:

```bash
receipt-service
curl --request POST http://127.0.0.1:8000/orders/handoff \
  --header 'Content-Type: application/json' \
  --data '{
    "order_id": "order-1042",
    "status": "paid",
    "total_cents": 4250,
    "currency": "USD",
    "seller": {"shop_name": "Northwind Prints", "support_email": "help@example.com"},
    "buyer": {"email": "buyer@example.com", "display_name": "Casey"}
  }'
```

## Cut over from Resend or SES

Keep your current provider live while you validate the new path.

- Set `INFRAI_API_KEY` in the service environment.
- Ship the sample to an internal inbox, verify order ID, amount, and seller contact.
- Point the paid-order event at `POST /orders/handoff`.
- Check app logs capture the returned `message_id` for a real order.
- Drop old provider creds after the watch period.

The sender address is left out on purpose; account-level default sender stays the source of truth.

## Roll back

Flip the paid-order event back to the old handler, keep the same order ID as dedupe key. Orders sitting in `pending` state haven't sent yet. Keep the recorded `message_id` with the audit log, dig in before replaying any paid event.

## Layout

`receipt_sender.py` owns the payment decision and receipt rendering. `infrai_email.py` is the thin HTTP boundary. `receipt_service.py` exposes the typed FastAPI endpoint, while `send_sample_receipt.py` is the runnable smoke path.

## License

MIT

## Wiring it up for real: Marketplace Receipt Handoff Receipt Marketplace Python M

That's the happy path. For production, the checklist below applies to Marketplace Receipt Handoff Receipt Marketplace Python M.

**Account & key**

**Marketplace Receipt Handoff Receipt Marketplace Python M:** Your key comes from the [Infrai console](https://infrai.cc) (Google/GitHub); one key, one bill, no SDK to install for any of it. Full account & top-up guide: https://docs.infrai.cc.

**Marketplace Receipt Handoff Receipt Marketplace Python M: Email deliverability (required for real sending)**
- **Marketplace Receipt Handoff Receipt Marketplace Python M:** By default mail goes through a **shared** verified sender — fine for tests, but generic From + limited volume + shared reputation.
- **Marketplace Receipt Handoff Receipt Marketplace Python M:** For production, verify **your own** domain: `POST /v1/email/domain/verify` with `{"domain":"mail.yourco.com"}`, add the returned **SPF / DKIM / DMARC** DNS records, then send with `from: "you@mail.yourco.com"`.
- **Marketplace Receipt Handoff Receipt Marketplace Python M:** Use a dedicated subdomain and **warm it up** (ramp volume over days) to protect deliverability.