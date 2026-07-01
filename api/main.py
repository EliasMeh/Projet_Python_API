from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Response, WebSocket, WebSocketDisconnect

from api.auth import verify_api_key
from api.metrics import get_system_metrics
from api.models import Server, ServerIn, ServerOut
from api.poller import poll_server, run_poll_loop


_store: dict[int, Server] = {}
_counter = 0
_poller_task: asyncio.Task | None = None


def _get_servers() -> list[Server]:
    return list(_store.values())


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _poller_task
    _poller_task = asyncio.create_task(run_poll_loop(_get_servers))
    try:
        yield
    finally:
        if _poller_task is not None:
            _poller_task.cancel()
            try:
                await _poller_task
            except asyncio.CancelledError:
                pass


app = FastAPI(title="DevOps Monitoring Dashboard API", version="1.0.0", lifespan=lifespan)


@app.get("/health")
async def health_check() -> dict:
    return {"status": "ok"}


@app.get("/metrics")
async def metrics() -> dict:
    return get_system_metrics()


@app.post("/servers", response_model=ServerOut, status_code=201, dependencies=[Depends(verify_api_key)])
async def register_server(server: ServerIn) -> ServerOut:
    global _counter
    _counter += 1
    record = Server(
        id=_counter,
        name=server.name,
        host=server.host,
        port=server.port,
        status="unknown",
        tags=server.tags,
    )
    _store[record.id] = record
    return record


@app.get("/servers", response_model=list[ServerOut])
async def list_servers(status: str | None = None) -> list[ServerOut]:
    servers = list(_store.values())
    if status is not None:
        servers = [server for server in servers if server.status == status]
    return servers


@app.get("/servers/{server_id}", response_model=ServerOut)
async def get_server(server_id: int) -> ServerOut:
    if server_id not in _store:
        raise HTTPException(status_code=404, detail="Server not found")
    return _store[server_id]


@app.delete("/servers/{server_id}", status_code=204, response_class=Response, dependencies=[Depends(verify_api_key)])
async def delete_server(server_id: int) -> Response:
    if server_id not in _store:
        raise HTTPException(status_code=404, detail="Server not found")
    del _store[server_id]
    return Response(status_code=204)


@app.post("/servers/{server_id}/check", response_model=ServerOut, dependencies=[Depends(verify_api_key)])
async def trigger_health_check(server_id: int) -> ServerOut:
    if server_id not in _store:
        raise HTTPException(status_code=404, detail="Server not found")
    return await poll_server(_store[server_id])


@app.websocket("/ws/metrics")
async def websocket_metrics(websocket: WebSocket) -> None:
    await websocket.accept()
    try:
        while True:
            await websocket.send_json(get_system_metrics())
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        return
