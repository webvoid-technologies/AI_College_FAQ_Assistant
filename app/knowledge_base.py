import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from typing import List, Dict
import json
import os
from app.config import Config


class KnowledgeBase:
    def __init__(self):
        self.config = Config()
        
        # Initialize ChromaDB
        self.client = chromadb.PersistentClient(
            path=self.config.CHROMA_PERSIST_DIRECTORY,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # Initialize embedding model
        print(f"Loading embedding model: {self.config.EMBEDDING_MODEL}")
        self.embedding_model = SentenceTransformer(self.config.EMBEDDING_MODEL)
        
        # Get or create collection
        self.collection_name = "mjrcet_knowledge"
        try:
            self.collection = self.client.get_collection(name=self.collection_name)
            print(f"Loaded existing collection: {self.collection_name}")
        except:
            self.collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"description": "MJRCET College Information"}
            )
            print(f"Created new collection: {self.collection_name}")
    
    def chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
        """Split text into overlapping chunks"""
        words = text.split()
        chunks = []
        
        for i in range(0, len(words), chunk_size - overlap):
            chunk = ' '.join(words[i:i + chunk_size])
            if chunk:
                chunks.append(chunk)
        
        return chunks
    
    def load_and_index_data(self, data_path: str):
        """Load scraped data and create embeddings"""
        print(f"Loading data from {data_path}")
        
        if not os.path.exists(data_path):
            print(f"Error: Data file not found at {data_path}")
            return False
        
        with open(data_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"Loaded {len(data)} documents")
        
        # Prepare documents for indexing
        documents = []
        metadatas = []
        ids = []
        
        doc_id = 0
        for item in data:
            # Chunk the content
            chunks = self.chunk_text(item['content'])
            
            for chunk in chunks:
                if len(chunk.strip()) > 50:  # Only add meaningful chunks
                    documents.append(chunk)
                    metadatas.append({
                        'title': item['title'],
                        'url': item['url'],
                        'source': 'mjrcet_website'
                    })
                    ids.append(f"doc_{doc_id}")
                    doc_id += 1
        
        print(f"Created {len(documents)} chunks for indexing")
        
        # Clear existing collection
        try:
            self.client.delete_collection(name=self.collection_name)
            self.collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"description": "MJRCET College Information"}
            )
        except:
            pass
        
        # Add documents in batches
        batch_size = 100
        for i in range(0, len(documents), batch_size):
            batch_docs = documents[i:i + batch_size]
            batch_meta = metadatas[i:i + batch_size]
            batch_ids = ids[i:i + batch_size]
            
            # Generate embeddings
            embeddings = self.embedding_model.encode(batch_docs).tolist()
            
            self.collection.add(
                documents=batch_docs,
                metadatas=batch_meta,
                ids=batch_ids,
                embeddings=embeddings
            )
            
            print(f"Indexed {min(i + batch_size, len(documents))}/{len(documents)} chunks")
        
        print("Indexing completed!")
        return True
    
    def search(self, query: str, n_results: int = 5, where: Dict = None) -> List[Dict]:
        """Search for relevant documents"""
        # Generate query embedding
        query_embedding = self.embedding_model.encode([query]).tolist()

        query_args = {
            'query_embeddings': query_embedding,
            'n_results': n_results
        }
        if where:
            query_args['where'] = where

        # Search in ChromaDB
        results = self.collection.query(**query_args)
        
        # Format results
        formatted_results = []
        if results['documents'] and len(results['documents']) > 0:
            for i in range(len(results['documents'][0])):
                formatted_results.append({
                    'content': results['documents'][0][i],
                    'metadata': results['metadatas'][0][i],
                    'distance': results['distances'][0][i] if 'distances' in results else None
                })
        
        return formatted_results
    
    def get_collection_stats(self) -> Dict:
        """Get statistics about the collection"""
        count = self.collection.count()
        return {
            'collection_name': self.collection_name,
            'document_count': count,
            'embedding_model': self.config.EMBEDDING_MODEL
        }


def main():
    """Main function to build knowledge base"""
    kb = KnowledgeBase()
    
    # Load and index data
    data_path = Config.SCRAPED_DATA_PATH
    success = kb.load_and_index_data(data_path)
    
    if success:
        stats = kb.get_collection_stats()
        print(f"\nKnowledge Base Stats:")
        print(f"Collection: {stats['collection_name']}")
        print(f"Documents: {stats['document_count']}")
        print(f"Embedding Model: {stats['embedding_model']}")
        
        # Test search
        print("\nTesting search...")
        results = kb.search("What courses are available?", n_results=3)
        print(f"Found {len(results)} results")
        if results:
            print(f"\nTop result:")
            print(f"Content: {results[0]['content'][:200]}...")
            print(f"Source: {results[0]['metadata']['title']}")


if __name__ == "__main__":
    main()
