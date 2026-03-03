import os
from google import genai
from google.genai import types

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

async def stream_response(messages: list):
    system_prompt = ""
    history = []
    last_user_message = ""

    for msg in messages:
        if msg["role"] == "system":
            system_prompt = msg["content"]
        elif msg["role"] == "user":
            last_user_message = msg["content"]
        elif msg["role"] == "assistant":
            history.append(types.Content(role="model", parts=[types.Part(text=msg["content"])]))

    response = client.models.generate_content_stream(
        model="gemini-2.0-flash",
        contents=last_user_message,
        config=types.GenerateContentConfig(system_instruction=system_prompt)
    )

    for chunk in response:
        if chunk.text:
            yield chunk.text
