import os
import json
import pytest
from unittest.mock import MagicMock
from django.test import RequestFactory

from apps.knowledge.openapi_parser import OpenAPIParser
from apps.knowledge.postman_parser import PostmanParser
from apps.knowledge.chroma_store import (
    PersistentSQLiteVectorStore,
    ChromaVectorStore,
    BaseVectorStore,
)
from apps.knowledge.vector_store import get_vector_store
from apps.knowledge.hybrid_retriever import PureBM25, HybridRetriever
from apps.knowledge.service import KnowledgeService
from apps.ai_agents.iface_case_generator.iface_case_generator import (
    parse_api_definitions,
    convert_endpoints_to_api_definitions,
)
from apps.core.models import KnowledgeBase


SAMPLE_OPENAPI_SPEC = {
    "openapi": "3.0.3",
    "info": {"title": "Sample Store API", "version": "1.0.0"},
    "paths": {
        "/api/v1/orders/{order_id}": {
            "get": {
                "operationId": "getOrderById",
                "summary": "Find order by ID",
                "parameters": [
                    {
                        "name": "order_id",
                        "in": "path",
                        "required": True,
                        "schema": {"type": "integer", "example": 999}
                    },
                    {
                        "name": "include_items",
                        "in": "query",
                        "schema": {"type": "boolean", "example": True}
                    }
                ],
                "responses": {
                    "200": {"description": "Order details returned"},
                    "404": {"description": "Order not found"}
                }
            },
            "post": {
                "operationId": "createOrder",
                "summary": "Create a new order",
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/OrderInput"}
                        }
                    }
                },
                "responses": {
                    "201": {"description": "Order created"}
                }
            }
        }
    },
    "components": {
        "schemas": {
            "OrderInput": {
                "type": "object",
                "properties": {
                    "customer_id": {"type": "integer", "example": 42},
                    "item_name": {"type": "string", "example": "Wireless Mouse"},
                    "next_order": {"$ref": "#/components/schemas/OrderInput"}  # Circular reference
                }
            }
        }
    }
}


SAMPLE_POSTMAN_COLLECTION = {
    "info": {
        "name": "E-Commerce Collection",
        "_postman_id": "test-pm-col-1",
        "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
    },
    "item": [
        {
            "name": "Auth",
            "item": [
                {
                    "name": "User Login",
                    "request": {
                        "method": "POST",
                        "url": {
                            "raw": "https://api.shop.com/api/v1/auth/login",
                            "path": ["api", "v1", "auth", "login"]
                        },
                        "header": [
                            {"key": "Content-Type", "value": "application/json"}
                        ],
                        "body": {
                            "mode": "raw",
                            "raw": json.dumps({"username": "alice", "password": "secret"})
                        }
                    }
                }
            ]
        },
        {
            "name": "Get Products",
            "request": {
                "method": "GET",
                "url": {
                    "raw": "https://api.shop.com/api/v1/products?category=electronics",
                    "path": ["api", "v1", "products"],
                    "query": [{"key": "category", "value": "electronics"}]
                }
            }
        }
    ]
}


