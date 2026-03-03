import httpx
import json
import os

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL_NAME = "qwen/qwen2.5-3b-instruct:free"

async def stream_response(messages: list):
    api_key = os.getenv("OPENROUTER_API_KEY")
    print(f"DEBUG: api_key present = {bool(api_key)}", flush=True)

    try:
        async with httpx.AsyncClient(timeout=60) as client:
            async with client.stream("POST", OPENROUTER_URL,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": MODEL_NAME,
                    "messages": messages,
                    "stream": True
                }
            ) as response:
                print(f"DEBUG: OpenRouter status = {response.status_code}", flush=True)
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        line = line[6:]
                    if line and line != "[DONE]":
                        try:
                            data = json.loads(line)
                            delta = data["choices"][0]["delta"].get("content")
                            if delta:
                                yield delta
                        except Exception as parse_err:
                            print(f"DEBUG: parse error: {parse_err} | line: {line}", flush=True)
    except Exception as e:
        print(f"ERROR in stream_response: {e}", flush=True)
        raise
