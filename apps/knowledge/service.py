from ..core.models import KnowledgeBase
from apps.utils.logger_manager import get_logger
from django.apps import apps


class KnowledgeService:
    """Knowledge base service integrating vector store and embedding models"""
    
    def __init__(self):
        config = apps.get_app_config('knowledge')
        self.vector_store = config.vector_store
        self.embedder = config.embedder
        self.logger = get_logger(self.__class__.__name__)

        if self.vector_store is None:
            from .vector_store import get_vector_store
            self.vector_store = get_vector_store()

        if self.embedder is None:
            try:
                from .embedding import create_embedder
                self.embedder = create_embedder()
            except Exception as e:
                self.logger.warning(f"Embedder unavailable in KnowledgeService: {e}")

    def add_knowledge(self, title: str, content: str) -> int:
        """Add knowledge entry to knowledge base"""
        knowledge = KnowledgeBase(
            title=title,
            content=content
        )
        knowledge.save()

        embedding = []
        if self.embedder:
            try:
                embedding = self.embedder.get_embeddings(content)[0]
            except Exception as e:
                self.logger.warning(f"Failed to generate embedding for entry: {e}")

        self.vector_store.add_documents([{
            "id": str(knowledge.id),
            "title": title,
            "content": content,
            "embedding": embedding
        }])

        return knowledge.id

    def search_relevant_knowledge(self, query: str, top_k: int = 5, min_score_threshold: float = 0.6) -> str:
        """Search relevant knowledge

        Args:
            query: Query text
            top_k: Max results to return
            min_score_threshold: Minimum similarity threshold

        Returns:
            Combined relevant knowledge text
        """
        if not self.embedder:
            return self.search_relevant_knowledge_hybrid(query, top_k=top_k)

        query_embedding = self.embedder.get_embeddings(query)[0]
        self.logger.info(
            f"Knowledge search context: '{query}'\n"
            f"Vector dimension: {len(query_embedding)}\n"
        )

        search_k = top_k * 3
        results = self.vector_store.search(query_embedding, top_k=search_k)

        # 1. Similarity threshold filtering
        threshold_filtered = [
            item for item in results
            if (item.get("score") if item.get("score") is not None else item.get("similarity", 0.0)) >= min_score_threshold
        ]
        self.logger.info(f"Knowledge search after threshold filter: {threshold_filtered}")

        # 2. Sort descending by score
        sorted_results = sorted(
            threshold_filtered,
            key=lambda x: (x.get("score") if x.get("score") is not None else x.get("similarity", 0.0)),
            reverse=True
        )

        # 3. Keyword post-processing filter
        keywords = [kw.strip() for kw in query.split() if len(kw.strip()) > 1]

        keyword_filtered = []
        for item in sorted_results:
            content = item.get("content") or item.get("text", "")
            if any(keyword in content for keyword in keywords):
                keyword_filtered.append(item)
            elif len(keyword_filtered) < 2:
                keyword_filtered.append(item)
        self.logger.info(f"Knowledge search after keyword filter: {keyword_filtered}")

        # 4. Take top_k results
        top_results = keyword_filtered[:top_k]
        self.logger.info(f"Knowledge search top_k results: {top_results}")

        # 5. Extract and combine content
        content_list = [item.get("content") or item.get("text", "") for item in top_results if (item.get("content") or item.get("text"))]

        if not content_list:
            return ""

        combined_content = "\n\n".join(content_list)
        return combined_content

    def search_relevant_knowledge_hybrid(self, query: str, top_k: int = 5) -> str:
        """Search relevant knowledge using Hybrid BM25 + Dense RRF fusion."""
        from .hybrid_retriever import HybridRetriever
        embedder_func = self.embedder.get_embeddings if self.embedder else None
        retriever = HybridRetriever(self.vector_store, embedder_func=embedder_func)

        # Populate in-memory lexical corpus from KnowledgeBase database entries
        all_entries = [
            {"id": str(kb.id), "title": kb.title, "text": kb.content, "content": kb.content}
            for kb in KnowledgeBase.objects.all()
        ]
        retriever.index_documents(all_entries)

        hybrid_results = retriever.search_hybrid(query, top_k=top_k)
        content_list = [item.get("content") or item.get("text", "") for item in hybrid_results if item.get("content") or item.get("text")]
        return "\n\n".join(content_list)



def get_knowledgeService_instance():
    """Get knowledge base service instance"""
    config = apps.get_app_config("knowledge")
    return KnowledgeService()
