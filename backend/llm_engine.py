import os
import google.generativeai as genai

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

async def stream_response(messages: list):
    genai.configure(api_key=GEMINI_API_KEY)

    system_prompt = ""
    history = []
    last_user_message = ""

    for msg in messages:
        if msg["role"] == "system":
            system_prompt = msg["content"]
        elif msg["role"] == "user":
            last_user_message = msg["content"]
            if history:
                history.append({"role": "user", "parts": [msg["content"]]})
        elif msg["role"] == "assistant":
            history.append({"role": "model", "parts": [msg["content"]]})

    gemini_model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        system_instruction=system_prompt
    )

    chat = gemini_model.start_chat(history=history)
    response = chat.send_message(last_user_message, stream=True)

    for chunk in response:
        if chunk.text:
            yield chunk.text
