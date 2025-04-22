from google.cloud import storage
import os
from typing import Optional

class GCSManager:
    """Manager for Google Cloud Storage operations."""
    
    def __init__(self, bucket_name: str, credentials_path: Optional[str] = None):
        """
        Initialize the GCS manager.
        
        Args:
            bucket_name: Name of the GCS bucket
            credentials_path: Path to the service account key file
        """
        if credentials_path:
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "credentials.json"
        
        self.bucket_name = bucket_name
        self.storage_client = storage.Client()
        self.bucket = self.storage_client.bucket(bucket_name)
        
    def upload_file(self, source_file_path: str, destination_blob_name: str) -> bool:
        """
        Upload a file to GCS.
        
        Args:
            source_file_path: Path to the local file
            destination_blob_name: Name of the blob in GCS
            
        Returns:
            bool: True if upload was successful, False otherwise
        """
        try:
            blob = self.bucket.blob(destination_blob_name)
            blob.upload_from_filename(source_file_path)
            return True
        except Exception as e:
            print(f"Error uploading to GCS: {str(e)}")
            return False 