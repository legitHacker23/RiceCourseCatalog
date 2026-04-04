import os
import json
import pickle
import numpy as np
from typing import List, Dict, Tuple, Optional
import logging

# Prevent multiprocessing issues
os.environ['TOKENIZERS_PARALLELISM'] = 'false'

logger = logging.getLogger(__name__)

class RiceVectorStore:
    """Simplified vector store for Rice course data"""
    
    def __init__(self, model_name: str = 'sentence-transformers/all-MiniLM-L6-v2'):
        self.model = None
        self.index = None
        self.documents = []
        self.embeddings = None
        self.index_path = 'data/processed/faiss_index.bin'
        self.docs_path = 'data/processed/documents.pkl'
        
        # Try to import sentence_transformers, but don't fail if not available
        try:
            from sentence_transformers import SentenceTransformer
            self.SentenceTransformer = SentenceTransformer
            self.sentence_transformers_available = True
        except ImportError:
            logger.warning("sentence_transformers not available. Using fallback mode.")
            self.sentence_transformers_available = False
        
        # Try to import faiss with safety measures
        try:
            import faiss
            # Configure FAISS for single-threaded operation to avoid segfaults
            faiss.omp_set_num_threads(1)
            self.faiss = faiss
            self.faiss_available = True
            logger.info("✅ FAISS loaded successfully with single-threaded mode")
        except ImportError:
            logger.warning("faiss not available. Using fallback mode.")
            self.faiss_available = False
        except Exception as e:
            logger.warning(f"FAISS import failed: {e}. Using fallback mode.")
            self.faiss_available = False
        
    def load_and_index_courses(self, force_rebuild: bool = False):
        """Load courses and create/load vector index"""
        
        # Try to load existing index
        if not force_rebuild and self._load_existing_index():
            logger.info(f"✅ Loaded existing vector index with {len(self.documents)} documents")
            return
            
        logger.info("🔄 Building new vector index...")
        
        # Load course data
        self._load_course_documents()
        
        if not self.sentence_transformers_available:
            logger.warning("⚠️ sentence_transformers not available. Using simple text search.")
            return
        
        # Create embeddings
        self._create_embeddings()
        
        # Build FAISS index
        if self.faiss_available:
            self._build_faiss_index()
            # Save index
            self._save_index()
        
        logger.info(f"✅ Built vector index with {len(self.documents)} documents")
    
    def _load_course_documents(self):
        """Load and prepare course documents"""
        self.documents = []
        
        # Try multiple possible paths for the data file
        possible_paths = [
            'data/organized/rice_organized_data.json',
            '../data/organized/rice_organized_data.json',
            os.path.join(os.path.dirname(__file__), '..', 'data', 'organized', 'rice_organized_data.json')
        ]
        
        organized_data = None
        for path in possible_paths:
            try:
                abs_path = os.path.abspath(path)
                if os.path.exists(abs_path):
                    with open(abs_path, 'r') as f:
                        organized_data = json.load(f)
                    logger.info(f"✅ Loaded organized data from: {abs_path}")
                    break
            except Exception as e:
                continue
        
        if organized_data is None:
            logger.error(f"❌ rice_organized_data.json not found in any of these paths:")
            for path in possible_paths:
                logger.error(f"   - {os.path.abspath(path)}")
            return
        
        # Process each course
        for dept_code, dept_data in organized_data.get('departments', {}).items():
            for course in dept_data.get('courses', []):
                doc = self._create_document(course, dept_code)
                self.documents.append(doc)
        
        # Also load Fall 2025 specific data
        fall_paths = [
            'data/raw/rice_courses_202610_with_instructors.json',
            '../data/raw/rice_courses_202610_with_instructors.json',
            os.path.join(os.path.dirname(__file__), '..', 'data', 'raw', 'rice_courses_202610_with_instructors.json')
        ]
        
        for path in fall_paths:
            try:
                abs_path = os.path.abspath(path)
                if os.path.exists(abs_path):
                    with open(abs_path, 'r') as f:
                        fall_data = json.load(f)
                    
                    logger.info(f"✅ Loaded Fall 2025 data from: {abs_path}")
                    
                    if isinstance(fall_data, list):
                        fall_courses = fall_data
                    else:
                        fall_courses = fall_data.get('courses', [])
                        
                    for course in fall_courses:
                        doc = self._create_document(course, course.get('subject_code', ''), is_fall2025=True)
                        self.documents.append(doc)
                    break
                    
            except Exception as e:
                continue
        else:
            logger.warning("Fall 2025 data not found in any location, skipping...")
    
    def _create_document(self, course: Dict, department: str, is_fall2025: bool = False) -> Dict:
        """Create searchable document from course data"""
        
        # Create rich text for embedding
        text_parts = []
        
        # Course identification
        course_code = course.get('course_code', '')
        title = course.get('title', '')
        text_parts.append(f"Course: {course_code}")
        text_parts.append(f"Title: {title}")
        text_parts.append(f"Department: {department}")
        
        # Description
        description = course.get('description', '')
        if description:
            text_parts.append(f"Description: {description}")
        
        # Prerequisites
        prerequisites = course.get('prerequisites', '')
        if prerequisites:
            text_parts.append(f"Prerequisites: {prerequisites}")
        
        # Additional metadata
        credit_hours = course.get('credit_hours', course.get('credits', ''))
        if credit_hours:
            text_parts.append(f"Credits: {credit_hours}")
        
        course_type = course.get('course_type', '')
        if course_type:
            text_parts.append(f"Type: {course_type}")
        
        distribution_group = course.get('distribution_group', '')
        if distribution_group:
            text_parts.append(f"Distribution: {distribution_group}")
        
        # Fall 2025 specific info
        if is_fall2025:
            text_parts.append("Available: Fall 2025")
            instructor = course.get('instructor', '')
            if instructor:
                text_parts.append(f"Instructor: {instructor}")
        
        combined_text = " ".join(text_parts)
        
        return {
            'id': f"{course_code}{'_fall2025' if is_fall2025 else ''}",
            'course_code': course_code,
            'title': title,
            'department': department,
            'text': combined_text,
            'metadata': {
                'course': course,
                'is_fall2025': is_fall2025,
                'department': department
            }
        }
    
    def _create_embeddings(self):
        """Create embeddings for all documents"""
        if not self.sentence_transformers_available:
            logger.warning("⚠️ sentence_transformers not available, skipping embeddings")
            return
            
        try:
            texts = [doc['text'] for doc in self.documents]
            self.model = self.SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2', device='cpu')
            # Process in smaller batches to avoid memory issues
            batch_size = 32
            self.embeddings = self.model.encode(texts, show_progress_bar=True, batch_size=batch_size)
            logger.info("✅ Created embeddings successfully")
        except Exception as e:
            logger.error(f"❌ Failed to create embeddings: {e}")
            self.embeddings = None
    
    def _build_faiss_index(self):
        """Build FAISS index"""
        if not self.faiss_available or self.embeddings is None:
            logger.warning("⚠️ FAISS or embeddings not available, skipping index build")
            return
            
        try:
            dimension = self.embeddings.shape[1]
            self.index = self.faiss.IndexFlatIP(dimension)  # Inner product for cosine similarity
            
            # Normalize embeddings for cosine similarity
            self.faiss.normalize_L2(self.embeddings)
            self.index.add(self.embeddings.astype('float32'))
            logger.info("✅ Built FAISS index successfully")
        except Exception as e:
            logger.error(f"❌ Failed to build FAISS index: {e}")
            self.index = None
    
    def search(self, query: str, k: int = 10) -> List[Dict]:
        """Search for relevant documents"""
        
        if not self.sentence_transformers_available or not self.faiss_available:
            # Fallback to simple text search
            return self._simple_text_search(query, k)
        
        if self.index is None:
            logger.warning("⚠️ Index not loaded. Using simple text search.")
            return self._simple_text_search(query, k)
        
        # Ensure model is loaded
        if self.model is None:
            try:
                self.model = self.SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2', device='cpu')
            except Exception as e:
                logger.error(f"❌ Failed to load model for search: {e}")
                return self._simple_text_search(query, k)
        
        try:
            # Create query embedding
            query_embedding = self.model.encode([query])
            self.faiss.normalize_L2(query_embedding)
            
            # Search
            scores, indices = self.index.search(query_embedding.astype('float32'), k)
            
            # Format results
            results = []
            for score, idx in zip(scores[0], indices[0]):
                if idx != -1:  # Valid result
                    doc = self.documents[idx]
                    results.append({
                        'document': doc,
                        'score': float(score),
                        'course_code': doc['course_code'],
                        'title': doc['title'],
                        'department': doc['department'],
                        'text': doc['text']
                    })
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Vector search failed: {e}. Falling back to text search.")
            return self._simple_text_search(query, k)
    
    def _simple_text_search(self, query: str, k: int = 10) -> List[Dict]:
        """Simple text-based search as fallback"""
        query_lower = query.lower()
        results = []
        
        for doc in self.documents:
            text_lower = doc['text'].lower()
            
            # Simple keyword matching
            if query_lower in text_lower:
                # Calculate a simple score based on how many query words match
                query_words = query_lower.split()
                matches = sum(1 for word in query_words if word in text_lower)
                score = matches / len(query_words) if query_words else 0
                
                results.append({
                    'document': doc,
                    'score': score,
                    'course_code': doc['course_code'],
                    'title': doc['title'],
                    'department': doc['department'],
                    'text': doc['text']
                })
        
        # Sort by score and return top k
        results.sort(key=lambda x: x['score'], reverse=True)
        return results[:k]
    
    def _save_index(self):
        """Save index and documents"""
        if not self.faiss_available or self.index is None:
            return
            
        try:
            os.makedirs(os.path.dirname(self.index_path), exist_ok=True)
            
            # Save FAISS index
            self.faiss.write_index(self.index, self.index_path)
            
            # Save documents
            with open(self.docs_path, 'wb') as f:
                pickle.dump(self.documents, f)
                
            logger.info("✅ Saved index and documents")
        except Exception as e:
            logger.error(f"❌ Failed to save index: {e}")
    
    def _load_existing_index(self) -> bool:
        """Load existing index if available"""
        if not self.faiss_available:
            return False
            
        try:
            if os.path.exists(self.index_path) and os.path.exists(self.docs_path):
                # Load FAISS index
                self.index = self.faiss.read_index(self.index_path)
                
                # Load documents
                with open(self.docs_path, 'rb') as f:
                    self.documents = pickle.load(f)
                
                return True
        except Exception as e:
            logger.warning(f"Failed to load existing index: {e}")
        
        return False
