import os
from google import genai

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

async def stream_response(messages: list):
    client = genai.Client(api_key=GEMINI_API_KEY)

    system_prompt = ""
    history = []
    last_user_message = ""

    for msg in messages:
        if msg["role"] == "system":
            system_prompt = msg["content"]
        elif msg["role"] == "user":
            last_user_message = msg["content"]
        elif msg["role"] == "assistant":
            history.append({"role": "model", "parts": [{"text": msg["content"]}]})
            history.append({"role": "user", "parts": [{"text": "ok"}]})

    response = client.models.generate_content_stream(
        model="gemini-2.0-flash",
        contents=last_user_message,
        config={"system_instruction": system_prompt}
    )

    for chunk in response:
        if chunk.text:
            yield chunk.text
