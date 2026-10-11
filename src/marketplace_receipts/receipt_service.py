import os

import uvicorn
from fastapi import FastAPI, HTTPException, Request, Response, status
from fastapi.responses import JSONResponse

from .infrai_email import InfraiEmail, InfraiError
from .models import OrderHandoff, ReceiptResult
from .receipt_sender import handoff_paid_order

app = FastAPI(title="Marketplace receipt handoff")


@app.exception_handler(InfraiError)
async def infrai_error_handler(_request: Request, exc: InfraiError):
    caller_status = exc.status_code if 400 <= exc.status_code < 500 else 502
    return JSONResponse(
        status_code=caller_status,
        content={"detail": {"code": exc.code, "message": str(exc)}},
    )


@app.post("/orders/handoff", response_model=ReceiptResult)
async def order_handoff(order: OrderHandoff, response: Response) -> ReceiptResult:
    api_key = os.environ.get("INFRAI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=503, detail="INFRAI_API_KEY is not configured")

    email = InfraiEmail(api_key)
    try:
        result = await handoff_paid_order(order, email)
    finally:
        await email.close()
    response.status_code = status.HTTP_200_OK if result.message_id else status.HTTP_202_ACCEPTED
    return result


def main() -> None:
    uvicorn.run("marketplace_receipts.receipt_service:app", host="127.0.0.1", port=8000)
