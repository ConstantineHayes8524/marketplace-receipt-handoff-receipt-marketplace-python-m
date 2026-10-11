import httpx
import pytest

from marketplace_receipts.infrai_email import InfraiEmail


@pytest.mark.asyncio
async def test_email_send_retries_429_and_reads_message_id() -> None:
    requests: list[httpx.Request] = []
    sleeps: list[float] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if len(requests) == 1:
            return httpx.Response(
                429,
                headers={"Retry-After": "2"},
                json={"ok": False, "data": None, "error": {"code": "RATE_LIMITED"}, "metadata": {}},
            )
        return httpx.Response(
            200,
            json={"ok": True, "data": {"message_id": "msg_1042"}, "error": None, "metadata": {}},
        )

    async def record_sleep(seconds: float) -> None:
        sleeps.append(seconds)

    email = InfraiEmail("test-key", transport=httpx.MockTransport(handler), sleep=record_sleep)
    try:
        result = await email.email_send(
            to="buyer@example.com",
            subject="Receipt for order order-1042",
            html="<p>Paid</p>",
            idempotency_key="marketplace-receipt:order-1042",
        )
    finally:
        await email.close()

    assert result["message_id"] == "msg_1042"
    assert sleeps == [2.0]
    assert requests[0].method == "POST"
    assert requests[0].url.path == "/v1/email/send"
    assert requests[0].headers["Idempotency-Key"] == "marketplace-receipt:order-1042"
