import os
import json
import httpx
from fastapi import FastAPI, Request
from sse_starlette.sse import EventSourceResponse
from dotenv import load_dotenv

load_dotenv()

YANDEX_TOKEN = os.getenv("YANDEX_WORDSTAT_TOKEN")

WORDSTAT_BASE = "https://api.wordstat.yandex.net/v1"

app = FastAPI()


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


TOOLS = {
    "wordstat_top_requests": {
        "endpoint": "/topRequests"
    },
    "wordstat_dynamics": {
        "endpoint": "/dynamics"
    },
    "wordstat_regions": {
        "endpoint": "/regions"
    },
    "wordstat_user_info": {
        "endpoint": "/userInfo"
    }
}


@app.get("/mcp")
async def mcp_endpoint(request: Request):

    async def event_generator():

        # MCP handshake
        yield {
            "event": "ready",
            "data": json.dumps({
                "tools": [
                    {
                        "name": name,
                        "description": f"Call Yandex Wordstat {cfg['endpoint']}",
                        "input_schema": {
                            "type": "object",
                            "properties": {
                                "query": {"type": "string"}
                            }
                        }
                    }
                    for name, cfg in TOOLS.items()
                ]
            })
        }

        async for message in request.stream():

            if not message:
                continue

            try:
                data = json.loads(message)
            except:
                continue

            tool = data.get("tool")
            params = data.get("params", {})

            if tool not in TOOLS:
                yield {
                    "event": "error",
                    "data": json.dumps({"error": "Unknown tool"})
                }
                continue

            endpoint = TOOLS[tool]["endpoint"]

            result = await call_wordstat(endpoint, params)

            yield {
                "event": "result",
                "data": json.dumps(result)
            }

    return EventSourceResponse(event_generator())