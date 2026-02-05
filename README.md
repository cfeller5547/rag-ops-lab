# RAGOps Lab

A production-grade agentic RAG + evaluation + observability platform.

## Features

- **Document Ingestion**: Upload PDF/TXT documents with automatic chunking and embedding
- **Agentic RAG Chat**: Chat with your documents using GPT-4 with mandatory citations
- **Evaluation Harness**: Run comprehensive evaluations with 5 key metrics
- **Full Tracing**: Capture and replay every retrieval, tool call, and model interaction
- **Cross-Encoder Reranking**: Improve retrieval quality with semantic reranking
- **Modern UI**: Dark-themed Gradio interface with real-time updates

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
│              PostgreSQL + pgvector                       │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Documents │ Chunks + Embeddings │ Traces │ Evals │  │
│  │  (BYTEA)   │ (vector 1536)       │        │       │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

## Quick Start

### Prerequisites

- Docker and Docker Compose
- OpenAI API key

### Running with Docker Compose (Local Development)

1. Clone the repository:
```bash
git clone https://github.com/cfeller5547/rag-ops-lab.git
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

### Deploy to Render

1. Fork this repository to your GitHub account

2. Create a new Blueprint on Render:
   - Go to https://dashboard.render.com/blueprints
   - Click "New Blueprint Instance"
   - Connect your forked repository
   - Render will detect `render.yaml` and configure services

3. Set your OpenAI API key:
   - After deployment, go to your web service settings
   - Add `OPENAI_API_KEY` environment variable

4. Your app will be live at `https://ragops-lab.onrender.com`

### Local Development (Without Docker)

1. Install PostgreSQL with pgvector extension:
```bash
# macOS with Homebrew
brew install postgresql@16
brew install pgvector

# Ubuntu
sudo apt install postgresql-16 postgresql-16-pgvector
```

2. Create database and enable pgvector:
```sql
CREATE DATABASE ragops;
\c ragops
CREATE EXTENSION vector;
```

3. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

4. Install dependencies:
```bash
pip install -r requirements.txt
```

5. Set environment variables:
```bash
export DATABASE_URL="postgresql+asyncpg://user:password@localhost:5432/ragops"
export OPENAI_API_KEY="your-key-here"
```

6. Run the application:
```bash
uvicorn src.main:app --reload
```

## Evaluation Metrics

1. **Groundedness**: Percentage of claims backed by citations
2. **Hallucination Rate**: Percentage of claims contradicting sources
3. **Schema Compliance**: Percentage of responses matching expected structure
4. **Tool Correctness**: Percentage of correct tool invocations
5. **Latency (P95)**: 95th percentile response time (target: <4s)

## CI/CD Pipeline

The project includes a GitHub Actions CI pipeline with:

- **Lint & Type Check**: Ruff and Black formatting
- **Unit Tests**: pytest with async support
- **Evaluation Gate**: Runs on PRs with pgvector service container
- **Docker Build**: Validates container builds successfully

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
| `DATABASE_URL` | - | PostgreSQL connection string |
| `OPENAI_API_KEY` | - | Your OpenAI API key |
| `OPENAI_MODEL` | `gpt-4-turbo-preview` | Chat model to use |
| `EMBEDDING_MODEL` | `text-embedding-3-small` | Embedding model |
| `RERANK_MODEL` | `cross-encoder/ms-marco-MiniLM-L-6-v2` | Reranking model |
| `CHUNK_SIZE` | `512` | Document chunk size |
| `CHUNK_OVERLAP` | `50` | Overlap between chunks |
| `TOP_K_RETRIEVAL` | `10` | Number of chunks to retrieve |
| `RERANK_TOP_K` | `5` | Number of chunks after reranking |
| `MAX_FILE_SIZE_MB` | `10` | Maximum upload file size |
| `STORE_RAW_FILES` | `true` | Store original files in database |

## Tech Stack

- **Backend**: FastAPI, SQLAlchemy 2.0 (async)
- **Database**: PostgreSQL 16 + pgvector
- **Embeddings**: OpenAI text-embedding-3-small (1536 dimensions)
- **Reranking**: sentence-transformers CrossEncoder
- **UI**: Gradio 5.0+
- **Deployment**: Docker, Render

## License

MIT
