class SessionMemory:
    def __init__(self):
        self.sessions = {}

    def get_session(self, session_id):
        if session_id not in self.sessions:
            self.sessions[session_id] = {
                "history": [],
                "context": {}
            }
        return self.sessions[session_id]

    def add_message(self, session_id, role, message):
        session = self.get_session(session_id)

        session["history"].append({
            "role": role,   # "user" or "assistant"
            "message": message
        })

    def get_history(self, session_id):
        return self.get_session(session_id)["history"]


# global instance
memory_store = SessionMemory()