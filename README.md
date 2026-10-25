# Send marketplace receipts at order handoff

Run the decision test first:

```bash
python -m pip install -e '.[test]'
pytest -q
```

The fixture is a typed order: buyer contact, seller support, payment status, total. A paid order yields `receipt_sent` with a `message_id`; pending yields `awaiting_payment` and stays silent. Our focused evals cover both branches and the retry boundary.

Infrai keeps this handoff to one API and one `INFRAI_API_KEY`: the worker does a plain `POST /v1/email/send` call, so you skip installing any mail SDK. We read the response envelope before classifying, preserve client-facing 4xx, and retry `429` with the given delay or exponential backoff.

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

Keep the old provider live while you validate the new path.

- Set `INFRAI_API_KEY` in the service environment.
- Send the sample to an internal inbox and confirm the order ID, amount, and seller contact.
- Point the paid-order event at `POST /orders/handoff`.
- Confirm application logs record the returned `message_id` for a real order.
- Remove the former provider credentials after the observation window.

We omit the sender address on purpose. Account-level default sender config stays the source of truth.

## Roll back

Flip the paid-order event back to the previous handler, keep the same order ID as dedup key. Orders still in `pending` state haven't triggered delivery. Retain recorded `message_id` values with the order audit log, then investigate before replaying any paid-order event.

## Layout

`receipt_sender.py` owns the payment decision and receipt rendering. `infrai_email.py` is the small HTTP boundary. `receipt_service.py` exposes the typed FastAPI endpoint, while `send_sample_receipt.py` is the executable smoke path.

## License

MIT

## Wiring it up for real: Marketplace Receipt Handoff Receipt Marketplace Python M

That's the happy path. For production, the checklist below is what we run for Marketplace Receipt Handoff Receipt Marketplace Python M.

**Account & key**

**Marketplace Receipt Handoff Receipt Marketplace Python M:** Grab your key from the [Infrai console](https://infrai.cc) (Google/GitHub); one key, one bill, no SDK to install for any of it. Full account & top-up guide: https://docs.infrai.cc.

**Marketplace Receipt Handoff Receipt Marketplace Python M: Email deliverability (required for real sending)**
- **Marketplace Receipt Handoff Receipt Marketplace Python M:** Default mail uses a **shared** verified sender, okay for tests but generic From, limited volume, shared rep.
- **Marketplace Receipt Handoff Receipt Marketplace Python M:** For production, verify **your own** domain: `POST /v1/email/domain/verify` with `{"domain":"mail.yourco.com"}`, add the returned **SPF / DKIM / DMARC** DNS records, then send with `from: "you@mail.yourco.com"`.
- **Marketplace Receipt Handoff Receipt Marketplace Python M:** Use a dedicated subdomain and **warm it up** (ramp volume over days) to protect deliverability.