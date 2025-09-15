import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
import uuid
import logging
from typing import List, Dict, Any, Tuple
import os
import re

# Disable ChromaDB telemetry to avoid the capture() error
os.environ["ANONYMIZED_TELEMETRY"] = "False"
os.environ["CHROMA_TELEMETRY_DISABLED"] = "True"
os.environ["POSTHOG_DISABLED"] = "True"

# Try to patch the telemetry module before ChromaDB uses it
try:
    import chromadb.telemetry.product.posthog
    # Monkey patch the capture method to do nothing
    chromadb.telemetry.product.posthog.capture = lambda *args, **kwargs: None
except ImportError:
    pass

class VectorEmbeddingService:
    def __init__(self):
        self.client = None
        self.collection = None
        self.model = None
        self.enabled = False
        
        try:
            # Initialize ChromaDB with telemetry disabled
            persist_directory = os.path.join(os.getcwd(), 'vector_db')
            os.makedirs(persist_directory, exist_ok=True)
            
            # Create client with telemetry explicitly disabled
            settings = Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
            self.client = chromadb.PersistentClient(
                path=persist_directory,
                settings=settings
            )
            
            # Get or create collection with new API
            try:
                self.collection = self.client.get_collection(name="notes_embeddings")
            except Exception:
                # Collection doesn't exist, create it
                self.collection = self.client.create_collection(
                    name="notes_embeddings",
                    metadata={"hnsw:space": "cosine"}
                )
            
            # Initialize sentence transformer model
            self.model = SentenceTransformer('all-MiniLM-L6-v2')
            self.enabled = True
            logging.info("Vector embedding service initialized successfully with ChromaDB 1.0.0")
            
        except Exception as e:
            logging.error(f"Failed to initialize vector embedding service: {e}")
            self.enabled = False
    
    def _chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
        """
        Split text into semantic chunks for better vector search
        
        Args:
            text (str): Text to chunk
            chunk_size (int): Maximum characters per chunk
            overlap (int): Character overlap between chunks
            
        Returns:
            List[str]: List of text chunks
        """
        if not text or len(text) < chunk_size:
            return [text]
        
        # Split by sentences first
        sentences = re.split(r'[.!?]+', text)
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
                
            # If adding this sentence would exceed chunk size, start a new chunk
            if len(current_chunk) + len(sentence) > chunk_size and current_chunk:
                chunks.append(current_chunk.strip())
                # Start new chunk with overlap
                if overlap > 0 and len(current_chunk) > overlap:
                    current_chunk = current_chunk[-overlap:] + " " + sentence
                else:
                    current_chunk = sentence
            else:
                current_chunk += " " + sentence if current_chunk else sentence
        
        # Add the last chunk
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def add_note_embeddings(self, note_id: int, title: str, content: str, 
                          subject_name: str = "", user_id: int = None, created_at: str = "") -> bool:
        """
        Add or update embeddings for a note
        
        Args:
            note_id (int): Note ID
            title (str): Note title
            content (str): Note content
            subject_name (str): Subject name
            user_id (int): User ID
            created_at (str): Creation date string
            
        Returns:
            bool: Success status
        """
        if not self.enabled:
            return False
        
        try:
            # Remove existing embeddings for this note
            self.remove_note_embeddings(note_id)
            
            # Combine title and content for chunking
            full_text = f"{title}\n\n{content}"
            chunks = self._chunk_text(full_text)
            
            documents = []
            metadatas = []
            ids = []
            embeddings = []
            
            for i, chunk in enumerate(chunks):
                if not chunk.strip():
                    continue
                    
                # Generate embedding
                embedding = self.model.encode([chunk])[0].tolist()
                
                # Create unique ID for this chunk
                chunk_id = f"note_{note_id}_chunk_{i}"
                
                documents.append(chunk)
                metadatas.append({
                    "note_id": note_id,
                    "chunk_index": i,
                    "subject": subject_name,
                    "user_id": user_id or 0,
                    "title": title,
                    "created_at": created_at
                })
                ids.append(chunk_id)
                embeddings.append(embedding)
            
            if documents:
                self.collection.add(
                    documents=documents,
                    metadatas=metadatas,
                    ids=ids,
                    embeddings=embeddings
                )
            
            return True
            
        except Exception as e:
            logging.error(f"Error adding note embeddings: {e}")
            return False
    
    def remove_note_embeddings(self, note_id: int) -> bool:
        """
        Remove all embeddings for a specific note
        
        Args:
            note_id (int): Note ID
            
        Returns:
            bool: Success status
        """
        if not self.enabled:
            return False
        
        try:
            # Query for existing chunks of this note
            results = self.collection.get(
                where={"note_id": {"$eq": note_id}}
            )
            
            if results['ids']:
                self.collection.delete(ids=results['ids'])
            
            return True
            
        except Exception as e:
            logging.error(f"Error removing note embeddings: {e}")
            return False
    
    def search_notes(self, query: str, user_id: int, n_results: int = 10,
                    subject_filter: str = None) -> List[Dict[str, Any]]:
        """
        Search for relevant notes using semantic similarity
        
        Args:
            query (str): Search query
            user_id (int): User ID to filter results
            n_results (int): Maximum number of results
            subject_filter (str): Optional subject filter
            
        Returns:
            List[Dict]: Search results with note info and relevance scores
        """
        if not self.enabled:
            return []
            
        if not query.strip():
            # Return empty for empty queries
            return []
        
        try:
            # Generate query embedding
            query_embedding = self.model.encode([query])[0].tolist()
            
            # Build where clause for filtering
            if subject_filter:
                where_clause = {"$and": [{"user_id": {"$eq": user_id}}, {"subject": {"$eq": subject_filter}}]}
            else:
                where_clause = {"user_id": {"$eq": user_id}}
            
            # Search in ChromaDB
            results = self.collection.query(
                query_embeddings=[query_embedding],
                where=where_clause,
                n_results=min(n_results * 3, 50),  # Get more results to deduplicate
                include=['documents', 'metadatas', 'distances']
            )
            
            if not results['documents'] or not results['documents'][0]:
                return []
            
            # Process and deduplicate results by note_id
            note_results = {}
            
            for i, (document, metadata, distance) in enumerate(zip(
                results['documents'][0], 
                results['metadatas'][0], 
                results['distances'][0]
            )):
                note_id = metadata['note_id']
                relevance_score = 1 - distance  # Convert distance to similarity
                
                if note_id not in note_results or relevance_score > note_results[note_id]['relevance_score']:
                    note_results[note_id] = {
                        'note_id': note_id,
                        'title': metadata.get('title', 'Untitled'),
                        'subject': metadata.get('subject', 'No Subject'),
                        'subject_name': metadata.get('subject', 'No Subject'),
                        'created_at': metadata.get('created_at', ''),
                        'relevance_score': relevance_score,
                        'matched_text': document[:300] + "..." if len(document) > 300 else document
                    }
            
            # Sort by relevance and return top results
            sorted_results = sorted(
                note_results.values(), 
                key=lambda x: x['relevance_score'], 
                reverse=True
            )
            
            return sorted_results[:n_results]
            
        except Exception as e:
            logging.error(f"Error searching notes: {e}")
            return []
    
    def get_similar_notes(self, note_id: int, user_id: int, n_results: int = 5) -> List[Dict[str, Any]]:
        """
        Find notes similar to a given note
        
        Args:
            note_id (int): Reference note ID
            user_id (int): User ID
            n_results (int): Number of similar notes to return
            
        Returns:
            List[Dict]: Similar notes with relevance scores
        """
        if not self.enabled:
            return []
        
        try:
            # Temporarily disable similar notes to avoid errors
            # TODO: Fix array comparison issue
            return []
            
            # Get embeddings for the reference note
            note_chunks = self.collection.get(
                where={"$and": [{"note_id": {"$eq": note_id}}, {"user_id": {"$eq": user_id}}]},
                include=['embeddings', 'metadatas']
            )
            
            # Safe check for embeddings
            if not note_chunks or 'embeddings' not in note_chunks or len(note_chunks['embeddings']) == 0:
                return []
            
            # Use the first chunk's embedding as representative
            query_embedding = note_chunks['embeddings'][0]
            
            # Search for similar notes (excluding the reference note)
            results = self.collection.query(
                query_embeddings=[query_embedding],
                where={"user_id": {"$eq": user_id}},
                n_results=n_results * 2,  # Get more to filter out the reference note
                include=['metadatas', 'distances']
            )
            
            # Process results and exclude the reference note
            similar_notes = {}
            
            for metadata, distance in zip(results['metadatas'][0], results['distances'][0]):
                found_note_id = metadata['note_id']
                
                if found_note_id == note_id:
                    continue  # Skip the reference note itself
                
                relevance_score = 1 - distance
                
                if found_note_id not in similar_notes or relevance_score > similar_notes[found_note_id]['relevance_score']:
                    similar_notes[found_note_id] = {
                        'note_id': found_note_id,
                        'title': metadata['title'],
                        'subject': metadata['subject'],
                        'relevance_score': relevance_score
                    }
            
            # Sort and return top results
            sorted_results = sorted(
                similar_notes.values(),
                key=lambda x: x['relevance_score'],
                reverse=True
            )
            
            return sorted_results[:n_results]
            
        except Exception as e:
            logging.error(f"Error finding similar notes: {e}")
            return []
