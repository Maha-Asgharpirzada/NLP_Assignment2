#!/bin/bash
ollama serve &
sleep 5
ollama pull qwen2.5:0.5b
uvicorn main:app --host 0.0.0.0 --port 8000
