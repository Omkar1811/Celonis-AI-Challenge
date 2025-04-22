from langchain.vectorstores import Chroma
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.schema import Document
import os
from typing import List, Tuple
import logging

logger = logging.getLogger(__name__)

class VectorStore:
    """Vector store for document retrieval."""
    
    def __init__(self, persist_directory="chromadb_store", collection_name="customer_support_responses"):
        """Initialize the vector store with the specified embedding model."""
        self.persist_directory = persist_directory
        self.collection_name = collection_name
        self.embedding_model = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        
        # Create the persist directory if it doesn't exist
        os.makedirs(self.persist_directory, exist_ok=True)
        
        # Initialize the vector store
        self.db = Chroma(
            persist_directory=self.persist_directory,
            embedding_function=self.embedding_model,
            collection_name=self.collection_name
        )
        
        # Log the collection count on initialization
        try:
            collection_count = self.db._collection.count()
            logger.info(f"Vector store initialized with {collection_count} documents")
            print(f"Vector store initialized with {collection_count} documents")
        except Exception as e:
            logger.warning(f"Could not get collection count: {str(e)}")
            print(f"WARNING: Could not get collection count: {str(e)}")
    
    def add_documents(self, documents: List[Document]):
        documents=documents[:2000]
        """Add documents to the vector store in batches to avoid size limits."""
        try:
            # ChromaDB has a batch size limit of 41666 documents
            MAX_BATCH_SIZE = 20000  # Using 40k to be safe
            total_docs = len(documents)
            
            logger.info(f"Adding {total_docs} documents to Chroma vector store in batches...")
            print(f"Adding {total_docs} documents to Chroma vector store in batches...")
            
            # Process first batch to initialize or use existing collection
            first_batch_size = min(MAX_BATCH_SIZE, total_docs)
            first_batch = documents[:first_batch_size]
            
            # For the first batch, either initialize or add to the existing collection
            if hasattr(self, 'db') and self.db is not None:
                # If db already exists, add documents to it
                self.db.add_documents(documents=first_batch)
            else:
                # Initialize the db with the first batch
                self.db = Chroma.from_documents(
                    documents=first_batch,
                    embedding=self.embedding_model,
                    persist_directory=self.persist_directory,
                    collection_name=self.collection_name
                )
            
            # Log progress
            progress = min(first_batch_size / total_docs * 100, 100)
            logger.info(f"Progress: {progress:.2f}% ({first_batch_size}/{total_docs} documents processed)")
            print(f"Progress: {progress:.2f}% ({first_batch_size}/{total_docs} documents processed)")
            
            # Process remaining batches
            for i in range(first_batch_size, total_docs, MAX_BATCH_SIZE):
                end_idx = min(i + MAX_BATCH_SIZE, total_docs)
                batch = documents[i:end_idx]
                batch_size = len(batch)
                
                logger.info(f"Processing batch {i//MAX_BATCH_SIZE + 1}: documents {i+1} to {end_idx} ({batch_size} documents)")
                print(f"Processing batch {i//MAX_BATCH_SIZE + 1}: documents {i+1} to {end_idx} ({batch_size} documents)")
                
                # Add this batch to the existing db
                self.db.add_documents(documents=batch)
                
                # Optionally persist after each batch for safety
                # self.db.persist()
                
                # Log progress
                progress = min(end_idx / total_docs * 100, 100)
                logger.info(f"Progress: {progress:.2f}% ({end_idx}/{total_docs} documents processed)")
                print(f"Progress: {progress:.2f}% ({end_idx}/{total_docs} documents processed)")
            
            # Persist the database
            self.db.persist()
            logger.info("All documents added successfully and database persisted")
            print("All documents added successfully and database persisted")
            
            # Verify document count after adding
            try:
                collection_count = self.db._collection.count()
                logger.info(f"Vector store now contains {collection_count} documents")
                print(f"Vector store now contains {collection_count} documents")
            except Exception as e:
                logger.warning(f"Could not verify document count: {str(e)}")
                print(f"WARNING: Could not verify document count: {str(e)}")
                
        except Exception as e:
            logger.error(f"Error adding documents: {str(e)}", exc_info=True)
            print(f"ERROR: Failed to add documents: {str(e)}")
            raise
        
    def get_retriever(self, k=5):
        """Get a retriever for the vector store."""
        print(f"\nGetting retriever with k={k}")
        try:
            retriever = self.db.as_retriever(search_kwargs={"k": k})
            print("Retriever created successfully")
            return retriever
        except Exception as e:
            print(f"ERROR creating retriever: {str(e)}")
            logger.error(f"Error creating retriever: {str(e)}", exc_info=True)
            raise
    
    def get_similar_documents(self, query: str, k: int = 5) -> List[Tuple[Document, float]]:
        """Get similar documents using the retriever."""
        print(f"\nGetting similar documents for query: '{query}'")
        print(f"Looking for top {k} matches")
        
        try:
            # Get the retriever
            retriever = self.get_retriever(k=k)
            
            # Get documents using the retriever
            print("Retrieving documents...")
            docs = retriever.get_relevant_documents(query)
            
            # Log results
            print(f"Found {len(docs)} results")
            if docs:
                for i, doc in enumerate(docs):
                    print(f"Result {i+1}:")
                    print(f"  Content: {doc.page_content[:100]}...")  # Print first 100 chars
                    print(f"  Metadata: {doc.metadata}")
            
            return docs
        except Exception as e:
            print(f"ERROR getting similar documents: {str(e)}")
            logger.error(f"Error getting similar documents: {str(e)}", exc_info=True)
            return []

    def similarity_search(self, query, k=5):
        """Perform a similarity search for the given query."""
        print(f"\nPerforming similarity search for query: '{query}'")
        print(f"Looking for top {k} matches")
        
        try:
            # First check if we have documents
            try:
                collection_count = self.db._collection.count()
                print(f"Current document count in vector store: {collection_count}")
                if collection_count == 0:
                    print("WARNING: Vector store is empty! No documents to search.")
                    return []
            except Exception as e:
                print(f"WARNING: Could not get collection count: {str(e)}")
            
            # Generate embedding for the query (for debugging)
            print("Generating embedding for the query...")
            query_embedding = self.embedding_model.embed_query(query)
            embedding_dimension = len(query_embedding)
            print(f"Query embedding generated successfully. Dimension: {embedding_dimension}")
            
            # Perform the search
            print("Executing similarity search...")
            results = self.db.similarity_search(query, k=k)
            
            # Log results
            print(f"Found {len(results)} results")
            if results:
                for i, doc in enumerate(results):
                    print(f"Result {i+1}:")
                    print(f"  Content: {doc.page_content[:100]}...")  # Print first 100 chars
                    print(f"  Metadata: {doc.metadata}")
                
            return results
        except Exception as e:
            print(f"ERROR in similarity search: {str(e)}")
            logger.error(f"Error in similarity search: {str(e)}", exc_info=True)
            return []
            
    def similarity_search_with_score(self, query, k=5):
        """Perform a similarity search with scores for the given query."""
        print(f"\nPerforming similarity search with scores for query: '{query}'")
        print(f"Looking for top {k} matches")
        
        try:
            # First check if we have documents
            try:
                collection_count = self.db._collection.count()
                print(f"Current document count in vector store: {collection_count}")
                if collection_count == 0:
                    print("WARNING: Vector store is empty! No documents to search.")
                    return []
            except Exception as e:
                print(f"WARNING: Could not get collection count: {str(e)}")
            
            # Perform the search with scores
            print("Executing similarity_search_with_score...")
            docs_and_scores = self.db.similarity_search_with_score(query, k=k)
            
            # Log results
            print(f"Found {len(docs_and_scores)} results")
            if docs_and_scores:
                for i, (doc, score) in enumerate(docs_and_scores):
                    print(f"Result {i+1}: Score = {score}")
                    print(f"  Content: {doc.page_content[:100]}...")  # Print first 100 chars
                    print(f"  Metadata: {doc.metadata}")
                
            return docs_and_scores
        except Exception as e:
            print(f"ERROR in similarity search with score: {str(e)}")
            logger.error(f"Error in similarity search with score: {str(e)}", exc_info=True)
            return [] 