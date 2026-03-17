import os
import contextlib
from typing import Any, Literal

import httpx
from dotenv import load_dotenv
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Mount, Route

from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings

load_dotenv()

YANDEX_TOKEN = os.getenv("YANDEX_WORDSTAT_TOKEN")
WORDSTAT_BASE = "https://api.wordstat.yandex.net/v1"

if not YANDEX_TOKEN:
    raise RuntimeError("Не задан YANDEX_WORDSTAT_TOKEN")

RENDER_HOST = os.getenv("RENDER_EXTERNAL_HOSTNAME")
CUSTOM_HOST = os.getenv("CUSTOM_DOMAIN")

Device = Literal["all", "desktop", "phone", "tablet"]
Period = Literal["daily", "weekly", "monthly"]
RegionType = Literal["cities", "regions", "all"]

allowed_hosts = [
    "127.0.0.1:*",
    "localhost:*",
    "[::1]:*",
]

allowed_origins = [
    "http://127.0.0.1:*",
    "http://localhost:*",
]

if RENDER_HOST:
    allowed_hosts.append(f"{RENDER_HOST}:*")
    allowed_origins.append(f"https://{RENDER_HOST}")

if CUSTOM_HOST:
    allowed_hosts.append(f"{CUSTOM_HOST}:*")
    allowed_origins.append(f"https://{CUSTOM_HOST}")

mcp = FastMCP(
    name="Yandex Wordstat",
    instructions="Инструменты для Wordstat: top requests, dynamics, regions, user info",
    transport_security=TransportSecuritySettings(
        enable_dns_rebinding_protection=True,
        allowed_hosts=allowed_hosts,
        allowed_origins=allowed_origins,
    ),
    json_response=True,
)


async def _post_wordstat(endpoint: str, payload: dict[str, Any]) -> dict[str, Any]:
    headers = {
        "Authorization": f"Bearer {YANDEX_TOKEN}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            resp = await client.post(
                f"{WORDSTAT_BASE}{endpoint}",
                headers=headers,
                json=payload,
            )
            resp.raise_for_status()
            return {"ok": True, "data": resp.json()}
        except httpx.HTTPStatusError as e:
            try:
                detail = e.response.json()
            except Exception:
                detail = e.response.text

            return {
                "ok": False,
                "status_code": e.response.status_code,
                "error": "wordstat_http_error",
                "detail": detail,
            }
        except Exception as e:
            return {
                "ok": False,
                "error": "internal_error",
                "detail": str(e),
            }


@mcp.tool()
async def wordstat_top_requests(
    phrase: str,
    regions: list[int] | None = None,
    devices: list[Device] | None = None,
    num_phrases: int = 50,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "phrase": phrase,
        "numPhrases": num_phrases,
    }
    if regions:
        payload["regions"] = regions
    if devices:
        payload["devices"] = devices
    return await _post_wordstat("/topRequests", payload)


@mcp.tool()
async def wordstat_dynamics(
    phrase: str,
    period: Period,
    from_date: str,
    to_date: str | None = None,
    regions: list[int] | None = None,
    devices: list[Device] | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "phrase": phrase,
        "period": period,
        "fromDate": from_date,
    }
    if to_date:
        payload["toDate"] = to_date
    if regions:
        payload["regions"] = regions
    if devices:
        payload["devices"] = devices
    return await _post_wordstat("/dynamics", payload)


@mcp.tool()
async def wordstat_regions(
    phrase: str,
    region_type: RegionType = "all",
    devices: list[Device] | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "phrase": phrase,
        "regionType": region_type,
    }
    if devices:
        payload["devices"] = devices
    return await _post_wordstat("/regions", payload)


@mcp.tool()
async def wordstat_user_info() -> dict[str, Any]:
    return await _post_wordstat("/userInfo", {})


async def health(request):
    return JSONResponse({"ok": True, "service": "wordstat-mcp"})


@contextlib.asynccontextmanager
async def lifespan(app: Starlette):
    # Запускаем MCP-сессию и держим её активной на весь lifetime приложения
    await mcp.session_manager.start()
    try:
        yield
    finally:
        await mcp.session_manager.stop()


app = Starlette(
    routes=[
        Route("/", health),
        Mount("/", app=mcp.streamable_http_app()),
    ],
    lifespan=lifespan,
)
