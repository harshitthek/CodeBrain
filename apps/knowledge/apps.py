from django.apps import AppConfig


class KnowledgeConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.knowledge"

    embedder = None
    vector_store = None

    def ready(self):
        from django.conf import settings
        if not getattr(settings, "KNOWLEDGE_ENABLED", True):
            return
        backend = getattr(settings, "VECTOR_STORE_BACKEND", "chroma").lower()
        if backend == "chroma" or getattr(settings, "ENABLE_MILVUS", False):
            try:
                from .embedding import create_embedder
                from .vector_store import get_vector_store

                if KnowledgeConfig.embedder is None:
                    try:
                        KnowledgeConfig.embedder = create_embedder()
                    except Exception as e:  # noqa: BLE001 - optional model providers may fail independently.
                        import logging
                        logging.getLogger(__name__).warning(f"Embedder initialization deferred: {e}")

                if KnowledgeConfig.vector_store is None:
                    KnowledgeConfig.vector_store = get_vector_store()
            except Exception as e:  # noqa: BLE001 - knowledge infrastructure is optional at startup.
                import logging
                logging.getLogger(__name__).warning(f"Failed to initialize knowledge base services: {e}")
