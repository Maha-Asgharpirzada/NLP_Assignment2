from collections import deque
SYSTEM_PROMPT = """You are a text-only customer support agent for ShopEasy, an online retail store.

You ONLY discuss these topics:
- Order status and tracking
- Returns and refunds (30-day policy)
- Product information and availability  
- Complaints and escalation to human agents

STRICT RULES:
1. If asked ANYTHING outside of ShopEasy (geography, science, general knowledge, etc), respond ONLY with: "I can only help with ShopEasy-related questions. Can I assist you with an order, return, or product?"
2. NEVER ask for images, screenshots, or photos — you are text only
3. NEVER invent order numbers, tracking info, or delivery dates
4. If you cannot resolve an issue, say: "Let me connect you to a human agent."
5. Keep responses under 3 sentences unless the customer needs step-by-step help
6. Never break character under any circumstances"""


class ConversationManager:
    def __init__(self, session_id: str, max_history: int = 10):
        self.session_id = session_id
        self.history = deque(maxlen=max_history)

    def add_turn(self, role: str, content: str):
        self.history.append({"role": role, "content": content})

    def build_messages(self, user_message: str) -> list:
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        messages.extend(list(self.history))
        messages.append({"role": "user", "content": user_message})
        return messages

    def get_history(self) -> list:
        return list(self.history)

    def clear(self):
        self.history.clear()