@pytest.mark.django_db
class TestPhase3Suite:

    def test_openapi_parser_endpoints_and_parameters(self):
        """OpenAPI parser resolves paths, query/path parameters, and responses."""
        parser = OpenAPIParser(SAMPLE_OPENAPI_SPEC)
        endpoints = parser.parse_endpoints()

        assert len(endpoints) == 2
        get_ep = next(e for e in endpoints if e["method"] == "GET")
        assert get_ep["path"] == "/api/v1/orders/{order_id}"
        assert len(get_ep["path_params"]) == 1
        assert get_ep["path_params"][0]["name"] == "order_id"
        assert len(get_ep["query_params"]) == 1
        assert get_ep["query_params"][0]["name"] == "include_items"
        assert "200" in get_ep["responses"]

    def test_openapi_circular_ref_prevention(self):
        """OpenAPI parser detects circular $ref without infinite recursion."""
        parser = OpenAPIParser(SAMPLE_OPENAPI_SPEC)
        resolved = parser.resolve_ref("#/components/schemas/OrderInput")
        assert isinstance(resolved, dict)
        assert "properties" in resolved

        endpoints = parser.parse_endpoints()
        post_ep = next(e for e in endpoints if e["method"] == "POST")
        example = post_ep["request_body_example"]
        assert isinstance(example, dict)
        assert example.get("customer_id") == 42
        assert example.get("item_name") == "Wireless Mouse"

    def test_postman_parser_recursive_hierarchy(self):
        """Postman parser extracts nested items, methods, URLs, and headers."""
        parser = PostmanParser(SAMPLE_POSTMAN_COLLECTION)
        endpoints = parser.parse_endpoints()

        assert len(endpoints) == 2
        login_ep = next(e for e in endpoints if e["method"] == "POST")
        assert login_ep["name"] == "User Login"
        assert "/api/v1/auth/login" in login_ep["path"]
        assert login_ep["request_body_example"]["username"] == "alice"
        assert "Auth" in login_ep["tags"]

        products_ep = next(e for e in endpoints if e["method"] == "GET")
        assert products_ep["name"] == "Get Products"
        assert len(products_ep["query_params"]) == 1
        assert products_ep["query_params"][0]["name"] == "category"

    def test_convert_endpoints_to_api_definitions(self):
        """Conversion helper produces valid MeterSphere apiDefinitions schema."""
        parser = OpenAPIParser(SAMPLE_OPENAPI_SPEC)
        endpoints = parser.parse_endpoints()
        converted = convert_endpoints_to_api_definitions(endpoints)

        assert "apiDefinitions" in converted
        api_defs = converted["apiDefinitions"]
        assert len(api_defs) == 2
        assert api_defs[0]["path"] == "/api/v1/orders/{order_id}"
        assert "request" in api_defs[0]
        assert "apiTestCaseList" in api_defs[0]

    def test_parse_api_definitions_auto_detection(self, tmp_path):
        """parse_api_definitions auto-detects and converts OpenAPI and Postman files."""
        # 1. OpenAPI JSON
        openapi_file = tmp_path / "openapi_test.json"
        openapi_file.write_text(json.dumps(SAMPLE_OPENAPI_SPEC), encoding="utf-8")
        apis = parse_api_definitions(str(openapi_file))
        assert len(apis) == 2
        assert apis[0]["path"] == "/api/v1/orders/{order_id}"

        # 2. Postman Collection
        postman_file = tmp_path / "postman_test.json"
        postman_file.write_text(json.dumps(SAMPLE_POSTMAN_COLLECTION), encoding="utf-8")
        pm_apis = parse_api_definitions(str(postman_file))
        assert len(pm_apis) == 2

    def test_persistent_sqlite_vector_store(self, tmp_path):
        """PersistentSQLiteVectorStore adds, searches, counts, and deletes vectors."""
        db_path = str(tmp_path / "test_vectors.db")
        store = PersistentSQLiteVectorStore(db_path=db_path, collection_name="test_col")

        ids = ["doc_1", "doc_2"]
        docs = ["User authentication API", "Billing invoice checkout endpoint"]
        embs = [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]]
        metas = [{"tag": "auth"}, {"tag": "billing"}]

        store.add_documents(ids, docs, embs, metas)
        assert store.count() == 2

        # Search query matching doc_1
        results = store.search([0.9, 0.1, 0.0], top_k=2)
        assert len(results) == 2
        assert results[0]["id"] == "doc_1"
        assert results[0]["similarity"] > 0.8
        assert results[0]["content"] == "User authentication API"

        # Delete doc_1
        store.delete(["doc_1"])
        assert store.count() == 1
        assert store.search([1.0, 0.0, 0.0], top_k=2)[0]["id"] == "doc_2"

    def test_pure_bm25_lexical_scoring(self):
        """PureBM25 scores documents higher when query tokens match."""
        corpus = [
            ["get", "user", "profile", "endpoint"],
            ["post", "create", "order", "checkout"],
            ["delete", "order", "by", "id"]
        ]
        bm25 = PureBM25(corpus)
        scores = bm25.get_scores(["user", "profile"])
        assert scores[0] > scores[1]
        assert scores[0] > scores[2]

    def test_hybrid_retriever_rrf_fusion(self, tmp_path):
        """HybridRetriever merges dense vector and BM25 ranks via RRF."""
        db_path = str(tmp_path / "hybrid_vectors.db")
        vector_store = PersistentSQLiteVectorStore(db_path=db_path, collection_name="test_hybrid")

        documents = [
            {"id": "doc_1", "text": "GET /api/v1/users/{id} retrieves user account details", "content": "GET /api/v1/users/{id} retrieves user account details"},
            {"id": "doc_2", "text": "POST /api/v1/orders places new shopping cart order", "content": "POST /api/v1/orders places new shopping cart order"},
            {"id": "doc_3", "text": "DELETE /api/v1/orders/{id} cancels pending customer order", "content": "DELETE /api/v1/orders/{id} cancels pending customer order"}
        ]

        vector_store.add_documents(
            ids=[d["id"] for d in documents],
            documents=[d["text"] for d in documents],
            embeddings=[[1.0, 0.0], [0.0, 1.0], [0.5, 0.5]],
            metadatas=[{}] * 3
        )

        retriever = HybridRetriever(vector_store)
        retriever.index_documents(documents)

        # Lexical search for specific endpoint
        bm25_res = retriever.search_bm25("DELETE orders", top_k=2)
        assert len(bm25_res) > 0
        assert bm25_res[0]["id"] == "doc_3"

        # Hybrid RRF search
        hybrid_res = retriever.search_hybrid("DELETE orders", query_embedding=[0.5, 0.5], top_k=3)
        assert len(hybrid_res) == 3
        assert hybrid_res[0]["id"] == "doc_3"
        assert "rrf_score" in hybrid_res[0]

    def test_knowledge_service_zero_docker_fallback(self):
        """KnowledgeService initializes and operates cleanly with embedded vector storage."""
        KnowledgeBase.objects.create(
            title="Authentication Guidelines",
            content="Bearer token required in Authorization header for all /api/v1 endpoints."
        )

        service = KnowledgeService()
        assert service.vector_store is not None

        # Hybrid search retrieves created knowledge base content
        combined = service.search_relevant_knowledge_hybrid("Bearer token Authorization", top_k=2)
        assert "Authorization header" in combined
