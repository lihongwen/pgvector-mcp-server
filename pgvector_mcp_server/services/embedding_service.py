"""Embedding service for pgvector MCP server."""

from typing import List

from ..config import get_settings
from ..exceptions import ConfigurationError, EmbeddingError

import logging
logger = logging.getLogger("embedding_service")

class EmbeddingService:
    """Service for generating text embeddings using DashScope."""

    def __init__(self):
        self.settings = get_settings()
        self._client = None
        self._dashscope_client = None

    def _get_client(self):
        """Get DashScope embedding client (lazy initialization)."""
        if self._dashscope_client is not None:
            return self._dashscope_client

        # Only use DashScope
        if not self.settings.dashscope_api_key:
            logger.error("DashScope API key not configured")
            raise ConfigurationError(
                "DashScope API key is required but not configured. "
                "Please set DASHSCOPE_API_KEY environment variable",
                code="MISSING_API_KEY"
            )

        try:
            import dashscope
            from dashscope import TextEmbedding
            dashscope.api_key = self.settings.dashscope_api_key
            self._dashscope_client = TextEmbedding
            self._client = "dashscope"
            logger.info("DashScope client initialized successfully")
            return self._dashscope_client
        except ImportError as e:
            logger.error(f"DashScope library not available: {e}")
            raise ConfigurationError(
                "DashScope library is required but not installed. "
                "Please install: pip install dashscope",
                code="MISSING_DEPENDENCY"
            ) from e

    def embed_text(self, text: str) -> List[float]:
        """Generate embedding for a single text using DashScope."""
        if not text or not text.strip():
            logger.warning("Empty text provided for embedding")
            raise EmbeddingError("Cannot generate embedding for empty text", code="EMPTY_INPUT")

        # If text exceeds API limit, this indicates a chunking system bug and should error
        if len(text) > 8192:
            logger.error(f"Text too long for embedding API - this indicates a chunking system bug! "
                        f"Length: {len(text)}, max allowed: 8192")
            raise EmbeddingError(
                f"Text too long: {len(text)} characters exceeds API limit of 8192. "
                f"This indicates the chunking system is not working correctly.",
                code="TEXT_TOO_LONG"
            )

        try:
            self._get_client()
            result = self._embed_with_dashscope(text)
            logger.debug(f"Generated embedding for single text (length: {len(text)})")
            return result
        except (ConfigurationError, EmbeddingError):
            # Re-raise our custom errors
            raise
        except Exception as e:
            logger.error(f"Unexpected error in embed_text: {e}, text length: {len(text)}")
            raise EmbeddingError(f"Failed to generate embedding: {e}") from e

    def embed_texts(self, texts: List[str], batch_size: int = 10) -> List[List[float]]:
        """Generate embeddings for multiple texts with batch processing."""
        if not texts:
            return []

        client = self._get_client()
        all_embeddings = []

        # Process texts in batches
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            try:
                # DashScope supports batch processing
                response = client.call(
                    model="text-embedding-v4",
                    input=batch
                )

                if response.status_code == 200:
                    batch_embeddings = []
                    for embedding_data in response.output['embeddings']:
                        embedding = embedding_data['embedding']
                        # Apply MRL transform and L2 normalization
                        if len(embedding) != 1024:
                            embedding = self._mrl_transform_to_1024(embedding)
                        embedding = self._l2_normalize_vector(embedding)
                        batch_embeddings.append(embedding)

                    all_embeddings.extend(batch_embeddings)
                    logger.debug(f"Processed batch {i//batch_size + 1}, embeddings: {len(batch)}")
                else:
                    logger.error(f"DashScope batch embedding failed: {response}")
                    # Fallback to individual processing
                    for text in batch:
                        all_embeddings.append(self.embed_text(text))

            except Exception as e:
                logger.warning(f"Batch embedding failed, falling back to individual processing: {e}")
                # Fallback to individual processing
                for text in batch:
                    all_embeddings.append(self.embed_text(text))

        return all_embeddings

    def _embed_with_dashscope(self, text: str) -> List[float]:
        """Generate embedding using DashScope."""
        try:
            from dashscope import TextEmbedding

            response = TextEmbedding.call(
                model="text-embedding-v4",
                input=text
            )

            if response.status_code == 200:
                embedding = response.output['embeddings'][0]['embedding']
                # Use MRL transform to 1024 dimensions
                if len(embedding) != 1024:
                    embedding = self._mrl_transform_to_1024(embedding)
                    logger.info(f"Using MRL transform from {len(response.output['embeddings'][0]['embedding'])} to 1024 dimensions")

                # L2 normalize vector for optimized cosine distance calculation
                embedding = self._l2_normalize_vector(embedding)
                logger.debug("Applied L2 normalization, vector length normalized to 1")

                return embedding
            else:
                logger.error(f"DashScope embedding failed: {response}")
                raise Exception(f"DashScope API error: {response}")

        except Exception as e:
            logger.error(f"DashScope embedding error: {e}")
            raise

    def _mrl_transform_to_1024(self, embedding: list) -> list:
        """Use MRL (Multi-Representation Learning) to transform vector to 1024 dimensions"""
        import numpy as np

        input_dim = len(embedding)
        target_dim = 1024

        if input_dim == target_dim:
            return embedding

        # Convert to numpy array
        vec = np.array(embedding, dtype=np.float32)

        if input_dim > target_dim:
            # Dimensionality reduction: use chunked averaging + weighting to preserve important info
            chunk_size = input_dim // target_dim
            remainder = input_dim % target_dim

            result = []
            idx = 0

            for i in range(target_dim):
                # Dynamically adjust chunk size to handle remainder
                current_chunk_size = chunk_size + (1 if i < remainder else 0)
                chunk = vec[idx:idx + current_chunk_size]

                # Use L2 norm weighted averaging to preserve semantic info
                chunk_norm = np.linalg.norm(chunk)
                if chunk_norm > 0:
                    weighted_avg = np.mean(chunk) * (chunk_norm / np.sqrt(current_chunk_size))
                else:
                    weighted_avg = np.mean(chunk)

                result.append(float(weighted_avg))
                idx += current_chunk_size

            return result

        else:
            # Dimensionality expansion: use interpolation strategy
            try:
                # Use linear interpolation
                old_indices = np.linspace(0, 1, input_dim)
                new_indices = np.linspace(0, 1, target_dim)
                interpolated = np.interp(new_indices, old_indices, vec)

                # Normalize to keep vector norm relatively stable
                original_norm = np.linalg.norm(vec)
                new_norm = np.linalg.norm(interpolated)
                if new_norm > 0:
                    interpolated = interpolated * (original_norm / new_norm)

                return interpolated.tolist()

            except Exception:
                # If interpolation fails, use repeat padding strategy
                scale_factor = target_dim / input_dim
                result = []

                for i in range(input_dim):
                    repeat_count = int(scale_factor)
                    if i < target_dim % input_dim:
                        repeat_count += 1
                    result.extend([vec[i]] * repeat_count)

                return result[:target_dim]

    def _l2_normalize_vector(self, vector: list) -> list:
        """L2 normalize vector to ensure vector length is 1, optimize cosine distance calculation"""
        import numpy as np

        vec = np.array(vector, dtype=np.float32)
        norm = np.linalg.norm(vec)

        if norm == 0:
            logger.warning("Vector norm is 0, cannot perform L2 normalization")
            return vector

        normalized = vec / norm
        return normalized.tolist()

    def check_api_status(self) -> bool:
        """Check if DashScope embedding service is available."""
        try:
            client = self._get_client()
            return client == "dashscope"
        except Exception:
            return False
