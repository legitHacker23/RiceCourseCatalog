#!/usr/bin/env python3
"""
Initialize vector store for Rice Course Assistant
"""

import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from vector_store import RiceVectorStore

def main():
    print("🚀 Initializing Rice Course Vector Store...")
    
    try:
        vector_store = RiceVectorStore()
        vector_store.load_and_index_courses(force_rebuild=True)
        
        print(f"✅ Successfully indexed {len(vector_store.documents)} documents")
        print("🎉 Vector store ready for chat!")
        
        # Test search
        print("\n🔍 Testing search functionality...")
        results = vector_store.search("computer science programming", k=3)
        
        for i, result in enumerate(results):
            print(f"\n{i+1}. {result['course_code']} - {result['title']}")
            print(f"   Score: {result['score']:.3f}")
            print(f"   Dept: {result['department']}")
        
    except Exception as e:
        print(f"❌ Error initializing vector store: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
