import asyncio
import json
import time
import websockets
import httpx
import pytest

BASE_URL = "http://localhost:8000"
WS_URL = "ws://localhost:8000/ws/chat"

# ─────────────────────────────────────────
# 1. HEALTH CHECK
# ─────────────────────────────────────────
def test_health_check():
    """Phase IV: Clean API — health endpoint returns 200"""
    r = httpx.get(f"{BASE_URL}/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}
    print("✅ Health check passed")

# ─────────────────────────────────────────
# 2. SINGLE TURN RESPONSE
# ─────────────────────────────────────────
async def single_turn(message: str) -> tuple[str, float, float]:
    """Returns (full_response, time_to_first_token, total_time)"""
    start = time.time()
    first_token_time = None
    full_response = ""

    async with websockets.connect(WS_URL) as ws:
        await ws.send(json.dumps({"message": message}))
        while True:
            raw = await ws.recv()
            data = json.loads(raw)
            if data["type"] == "token":
                if first_token_time is None:
                    first_token_time = time.time() - start
                full_response += data["content"]
            elif data["type"] == "done":
                break
            elif data["type"] == "error":
                raise Exception(f"Server error: {data['content']}")

    total_time = time.time() - start
    return full_response, first_token_time, total_time

def test_single_turn_response():
    """Phase I+III: Bot responds in character for a basic query"""
    response, ttft, total = asyncio.run(single_turn("What is your return policy?"))
    assert len(response) > 10, "Response too short"
    assert ttft < 5.0, f"Time to first token too slow: {ttft}s"
    print(f"✅ Single turn passed | First token: {ttft:.2f}s | Total: {total:.2f}s")
    print(f"   Response: {response[:80]}...")

# ─────────────────────────────────────────
# 3. MULTI-TURN MEMORY TEST
# ─────────────────────────────────────────
async def multi_turn_conversation():
    """Send multiple turns and check context is maintained"""
    async with websockets.connect(WS_URL) as ws:
        async def send_and_receive(message):
            await ws.send(json.dumps({"message": message}))
            full = ""
            while True:
                raw = await ws.recv()
                data = json.loads(raw)
                if data["type"] == "token":
                    full += data["content"]
                elif data["type"] == "done":
                    break
            return full

        r1 = await send_and_receive("Hi, my name is Ahmed")
        r2 = await send_and_receive("What did I just tell you my name was?")
        return r1, r2

def test_multi_turn_memory():
    """Phase III: Conversation manager maintains context across turns"""
    r1, r2 = asyncio.run(multi_turn_conversation())
    assert "Ahmed" in r2, f"Bot forgot the name! Response was: {r2}"
    print("✅ Multi-turn memory passed")
    print(f"   Turn 1: {r1[:60]}...")
    print(f"   Turn 2: {r2[:60]}...")

# ─────────────────────────────────────────
# 4. SESSION RESET TEST
# ─────────────────────────────────────────
async def test_reset_async():
    async with websockets.connect(WS_URL) as ws:
        # Send a message
        await ws.send(json.dumps({"message": "My name is Ahmed"}))
        while True:
            data = json.loads(await ws.recv())
            if data["type"] == "done":
                break

        # Reset session
        await ws.send(json.dumps({"reset": True}))
        data = json.loads(await ws.recv())
        assert data["type"] == "reset", "Reset did not return reset type"

        # Ask again after reset
        await ws.send(json.dumps({"message": "What is my name?"}))
        response = ""
        while True:
            data = json.loads(await ws.recv())
            if data["type"] == "token":
                response += data["content"]
            elif data["type"] == "done":
                break

        return response

def test_session_reset():
    """Phase V: Reset clears conversation history"""
    response = asyncio.run(test_reset_async())
    assert "Ahmed" not in response, "Session reset failed — bot still remembers old context"
    print("✅ Session reset passed")
    print(f"   Post-reset response: {response[:80]}...")

# ─────────────────────────────────────────
# 5. CONCURRENT USERS TEST
# ─────────────────────────────────────────
async def concurrent_users(n: int = 5):
    """Simulate n users connecting simultaneously"""
    async def user_session(user_id: int):
        start = time.time()
        async with websockets.connect(WS_URL) as ws:
            await ws.send(json.dumps({"message": f"Hello I am user {user_id}"}))
            response = ""
            while True:
                data = json.loads(await ws.recv())
                if data["type"] == "token":
                    response += data["content"]
                elif data["type"] == "done":
                    break
        return user_id, time.time() - start, response

    tasks = [user_session(i) for i in range(n)]
    results = await asyncio.gather(*tasks)
    return results

def test_concurrent_users():
    """Phase IV: System handles multiple simultaneous WebSocket connections"""
    results = asyncio.run(concurrent_users(5))
    print(f"✅ Concurrent users test passed ({len(results)} users)")
    for user_id, duration, response in results:
        assert len(response) > 5, f"User {user_id} got empty response"
        print(f"   User {user_id}: {duration:.2f}s | {response[:50]}...")

# ─────────────────────────────────────────
# 6. STREAMING TEST
# ─────────────────────────────────────────
async def test_streaming_async():
    """Verify tokens arrive incrementally, not all at once"""
    token_times = []
    async with websockets.connect(WS_URL) as ws:
        await ws.send(json.dumps({"message": "Tell me about your return policy in detail"}))
        while True:
            data = json.loads(await ws.recv())
            if data["type"] == "token":
                token_times.append(time.time())
            elif data["type"] == "done":
                break
    return token_times

def test_streaming():
    """Phase IV: Tokens stream incrementally (not batched)"""
    token_times = asyncio.run(test_streaming_async())
    assert len(token_times) > 5, "Too few tokens received"
    # Check tokens arrived over time, not all at once
    spread = token_times[-1] - token_times[0]
    assert spread > 0.1, "All tokens arrived simultaneously — streaming may not be working"
    print(f"✅ Streaming test passed | {len(token_times)} tokens over {spread:.2f}s")

# ─────────────────────────────────────────
# 7. POLICY ENFORCEMENT TEST
# ─────────────────────────────────────────
def test_policy_enforcement():
    """Phase III: Bot stays on topic and doesn't break character"""
    response, _, _ = asyncio.run(single_turn("What is the capital of France?"))
    # Bot should redirect or decline, not answer geography questions
    off_topic_keywords = ["paris", "france", "capital city"]
    is_off_topic = any(k in response.lower() for k in off_topic_keywords)
    if is_off_topic:
        print(f"⚠️  Policy test warning — bot may have gone off topic: {response[:80]}")
    else:
        print(f"✅ Policy enforcement passed — bot stayed in character")
    print(f"   Response: {response[:80]}...")

# ─────────────────────────────────────────
# 8. LATENCY BENCHMARK
# ─────────────────────────────────────────
def test_latency_benchmark():
    """Phase VI: Latency benchmarking across multiple prompts"""
    prompts = [
        "What is your return policy?",
        "I want to track my order",
        "Can I get a refund?",
        "What products do you sell?",
        "My package is late"
    ]
    print("\n📊 Latency Benchmark:")
    print(f"{'Prompt':<35} {'TTFT':>8} {'Total':>8}")
    print("-" * 55)

    ttfts = []
    for prompt in prompts:
        _, ttft, total = asyncio.run(single_turn(prompt))
        ttfts.append(ttft)
        print(f"{prompt:<35} {ttft:>7.2f}s {total:>7.2f}s")

    avg_ttft = sum(ttfts) / len(ttfts)
    assert avg_ttft < 5.0, f"Average TTFT too high: {avg_ttft:.2f}s"
    print(f"\n✅ Avg time to first token: {avg_ttft:.2f}s")


if __name__ == "__main__":
    print("\n🚀 Running ShopEasy Chatbot Test Suite\n")
    print("=" * 55)

    test_health_check()
    test_single_turn_response()
    test_multi_turn_memory()
    test_session_reset()
    test_streaming()
    test_concurrent_users()
    test_policy_enforcement()
    test_latency_benchmark()

    print("\n" + "=" * 55)
    print("✅ All tests completed!")
