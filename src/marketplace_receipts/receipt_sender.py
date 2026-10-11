from html import escape
from typing import Any, Protocol

from .models import OrderHandoff, OrderStatus, ReceiptResult


class EmailSender(Protocol):
    async def email_send(self, **request: Any) -> dict[str, Any]:
        pass


def render_receipt(order: OrderHandoff) -> str:
    amount = f"{order.total_cents / 100:.2f} {escape(order.currency)}"
    return (
        f"<h1>Receipt from {escape(order.seller.shop_name)}</h1>"
        f"<p>Hi {escape(order.buyer.display_name)}, your order "
        f"<strong>{escape(order.order_id)}</strong> is paid.</p>"
        f"<p>Total: {amount}</p>"
        f"<p>The seller has received the handoff. Questions: "
        f"{escape(str(order.seller.support_email))}</p>"
    )


async def handoff_paid_order(order: OrderHandoff, email: EmailSender) -> ReceiptResult:
    if order.status is not OrderStatus.PAID:
        return ReceiptResult(order_id=order.order_id, action="awaiting_payment")

    sent = await email.email_send(
        to=str(order.buyer.email),
        subject=f"Receipt for order {order.order_id}",
        html=render_receipt(order),
        idempotency_key=f"marketplace-receipt:{order.order_id}",
    )
    return ReceiptResult(
        order_id=order.order_id,
        action="receipt_sent",
        message_id=str(sent["message_id"]),
    )
