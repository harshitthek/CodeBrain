from pymilvus import connections, Collection, utility, DataType
from pymilvus import CollectionSchema, FieldSchema
# import numpy as np
from typing import List, Dict, Any, Optional
from django.conf import settings
from apps.utils.logger_manager import get_logger

logger = get_logger(__name__)

class MilvusVectorStore:
    """Milvus Vector Database Service"""
    
    def __init__(self, 
                host: Optional[str] = None, 
                port: Optional[str] = None,
                db_name: Optional[str] = None,
                collection_name: Optional[str] = None):
        config = getattr(settings, "VECTOR_DB_CONFIG", {}) or {}
        self.host = host or config.get("host", "localhost")
        self.port = port or config.get("port", "19530")
        self.db_name = db_name or config.get("db_name", "default")
        self.collection_name = collection_name or config.get("collection_name", "vv_knowledge_collection")
        if getattr(settings, 'ENABLE_MILVUS', False):
            self._connect()
            self._ensure_collection()
        else:
            logger.info("Milvus connection disabled in settings (ENABLE_MILVUS=False)")
        
    def _connect(self):
        """Connect to Milvus server"""
        connections.connect(
            alias="default", 
            host=self.host,
            port=self.port,
            db_name=self.db_name
        )
        
    def _ensure_collection(self):
        """Ensure collection exists, create if not present"""
        logger.info("Entering _ensure_collection method")
        if not utility.has_collection(self.collection_name):
            logger.info(f"Collection {self.collection_name} does not exist, creating...")
            # Define collection schema
            fields = [
                FieldSchema(
                    name="id",
                    dtype=DataType.INT64,
                    is_primary=True,
                    auto_id=True
                ),
                FieldSchema(
                    name="embedding",
                    dtype=DataType.FLOAT_VECTOR,
                    dim=1024  
                ),
                FieldSchema(
                    name="content",    # Stores the actual content of the document chunk
                    dtype=DataType.VARCHAR,
                    max_length=4096
                ),
                FieldSchema(
                    name="metadata",   # Stores metadata of the document (JSON string)
                    dtype=DataType.VARCHAR,
                    max_length=1024
                ),
                FieldSchema(
                    name="source",     # Source info of original document (file path or URL)
                    dtype=DataType.VARCHAR,
                    max_length=512
                ),
                FieldSchema(
                    name="doc_type",   # Document type (pdf/doc/excel, etc.)
                    dtype=DataType.VARCHAR,
                    max_length=32
                ),
                FieldSchema(
                    name="chunk_id",   # Chunk ID used to track different parts of document
                    dtype=DataType.VARCHAR,
                    max_length=128
                ),
                FieldSchema(
                    name="upload_time",
                    dtype=DataType.VARCHAR,
                    max_length=50
                )  # Field for upload timestamp
            ]
            schema = CollectionSchema(fields=fields, description="Knowledge base")
            collection = Collection(name=self.collection_name, schema=schema)
            logger.info("Collection created successfully")
            
            # Create index
            logger.info("Creating index...")
            index_params = {
                "metric_type": "COSINE",
                "index_type": "HNSW",
                "params": {"M": 8, "efConstruction": 64}
            }
            collection.create_index(
                field_name="embedding", 
                index_params=index_params
            )
            logger.info("Index created successfully")
            collection.load()
            return collection
        else:
            logger.info(f"Collection {self.collection_name} already exists, returning directly")
            collection = Collection(self.collection_name)
            collection.load()
            return collection
        
    def add_data(self, data: List[Dict[str, Any]]):
        """Add documents to vector database"""
        logger.info("Entering add_data method")
        collection = Collection(self.collection_name)

        # Truncation logic: iterate through data to ensure content does not exceed 4096
        safe_data = []
        for item in data:
            content = item.get("content", "")
            if len(content) > 4096:
                logger.warning(f"Content length {len(content)} exceeds 4096, truncating.")
                item["content"] = content[:4092] + "..."
            safe_data.append(item)
        
        # Insert processed safe_data
        collection.insert(safe_data)
        collection.flush()
    
    def delete_by_source(self, source_path: str):
        """Delete all document records by source file path"""
        logger.info(f"Starting deletion of vector records for file: {source_path}")
        collection = Collection(self.collection_name)
        
        try:
            # Build deletion expression: delete by source field
            expr = f'source == "{source_path}"'
            collection.delete(expr)
            collection.flush()
            logger.info(f"Successfully deleted vector records for file: {source_path}")
        except Exception as e:
            logger.error(f"Failed to delete vector records for file {source_path}: {str(e)}")
            raise
        
    def search(self, query_vector: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
        """Search for most similar documents"""
        collection = Collection(self.collection_name)
        collection.load()
        
        search_params = {"metric_type": "COSINE", "params": {"ef": 32}}
        results = collection.search(
            data=[query_vector], 
            anns_field="embedding", 
            param=search_params,
            limit=top_k,
            output_fields=[
                "content", "metadata", "source", 
                "doc_type", "chunk_id", "upload_time"
            ]
        )
        
        ret = []
        for hits in results:
            for hit in hits:
                ret.append({
                    "id": hit.id,
                    "score": hit.score,
                    "content": hit.entity.get("content"),
                    "metadata": hit.entity.get("metadata"),
                    "source": hit.entity.get("source"),
                    "doc_type": hit.entity.get("doc_type"),
                    "chunk_id": hit.entity.get("chunk_id"),
                    "upload_time": hit.entity.get("upload_time")
                })
        
        collection.release()
        return ret 