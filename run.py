import uvicorn
from app.main import app
from app.db.vector_store import VectorStore
from app.utils.data_loader import load_csv_data
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    try:
        # Initialize vector store
        logger.info("Initializing vector store...")
        vector_store = VectorStore()
        
        # Load data from CSV
        csv_path = os.path.join("data", "final_data.csv")
        logger.info(f"Loading data from {csv_path}...")
        
        if not os.path.exists(csv_path):
            logger.error(f"CSV file not found at {csv_path}")
            # Optionally create dummy data or handle this case
            # For now, we proceed assuming the store might exist or be populated later
        else:
            documents = load_csv_data(csv_path)
            logger.info(f"Loaded {len(documents)} documents from CSV.")
            vector_store.add_documents(documents)
        
        # Start FastAPI server
        logger.info("Starting FastAPI server...")
        uvicorn.run(
            "app.main:app",
            host="0.0.0.0",
            port=8000,
            reload=True
        )
        
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    main() 