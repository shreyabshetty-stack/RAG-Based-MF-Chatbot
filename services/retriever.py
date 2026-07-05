import os
import sys

# On Vercel, override system SQLite if pysqlite3-binary is installed
if os.environ.get("VERCEL"):
    try:
        __import__('pysqlite3')
        sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
    except ImportError:
        pass

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
        Uses keyword-based re-ranking to prioritize the exact fund requested in the query.
        """
        # Prefix the query for BGE retrieval
        prefixed_query = f"Represent this sentence for searching relevant passages: {query_text}"
        
        # Embed query
        query_embedding = self.model.encode(prefixed_query).tolist()
        
        # Query DB (fetch more candidates to allow for re-ranking)
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k * 2
        )
        
        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]
        
        retrieved_items = []
        for i in range(len(documents)):
            similarity = 1.0 - distances[i]
            if similarity >= 0.35:
                retrieved_items.append({
                    "text": documents[i],
                    "metadata": metadatas[i],
                    "similarity": similarity
                })
            
        # Re-rank based on explicit fund keywords in the query to avoid cross-fund confusion
        q_lower = query_text.lower()
        target_fund_keyword = None
        if "mid" in q_lower:
            target_fund_keyword = "mid"
        elif "flexi" in q_lower or "equity" in q_lower:
            target_fund_keyword = "flexi"
        elif "focused" in q_lower:
            target_fund_keyword = "focused"
        elif "elss" in q_lower or "tax" in q_lower:
            target_fund_keyword = "elss"
        elif "large" in q_lower or "100" in q_lower:
            target_fund_keyword = "large"
            
        if target_fund_keyword:
            matching = []
            non_matching = []
            for item in retrieved_items:
                fname = item["metadata"].get("fund_name", "").lower()
                if target_fund_keyword == "flexi" and ("flexi" in fname or "equity" in fname):
                    matching.append(item)
                elif target_fund_keyword == "large" and ("large" in fname or "100" in fname):
                    matching.append(item)
                elif target_fund_keyword in fname:
                    matching.append(item)
                else:
                    non_matching.append(item)
            retrieved_items = matching + non_matching
            
        return retrieved_items[:top_k]

    def retrieve(self, query_text, k=3):
        """
        Alias used by the FastAPI pipeline (main.py).
        Delegates to retrieve_relevant_contexts with k as top_k.
        """
        return self.retrieve_relevant_contexts(query_text, top_k=k)

# Simple singleton initialization helper
_retriever_instance = None

def get_retriever():
    global _retriever_instance
    if _retriever_instance is None:
        _retriever_instance = MutualFundRetriever()
    return _retriever_instance
