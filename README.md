# RAGOps Lab

A production-grade agentic RAG + evaluation + observability platform.

## Features

- **Document Ingestion**: Upload PDF/TXT documents with automatic chunking and embedding
- **Agentic RAG Chat**: Chat with your documents using GPT-4 with mandatory citations
- **Evaluation Harness**: Run comprehensive evaluations with 5 key metrics
- **Full Tracing**: Capture and replay every retrieval, tool call, and model interaction
- **Modern UI**: Dark-themed Gradio interface with real-time updates

## Quick Start

### Prerequisites

- Docker and Docker Compose
- OpenAI API key

### Running with Docker

1. Clone the repository:
```bash
git clone https://github.com/yourusername/rag-ops-lab.git
cd rag-ops-lab
```

2. Create your environment file:
```bash
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
```

3. Start the application:
```bash
docker-compose up --build
```

4. Open http://localhost:8000 in your browser

### Local Development

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
uvicorn src.main:app --reload
```

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Gradio UI                            │
│  ┌─────────┬─────────┬─────────┬─────────┬─────────┐   │
│  │  Chat   │ Corpus  │  Evals  │ Traces  │Settings │   │
│  └─────────┴─────────┴─────────┴─────────┴─────────┘   │
└─────────────────────────────────────────────────────────┘
                          │
┌─────────────────────────────────────────────────────────┐
│                   FastAPI Backend                        │
│  ┌─────────────────────────────────────────────────┐   │
│  │               API Routes                         │   │
│  │  /documents  /chat  /evals  /traces  /health    │   │
│  └─────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────┐   │
│  │              Services Layer                      │   │
│  │  Ingestion  Retrieval  Agent  Eval  Tracing     │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
                          │
┌─────────────────────────────────────────────────────────┐
│                    Data Layer                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │   SQLite     │  │   ChromaDB   │  │  File Store  │  │
│  │  (metadata)  │  │  (vectors)   │  │  (uploads)   │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────┘
```

## Evaluation Metrics

1. **Groundedness**: Percentage of claims backed by citations
2. **Hallucination Rate**: Percentage of claims contradicting sources
3. **Schema Compliance**: Percentage of responses matching expected structure
4. **Tool Correctness**: Percentage of correct tool invocations
5. **Latency (P95)**: 95th percentile response time (target: <4s)

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/api/documents` | GET, POST | List/upload documents |
| `/api/documents/{id}` | GET, DELETE | Get/delete document |
| `/api/chat` | POST | Send chat message |
| `/api/chat/stream` | POST | Streaming chat |
| `/api/evals` | GET, POST | List/run evaluations |
| `/api/evals/{id}` | GET | Get eval results |
| `/api/traces` | GET | List traces |
| `/api/traces/{id}` | GET | Get trace details |

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_API_KEY` | - | Your OpenAI API key |
| `OPENAI_MODEL` | `gpt-4-turbo-preview` | Model to use |
| `CHUNK_SIZE` | `512` | Document chunk size |
| `CHUNK_OVERLAP` | `50` | Overlap between chunks |
| `TOP_K_RETRIEVAL` | `5` | Number of chunks to retrieve |

## License

MIT
