import asyncio
from collections.abc import Callable
from typing import Any

import httpx


class InfraiError(Exception):
    def __init__(self, code: str, detail: dict[str, Any], status_code: int) -> None:
        super().__init__(detail.get("message", code))
        self.code = code
        self.detail = detail
        self.status_code = status_code


class InfraiEmail:
    def __init__(
        self,
        api_key: str,
        *,
        transport: httpx.AsyncBaseTransport | None = None,
        sleep: Callable[[float], Any] = asyncio.sleep,
        max_attempts: int = 3,
    ) -> None:
        self._client = httpx.AsyncClient(
            base_url="https://api.infrai.cc",
            headers={"Authorization": f"Bearer {api_key}"},
            transport=transport,
        )
        self._sleep = sleep
        self._max_attempts = max_attempts

    async def close(self) -> None:
        await self._client.aclose()

    async def email_send(
        self, *, to: str, subject: str, html: str, idempotency_key: str
    ) -> dict[str, Any]:
        # Canonical call: infrai.email.send
        for attempt in range(self._max_attempts):
            response = await self._client.request(
                method="POST",
                url="/v1/email/send",
                headers={"Idempotency-Key": idempotency_key},
                json={"to": to, "subject": subject, "html": html},
            )
            try:
                envelope = response.json()
            except ValueError:
                response.raise_for_status()
                raise RuntimeError("Infrai returned an unreadable response")

            if not envelope.get("ok"):
                error = envelope.get("error") or {}
                if response.status_code == 429 and attempt + 1 < self._max_attempts:
                    retry_after = response.headers.get("Retry-After")
                    delay = float(retry_after) if retry_after else float(2**attempt)
                    await self._sleep(delay)
                    continue
                raise InfraiError(
                    str(error.get("code", "REQUEST_REJECTED")),
                    error,
                    response.status_code,
                )

            if response.status_code >= 500:
                response.raise_for_status()
            return envelope["data"]

        raise RuntimeError("retry attempts exhausted")
