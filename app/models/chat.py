from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Union


class SimilarityScore(BaseModel):
    """Model for a document similarity score result."""
    content: str = Field(..., description="The content of the document")
    score: float = Field(..., description="The similarity score")
    source: Optional[str] = Field(None, description="The source of the document")
    answer: Optional[str] = Field(None, description="The answer associated with this document")


class ChatRequest(BaseModel):
    """Chat request model."""
    input: str = Field(..., description="The input from the user")
    session_id: Optional[str] = Field(None, description="Session ID for the chat. If None, a new session will be created")


class ChatResponse(BaseModel):
    """Chat response model."""
    session_id: str = Field(..., description="Session ID for the chat")
    response: str = Field(..., description="The response from the LLM")
    similarity_scores: List[SimilarityScore] = Field(default_factory=list, description="List of similarity scores for the documents retrieved")
    sources: List[str] = Field(default_factory=list, description="List of document sources") 