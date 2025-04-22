# RAG Chatbot with FastAPI

A Twitter-style customer support chatbot built with FastAPI, LangChain, and Hugging Face models.

## Features

- **RAG-based Chatbot**: Uses Retrieval-Augmented Generation to provide accurate responses based on a knowledge base
- **Session Management**: Maintains chat sessions for continuous conversations
- **Modern UI**: Twitter-inspired chat interface
- **Vector Storage**: Stores documents in a vector database for semantic search
- **Modular Architecture**: Well-organized codebase with proper separation of concerns

## Requirements

- Python 3.8+
- See `requirements.txt` for all dependencies

## Project Structure

```
app/
  ├─ api/                # API routes
  ├─ core/               # Core functionality
  │   ├─ llm.py          # Language model management
  │   ├─ prompts.py      # Prompt templates
  │   └─ session_manager.py # Chat session management
  ├─ db/                 # Database operations
  │   └─ vector_store.py # Vector database operations
  ├─ models/             # Data models
  │   ├─ chat.py         # Chat request/response models
  │   └─ document.py     # Document model
  ├─ services/           # Business logic
  │   └─ chat_service.py # Chat service
  ├─ static/             # Static files
  ├─ templates/          # HTML templates
  │   └─ index.html      # Chat UI
  ├─ utils/              # Utility functions
  │   ├─ data_loader.py  # Data loading utilities
  │   └─ setup.py        # Setup script
  └─ main.py             # FastAPI application
```

## Setup and Installation

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Place your CSV data file in the `data` directory (should have 'input' and 'output' columns)
4. Initialize the vector database:
   ```bash
   python -m app.utils.setup
   ```
5. Run the application:
   ```bash
   python -m app.main
   ```
6. Access the application at: http://localhost:8000

## Configuration

You can customize the application by modifying:

- Model selection in `app/core/llm.py`
- Vector database settings in `app/db/vector_store.py`
- Prompt templates in `app/core/prompts.py`

## API Endpoints

- `GET /`: Main chat UI
- `POST /api/chat`: Submit a chat message
  - Request Body: `{"question": "string", "session_id": "string"}`
  - Response: `{"session_id": "string", "response": "string"}`
- `POST /api/new_session`: Create a new chat session
  - Response: `{"session_id": "string", "response": "string"}` 