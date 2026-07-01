from __future__ import annotations

import asyncio
from collections.abc import Callable

import httpx

from api.models import Server


async def poll_server(server: Server, timeout: float = 5.0) -> Server:
    url = f"{server.base_url()}/health"
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(url)
        server.status = "UP" if response.status_code == 200 else "DEGRADED"
    except (httpx.ConnectError, httpx.TimeoutException):
        server.status = "DOWN"
    return server


async def run_poll_loop(get_servers: Callable[[], list[Server]], interval: float = 10.0) -> None:
    while True:
        servers = get_servers()
        if servers:
            await asyncio.gather(*(poll_server(server) for server in servers))
        await asyncio.sleep(interval)
