import os
import sys

# Ensure project root is in sys.path
sys.path.append(os.getcwd())

try:
    from services.retriever import get_retriever
    from services.generator import get_generator
except Exception as e:
    print(f"Error importing services: {e}")
    sys.exit(1)

TEST_QUERIES = [
    "What is the expense ratio of HDFC Mid Cap Fund Direct Growth?",
    "What is the exit load of HDFC Large Cap Fund Direct Growth?",
    "Can you provide download instructions for statement reports?"
]

def main():
    print("Initializing RAG End-to-End Pipeline Verification...")
    
    # 1. Initialize Retriever
    try:
        retriever = get_retriever()
    except Exception as e:
        print(f"Failed to initialize retriever: {e}")
        return
        
    # 2. Initialize Generator (will fail if GROQ_API_KEY is not set)
    try:
        generator = get_generator()
    except ValueError as ve:
        print("\n" + "="*80)
        print("[CONFIGURATION REQUIRED]")
        print(ve)
        print("Please edit the '.env' file in the root of the workspace to set your Groq API key:")
        print("  GROQ_API_KEY=your_groq_api_key_here")
        print("="*80 + "\n")
        return
    except Exception as e:
        print(f"Failed to initialize generator: {e}")
        return

    print("\nStarting RAG Generation Tests...\n")
    for query in TEST_QUERIES:
        print(f"Query: '{query}'")
        print("Retrieving context from ChromaDB...")
        
        # Query retriever
        contexts = retriever.retrieve_relevant_contexts(query, top_k=2)
        
        print(f"Retrieved {len(contexts)} relevant document(s):")
        for i, ctx in enumerate(contexts):
            meta = ctx["metadata"]
            print(f"  [{i+1}] Similarity: {ctx['similarity']:.4f} | Fund: {meta.get('fund_name')} | Chunk Type: {meta.get('chunk_type')}")
            
        print("Querying Groq API for answer...")
        # Generate answer
        answer = generator.generate_response(query, contexts)
        
        print("\nGenerated Response:")
        print(answer)
        print("-" * 80 + "\n")

if __name__ == "__main__":
    main()
