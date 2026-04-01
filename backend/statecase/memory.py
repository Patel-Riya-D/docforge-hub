class SessionMemory:
    """
    In-memory session manager for storing conversational data per session.

    This class maintains a dictionary of sessions, where each session contains:
    - history: List of chat messages (user & assistant)
    - context: Additional metadata for the session (e.g., filters, document info)

    Primarily used for fast access during runtime. Not persistent.
    """

    def __init__(self):
        """
        Initialize the session memory store.
        """
        self.sessions = {}

    def get_session(self, session_id):
        """
        Retrieve or initialize a session.

        Args:
            session_id (str): Unique identifier for the session.

        Returns:
            dict: Session object containing:
                - history (list): List of message dictionaries
                - context (dict): Session-specific metadata
        """
        if session_id not in self.sessions:
            self.sessions[session_id] = {
                "history": [],
                "context": {}
            }
        return self.sessions[session_id]

    def add_message(self, session_id, role, message):
        """
        Add a message to the session history.

        Args:
            session_id (str): Unique session identifier
            role (str): Role of the sender ("user" or "assistant")
            message (str): Message content

        Returns:
            None
        """
        session = self.get_session(session_id)

        session["history"].append({
            "role": role,
            "message": message
        })

    def get_history(self, session_id):
        """
        Retrieve conversation history for a session.

        Args:
            session_id (str): Unique session identifier

        Returns:
            list: List of message dictionaries in chronological order
        """
        return self.get_session(session_id)["history"]


# global instance
memory_store = SessionMemory()