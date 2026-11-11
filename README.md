# Bounded Dual-Stream RAG & Ingestion Firewall

An n8n-based Retrieval-Augmented Generation (RAG) system for coaching transcripts. It combines an ingestion firewall, dual-stream knowledge extraction, vector retrieval, and deterministic no-match handling.

## Architecture

### Workflow A — Ingestion Firewall

1. Read and parse mock coaching transcripts.
2. Validate sessions and sample transcript turns.
3. Classify meetings using Llama 3.
4. Accept only Client Coaching sessions with confidence >= 0.80.
5. Archive rejected sessions in PostgreSQL.
6. Validate the coach identity.
7. Create two separate streams:
   - **Framework:** structured coaching frameworks extracted from coach dialogue.
   - **Voice sample:** verbatim coach dialogue.
8. Validate framework extraction.
9. Generate BGE-M3 embeddings (1024 dimensions).
10. Store documents and embeddings in PostgreSQL with pgvector.

### Workflow B — Gated Retrieval

1. Receive a query through `POST /rag/query`.
2. Validate the query and handle greetings with a static response.
3. Generate a BGE-M3 query embedding.
4. Retrieve documents using cosine similarity.
5. Apply independent SQL thresholds:
   - Framework: >= 0.50
   - Voice sample: >= 0.60
6. Retrieve at most two documents per stream.
7. If no documents qualify, return a deterministic fallback without calling the LLM.
8. Otherwise, generate an answer using Llama 3 and retrieved context.

## Technology

- n8n
- PostgreSQL 16
- pgvector
- HNSW approximate nearest-neighbor index
- Ollama
- BGE-M3 embeddings
- Llama 3
- Docker Compose
- Python

## Requirements

- Docker and Docker Compose
- Ollama installed and running on the host
- `bge-m3` and `llama3` Ollama models

Pull the models:

```bash
ollama pull bge-m3
ollama pull llama3
```

## Setup

Clone the repository:

```bash
git clone https://github.com/Mohammed18-19/bounded-dual-stream-rag.git
cd bounded-dual-stream-rag
```

Create a local `.env` file containing the environment variables required by `docker-compose.yml`. Never commit credentials.

Start services:

```bash
docker compose up -d
```

Open n8n at:

`http://localhost:5678`

Configure the Postgres and Ollama credentials in n8n. The Ollama API address from inside the n8n container is:

`http://host.docker.internal:11434`

Import the workflows:

- `workflows/ingestion_firewall.json`
- `workflows/gated_retrieval.json`

Configure imported node credentials, then execute Workflow A to ingest the sample data.

The Compose configuration mounts `./data` read-only at `/data`.

## Database

The schema is defined in `init.sql`.

`knowledge_vault` stores framework and voice-sample documents with 1024-dimensional embeddings.

`archived_sessions` stores sessions rejected by the ingestion firewall.

The HNSW index uses `vector_cosine_ops`.

## Retrieval and safety design

The SQL query enforces similarity thresholds before generation. A prompt-only instruction such as "do not answer if context is missing" is not a reliable retrieval boundary.

The deterministic fallback is an application-level gate: when no qualifying document is retrieved, the LLM generation node is skipped.

HNSW is an approximate nearest-neighbor index. Its `ef_search` parameter controls the search breadth. Increasing it can improve recall at the cost of query latency. The HNSW search breadth and SQL similarity thresholds serve different purposes.

## Verification

Prepare and validate the sample dataset:

```bash
python3 scripts/prepare_dataset.py
```

Verify the database:

```bash
python3 scripts/verify_database.py
```

After activating Workflow B, test its production webhook:

```bash
RAG_URL=http://localhost:5678/webhook/rag/query python3 scripts/test_retrieval.py
```

The retrieval smoke test checks:
- An unrelated query receives the exact no-match fallback.
- A coaching query receives a non-empty answer.

For local n8n test-webhook requests, click **Execute Workflow** before sending a request to `/webhook-test/rag/query`. Test webhooks are temporary and generally accept one request per execution.

## API example

```bash
curl -X POST http://localhost:5678/webhook/rag/query \
  -H "Content-Type: application/json" \
  -d '{"query":"How can a manager reduce micromanagement while maintaining accountability?"}'
```

Expected no-match response:

```json
{
  "answer": "No documented coaching frameworks match this topic."
}
```

## Project structure

```text
.
├── data/
│   └── mock_transcripts.json
├── scripts/
│   ├── prepare_dataset.py
│   ├── verify_database.py
│   └── test_retrieval.py
├── workflows/
│   ├── ingestion_firewall.json
│   └── gated_retrieval.json
├── docker-compose.yml
├── init.sql
└── README.md
```

## Scope and limitations

This project demonstrates a bounded RAG pipeline using a sample coaching dataset. Retrieval quality depends on dataset coverage, embedding quality, thresholds, and index configuration. The sample tests do not establish general-purpose coaching accuracy.
