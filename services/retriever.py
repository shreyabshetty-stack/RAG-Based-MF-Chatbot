import os
import chromadb
from sentence_transformers import SentenceTransformer

# Constants (aligned with chunk_and_embed.py)
CHROMA_DB_DIR = "data/chroma_db"
COLLECTION_NAME = "hdfc_funds_faq"
EMBEDDING_MODEL_NAME = "BAAI/bge-small-en-v1.5"

class MutualFundRetriever:
    def __init__(self):
        # Resolve path relative to current working directory
        cwd = os.getcwd()
        self.db_path = os.path.join(cwd, CHROMA_DB_DIR)
        
        if not os.path.exists(self.db_path):
            raise FileNotFoundError(f"ChromaDB not found at {self.db_path}. Please run chunk_and_embed.py first.")
            
        print("Loading BGE embedding model in retriever...")
        self.model = SentenceTransformer(EMBEDDING_MODEL_NAME)
        
        print("Connecting to ChromaDB client...")
        self.chroma_client = chromadb.PersistentClient(path=self.db_path)
        self.collection = self.chroma_client.get_collection(COLLECTION_NAME)

    def retrieve_relevant_contexts(self, query_text, top_k=3):
        """
        Queries ChromaDB using BGE embeddings and returns top_k matching chunks with their metadata.
        """
        # Prefix the query for BGE retrieval
        prefixed_query = f"Represent this sentence for searching relevant passages: {query_text}"
        
        # Embed query
        query_embedding = self.model.encode(prefixed_query).tolist()
        
        # Query DB
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k
        )
        
        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]
        
        retrieved_items = []
        for i in range(len(documents)):
            similarity = 1.0 - distances[i]
            retrieved_items.append({
                "text": documents[i],
                "metadata": metadatas[i],
                "similarity": similarity
            })
            
        return retrieved_items

# Simple singleton initialization helper
_retriever_instance = None

def get_retriever():
    global _retriever_instance
    if _retriever_instance is None:
        _retriever_instance = MutualFundRetriever()
    return _retriever_instance
