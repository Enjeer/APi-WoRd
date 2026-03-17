# server.py
import os
import httpx
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

load_dotenv()

YANDEX_TOKEN = os.getenv("YANDEX_WORDSTAT_TOKEN")
WORDSTAT_BASE = "https://api.wordstat.yandex.net/v1"

app = FastAPI()

TOOLS = ["wordstat_top_requests", "wordstat_dynamics", "wordstat_regions", "wordstat_user_info"]

async def call_wordstat(tool, params):
    """
    Конвертирует входящие params в JSON для Wordstat API
    """
    headers = {
        "Authorization": f"Bearer {YANDEX_TOKEN}",
        "Content-Type": "application/json"
    }

    # Конвертация params в payload в зависимости от инструмента
    if tool == "wordstat_top_requests":
        endpoint = "/topRequests"
        payload = {
            "phrase": params.get("phrase"),
            "regions": params.get("regions", [225]),
            "devices": params.get("devices", ["all"])
        }
    elif tool == "wordstat_dynamics":
        endpoint = "/dynamics"
        payload = {
            "phrase": params.get("phrase"),
            "period": params.get("period", "daily"),
            "fromDate": params.get("fromDate"),
            "toDate": params.get("toDate"),
            "regions": params.get("regions", [225]),
            "devices": params.get("devices", ["all"])
        }
    elif tool == "wordstat_regions":
        endpoint = "/regions"
        payload = {
            "phrase": params.get("phrase"),
            "regionType": params.get("regionType", "regions"),
            "devices": params.get("devices", ["all"])
        }
    elif tool == "wordstat_user_info":
        endpoint = "/userInfo"
        payload = {}
    else:
        return {"error": "Unknown tool"}

    # POST-запрос в Wordstat
    async with httpx.AsyncClient() as client:
        try:
            r = await client.post(f"{WORDSTAT_BASE}{endpoint}", headers=headers, json=payload)
            r.raise_for_status()
            return r.json()
        except httpx.HTTPStatusError:
            return {"error": f"Wordstat returned {r.status_code}", "detail": r.text}
        except Exception as e:
            return {"error": "Internal Server Error", "detail": str(e)}

# MCP endpoint
@app.post("/mcp")
async def mcp_endpoint(request: Request):
    data = await request.json()
    tool = data.get("tool")
    params = data.get("params", {})

    if tool not in TOOLS:
        return JSONResponse({"error": "Unknown tool"}, status_code=400)

    result = await call_wordstat(tool, params)
    return JSONResponse({"result": result})

# Корневой endpoint
@app.get("/")
def root():
    return {"status": "server works"}

# Проверка токена
@app.get("/check-token")
def check_token():
    return {"token_set": bool(YANDEX_TOKEN)}
