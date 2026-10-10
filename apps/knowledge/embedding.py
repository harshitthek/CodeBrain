from typing import List, Union
from abc import ABC, abstractmethod
import os
import time
import logging
import requests
import numpy as np
from concurrent.futures import ThreadPoolExecutor, as_completed
from django.conf import settings

logger = logging.getLogger(__name__)


class BaseEmbedder(ABC):
    """Base class for embedding models"""
    
    @abstractmethod
    def get_embeddings(self, texts: Union[str, List[str]], show_progress_bar: bool = False) -> List[List[float]]:
        """Get embeddings for text"""
        pass


class BGEM3Embedder(BaseEmbedder):
    """BGE-M3 local embedding model service"""
    
    def __init__(self, model_name: str = "BAAI/bge-m3"):
        """
        Initialize BGE-M3 embedding model
        
        Args:
            model_name: Model name, default 'BAAI/bge-m3'
        """
        logger.info("Loading BGE-M3 model...")
        try:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer(model_name)
        except ImportError:
            raise ImportError("sentence-transformers is not installed. Please install it to use BGEM3Embedder.")
        
    def get_embeddings(self, texts: Union[str, List[str]], show_progress_bar: bool = False) -> List[List[float]]:
        """Get embeddings for text"""
        if isinstance(texts, str):
            texts = [texts]
        embeddings = self.model.encode(sentences=texts, normalize_embeddings=True, show_progress_bar=show_progress_bar)
        return embeddings.tolist()
    
    def compute_similarity(self, text1: str, text2: str) -> float:
        """Compute cosine similarity between two texts"""
        embeddings = self.get_embeddings([text1, text2])
        similarity = np.dot(embeddings[0], embeddings[1])
        return similarity


