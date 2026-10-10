# CodeBrain Memory & Knowledge Architecture

CodeBrain incorporates a Retrieval-Augmented Generation (RAG) knowledge base subsystem located in `apps/knowledge/`. This subsystem provides long-term context retention, organizational testing memory, and domain specification retrieval across all agents.

---

## Architecture Overview

```
                      ┌─────────────────────────────────┐
                      │    Document Upload & Intake     │
                      │   (PDF, DOCX, Markdown, TXT)    │
                      └────────────────┬────────────────┘
                                       │
                                       ▼
                      ┌─────────────────────────────────┐
                      │        Document Parser          │
                      │  (Chunking, Normalization, Meta) │
                      └────────────────┬────────────────┘
                                       │
                                       ▼
                      ┌─────────────────────────────────┐
                      │        Embedding Service        │
                      │  (BGE-M3 Local or Aliyun Cloud) │
                      └────────────────┬────────────────┘
                                       │
                                       ▼
                      ┌─────────────────────────────────┐
                      │       Vector Database Store     │
                      │        (Milvus 2.4.x / Mock)    │
                      └────────────────┬────────────────┘
                                       │
                     ┌─────────────────┴─────────────────┐
                     ▼                                   ▼
          ┌─────────────────────┐             ┌────────────────────┐
          │ test_case_generator │             │ test_case_reviewer │
          │ (Context Augmented) │             │ (Rubric Augmented) │
          └─────────────────────┘             └────────────────────┘
```

---

## 1. Vector Database Layer (`MilvusVectorStore`)

The primary vector store implementation lives in `apps/knowledge/vector_store.py` and `apps/knowledge/milvus_helper.py`.

### Collection Schema
- **Collection Name**: Configurable via `VECTOR_DB_CONFIG['collection_name']` (default: `vv_knowledge_collection`).
- **Primary Key**: `id` (`INT64`, auto-generated or document ID).
- **Vector Field**: `embedding` (`FLOAT_VECTOR`, dimension matches embedding model).
- **Metadata Fields**:
  - `doc_id` (`VARCHAR`): Unique identifier of parent document.
  - `doc_name` (`VARCHAR`): File name or title.
  - `chunk_id` (`INT64`): Sequential index of chunk within parent document.
  - `text` (`VARCHAR`): Raw text chunk content.
  - `category` (`VARCHAR`): Functional category (e.g., requirement, past defect, interface spec).
  - `timestamp` (`INT64`): Ingestion timestamp.

### Indexing and Search Metrics
- **Metric Type**: `L2` (Euclidean distance) or `COSINE`.
- **Index Type**: `IVF_FLAT` (low resource overhead) or `HNSW` (high recall, high throughput).
- **Query Strategy**: Top-K retrieval with minimum similarity threshold filtering.

---

## 2. Embedding Subsystem (`EmbeddingService`)

The embedding engine is abstracted under `apps/knowledge/embedding.py` and supports two operational modes:

### Local Mode (`local`)
- **Model**: `BAAI/bge-m3` via `sentence-transformers`.
- **Vector Dimension**: 1024.
- **Strengths**: Zero cloud egress, offline execution, native multilingual support (English, Chinese, code tokens).
- **Initialization**: Loaded into memory via PyTorch with lazy initialization.

### Cloud Mode (`aliyun`)
- **Model**: `text-embedding-v4` via DashScope REST API.
- **Vector Dimension**: Configurable (e.g. 1536 / 1024).
- **Strengths**: Minimal memory footprint, suited for low-resource server environments.

### Provider Configuration
Controlled via environment variable:
```bash
# Toggle between 'local' and 'aliyun'
export EMBEDDING_PROVIDER="aliyun"
export DASHSCOPE_API_KEY="your-api-key"
```

---

## 3. Ingestion & Retrieval Workflow

### Document Parsing & Chunking
1. Document upload handled via `apps/core/views.py` (`knowledge_upload`).
2. Parsers break incoming documents into chunks of 300 to 800 tokens with an overlap of 50 to 100 tokens.
3. Metadata is generated and associated with each chunk before vectorization.

### Context Retrieval Pipeline
1. When an agent receives a prompt, it queries `KnowledgeService.search(query, top_k=5)`.
2. The query text is vectorized using the active embedding model.
3. Milvus executes vector similarity search against the collection.
4. Matching text chunks are formatted as context blocks and injected into agent prompts under a `# Reference Knowledge` section.

---

## 4. Graceful Degradation & Non-Docker Mode

To permit local development and testing without spinning up Milvus containers:

1. **`ENABLE_MILVUS = False`**: Setting this flag in `config/settings.py` prevents connection attempts to Milvus host.
2. **Lazy NLP Loading**: Heavy dependencies (`sentence_transformers`, `spacy`, `unstructured`) are imported inside their respective caller functions rather than module root, avoiding startup crashes when dependencies or GPU environments are absent.
3. **Fallback Search**: When Milvus is inactive, `KnowledgeService` returns an empty context set without throwing exceptions, allowing agents to function in zero-context standalone mode.
