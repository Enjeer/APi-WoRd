# server.py
import os
import json
import httpx
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

load_dotenv()

YANDEX_TOKEN = os.getenv("YANDEX_WORDSTAT_TOKEN")
WORDSTAT_BASE = "https://api.wordstat.yandex.net/v1"

app = FastAPI()

TOOLS = {
    "wordstat_top_requests": "/topRequests",
    "wordstat_dynamics": "/dynamics",
    "wordstat_regions": "/regions",
    "wordstat_user_info": "/userInfo"
}

async def call_wordstat(endpoint, payload):
    headers = {
        "Authorization": f"Bearer {YANDEX_TOKEN}",
        "Content-Type": "application/json"
    }
    async with httpx.AsyncClient() as client:
        r = await client.post(f"{WORDSTAT_BASE}{endpoint}", headers=headers, json=payload)
        return r.json()

@app.post("/mcp")
async def mcp_endpoint(request: Request):
    """
    Простая реализация MCP: ChatGPT присылает JSON с полями:
    { "tool": "<tool_name>", "params": {...} }
    """
    data = await request.json()
    tool = data.get("tool")
    params = data.get("params", {})

    if tool not in TOOLS:
        return JSONResponse({"error": "Unknown tool"}, status_code=400)

    endpoint = TOOLS[tool]
    result = await call_wordstat(endpoint, params)
    return JSONResponse({"result": result})

@app.get("/")
def root():
    return {"status": "server works"}
