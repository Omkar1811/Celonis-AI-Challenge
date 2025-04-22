from fastapi import APIRouter, Depends, HTTPException, status
import uuid
from pydantic import BaseModel
import chromadb
from sentence_transformers import SentenceTransformer
import os
from typing import List, Optional
from app.db.vector_store import VectorStore
from app.core.llm import LLMManager
from app.core.session_manager import SessionManager
# from app.utils.cache_utils import cache_result
from app.utils.logging_config import logger

from app.models.chat import ChatRequest, ChatResponse, SimilarityScore
from app.services.chat_service import ChatService



logger.info("Initializing API router...")
router = APIRouter(tags=["chat"])

# Initialize chat service
logger.info("Initializing chat service...")
chat_service = ChatService()

logger.info("Creating LLM instance...")
llm_manager = LLMManager()  # Using the correct LLMManager from llm.py

logger.info("Creating Vector Store instance...")
vector_store = VectorStore()

# Initialize managers
logger.info("Initializing session manager...")
session_manager = SessionManager(
    gcs_bucket=os.getenv("GCS_BUCKET_NAME"),
    gcs_credentials=os.getenv("GCS_CREDENTIALS_PATH")
)

@router.post("/chat", response_model=ChatResponse)
# @cache_result(ttl=600)  # Cache for 10 minutes
async def chat(chat_request: ChatRequest):
    """
    Process a chat message and return a response.
    
    Args:
        chat_request: The chat request containing the input and optional session ID
        
    Returns:
        ChatResponse: The response from the chatbot
    """
    logger.info(f"Received chat request - Session ID: {chat_request.session_id}")
    logger.info(f"Message: {chat_request.input}")
    
    try:
        # Use the chat service to handle the request
        session_id, response = chat_service.handle_query(
            query=chat_request.input,
            session_id=chat_request.session_id
        )
        
        logger.info(f"Generated response for session {session_id}")
        
        # Get similarity scores from the session manager
        session_data = chat_service.session_manager.get_history(session_id)
        last_interaction = session_data[-1] if session_data else None
        
        similarity_scores = []
        sources = []
        
        if last_interaction and "similarity_scores" in last_interaction:
            for score_data in last_interaction["similarity_scores"]:
                similarity_scores.append(SimilarityScore(
                    content=score_data["content"],
                    score=score_data["score"],
                    source="customer_support_responses",
                    answer=score_data.get("answer", None)  # Try to get answer from metadata
                ))
                sources.append("customer_support_responses")
        
        logger.info(f"Returning response with {len(similarity_scores)} similarity scores")
        return ChatResponse(
            session_id=session_id,
            response=response,
            similarity_scores=similarity_scores,
            sources=sources
        )
    except Exception as e:
        logger.error(f"Error processing chat request: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing chat: {str(e)}"
        )

@router.post("/generate_response", response_model=ChatResponse)
# @cache_result(ttl=1800)  # Cache for 30 minutes
async def generate_response(request: ChatRequest):
    """
    Generate a response for the given chat message.
    
    Args:
        request: ChatRequest containing session_id and message
        
    Returns:
        ChatResponse containing the generated response, similarity scores, and sources
    """
    logger.info(f"Generating response for session {request.session_id}")
    logger.info(f"Message: {request.input}")
    
    try:
        # Get relevant documents from vector store
        logger.info("Searching vector store for relevant documents...")
        search_results = vector_store.search(request.input)
        
        # Format similarity scores with metadata
        formatted_scores = []
        sources = []
        
        for doc, score in zip(search_results['documents'][0], search_results['distances'][0]):
            formatted_scores.append({
                "text": doc,
                "score": float(score),
                "answer": search_results['metadatas'][0][search_results['documents'][0].index(doc)].get('answer', 'No answer available')
            })
            sources.append("customer_support_responses")
        
        logger.info(f"Found {len(formatted_scores)} relevant documents")
        
        # Generate response using LLM
        logger.info("Generating response using LLM...")
        response = llm_manager.generate_response(
            query=request.input,
            context=formatted_scores
        )
        
        # Store the interaction
        logger.info("Storing interaction in session manager...")
        session_manager.add_interaction(
            session_id=request.session_id,
            user_input=request.input,
            ai_response=response,
            similarity_scores=formatted_scores
        )
        
        logger.info("Response generation complete")
        return ChatResponse(
            session_id=request.session_id,
            response=response,
            similarity_scores=[
                SimilarityScore(
                    content=score["text"],
                    score=score["score"],
                    source="customer_support_responses",
                    answer=score["answer"]
                ) for score in formatted_scores
            ],
            sources=sources
        )
        
    except Exception as e:
        logger.error(f"Error generating response: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error generating response: {str(e)}"
        )

@router.post("/new_session", response_model=ChatResponse)
async def new_session():
    """
    Create a new chat session.
    
    Returns:
        ChatResponse: A response with a new session ID
    """
    try:
        logger.info("Creating new session...")
        session_id = str(uuid.uuid4())
        logger.info(f"New session created with ID: {session_id}")
        return ChatResponse(
            session_id=session_id,
            response="New session created. How can I help you today?",
            sources=[]
        )
    except Exception as e:
        logger.error(f"Error creating new session: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating new session: {str(e)}"
        )

@router.get("/health")
async def health_check():
    """Check if the API is healthy"""
    logger.info("API health check requested")
    try:
        logger.info("Checking LLM health...")
        llm_manager.health_check()  # Using LLMManager health check
        logger.info("LLM is healthy")
        
        logger.info("Checking Vector Store health...")
        vector_store.health_check()
        logger.info("Vector Store is healthy")
        
        return {"status": "healthy"}
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 