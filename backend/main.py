from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from sessions import get_or_create_session, delete_session
from llm_engine import stream_response
import json, uuid

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.websocket("/ws/chat")
async def chat_endpoint(websocket: WebSocket):
    await websocket.accept()
    session_id = str(uuid.uuid4())

    try:
        while True:
            data = await websocket.receive_text()
            payload = json.loads(data)

            if payload.get("reset"):
                delete_session(session_id)
                session_id = str(uuid.uuid4())
                await websocket.send_text(json.dumps({"type": "reset"}))
                continue

            user_msg = payload.get("message", "").strip()
            if not user_msg:
                continue

            manager = get_or_create_session(session_id)
            messages = manager.build_messages(user_msg)

            full_response = ""
            async for token in stream_response(messages):
                full_response += token
                await websocket.send_text(json.dumps({"type": "token", "content": token}))

            manager.add_turn("user", user_msg)
            manager.add_turn("assistant", full_response)
            await websocket.send_text(json.dumps({"type": "done"}))

    except WebSocketDisconnect:
        delete_session(session_id)
    except Exception as e:
        await websocket.send_text(json.dumps({"type": "error", "content": str(e)}))