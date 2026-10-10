import os
import json
import sqlite3
import math
from typing import List, Dict, Any, Optional, Union
from apps.utils.logger_manager import get_logger

logger = get_logger(__name__)


def _normalize_add_args(
    ids: Union[List[str], List[Dict[str, Any]]],
    documents: Optional[List[str]] = None,
    embeddings: Optional[List[List[float]]] = None,
    metadatas: Optional[List[Dict[str, Any]]] = None
):
    """Normalize input documents to support both 4-tuple and list-of-dicts conventions."""
    if isinstance(ids, list) and ids and isinstance(ids[0], dict):
        import uuid
        doc_dicts = ids
        norm_ids = [str(d.get('id') if d.get('id') is not None else uuid.uuid4().hex) for d in doc_dicts]
        norm_docs = [d.get('content') or d.get('text', '') for d in doc_dicts]
        norm_embs = [d.get('embedding', []) for d in doc_dicts]
        norm_metas = [{"title": d.get('title', '')} for d in doc_dicts]
        return norm_ids, norm_docs, norm_embs, norm_metas

    n_ids = ids or []
    n_docs = documents or []
    n_embs = embeddings or []
    n_metas = metadatas or [{}] * len(n_ids)
    return n_ids, n_docs, n_embs, n_metas


class BaseVectorStore:
    """Unified interface for CodeBrain vector stores."""

    def add_documents(
        self,
        ids: Union[List[str], List[Dict[str, Any]]],
        documents: Optional[List[str]] = None,
        embeddings: Optional[List[List[float]]] = None,
        metadatas: Optional[List[Dict[str, Any]]] = None
    ) -> None:
        raise NotImplementedError

    def search(self, query_embedding: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
        raise NotImplementedError

    def delete(self, ids: List[str]) -> None:
        raise NotImplementedError

    def count(self) -> int:
        raise NotImplementedError

    def clear(self) -> None:
        raise NotImplementedError


class PersistentSQLiteVectorStore(BaseVectorStore):
    """Pure SQLite fallback vector store supporting cosine similarity without external dependencies."""

    def __init__(self, db_path: str = "data/chroma_db/fallback_vector_store.db", collection_name: str = "qa_knowledge"):
        self.db_path = db_path
        self.collection_name = collection_name
        os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS vector_entries (
                    id TEXT PRIMARY KEY,
                    collection TEXT,
                    document TEXT,
                    embedding TEXT,
                    metadata TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_collection ON vector_entries(collection)")
            conn.commit()

    def add_documents(
        self,
        ids: Union[List[str], List[Dict[str, Any]]],
        documents: Optional[List[str]] = None,
        embeddings: Optional[List[List[float]]] = None,
        metadatas: Optional[List[Dict[str, Any]]] = None
    ) -> None:
        norm_ids, norm_docs, norm_embs, norm_metas = _normalize_add_args(ids, documents, embeddings, metadatas)
        with sqlite3.connect(self.db_path) as conn:
            for doc_id, doc, emb, meta in zip(norm_ids, norm_docs, norm_embs, norm_metas):
                conn.execute("""
                    INSERT OR REPLACE INTO vector_entries (id, collection, document, embedding, metadata)
                    VALUES (?, ?, ?, ?, ?)
                """, (doc_id, self.collection_name, doc, json.dumps(emb), json.dumps(meta or {})))
            conn.commit()

    @staticmethod
    def _cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
        dot = sum(a * b for a, b in zip(vec_a, vec_b))
        norm_a = math.sqrt(sum(a * a for a in vec_a))
        norm_b = math.sqrt(sum(b * b for b in vec_b))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)

    def search(self, query_embedding: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
        scored = []
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT id, document, embedding, metadata FROM vector_entries WHERE collection = ?",
                (self.collection_name,)
            )
            for doc_id, doc, emb_str, meta_str in cursor.fetchall():
                try:
                    emb = json.loads(emb_str)
                    sim = self._cosine_similarity(query_embedding, emb)
                    scored.append({
                        "id": doc_id,
                        "text": doc,
                        "content": doc,
                        "metadata": json.loads(meta_str) if meta_str else {},
                        "similarity": round(sim, 4),
                        "score": round(sim, 4),
                        "distance": round(1.0 - sim, 4)
                    })
                except Exception as e:
                    logger.debug(f"Error computing similarity for {doc_id}: {e}")

        scored.sort(key=lambda x: x["similarity"], reverse=True)
        return scored[:top_k]

    def delete(self, ids: List[str]) -> None:
        with sqlite3.connect(self.db_path) as conn:
            for doc_id in ids:
                conn.execute("DELETE FROM vector_entries WHERE id = ? AND collection = ?", (doc_id, self.collection_name))
            conn.commit()

    def count(self) -> int:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.execute("SELECT COUNT(*) FROM vector_entries WHERE collection = ?", (self.collection_name,))
            return cur.fetchone()[0]

    def clear(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM vector_entries WHERE collection = ?", (self.collection_name,))
            conn.commit()


class ChromaVectorStore(BaseVectorStore):
    """Zero-Docker In-Process Vector Store using ChromaDB PersistentClient."""

    def __init__(self, persist_dir: str = "data/chroma_db", collection_name: str = "qa_knowledge"):
        self.persist_dir = persist_dir
        self.collection_name = collection_name
        self.chroma_available = False
        self._fallback_store = None

        try:
            import chromadb
            os.makedirs(persist_dir, exist_ok=True)
            self.client = chromadb.PersistentClient(path=persist_dir)
            self.collection = self.client.get_or_create_collection(
                name=collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            self.chroma_available = True
            logger.info(f"Initialized ChromaDB PersistentClient at {persist_dir} (collection: {collection_name})")
        except Exception as e:
            logger.warning(f"ChromaDB not available ({e}); activating PersistentSQLiteVectorStore fallback.")
            self._fallback_store = PersistentSQLiteVectorStore(
                db_path=os.path.join(persist_dir, "fallback_vectors.db"),
                collection_name=collection_name
            )

    def add_documents(
        self,
        ids: Union[List[str], List[Dict[str, Any]]],
        documents: Optional[List[str]] = None,
        embeddings: Optional[List[List[float]]] = None,
        metadatas: Optional[List[Dict[str, Any]]] = None
    ) -> None:
        norm_ids, norm_docs, norm_embs, norm_metas = _normalize_add_args(ids, documents, embeddings, metadatas)
        if not self.chroma_available:
            return self._fallback_store.add_documents(norm_ids, norm_docs, norm_embs, norm_metas)

        sanitized_metadatas = []
        for m in norm_metas:
            s_m = {}
            for k, v in (m or {}).items():
                if isinstance(v, (str, int, float, bool)):
                    s_m[k] = v
                else:
                    s_m[k] = json.dumps(v, ensure_ascii=False)
            sanitized_metadatas.append(s_m)

        # Filter entries with valid non-empty embeddings for Chroma
        valid_indices = [i for i, emb in enumerate(norm_embs) if emb and len(emb) > 0]
        if not valid_indices:
            logger.info("No non-empty embeddings provided for Chroma upsert; skipped.")
            return

        v_ids = [norm_ids[i] for i in valid_indices]
        v_docs = [norm_docs[i] for i in valid_indices]
        v_embs = [norm_embs[i] for i in valid_indices]
        v_metas = [sanitized_metadatas[i] for i in valid_indices]

        self.collection.upsert(
            ids=v_ids,
            documents=v_docs,
            embeddings=v_embs,
            metadatas=v_metas
        )

    def search(self, query_embedding: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
        if not self.chroma_available:
            return self._fallback_store.search(query_embedding, top_k)

        count = self.collection.count()
        if count == 0:
            return []

        actual_k = min(top_k, count)
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=actual_k
        )

        formatted = []
        ids_list = results.get('ids', [[]])[0]
        docs_list = results.get('documents', [[]])[0]
        metas_list = results.get('metadatas', [[]])[0]
        distances = results.get('distances', [[]])[0]

        for i in range(len(ids_list)):
            dist = distances[i] if i < len(distances) else 0.0
            sim = round(1.0 - dist, 4)
            formatted.append({
                "id": ids_list[i],
                "text": docs_list[i] if i < len(docs_list) else "",
                "content": docs_list[i] if i < len(docs_list) else "",
                "metadata": metas_list[i] if i < len(metas_list) else {},
                "distance": round(dist, 4),
                "similarity": sim,
                "score": sim
            })

        return formatted

    def delete(self, ids: List[str]) -> None:
        if not self.chroma_available:
            return self._fallback_store.delete(ids)
        if ids:
            self.collection.delete(ids=ids)

    def count(self) -> int:
        if not self.chroma_available:
            return self._fallback_store.count()
        return self.collection.count()

    def clear(self) -> None:
        if not self.chroma_available:
            return self._fallback_store.clear()
        try:
            self.client.delete_collection(self.collection_name)
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}
            )
        except Exception as e:
            logger.warning(f"Error resetting collection: {e}")
