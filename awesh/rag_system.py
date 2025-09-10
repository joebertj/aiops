#!/usr/bin/env python3
"""
Local RAG (Retrieval-Augmented Generation) system for awesh prompt context enhancement.
This system uses ChromaDB as a local vector database with sentence transformers for semantic search.
"""

import os
import re
import json
import time
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

try:
    from sentence_transformers import SentenceTransformer
    import chromadb
    from chromadb.config import Settings
    HAVE_VECTOR_DB = True
except ImportError:
    HAVE_VECTOR_DB = False
    print("⚠️ Vector database dependencies not available. Install with: pip install sentence-transformers chromadb")


@dataclass
class RAGDocument:
    """Represents a document in the RAG system"""
    id: str
    content: str
    metadata: Dict
    embedding: Optional[List[float]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class RAGResult:
    """Result from RAG retrieval"""
    document: RAGDocument
    similarity_score: float
    relevance_context: str


class LocalRAGSystem:
    """
    Local RAG system for awesh prompt context enhancement using ChromaDB vector database.
    
    Features:
    - Document storage with embeddings in ChromaDB
    - Semantic search using sentence transformers
    - Entity extraction and indexing
    - Context-aware prompt enhancement
    """
    
    def __init__(self, db_path: str = "./awesh_rag_chroma", model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize the RAG system with ChromaDB.
        
        Args:
            db_path: Path to ChromaDB storage directory
            model_name: Sentence transformer model name
        """
        self.db_path = db_path
        self.model_name = model_name
        self.model = None
        self.chroma_client = None
        self.collection = None
        
        # Initialize vector database
        self._init_vector_database()
        
        # Load embedding model if available
        if HAVE_VECTOR_DB:
            try:
                self.model = SentenceTransformer(model_name)
                print(f"✅ Loaded embedding model: {model_name}")
            except Exception as e:
                print(f"⚠️ Failed to load embedding model: {e}")
                self.model = None
        else:
            print("⚠️ Vector database dependencies not available, using fallback search")
    
    def _init_vector_database(self):
        """Initialize ChromaDB vector database"""
        if not HAVE_VECTOR_DB:
            return
            
        try:
            # Create ChromaDB client with persistent storage
            self.chroma_client = chromadb.PersistentClient(
                path=self.db_path,
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            
            # Get or create collection
            self.collection = self.chroma_client.get_or_create_collection(
                name="awesh_documents",
                metadata={"description": "Awesh RAG system documents"}
            )
            
            print(f"✅ Initialized ChromaDB at: {self.db_path}")
            
        except Exception as e:
            print(f"❌ Failed to initialize ChromaDB: {e}")
            self.chroma_client = None
            self.collection = None
    
    def add_document(self, doc_id: str, content: str, metadata: Optional[Dict] = None) -> bool:
        """
        Add a document to the RAG system using ChromaDB.
        
        Args:
            doc_id: Unique identifier for the document
            content: Document content
            metadata: Optional metadata dictionary
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not self.collection:
                print("❌ ChromaDB collection not initialized")
                return False
            
            # Prepare metadata with timestamp
            doc_metadata = {
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "content_length": len(content)
            }
            if metadata:
                doc_metadata.update(metadata)
            
            # Add document to ChromaDB collection
            self.collection.add(
                documents=[content],
                metadatas=[doc_metadata],
                ids=[doc_id]
            )
            
            print(f"✅ Added document to ChromaDB: {doc_id}")
            return True
            
        except Exception as e:
            print(f"❌ Error adding document {doc_id}: {e}")
            return False
    
    def _extract_and_store_entities(self, cursor, doc_id: str, content: str):
        """Extract entities from content and store them"""
        # Clear existing entities for this document
        cursor.execute("DELETE FROM entities WHERE document_id = ?", (doc_id,))
        
        # Entity extraction patterns
        patterns = {
            'ip': r'\b(?:\d{1,3}\.){3}\d{1,3}\b',
            'hostname': r'\b[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*\b',
            'email': r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
            'url': r'https?://[^\s]+',
            'port': r':(\d{1,5})\b',
            'path': r'/[^\s]*',
            'command': r'\b(?:kubectl|docker|git|npm|pip|apt|yum|systemctl|service)\s+\w+',
            'file_extension': r'\.\w{2,4}\b',
            'version': r'v?\d+\.\d+(?:\.\d+)?',
        }
        
        for entity_type, pattern in patterns.items():
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    match = match[0] if match[0] else match[1]
                if match and len(match.strip()) > 0:
                    cursor.execute("""
                        INSERT INTO entities (document_id, entity_type, entity_value)
                        VALUES (?, ?, ?)
                    """, (doc_id, entity_type, match.strip()))
    
    def search_semantic(self, query: str, limit: int = 5, threshold: float = 0.3) -> List[RAGResult]:
        """
        Perform semantic search using embeddings.
        
        Args:
            query: Search query
            limit: Maximum number of results
            threshold: Minimum similarity threshold
            
        Returns:
            List of RAGResult objects
        """
        if not self.model:
            return self.search_keyword(query, limit)
        
        try:
            # Generate query embedding
            query_embedding = self.model.encode([query])[0]
            
            # Search database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT id, content, metadata, embedding FROM documents WHERE embedding IS NOT NULL")
            results = []
            
            for row in cursor.fetchall():
                doc_id, content, metadata_json, embedding_json = row
                
                if embedding_json:
                    doc_embedding = json.loads(embedding_json)
                    
                    # Calculate cosine similarity
                    similarity = self._cosine_similarity(query_embedding, doc_embedding)
                    
                    if similarity >= threshold:
                        metadata = json.loads(metadata_json) if metadata_json else {}
                        document = RAGDocument(
                            id=doc_id,
                            content=content,
                            metadata=metadata,
                            embedding=doc_embedding
                        )
                        
                        results.append(RAGResult(
                            document=document,
                            similarity_score=similarity,
                            relevance_context=self._extract_relevant_context(content, query)
                        ))
            
            conn.close()
            
            # Sort by similarity and return top results
            results.sort(key=lambda x: x.similarity_score, reverse=True)
            return results[:limit]
            
        except Exception as e:
            print(f"❌ Error in semantic search: {e}")
            return []
    
    def search_keyword(self, query: str, limit: int = 5) -> List[RAGResult]:
        """
        Perform keyword-based search using entities and content.
        
        Args:
            query: Search query
            limit: Maximum number of results
            
        Returns:
            List of RAGResult objects
        """
        try:
            # Extract keywords from query
            keywords = re.findall(r'\b\w+\b', query.lower())
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Search in entities first
            entity_matches = set()
            for keyword in keywords:
                cursor.execute("""
                    SELECT DISTINCT document_id FROM entities 
                    WHERE entity_value LIKE ? OR entity_type LIKE ?
                """, (f'%{keyword}%', f'%{keyword}%'))
                entity_matches.update([row[0] for row in cursor.fetchall()])
            
            # Search in content
            content_matches = set()
            for keyword in keywords:
                cursor.execute("""
                    SELECT id FROM documents 
                    WHERE content LIKE ?
                """, (f'%{keyword}%',))
                content_matches.update([row[0] for row in cursor.fetchall()])
            
            # Combine matches
            all_matches = entity_matches.union(content_matches)
            
            # Get documents
            results = []
            for doc_id in list(all_matches)[:limit]:
                cursor.execute("SELECT id, content, metadata FROM documents WHERE id = ?", (doc_id,))
                row = cursor.fetchone()
                
                if row:
                    doc_id, content, metadata_json = row
                    metadata = json.loads(metadata_json) if metadata_json else {}
                    
                    # Calculate relevance score based on keyword matches
                    relevance_score = self._calculate_keyword_relevance(content, keywords)
                    
                    document = RAGDocument(
                        id=doc_id,
                        content=content,
                        metadata=metadata
                    )
                    
                    results.append(RAGResult(
                        document=document,
                        similarity_score=relevance_score,
                        relevance_context=self._extract_relevant_context(content, query)
                    ))
            
            conn.close()
            
            # Sort by relevance
            results.sort(key=lambda x: x.similarity_score, reverse=True)
            return results
            
        except Exception as e:
            print(f"❌ Error in keyword search: {e}")
            return []
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        try:
            vec1 = np.array(vec1)
            vec2 = np.array(vec2)
            
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            return dot_product / (norm1 * norm2)
        except Exception:
            return 0.0
    
    def _calculate_keyword_relevance(self, content: str, keywords: List[str]) -> float:
        """Calculate relevance score based on keyword matches"""
        content_lower = content.lower()
        matches = sum(1 for keyword in keywords if keyword in content_lower)
        return matches / len(keywords) if keywords else 0.0
    
    def _extract_relevant_context(self, content: str, query: str, max_length: int = 200) -> str:
        """Extract relevant context around query terms"""
        query_words = re.findall(r'\b\w+\b', query.lower())
        content_lower = content.lower()
        
        # Find the best match position
        best_pos = 0
        best_score = 0
        
        for i, word in enumerate(query_words):
            pos = content_lower.find(word)
            if pos != -1:
                # Count nearby query words
                nearby_words = content_lower[max(0, pos-100):pos+100]
                score = sum(1 for qw in query_words if qw in nearby_words)
                if score > best_score:
                    best_score = score
                    best_pos = pos
        
        # Extract context around best position
        start = max(0, best_pos - max_length // 2)
        end = min(len(content), start + max_length)
        
        context = content[start:end]
        if start > 0:
            context = "..." + context
        if end < len(content):
            context = context + "..."
        
        return context.strip()
    
    def get_prompt_context(self, user_input: str, max_context_length: int = 500) -> str:
        """
        Get relevant context for prompt enhancement based on user input.
        
        Args:
            user_input: User's input prompt
            max_context_length: Maximum length of context to return
            
        Returns:
            Context string to enhance the prompt
        """
        # Search for relevant documents
        results = self.search_semantic(user_input, limit=3, threshold=0.2)
        
        if not results:
            return ""
        
        # Build context from results
        context_parts = []
        current_length = 0
        
        for result in results:
            if current_length >= max_context_length:
                break
            
            # Add relevance context
            context_part = f"[{result.document.id}] {result.relevance_context}"
            
            if current_length + len(context_part) <= max_context_length:
                context_parts.append(context_part)
                current_length += len(context_part)
            else:
                # Truncate if needed
                remaining = max_context_length - current_length
                if remaining > 50:  # Only add if there's meaningful space
                    context_parts.append(context_part[:remaining] + "...")
                break
        
        return "\n".join(context_parts)
    
    def list_documents(self) -> List[Dict]:
        """List all documents in the RAG system"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, content, metadata, created_at, updated_at 
                FROM documents 
                ORDER BY updated_at DESC
            """)
            
            documents = []
            for row in cursor.fetchall():
                doc_id, content, metadata_json, created_at, updated_at = row
                metadata = json.loads(metadata_json) if metadata_json else {}
                
                documents.append({
                    'id': doc_id,
                    'content_length': len(content),
                    'metadata': metadata,
                    'created_at': created_at,
                    'updated_at': updated_at
                })
            
            conn.close()
            return documents
            
        except Exception as e:
            print(f"❌ Error listing documents: {e}")
            return []
    
    def delete_document(self, doc_id: str) -> bool:
        """Delete a document from the RAG system"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Delete document and associated entities
            cursor.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
            cursor.execute("DELETE FROM entities WHERE document_id = ?", (doc_id,))
            
            conn.commit()
            conn.close()
            
            print(f"✅ Deleted document: {doc_id}")
            return True
            
        except Exception as e:
            print(f"❌ Error deleting document {doc_id}: {e}")
            return False
    
    def get_stats(self) -> Dict:
        """Get RAG system statistics"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Document count
            cursor.execute("SELECT COUNT(*) FROM documents")
            doc_count = cursor.fetchone()[0]
            
            # Entity count by type
            cursor.execute("""
                SELECT entity_type, COUNT(*) 
                FROM entities 
                GROUP BY entity_type 
                ORDER BY COUNT(*) DESC
            """)
            entity_stats = dict(cursor.fetchall())
            
            # Total entities
            cursor.execute("SELECT COUNT(*) FROM entities")
            total_entities = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                'documents': doc_count,
                'entities': total_entities,
                'entity_types': entity_stats,
                'model_loaded': self.model is not None,
                'model_name': self.model_name if self.model else None
            }
            
        except Exception as e:
            print(f"❌ Error getting stats: {e}")
            return {}


# Global RAG system instance
_rag_system = None


def get_rag_system() -> LocalRAGSystem:
    """Get the global RAG system instance"""
    global _rag_system
    if _rag_system is None:
        _rag_system = LocalRAGSystem()
    return _rag_system


def enhance_prompt_with_context(user_input: str, max_context_length: int = 500) -> str:
    """
    Enhance user prompt with relevant context from RAG system.
    
    Args:
        user_input: User's input prompt
        max_context_length: Maximum length of context to add
        
    Returns:
        Enhanced prompt with context
    """
    rag = get_rag_system()
    context = rag.get_prompt_context(user_input, max_context_length)
    
    if context:
        return f"{user_input}\n\nContext:\n{context}"
    else:
        return user_input


if __name__ == "__main__":
    # Test the RAG system
    rag = LocalRAGSystem()
    
    # Add some test documents
    rag.add_document("k8s_basics", """
    Kubernetes is a container orchestration platform.
    Common commands: kubectl get pods, kubectl apply -f deployment.yaml
    Namespaces: default, kube-system, monitoring
    """, {"category": "kubernetes", "level": "beginner"})
    
    rag.add_document("docker_commands", """
    Docker commands for container management:
    docker build -t myapp .
    docker run -p 8080:80 myapp
    docker ps -a
    docker logs container_id
    """, {"category": "docker", "level": "intermediate"})
    
    rag.add_document("git_workflow", """
    Git workflow for development:
    git clone <repo>
    git checkout -b feature-branch
    git add .
    git commit -m "message"
    git push origin feature-branch
    """, {"category": "git", "level": "beginner"})
    
    # Test search
    print("Testing semantic search...")
    results = rag.search_semantic("kubernetes pods", limit=2)
    for result in results:
        print(f"Score: {result.similarity_score:.3f}")
        print(f"Context: {result.relevance_context}")
        print()
    
    # Test prompt enhancement
    print("Testing prompt enhancement...")
    enhanced = enhance_prompt_with_context("show me kubernetes pods")
    print(f"Enhanced prompt:\n{enhanced}")
    
    # Show stats
    print("\nRAG System Stats:")
    stats = rag.get_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")
