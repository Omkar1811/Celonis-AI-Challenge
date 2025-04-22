import os
from app.utils.data_loader import load_data_from_csv
from app.db.vector_store import VectorStore


def initialize_vector_store(csv_file_path):
    """
    Initialize the vector store with data from the CSV file.
    
    Args:
        csv_file_path: Path to the CSV file
        
    Returns:
        bool: True if initialization was successful, False otherwise
    """
    try:
        # Check if the CSV file exists
        if not os.path.exists(csv_file_path):
            print(f"CSV file not found: {csv_file_path}")
            return False
        
        # Load documents from CSV
        documents = load_data_from_csv(csv_file_path)
        if not documents:
            print("No documents loaded from CSV file")
            return False
        
        print(f"Loaded {len(documents)} documents from CSV file")
        
        # Initialize vector store
        vector_store = VectorStore()
        vector_store.add_documents(documents)
        
        print("Vector store initialized successfully")
        return True
    except Exception as e:
        print(f"Error initializing vector store: {e}")
        return False


if __name__ == "__main__":
    # Default CSV file path
    default_csv_path = "data/final_data.csv"
    
    # Check if environment variable is set
    csv_path = os.environ.get("CSV_FILE_PATH", default_csv_path)
    
    # Initialize vector store
    success = initialize_vector_store(csv_path)
    
    if success:
        print("Setup completed successfully")
    else:
        print("Setup failed") 