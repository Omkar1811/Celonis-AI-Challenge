import os
import logging
from datetime import datetime
from typing import Optional

class SessionLogger:
    """Utility class for logging session activities."""
    
    def __init__(self, log_file: str = "logger.txt"):
        """Initialize the session logger."""
        self.log_file = log_file
        self._setup_logger()
        
    def _setup_logger(self):
        """Set up the logger with file handler."""
        # Create logs directory if it doesn't exist
        os.makedirs("logs", exist_ok=True)
        
        # Configure the logger
        self.logger = logging.getLogger("session_logger")
        self.logger.setLevel(logging.INFO)
        
        # Create file handler
        file_handler = logging.FileHandler(os.path.join("logs", self.log_file))
        file_handler.setLevel(logging.INFO)
        
        # Create formatter
        formatter = logging.Formatter('%(asctime)s - Session: %(session_id)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        
        # Add handler to logger
        self.logger.addHandler(file_handler)
        
    def log_session_creation(self, session_id: str):
        """Log when a new session is created."""
        self.logger.info("New session created", extra={"session_id": session_id})
        
    def log_interaction(self, session_id: str, user_input: str, ai_response: str, similarity_scores: Optional[list] = None):
        """Log a chat interaction."""
        log_data = {
            "user_input": user_input,
            "ai_response": ai_response,
            "similarity_scores": similarity_scores if similarity_scores else []
        }
        self.logger.info(
            f"Chat interaction: {log_data}",
            extra={"session_id": session_id}
        )
        
    def log_error(self, session_id: str, error_message: str):
        """Log an error related to a session."""
        self.logger.error(
            f"Error occurred: {error_message}",
            extra={"session_id": session_id}
        ) 