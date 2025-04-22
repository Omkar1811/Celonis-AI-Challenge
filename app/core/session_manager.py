import os
import csv
import re
import uuid
import json
from datetime import datetime
from collections import defaultdict
from typing import List, Dict, Any, Optional
from operator import itemgetter
from app.utils.gcs_utils import GCSManager
from app.utils.logging_utils import SessionLogger

class SessionManager:
    """Manager for chat sessions."""
    
    def __init__(self, csv_file="chat_history.csv", gcs_bucket: Optional[str] = None, gcs_credentials: Optional[str] = None):
        """Initialize the session manager."""
        self.sessions = defaultdict(list)
        self.csv_file = csv_file
        self._initialize_csv()
        
        # Initialize GCS manager if bucket name is provided
        self.gcs_manager = None
        if gcs_bucket:
            self.gcs_manager = GCSManager(bucket_name=gcs_bucket, credentials_path=gcs_credentials)
            
        # Initialize session logger
        self.logger = SessionLogger()
        
    def _initialize_csv(self):
        """Initialize the CSV file if it doesn't exist."""
        if not os.path.exists(self.csv_file):
            with open(self.csv_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["session_id", "user_input", "ai_response", "timestamp", "similarity_scores"])
                
    def get_history(self, session_id):
        """Get the chat history for the specified session."""
        return self.sessions[session_id]
    
    def add_interaction(self, session_id: str, user_input: str, ai_response: str, similarity_scores: Optional[List[tuple]] = None):
        """
        Add an interaction to the session.
        
        Args:
            session_id: The session ID
            user_input: The user's input
            ai_response: The AI's response
            similarity_scores: Optional list of (document, score) tuples from similarity search
        """
        try:
            # Clean the response if needed
            cleaned_response = self._clean_response(ai_response)
            self._store_interaction(session_id, user_input, cleaned_response, similarity_scores)
            
            # Log the interaction
            self.logger.log_interaction(session_id, user_input, cleaned_response, similarity_scores)
            
            # Upload to GCS if configured
            if self.gcs_manager:
                self._upload_to_gcs()
                
            return cleaned_response
        except Exception as e:
            self.logger.log_error(session_id, str(e))
            raise
            
    def _upload_to_gcs(self):
        """Upload the chat history CSV to GCS."""
        if not self.gcs_manager:
            return
            
        try:
            # Always upload the same file name
            destination_blob_name = "chat_history.csv"
            
            # Upload the file
            success = self.gcs_manager.upload_file(self.csv_file, destination_blob_name)
            if success:
                print(f"Successfully uploaded chat history to GCS: {destination_blob_name}")
            else:
                print("Failed to upload chat history to GCS")
        except Exception as e:
            print(f"Error uploading to GCS: {str(e)}")
            
    def _clean_response(self, response):
        """Clean the response if needed (e.g., remove model-specific artifacts)."""
        # Try to match both formats
        prefixes = [
            "**Response:**", 
            "**Response:** ",
            "Response:",
            "**Response** ",
            "Response: ",
            "Answer:",
            "Answer: "
        ]
        
        # Try removing each prefix
        cleaned = response
        for prefix in prefixes:
            if cleaned.startswith(prefix):
                cleaned = cleaned[len(prefix):].strip()
                break
                
        return cleaned
    
    def _write_to_csv(self, session_id, user_input, ai_response, timestamp, similarity_scores=None):
        """Write the interaction to the CSV file."""
        # Convert similarity scores to JSON for storage
        scores_json = ""
        if similarity_scores:
            # Format scores as a list of dicts with content, score, and answer
            formatted_scores = [
                {
                    "content": doc.page_content, 
                    "score": float(score),
                    "answer": doc.metadata.get("answer", None)
                }
                for doc, score in similarity_scores
            ]
            scores_json = json.dumps(formatted_scores)
            
        with open(self.csv_file, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([session_id, user_input, ai_response, timestamp, scores_json])
            
    def _store_interaction(self, session_id, user_input, ai_response, similarity_scores=None):
        """Store the interaction in memory and in the CSV file."""
        timestamp = datetime.now().isoformat()
        
        # Store in memory
        session_data = {
            "user": user_input,
            "ai": ai_response,
            "timestamp": timestamp
        }
        
        # Add similarity scores if available
        if similarity_scores:
            session_data["similarity_scores"] = [
                {
                    "content": doc.page_content, 
                    "score": float(score),
                    "answer": doc.metadata.get("answer", None)  # Get answer from metadata
                }
                for doc, score in similarity_scores
            ]
            
        self.sessions[session_id].append(session_data)
        
        # Write to CSV
        self._write_to_csv(session_id, user_input, ai_response, timestamp, similarity_scores)
        
    def create_new_session(self):
        """Create a new session."""
        # Upload current chat history before creating new session
        if self.gcs_manager:
            self._upload_to_gcs()
            
        session_id = str(uuid.uuid4())
        # Log the new session creation
        self.logger.log_session_creation(session_id)
        return session_id 