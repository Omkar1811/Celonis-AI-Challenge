import torch
from transformers import (
    AutoTokenizer,
    # AutoModelForCausalLM, # Commented out for endpoint usage
    # pipeline, # Commented out for endpoint usage
    # BitsAndBytesConfig # Commented out for endpoint usage
)
# from langchain_community.llms import HuggingFacePipeline # Commented out for endpoint usage
from langchain_huggingface import HuggingFaceEndpoint # Added for endpoint usage
from huggingface_hub import login
import logging
import os # Added for environment variables
from app.core.prompts import get_rag_prompt_template
from app.utils.logging_config import logger

logger = logging.getLogger(__name__)

# Define endpoint URL and token constants from environment variables
ENDPOINT_URL = os.environ.get("HUGGINGFACE_ENDPOINT_URL", "")
HUGGINGFACE_API_TOKEN = os.environ.get("HUGGINGFACE_TOKEN") # Get token from env

class LLMManager:
    """LLM Manager for handling the language model, prioritizing Hugging Face Endpoints."""
    
    # Removed use_gpu flag as endpoint is the primary method now
    def __init__(self, model_name="meta-llama/Meta-Llama-3-8B-Instruct", endpoint_url=ENDPOINT_URL): 
        """Initialize the LLMManager, attempting to use the specified endpoint."""
        logger.info(f"Initializing LLMManager with model: {model_name}")
        logger.info(f"Using endpoint URL: {endpoint_url}")
        logger.info(f"Hugging Face API Token available: {HUGGINGFACE_API_TOKEN is not None}")
        
        logger.info(f"Initializing LLMManager. Model name (for reference): {model_name}")
        
        self.model_name = model_name # Keep for reference or potential future tokenizer use
        self.endpoint_url = endpoint_url
        self.llm = self._initialize_llm()
        logger.info("LLMManager initialization complete")
        
    def _initialize_llm(self):
        """Initialize the language model using Hugging Face Endpoint."""
        logger.info("Initializing language model with Hugging Face Endpoint...")
        
        if not self.endpoint_url:
            logger.error("HUGGINGFACE_ENDPOINT_URL is not set. Cannot initialize LLM.")
            raise ValueError("Hugging Face Endpoint URL is required but not provided.")
            
        if not HUGGINGFACE_API_TOKEN:
            logger.warning("HUGGINGFACE_TOKEN environment variable not set. Endpoint calls may fail.")
            # Depending on the endpoint's security settings, a token might be required.
            
        logger.info(f"Attempting to initialize HuggingFaceEndpoint with URL: {self.endpoint_url}")
        
        try:
            # Initialize Hugging Face Endpoint
            llm_endpoint = HuggingFaceEndpoint(
                endpoint_url=self.endpoint_url,
                huggingfacehub_api_token=HUGGINGFACE_API_TOKEN,
                task="text-generation",
                max_new_tokens=512,
                top_k=10,
                top_p=0.95,
                typical_p=0.95,
                temperature=0.01,
                repetition_penalty=1.03,
            )
            
            logger.info("HuggingFaceEndpoint initialized successfully.")
            return llm_endpoint
            
        except Exception as e:
            logger.error(f"Failed to initialize HuggingFaceEndpoint: {str(e)}", exc_info=True)
            raise

    def get_llm(self):
        """Get the LLM instance."""
        logger.info("Getting LLM instance")
        return self.llm
            
    def health_check(self):
        """Check if the LLM is working properly"""
        logger.info("Performing LLM health check...")
        try:
            # Simple test query
            test_query = "Hello, can you give me a short response?"
            logger.info(f"Testing with query: {test_query}")
            
            # Invoke the endpoint with a simple query
            response = self.llm.invoke(test_query)
            logger.info("Health check successful - received response from endpoint")
            
            return True
        except Exception as e:
            logger.error(f"LLM health check failed: {str(e)}", exc_info=True)
            raise 