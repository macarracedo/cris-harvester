from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass

import httpx
import structlog
from tenacity import AsyncRetrying, retry_if_exception_type, stop_after_attempt, wait_exponential_jitter

from cris_harvester.config import Settings

logger = structlog.get_logger(__name__)


@dataclass
class HttpClientConfig:
    rate_limit_rps: float
    user_agent: str
    timeout: float
    retry_max_attempts: int
    retry_backoff_base: float
    respect_robots: bool


class AsyncHttpClient:
    def __init__(self, settings: Settings) -> None:
        self._config = HttpClientConfig(
            rate_limit_rps=settings.rate_limit_rps,
            user_agent=settings.user_agent,
            timeout=settings.request_timeout,
            retry_max_attempts=settings.retry_max_attempts,
            retry_backoff_base=settings.retry_backoff_base,
            respect_robots=settings.respect_robots,
        )
        self._client = httpx.AsyncClient(
            headers={"User-Agent": self._config.user_agent},
            timeout=self._config.timeout,
        )
        self._lock = asyncio.Lock()
        self._next_allowed_time = 0.0

    async def close(self) -> None:
        await self._client.aclose()

    async def _rate_limit(self) -> None:
        if self._config.rate_limit_rps <= 0:
            return

        async with self._lock:
            now = time.monotonic()
            sleep_for = self._next_allowed_time - now
            if sleep_for > 0:
                await asyncio.sleep(sleep_for)
            interval = 1.0 / self._config.rate_limit_rps
            self._next_allowed_time = time.monotonic() + interval

    async def get_text(self, url: str) -> str:
        if self._config.respect_robots:
            logger.info("robots_placeholder", message="Respect robots is enabled (placeholder)")

        await self._rate_limit()
        retrying = AsyncRetrying(
            retry=retry_if_exception_type(httpx.HTTPError),
            stop=stop_after_attempt(self._config.retry_max_attempts),
            wait=wait_exponential_jitter(initial=self._config.retry_backoff_base, max=10.0),
            reraise=True,
        )
        async for attempt in retrying:
            with attempt:
                response = await self._client.get(url)
                if 300 <= response.status_code < 400:
                    logger.warning(
                        "redirect_blocked",
                        url=url,
                        status=response.status_code,
                        location=response.headers.get("Location"),
                    )
                    return ""
                response.raise_for_status()
                return response.text
        raise RuntimeError("Unreachable")
