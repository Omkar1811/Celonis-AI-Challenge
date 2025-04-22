import pandas as pd
from langchain.schema import Document
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)

def load_csv_data(file_path: str) -> List[Document]:
    """
    Load data from a CSV file and convert it to a list of Document objects.
    
    Args:
        file_path: Path to the CSV file
        
    Returns:
        List of Document objects
    """
    try:
        logger.info(f"Reading CSV file: {file_path}")
        df = pd.read_csv(file_path)
        
        # Check if required columns exist
        required_columns = ["input", "output"]
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            raise ValueError(f"CSV file is missing required columns: {missing_columns}")
        
        # Convert DataFrame rows to Document objects
        logger.info(f"Converting {len(df)} rows to Document objects")
        documents = [
            Document(
                page_content=row["input"],
                metadata={"answer": row["output"]}
            )
            for _, row in df.iterrows()
        ]
        
        logger.info(f"Successfully created {len(documents)} Document objects")
        return documents
        
    except Exception as e:
        logger.error(f"Error loading data from CSV: {str(e)}", exc_info=True)
        raise 