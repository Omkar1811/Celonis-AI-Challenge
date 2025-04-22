import uuid
from operator import itemgetter
from langchain.schema.runnable import RunnablePassthrough, RunnableLambda
from langchain.schema.output_parser import StrOutputParser
from typing import List, Tuple, Optional

from app.core.session_manager import SessionManager
from app.core.llm import LLMManager
from app.db.vector_store import VectorStore
from app.core.prompts import get_rag_prompt_template


class ChatService:
    """Service for handling chat interactions."""
    
    def __init__(self):
        """Initialize the chat service with necessary components."""
        self.session_manager = SessionManager()
        self.vector_store = VectorStore()
        self.llm_manager = LLMManager()
        self.llm = self.llm_manager.get_llm()
        self.retriever = self.vector_store.get_retriever(k=5)
        self.qa_chain = self._create_qa_chain()
        
    def _create_qa_chain(self):
        """Create the question-answering chain."""
        rag_prompt_template = get_rag_prompt_template()
        
        return (
            {
                "context": itemgetter("question") | self.retriever,
                "question": itemgetter("question"),
                "chat_history": RunnableLambda(lambda x: self.session_manager.get_history(x["session_id"]))
            }
            | rag_prompt_template
            | self.llm
            | StrOutputParser()
        )
    
    def get_similar_documents(self, query: str, k: int = 5) -> List[Tuple]:
        """
        Retrieve documents similar to the query with their similarity scores.
        
        Args:
            query: The query to search for
            k: Number of documents to retrieve
            
        Returns:
            List of (document, score) tuples
        """
        return self.vector_store.similarity_search_with_score(query, k=k)
    
    def handle_query(self, query, session_id=None):
        """
        Handle a chat query.
        
        Args:
            query: The user's question
            session_id: Optional session ID. If None, a new session will be created.
            
        Returns:
            tuple: (session_id, response)
        """
        # Generate new session ID if none provided
        if not session_id:
            session_id = str(uuid.uuid4())
        
        # Get similar documents with scores
        docs_and_scores = self.get_similar_documents(query)
            
        # Get response from QA chain
        result = self.qa_chain.invoke({
            "question": query,
            "session_id": session_id
        })
        
        # Store interaction with similarity scores
        self.session_manager.add_interaction(session_id, query, result, docs_and_scores)
        
        return session_id, result 