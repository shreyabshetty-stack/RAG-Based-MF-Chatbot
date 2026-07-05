import os
from sentence_transformers import SentenceTransformer
import chromadb

CHROMA_DB_DIR = "data/chroma_db"
COLLECTION_NAME = "hdfc_funds_faq"
EMBEDDING_MODEL_NAME = "BAAI/bge-small-en-v1.5"

# Sample test queries
TEST_QUERIES = [
    "What is the exit load of HDFC Mid Cap?",
    "what is the benchmark index of HDFC Large Cap Fund?",
    "how do I download my capital gains report?",
    "should I invest in HDFC Focused Fund?" # Advisory query (retrieval should still work, but backend will refuse later)
]

def query_db(query_text, collection, model, top_k=2):
    print(f"\nUser Query: '{query_text}'")
    # For BGE, query needs to be prefixed with this instruction
    prefixed_query = f"Represent this sentence for searching relevant passages: {query_text}"
    
    # Generate query embedding
    query_embedding = model.encode(prefixed_query).tolist()
    
    # Perform search
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k
    )
    
    # Print results
    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]
    
    for i in range(len(documents)):
        # Convert cosine distance to similarity score
        similarity = 1.0 - distances[i]
        meta = metadatas[i]
        print(f"Result {i+1} [Similarity: {similarity:.4f}]")
        print(f"  Source URL: {meta.get('source_url')}")
        print(f"  Chunk Type: {meta.get('chunk_type')}")
        print(f"  Content: {documents[i]}")

def main():
    if not os.path.exists(CHROMA_DB_DIR):
        print(f"Error: Vector database not found at {CHROMA_DB_DIR}. Please run chunk_and_embed.py first.")
        return
        
    print("Loading BGE model...")
    model = SentenceTransformer(EMBEDDING_MODEL_NAME)
    
    print("Connecting to ChromaDB...")
    chroma_client = chromadb.PersistentClient(path=CHROMA_DB_DIR)
    collection = chroma_client.get_collection(COLLECTION_NAME)
    
    print("Running retrieval tests...")
    for query in TEST_QUERIES:
        query_db(query, collection, model)

if __name__ == "__main__":
    main()
