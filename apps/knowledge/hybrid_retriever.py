import re
import math
from typing import List, Dict, Any, Optional
from apps.utils.logger_manager import get_logger
from .chroma_store import BaseVectorStore

logger = get_logger(__name__)


class PureBM25:
    """Pure Python BM25 implementation for lexical retrieval without external compiled dependencies."""

    def __init__(self, corpus: List[List[str]], k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.corpus_size = len(corpus)
        self.avgdl = sum(len(doc) for doc in corpus) / max(1, self.corpus_size)
        self.doc_freqs: List[Dict[str, int]] = []
        self.idf: Dict[str, float] = {}
        self.doc_lens = [len(doc) for doc in corpus]
        self._initialize(corpus)

    def _initialize(self, corpus: List[List[str]]):
        df: Dict[str, int] = {}
        for doc in corpus:
            freqs: Dict[str, int] = {}
            for token in doc:
                freqs[token] = freqs.get(token, 0) + 1
            self.doc_freqs.append(freqs)
            for token in freqs.keys():
                df[token] = df.get(token, 0) + 1

        for token, freq in df.items():
            self.idf[token] = math.log(1.0 + (self.corpus_size - freq + 0.5) / (freq + 0.5))

    def get_scores(self, query: List[str]) -> List[float]:
        scores = [0.0] * self.corpus_size
        for token in query:
            if token not in self.idf:
                continue
            idf_val = self.idf[token]
            for idx, freqs in enumerate(self.doc_freqs):
                if token not in freqs:
                    continue
                tf = freqs[token]
                doc_len = self.doc_lens[idx]
                numerator = tf * (self.k1 + 1)
                denominator = tf + self.k1 * (1 - self.b + self.b * (doc_len / self.avgdl))
                scores[idx] += idf_val * (numerator / max(1e-6, denominator))
        return scores


class HybridRetriever:
    """Hybrid Search Engine combining Dense Vector Similarity and Lexical BM25 via Reciprocal Rank Fusion (RRF)."""

    def __init__(self, vector_store: BaseVectorStore, embedder_func=None):
        self.vector_store = vector_store
        self.embedder_func = embedder_func
        self.documents: List[Dict[str, Any]] = []
        self.bm25_model = None

    @staticmethod
    def tokenize(text: str) -> List[str]:
        """Simple alphanumeric tokenizer preserving path segments and query terms."""
        return [t.lower() for t in re.findall(r'[a-zA-Z0-9_\-\.]+', text) if t]

    def index_documents(self, documents: List[Dict[str, Any]]) -> None:
        """Update lexical corpus and refresh BM25 model."""
        self.documents = documents
        tokenized_corpus = [self.tokenize(doc.get('text', '')) for doc in documents]
        if tokenized_corpus:
            self.bm25_model = PureBM25(tokenized_corpus)


    def search_bm25(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """Retrieve top documents by BM25 lexical score."""
        if not self.bm25_model or not self.documents:
            return []

        tokens = self.tokenize(query)
        if not tokens:
            return []

        scores = self.bm25_model.get_scores(tokens)
        ranked_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]

        results = []
        for rank, idx in enumerate(ranked_indices, start=1):
            if scores[idx] > 0:
                doc = self.documents[idx].copy()
                doc['bm25_score'] = scores[idx]
                doc['bm25_rank'] = rank
                results.append(doc)
        return results

    def search_hybrid(self, query: str, query_embedding: Optional[List[float]] = None, top_k: int = 5, rrf_k: int = 60) -> List[Dict[str, Any]]:
        """
        Execute Reciprocal Rank Fusion (RRF) across Dense and Sparse retrieval.
        RRF Score = 1 / (rrf_k + dense_rank) + 1 / (rrf_k + bm25_rank)
        """
        # 1. Dense vector search
        dense_results = []
        if query_embedding is None and self.embedder_func:
            try:
                emb = self.embedder_func(query)
                query_embedding = emb[0] if isinstance(emb, list) and isinstance(emb[0], list) else emb
            except Exception as e:
                logger.warning(f"Failed to generate query embedding: {e}")

        if query_embedding:
            dense_results = self.vector_store.search(query_embedding, top_k=top_k * 2)

        # 2. Sparse lexical search
        bm25_results = self.search_bm25(query, top_k=top_k * 2)

        # 3. Reciprocal Rank Fusion
        rrf_scores: Dict[str, float] = {}
        doc_map: Dict[str, Dict[str, Any]] = {}

        for rank, item in enumerate(dense_results, start=1):
            doc_id = str(item.get('id', rank))
            rrf_scores[doc_id] = rrf_scores.get(doc_id, 0.0) + (1.0 / (rrf_k + rank))
            doc_map[doc_id] = item

        for rank, item in enumerate(bm25_results, start=1):
            doc_id = str(item.get('id', rank))
            rrf_scores[doc_id] = rrf_scores.get(doc_id, 0.0) + (1.0 / (rrf_k + rank))
            if doc_id not in doc_map:
                doc_map[doc_id] = item

        # 4. Sort by blended RRF score
        sorted_ids = sorted(rrf_scores.keys(), key=lambda d_id: rrf_scores[d_id], reverse=True)

        merged = []
        for doc_id in sorted_ids[:top_k]:
            doc = doc_map[doc_id].copy()
            doc['rrf_score'] = round(rrf_scores[doc_id], 5)
            merged.append(doc)

        return merged
