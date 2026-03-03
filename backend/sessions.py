from conversation_manager import ConversationManager

sessions: dict[str, ConversationManager] = {}

def get_or_create_session(session_id: str) -> ConversationManager:
    if session_id not in sessions:
        sessions[session_id] = ConversationManager(session_id)
    return sessions[session_id]

def delete_session(session_id: str):
    sessions.pop(session_id, None)