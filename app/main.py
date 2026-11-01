import asyncio
import json
import logging
import os
from pathlib import Path
from time import perf_counter
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import FileResponse, JSONResponse, Response
from prometheus_client import CONTENT_TYPE_LATEST, CollectorRegistry, Counter, Histogram, generate_latest

from app.provider import MockProvider, OpenMeteoProvider, ProviderError

logger = logging.getLogger("weather.requests")
logging.basicConfig(level=logging.INFO, format="%(message)s")
logging.getLogger("httpx").setLevel(logging.WARNING)


def create_app(provider=None, mode=None):
    mode = mode if mode is not None else os.getenv("WEATHER_MODE", "mock")
    if mode not in {"mock", "openmeteo"}:
        raise ValueError("WEATHER_MODE must be mock or openmeteo")
    api = FastAPI(title="Weather Status", version="0.1.0")
    api.state.provider = provider or (OpenMeteoProvider() if mode == "openmeteo" else MockProvider())
    registry = CollectorRegistry()
    requests = Counter("weather_http_requests_total", "Completed HTTP requests", ["route", "method", "status_class"], registry=registry)
    latency = Histogram("weather_http_duration_seconds", "HTTP duration", ["route"], registry=registry)
    failures = Counter("weather_provider_failures_total", "Provider failures", ["reason"], registry=registry)
    version = {"version": "0.1.0", "commit": os.getenv("APP_COMMIT", "local"), "mode": mode}

    @api.middleware("http")
    async def observe(request: Request, call_next):
        started, request_id, status = perf_counter(), str(uuid4()), 500
        try:
            response = await call_next(request)
            status = response.status_code
            response.headers["X-Request-ID"] = request_id
            return response
        finally:
            route = getattr(request.scope.get("route"), "path", "unmatched")
            method = request.method if request.method in {"GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"} else "OTHER"
            duration = perf_counter() - started
            requests.labels(route, method, f"{status // 100}xx").inc()
            latency.labels(route).observe(duration)
            logger.info(json.dumps({"request_id": request_id, "route": route, "status": status,
                                    "duration_ms": round(duration * 1000, 2), **version}))

    @api.get("/", include_in_schema=False)
    def index():
        return FileResponse(Path(__file__).parent / "static" / "index.html")

    @api.get("/health")
    def health():
        return {"status": "ok"}

    @api.get("/ready")
    def ready():
        return {"status": "ready", "mode": mode}

    @api.get("/version")
    def release():
        return version

    @api.get("/metrics", include_in_schema=False)
    def metrics():
        return Response(generate_latest(registry), headers={"Content-Type": CONTENT_TYPE_LATEST})

    @api.get("/api/locations")
    async def locations(q: str = Query(min_length=2, max_length=80)):
        if mode == "mock":
            return {"results": [{"id": None, "label": city} for city in
                                ("Atlanta", "New York", "London", "Lagos") if city.casefold().startswith(q.casefold())]}
        try:
            async with asyncio.timeout(4):
                return {"results": await api.state.provider.search(q.strip())}
        except (TimeoutError, ProviderError) as exc:
            status = exc.status if isinstance(exc, ProviderError) else 504
            return JSONResponse({"detail": "City search unavailable. Please try again."}, status_code=status)

    @api.get("/api/weather")
    async def weather(city: str = Query(default="", max_length=80), location_id: int | None = Query(default=None, gt=0)):
        city = city.strip()
        if (not city and location_id is None) or any(ord(c) < 32 for c in city):
            raise HTTPException(422, "Enter a city name without control characters.")
        try:
            async with asyncio.timeout(5):
                if location_id is not None:
                    if mode == "mock":
                        raise HTTPException(422, "Location IDs require live mode.")
                    return await api.state.provider.weather(city, location_id=location_id)
                return await api.state.provider.weather(city)
        except HTTPException:
            raise
        except TimeoutError:
            failures.labels("timeout").inc()
            return JSONResponse({"detail": "Weather provider timed out. Try again shortly."}, status_code=504)
        except ProviderError as exc:
            status = exc.status if exc.status in {404, 409, 429, 503} else 503
            if status >= 429:
                failures.labels("rate_limit" if status == 429 else "unavailable").inc()
            message = exc.message if status in {404, 409} else "Weather provider unavailable. Try again shortly."
            return JSONResponse({"detail": message}, status_code=status,
                                headers={"Retry-After": "30"} if status == 429 else {})
        except Exception:  # noqa: BLE001 - sanitize unexpected errors at the provider boundary
            failures.labels("unexpected").inc()
            return JSONResponse({"detail": "Weather provider unavailable. Try again shortly."}, status_code=503)

    return api


app = create_app()