class AliyunEmbedder(BaseEmbedder):
    """Aliyun text-embedding-v4 embedding model service"""
    
    def __init__(self, api_key: str = None, base_url: str = None, model: str = None, batch_size: int = None):
        """
        Initialize Aliyun embedding model
        
        Args:
            api_key: Aliyun API Key
            base_url: Aliyun API base URL
            model: Model name
            batch_size: Max texts per request (Aliyun limits to 10)
        """
        config = getattr(settings, 'ALIYUN_EMBEDDING_CONFIG', {})
        self.api_key = api_key or config.get('api_key')
        self.base_url = base_url or config.get('base_url')
        self.model = model or config.get('model')
        self.batch_size = batch_size if batch_size is not None else config.get('batch_size', 10)
        self.embeddings_url = self.base_url
        
        if not self.api_key:
            raise ValueError("Aliyun API Key not configured. Please set QWEN_API_KEY environment variable or configure in settings.py")
        
        logger.info(f"Aliyun embedder initialized. Model: {self.model}, batch_size: {self.batch_size}")
    
    def _get_embedding_batch(self, texts: List[str]) -> List[List[float]]:
        """Batch get embeddings (single API call)"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "input": texts
        }
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = requests.post(
                    self.embeddings_url,
                    headers=headers,
                    json=payload,
                    timeout=30
                )
                response.raise_for_status()
                
                data = response.json()
                embeddings = []
                for item in data.get('data', []):
                    embedding = item.get('embedding', [])
                    embeddings.append(embedding)
                
                if len(embeddings) != len(texts):
                    raise ValueError(f"Returned embeddings count ({len(embeddings)}) does not match input texts count ({len(texts)})")
                
                return embeddings
                
            except requests.exceptions.RequestException as e:
                error_detail = ""
                if hasattr(e, 'response') and e.response is not None:
                    try:
                        error_detail = e.response.text
                    except:
                        error_detail = str(e.response)
                logger.error(f"Aliyun embeddings API call failed (attempt {attempt + 1}/{max_retries}): {str(e)}")
                logger.error(f"Error response detail: {error_detail}")
                logger.error(f"Request parameters: model={self.model}, texts count={len(texts)}, first text length={len(texts[0]) if texts else 0}")
                if attempt == max_retries - 1:
                    raise Exception(f"Aliyun embeddings API call failed: {str(e)}, detail: {error_detail}")
                time.sleep(1)
            except Exception as e:
                logger.error(f"Failed to parse Aliyun embeddings API response: {str(e)}")
                raise
    
    def get_embeddings(self, texts: Union[str, List[str]], show_progress_bar: bool = False) -> List[List[float]]:
        """
        Get embeddings for text using thread pool concurrency for performance.
        """
        if isinstance(texts, str):
            texts = [texts]
        
        if not texts:
            return []
        
        total_batches = (len(texts) + self.batch_size - 1) // self.batch_size
        logger.info(f"Generating embeddings for {len(texts)} texts across {total_batches} batches")
        
        batches = []
        for i in range(0, len(texts), self.batch_size):
            batch = texts[i:i + self.batch_size]
            batch_num = i // self.batch_size + 1
            batches.append((batch_num, batch))
        
        all_embeddings = [None] * len(texts)
        
        max_workers = min(10, total_batches)
        completed = 0
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_batch = {
                executor.submit(self._get_embedding_batch, batch): (batch_num, batch, idx)
                for idx, (batch_num, batch) in enumerate(batches)
            }
            
            for future in as_completed(future_to_batch):
                batch_num, batch, batch_idx = future_to_batch[future]
                try:
                    batch_embeddings = future.result()
                    start_idx = batch_idx * self.batch_size
                    for i, embedding in enumerate(batch_embeddings):
                        all_embeddings[start_idx + i] = embedding
                    
                    completed += 1
                    if completed % 50 == 0 or completed == total_batches:
                        logger.info(f"Embedding progress: {completed}/{total_batches} batches completed")
                        
                except Exception as e:
                    logger.error(f"Batch {batch_num}/{total_batches} embedding request failed: {str(e)}")
                    raise
        
        logger.info(f"All embedding requests completed, processed {len([e for e in all_embeddings if e is not None])} texts")
        return all_embeddings


def create_embedder():
    """Create embedder instance based on settings"""
    provider = getattr(settings, 'EMBEDDING_PROVIDER', 'local')
    
    if provider == 'aliyun':
        logger.info("Using Aliyun embedding model")
        return AliyunEmbedder()
    else:
        logger.info("Using local BGE-M3 embedding model")
        return BGEM3Embedder()


# Test block
if __name__ == "__main__":
    os.environ['PYTORCH_ENABLE_MPS_FALLBACK'] = '1'
    
    print("Initializing BGE-M3 embedding model...")
    embedder = BGEM3Embedder()
    
    print("\nTesting single text embedding...")
    text = "BGE-M3 is a powerful multilingual embedding model"
    embedding = embedder.get_embeddings(text)
    print(f"Embedding dimension: {len(embedding[0])}")
    print(f"First 5 dimensions: {embedding[0][:5]}")
    
    print("\nTesting multiple texts embedding...")
    texts = ["Hello, world", "Testing embedding", "BGE-M3 supports multiple languages"]
    embeddings = embedder.get_embeddings(texts)
    print(f"Embedding count: {len(embeddings)}")
    print(f"Embedding dimension: {len(embeddings[0])}")
    
    print("\nTesting text similarity...")
    text1 = "I love artificial intelligence technology"
    text2 = "AI technology is fascinating"
    text3 = "The weather is nice today"
    
    sim1 = embedder.compute_similarity(text1, text2)
    sim2 = embedder.compute_similarity(text1, text3)
    
    print(f"Similar text similarity: {sim1:.4f}")
    print(f"Dissimilar text similarity: {sim2:.4f}")
    
    print("\nTesting batch processing performance...")
    import time
    batch_texts = ["Sample text " + str(i) for i in range(10)]
    
    start_time = time.time()
    batch_embeddings = embedder.get_embeddings(batch_texts)
    end_time = time.time()
    
    print(f"Processing 10 texts took: {end_time - start_time:.2f}s")