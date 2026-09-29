"""Служебное: проверка доступности API при старте и health-эндпоинт для PaaS."""
import logging
import os

import aiohttp
from aiohttp import web

log = logging.getLogger(__name__)


async def check_anthropic_reachable() -> None:
    """401 без ключа — API доступен из этого региона; 403 — регион заблокирован."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://api.anthropic.com/v1/models", timeout=aiohttp.ClientTimeout(total=10)
            ) as resp:
                status = resp.status
    except Exception as exc:
        log.error("Anthropic API unreachable: %s", exc)
        return
    if status == 403:
        log.error("Anthropic API returned 403: server region is not supported, move the bot")
    else:
        log.info("Anthropic API reachable from this server (HTTP %s without key)", status)


async def start_health_server() -> web.AppRunner | None:
    """Платформы вида «веб-сервис» ждут HTTP-порт; отвечаем ok на / и /health."""
    port = os.environ.get("PORT")
    if not port:
        return None
    app = web.Application()
    ok = lambda _request: web.Response(text="ok")  # noqa: E731
    app.router.add_get("/", ok)
    app.router.add_get("/health", ok)
    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, "0.0.0.0", int(port)).start()
    log.info("health server on port %s", port)
    return runner
