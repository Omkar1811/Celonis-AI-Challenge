from pydantic import BaseModel, Field
from typing import Dict, Any, Optional


class Document(BaseModel):
    """Document model for handling page content and metadata."""
    page_content: str
    metadata: Dict[str, Any] = Field(default_factory=dict) 