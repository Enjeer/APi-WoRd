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
    data = await request.json()
    tool = data.get("tool")
    params = data.get("params", {})

    if tool not in TOOLS:
        return JSONResponse({"error": "Unknown tool"}, status_code=400)

    endpoint = TOOLS[tool]

    try:
        async with httpx.AsyncClient() as client:
            headers = {
                "Authorization": f"Bearer {YANDEX_TOKEN}",
                "Content-Type": "application/json"
            }
            r = await client.post(f"{WORDSTAT_BASE}{endpoint}", headers=headers, json=params)
            r.raise_for_status()
            result = r.json()
    except httpx.HTTPStatusError as e:
        result = {"error": f"Wordstat returned {r.status_code}", "detail": r.text}
    except Exception as e:
        result = {"error": "Internal Server Error", "detail": str(e)}

    return JSONResponse({"result": result})

@app.get("/")
def root():
    return {"status": "server works"}

@app.get("/check-token")
def check_token():
    return {"token_set": bool(YANDEX_TOKEN)}
