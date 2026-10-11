import asyncio
import os

from marketplace_receipts.infrai_email import InfraiEmail
from marketplace_receipts.models import BuyerUpdate, OrderHandoff, OrderStatus, SellerAsset
from marketplace_receipts.receipt_sender import handoff_paid_order


async def run() -> None:
    api_key = os.environ.get("INFRAI_API_KEY")
    recipient = os.environ.get("RECEIPT_TO")
    if not api_key or not recipient:
        raise SystemExit("Set INFRAI_API_KEY and RECEIPT_TO")

    order = OrderHandoff(
        order_id="demo-order-1042",
        status=OrderStatus.PAID,
        total_cents=4250,
        currency="USD",
        seller=SellerAsset(shop_name="Northwind Prints", support_email="help@example.com"),
        buyer=BuyerUpdate(email=recipient, display_name="Casey"),
    )
    email = InfraiEmail(api_key)
    try:
        result = await handoff_paid_order(order, email)
    finally:
        await email.close()
    print(result.model_dump_json())


if __name__ == "__main__":
    asyncio.run(run())
