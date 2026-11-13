import time

import httpx
from fastapi import Depends, FastAPI, Request, Response
from fastapi.responses import JSONResponse
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from app.auth import require_api_key
from app.config import settings
from app.metrics import REQUEST_COUNT, REQUEST_LATENCY
from app.queue import gpu_slot
from app.ratelimit import enforce_rate_limit

app = FastAPI(title="llm-gateway")


@app.get("/healthz")
async def healthz() -> dict:
    return {"status": "ok"}


@app.get("/metrics")
async def metrics() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


async def _proxy(request: Request, path: str, api_key: str) -> Response:
    await enforce_rate_limit(api_key)

    route = f"/{path}"
    start = time.monotonic()
    body = await request.body()

    async with gpu_slot():
        try:
            async with httpx.AsyncClient(base_url=settings.ollama_base_url, timeout=120) as client:
                upstream = await client.request(
                    request.method,
                    f"/{path}",
                    content=body,
                    params=request.query_params,
                    headers={"content-type": request.headers.get("content-type", "application/json")},
                )
        except httpx.ConnectError:
            REQUEST_COUNT.labels(route=route, status="upstream_unavailable").inc()
            return JSONResponse(status_code=502, content={"error": "upstream Ollama instance unreachable"})

    REQUEST_LATENCY.labels(route=route).observe(time.monotonic() - start)
    REQUEST_COUNT.labels(route=route, status=str(upstream.status_code)).inc()

    return Response(
        content=upstream.content,
        status_code=upstream.status_code,
        media_type=upstream.headers.get("content-type", "application/json"),
    )


@app.api_route("/v1/chat/completions", methods=["POST"])
async def chat_completions(request: Request, api_key: str = Depends(require_api_key)) -> Response:
    return await _proxy(request, "v1/chat/completions", api_key)


@app.api_route("/v1/completions", methods=["POST"])
async def completions(request: Request, api_key: str = Depends(require_api_key)) -> Response:
    return await _proxy(request, "v1/completions", api_key)


@app.api_route("/v1/models", methods=["GET"])
async def models(request: Request, api_key: str = Depends(require_api_key)) -> Response:
    return await _proxy(request, "v1/models", api_key)
