import os
import httpx
from dotenv import load_dotenv
from fastapi import FastAPI
from mcp.server.fastapi import MCPServer

load_dotenv()

YANDEX_TOKEN = os.getenv("YANDEX_WORDSTAT_TOKEN")
WORDSTAT_BASE = "https://api.wordstat.yandex.net/v1"

app = FastAPI()
mcp = MCPServer(app)


async def call_wordstat(endpoint, payload):
    headers = {
        "Authorization": f"Bearer {YANDEX_TOKEN}",
        "Content-Type": "application/json"
    }

    async with httpx.AsyncClient() as client:
        r = await client.post(
            f"{WORDSTAT_BASE}{endpoint}",
            headers=headers,
            json=payload
        )
        return r.json()


@mcp.tool()
async def wordstat_top_requests(query: str):
    """Top search requests for a keyword"""
    return await call_wordstat("/topRequests", {"query": query})


@mcp.tool()
async def wordstat_dynamics(query: str):
    """Search dynamics"""
    return await call_wordstat("/dynamics", {"query": query})


@mcp.tool()
async def wordstat_regions(query: str):
    """Regional search distribution"""
    return await call_wordstat("/regions", {"query": query})


@mcp.tool()
async def wordstat_user_info():
    """User info from Wordstat"""
    return await call_wordstat("/userInfo", {})


mcp.mount("/mcp")
