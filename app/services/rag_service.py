"""
RAG (Retrieval-Augmented Generation) Service

This service handles knowledge retrieval using vector similarity search
with pgvector for enhanced AI chat responses.
"""
import uuid
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.repositories.ai_chat_repository import AIChatRepository
from app.models.ai_chat import DocumentChunk
from app.models.chat_configuration import KnowledgeSource
from app.core.ai_chat_config import get_ai_chat_settings
from app.services.base import BaseService


class RAGService(BaseService):
    """Service for knowledge retrieval and vector similarity search."""
    
    def __init__(self, db: Session):
        super().__init__(db, AIChatRepository)
        self.ai_chat_repo = self.repository
        self.settings = get_ai_chat_settings()
    
    async def index_knowledge_source(self, knowledge_source: KnowledgeSource) -> None:
        """Index a knowledge source by creating document chunks with embeddings."""
        try:
            # Read the content from the knowledge source
            content = await self._extract_content(knowledge_source)
            
            # Split content into chunks
            chunks = self._split_into_chunks(content)
            
            # Create document chunks with embeddings
            for i, chunk_content in enumerate(chunks):
                # Generate embedding (placeholder - would use OpenAI embeddings in production)
                embedding = await self._generate_embedding(chunk_content)
                
                chunk_data = {
                    "id": str(uuid.uuid4()),
                    "knowledge_source_id": knowledge_source.id,
                    "content": chunk_content,
                    "embedding": embedding,
                    "chunk_index": i,
                    "metadata": {
                        "source_file": knowledge_source.file_name,
                        "chunk_size": len(chunk_content),
                        "processing_date": datetime.utcnow().isoformat()
                    },
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
                
                self.ai_chat_repo.create_document_chunk(chunk_data)
            
            # Update knowledge source status
            self.ai_chat_repo.update_knowledge_source(knowledge_source.id, {
                "processing_status": "indexed",
                "updated_at": datetime.utcnow()
            })
            
        except Exception as e:
            # Update knowledge source with error status
            self.ai_chat_repo.update_knowledge_source(knowledge_source.id, {
                "processing_status": "error",
                "metadata": {
                    **knowledge_source.metadata,
                    "error": str(e)
                },
                "updated_at": datetime.utcnow()
            })
            raise HTTPException(status_code=500, detail=f"Failed to index knowledge source: {str(e)}")
    
    async def search_knowledge(
        self, 
        query: str, 
        strategy_id: Optional[str] = None,
        limit: int = 5,
        similarity_threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """Search for relevant knowledge using vector similarity."""
        try:
            # Generate embedding for the query
            query_embedding = await self._generate_embedding(query)
            
            # Get knowledge sources for the strategy
            knowledge_source_ids = None
            if strategy_id:
                strategy = self.ai_chat_repo.get_strategy_by_id(strategy_id)
                if strategy and strategy.knowledge_source_ids:
                    knowledge_source_ids = strategy.knowledge_source_ids
            
            # Perform vector similarity search
            similar_chunks = self.ai_chat_repo.search_similar_chunks(
                query_embedding=query_embedding,
                knowledge_source_ids=knowledge_source_ids,
                limit=limit,
                similarity_threshold=similarity_threshold
            )
            
            # Format results
            results = []
            for chunk, similarity in similar_chunks:
                results.append({
                    "content": chunk.content,
                    "similarity": similarity,
                    "source": {
                        "id": chunk.knowledge_source_id,
                        "file_name": chunk.metadata.get("source_file", "unknown"),
                        "chunk_index": chunk.chunk_index
                    },
                    "metadata": chunk.metadata
                })
            
            return results
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Knowledge search failed: {str(e)}")
    
    async def get_relevant_context(
        self, 
        session_id: str, 
        user_message: str,
        max_context_length: int = 2000
    ) -> str:
        """Get relevant context for AI response generation."""
        try:
            # Get session to determine strategy
            session = self.ai_chat_repo.get_session_by_id(session_id)
            if not session:
                return ""
            
            # Search for relevant knowledge
            knowledge_results = await self.search_knowledge(
                query=user_message,
                strategy_id=session.strategy_id,
                limit=3
            )
            
            # Build context string
            context_parts = []
            current_length = 0
            
            for result in knowledge_results:
                content = result["content"]
                if current_length + len(content) > max_context_length:
                    # Truncate if needed
                    remaining_length = max_context_length - current_length
                    if remaining_length > 100:  # Only add if meaningful length remains
                        context_parts.append(content[:remaining_length] + "...")
                    break
                
                context_parts.append(content)
                current_length += len(content)
            
            return "\n\n".join(context_parts)
            
        except Exception as e:
            # Log error but don't fail the conversation
            print(f"Error getting relevant context: {str(e)}")
            return ""
    
    def get_knowledge_source_chunks(
        self, 
        knowledge_source_id: str,
        limit: Optional[int] = None
    ) -> List[DocumentChunk]:
        """Get all chunks for a knowledge source."""
        return self.ai_chat_repo.get_chunks_by_knowledge_source(knowledge_source_id, limit=limit)
    
    async def reindex_knowledge_source(self, knowledge_source_id: str) -> None:
        """Reindex a knowledge source (delete existing chunks and recreate)."""
        # Delete existing chunks
        self.ai_chat_repo.delete_chunks_by_knowledge_source(knowledge_source_id)
        
        # Get knowledge source and reindex
        knowledge_source = self.ai_chat_repo.get_knowledge_source_by_id(knowledge_source_id)
        if knowledge_source:
            await self.index_knowledge_source(knowledge_source)
    
    async def _extract_content(self, knowledge_source: KnowledgeSource) -> str:
        """Extract text content from knowledge source."""
        # This is a placeholder implementation
        # In production, this would handle different file types (PDF, DOCX, etc.)
        
        # For now, assume content is stored in metadata or use file_path
        if "content" in knowledge_source.metadata:
            return knowledge_source.metadata["content"]
        
        # Placeholder content based on file type
        file_extension = knowledge_source.file_name.split(".")[-1].lower()
        
        if file_extension == "txt":
            return f"Sample text content from {knowledge_source.file_name}"
        elif file_extension == "pdf":
            return f"Sample PDF content extracted from {knowledge_source.file_name}"
        elif file_extension == "docx":
            return f"Sample Word document content from {knowledge_source.file_name}"
        else:
            return f"Content from {knowledge_source.file_name} (format: {file_extension})"
    
    def _split_into_chunks(self, content: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
        """Split content into overlapping chunks."""
        if len(content) <= chunk_size:
            return [content]
        
        chunks = []
        start = 0
        
        while start < len(content):
            end = start + chunk_size
            
            # Try to break at sentence boundary
            if end < len(content):
                # Look for sentence ending within the overlap region
                sentence_end = content.rfind(". ", start + chunk_size - overlap, end)
                if sentence_end > start:
                    end = sentence_end + 1
            
            chunk = content[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            # Move start position with overlap
            start = end - overlap
            if start >= len(content):
                break
        
        return chunks
    
    async def _generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text (placeholder implementation)."""
        # This is a placeholder implementation
        # In production, this would use OpenAI's embedding API or similar
        
        # Return a mock embedding vector (1536 dimensions for OpenAI ada-002)
        import hashlib
        import struct
        
        # Generate deterministic but realistic-looking embedding
        hash_bytes = hashlib.md5(text.encode()).digest()
        
        # Create 1536-dimensional vector from hash
        embedding = []
        for i in range(1536):
            # Use hash bytes to generate pseudo-random float between -1 and 1
            byte_index = i % len(hash_bytes)
            float_val = (hash_bytes[byte_index] / 255.0) * 2 - 1
            embedding.append(float_val)
        
        # Normalize the vector
        magnitude = sum(x * x for x in embedding) ** 0.5
        if magnitude > 0:
            embedding = [x / magnitude for x in embedding]
        
        return embedding
