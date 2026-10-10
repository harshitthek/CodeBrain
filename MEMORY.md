# CodeBrain Memory, Hybrid RAG & Spec Ingestion Architecture

CodeBrain incorporates a zero-Docker Retrieval-Augmented Generation (RAG) knowledge base and API specification ingestion subsystem located in `apps/knowledge/`. It provides long-term context retention, hybrid lexical + semantic search, and structured API contract extraction across all agents.

---

## Architecture Overview

```
      ┌───────────────────────────────────┐   ┌───────────────────────────────────┐
      │     Document Upload & Intake      │   │     API Specification Intake      │
      │    (PDF, DOCX, Markdown, TXT)     │   │  (OpenAPI 3.x, Swagger, Postman)  │
      └─────────────────┬─────────────────┘   └─────────────────┬─────────────────┘
                        │                                       │
                        ▼                                       ▼
      ┌───────────────────────────────────┐   ┌───────────────────────────────────┐
      │     Chunking & Normalization      │   │  openapi_parser / postman_parser  │
      └─────────────────┬─────────────────┘   └─────────────────┬─────────────────┘
                        │                                       │
         ┌──────────────┴──────────────┐                        │
         ▼                             ▼                        ▼
┌─────────────────────┐     ┌─────────────────────┐   ┌───────────────────────────┐
│  Dense Vector Store │     │   Lexical Index     │   │ Normalized API Contracts  │
│  - SQLite/ChromaDB  │     │  - PureBM25Index    │   │ (Endpoints, Params, Body) │
│  - Milvus (Cluster) │     │    (Okapi BM25)     │   └─────────────┬─────────────┘
└──────────┬──────────┘     └──────────┬──────────┘                 │
           │                           │                            │
           └─────────────┬─────────────┘                            │
                         ▼                                          │
           ┌───────────────────────────┐                            │
           │     HybridRetriever       │                            │
           │ (Reciprocal Rank Fusion)  │                            │
           └─────────────┬─────────────┘                            │
                         │                                          │
                         ▼                                          ▼
           ┌──────────────────────────────────────────────────────────┐
           │   Agent Context Augmentation & Test Suite Generation     │
           └──────────────────────────────────────────────────────────┘
```

---

## 1. Zero-Docker Embedded Vector Store (`chroma_store.py`)

To run locally without requiring external Milvus/Docker containers, CodeBrain provides [`PersistentSQLiteVectorStore`](apps/knowledge/chroma_store.py) in `apps/knowledge/chroma_store.py`:

- **Storage Engine**: Embedded SQLite table (`vector_chunks`) stored at `chroma_db/chroma_vectors.sqlite3` (or optional native `chromadb.PersistentClient`).
- **Deterministic Local Embeddings**: Computes normalized 384-dimensional dense token/n-gram feature embeddings out-of-the-box when heavy PyTorch models are offline, or integrates with `EmbeddingService`.
- **Cosine Similarity Search**: Evaluates exact cosine similarity over persisted vectors with category and metadata filtering.
- **CRUD Operations**: Supports `add_documents`, `search`, `delete_by_doc_id`, `count`, and `clear`.

---

## 2. Hybrid BM25 + Vector Retrieval (`hybrid_retriever.py`)

[`HybridRetriever`](apps/knowledge/hybrid_retriever.py) in `apps/knowledge/hybrid_retriever.py` combines dense semantic search with exact keyword matching:

- **Lexical Engine (`PureBM25Index`)**: Zero-dependency Okapi BM25 implementation (`k1=1.5`, `b=0.75`) with CJK character and alphanumeric token segmentation. Ensures exact matches on API paths (e.g. `/api/v1/orders`), error codes, and parameter names.
- **Reciprocal Rank Fusion (RRF)**: Merges dense vector rankings and BM25 lexical rankings using weighted RRF:
  $$\text{RRF\_Score}(d) = \frac{w_{\text{dense}}}{k + \text{rank}_{\text{dense}}(d)} + \frac{w_{\text{bm25}}}{k + \text{rank}_{\text{bm25}}(d)}$$
  where $k = 60$ by default.

---

## 3. API Specification Ingestion (`openapi_parser.py` & `postman_parser.py`)

CodeBrain ingests structured API definitions directly into the Knowledge Base and Interface Case Generator:

- **OpenAPI 3.x & Swagger 2.0 Parser ([`openapi_parser.py`](apps/knowledge/openapi_parser.py))**:
  - Parses JSON and YAML specifications.
  - Resolves internal `$ref` pointers (`#/components/schemas/...` and `#/definitions/...`) with cycle detection to prevent infinite recursion on self-referential schemas.
  - Synthesizes sample request bodies, query parameters, path variables, and header contracts.
- **Postman Collection v2.1 Parser ([`postman_parser.py`](apps/knowledge/postman_parser.py))**:
  - Recursively traverses nested Postman folder hierarchies (`item` trees), preserving folder breadcrumb paths.
  - Extracts URL templates, query parameters, headers, and raw/form-data request bodies.
- **Auto-Detection Facade**: `parse_api_definitions` in [`apps/knowledge/service.py`](apps/knowledge/service.py) automatically detects OpenAPI/Swagger vs. Postman schemas and converts endpoints into CodeBrain's internal `apiDefinitions` structure.

---

## 4. Enterprise Cluster Mode (`MilvusVectorStore` & `EmbeddingService`)

For multi-million-vector production deployments, CodeBrain supports external Milvus clusters (`apps/knowledge/vector_store.py`) and cloud/local neural embeddings (`apps/knowledge/embedding.py`):

- **Enable Milvus**: Set `ENABLE_MILVUS = True` in `config/settings.py`. When `ENABLE_MILVUS = False` (default), `KnowledgeService` automatically routes all storage and hybrid retrieval through the embedded zero-Docker store.
- **Embedding Providers**:
  - `local`: `BAAI/bge-m3` via `sentence-transformers` (1024-dim).
  - `aliyun`: `text-embedding-v4` via DashScope REST API.
