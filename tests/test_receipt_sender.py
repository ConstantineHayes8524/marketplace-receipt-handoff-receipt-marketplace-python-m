from typing import Any

import pytest

from marketplace_receipts.models import BuyerUpdate, OrderHandoff, OrderStatus, SellerAsset
from marketplace_receipts.receipt_sender import handoff_paid_order


class RecordingEmail:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    async def email_send(self, **request: Any) -> dict[str, str]:
        self.calls.append(request)
        return {"message_id": "msg_1042"}


def order(status: OrderStatus) -> OrderHandoff:
    return OrderHandoff(
        order_id="order-1042",
        status=status,
        total_cents=4250,
        currency="USD",
        seller=SellerAsset(shop_name="Northwind Prints", support_email="help@example.com"),
        buyer=BuyerUpdate(email="buyer@example.com", display_name="Casey"),
    )


@pytest.mark.asyncio
async def test_paid_order_sends_one_receipt_with_stable_handoff_key() -> None:
    email = RecordingEmail()

    result = await handoff_paid_order(order(OrderStatus.PAID), email)

    assert result.action == "receipt_sent"
    assert result.message_id == "msg_1042"
    assert len(email.calls) == 1
    assert email.calls[0]["to"] == "buyer@example.com"
    assert email.calls[0]["idempotency_key"] == "marketplace-receipt:order-1042"


@pytest.mark.asyncio
async def test_pending_order_waits_without_sending() -> None:
    email = RecordingEmail()

    result = await handoff_paid_order(order(OrderStatus.PENDING), email)

    assert result.action == "awaiting_payment"
    assert result.message_id is None
    assert email.calls == []
