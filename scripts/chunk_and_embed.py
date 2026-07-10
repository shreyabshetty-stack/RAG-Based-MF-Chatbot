import json
import os
import sys

# On Vercel, override system SQLite if pysqlite3-binary is installed
if os.environ.get("VERCEL"):
    try:
        __import__('pysqlite3')
        sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
    except ImportError:
        pass

from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings

# Path configurations
RAW_DATA_PATH = "data/raw_funds.json"
CHROMA_DB_DIR = "data/chroma_db"
COLLECTION_NAME = "hdfc_funds_faq"
EMBEDDING_MODEL_NAME = "BAAI/bge-small-en-v1.5"

# Generic procedural chunk for statement and capital gains report downloads
PROCEDURAL_CHUNK = {
    "text": (
        "HDFC Mutual Fund Statement & Capital Gains Report Download Guide: To download account statements, "
        "consolidation reports, or capital gains transaction statements, users can log into the Groww app or website, "
        "navigate to 'Profile' -> 'Reports' -> 'Mutual Funds' and download the PDF statement. Alternatively, "
        "investors can visit the official HDFC Mutual Fund investor portal or the registrar's website (CAMS) "
        "to request a statement via registered email."
    ),
    "metadata": {
        "fund_name": "General / FAQ",
        "source_url": "https://groww.in",
        "chunk_type": "procedural",
        "last_updated": "2026-07-04"
    }
}

def create_semantic_chunks(fund):
    """
    Splits a single mutual fund entry into three distinct semantic chunks:
    1. General Info & Stats (AUM, NAV, Turnover, Ratings)
    2. Fees, Loads & Lock-in
    3. Risk & Benchmark Index
    """
    scheme_name = fund.get("scheme_name")
    source_url = fund.get("source_url")
    isin = fund.get("isin")
    expense_ratio = fund.get("expense_ratio")
    exit_load = fund.get("exit_load")
    min_sip = fund.get("min_sip_investment")
    elss_lock_in = fund.get("elss_lock_in")
    risk = fund.get("risk_classification")
    benchmark = fund.get("benchmark_index")
    fund_manager = fund.get("fund_manager")
    launch_date = fund.get("launch_date")
    aum = fund.get("aum_in_cr")
    nav = fund.get("nav")
    nav_date = fund.get("nav_date")
    portfolio_turnover = fund.get("portfolio_turnover")
    face_value = fund.get("face_value")
    groww_rating = fund.get("groww_rating")
    crisil_rating = fund.get("crisil_rating")
    last_updated = fund.get("last_updated")

    chunks = []

    # Chunk 1: General Info & AUM
    rating_str = f"Groww Rating: {groww_rating} Stars. " if groww_rating else ""
    if crisil_rating:
        rating_str += f"Crisil Rating: {crisil_rating} Stars. "
    face_val_str = f"Face Value: {face_value} INR. " if face_value else ""
    turnover_str = f"Portfolio Turnover Ratio: {portfolio_turnover}%. " if portfolio_turnover else ""
    nav_str = f"Net Asset Value (NAV): {nav} INR as of {nav_date}. " if nav else ""
    
    chunk_1_text = (
        f"Mutual Fund Scheme: {scheme_name}. ISIN Code: {isin}. "
        f"Fund House: HDFC Mutual Fund. Fund Manager: {fund_manager}. "
        f"Launch Date: {launch_date}. Total Assets Under Management (AUM): {aum} Crores. "
        f"{nav_str}{turnover_str}{face_val_str}{rating_str}"
    ).strip()
    
    chunks.append({
        "text": chunk_1_text,
        "metadata": {
            "fund_name": scheme_name,
            "source_url": source_url,
            "chunk_type": "general_info",
            "last_updated": last_updated
        }
    })

    # Chunk 2: Fees, Loads & Lock-in
    chunk_2_text = (
        f"Mutual Fund Scheme: {scheme_name}. Expense Ratio: {expense_ratio}. "
        f"Exit Load Details: {exit_load}. ELSS Lock-in Period: {elss_lock_in}. "
        f"Minimum SIP Investment: {min_sip} INR."
    )
    chunks.append({
        "text": chunk_2_text,
        "metadata": {
            "fund_name": scheme_name,
            "source_url": source_url,
            "chunk_type": "fees_and_loads",
            "last_updated": last_updated
        }
    })

    # Chunk 3: Risk & Benchmark Index
    chunk_3_text = (
        f"Mutual Fund Scheme: {scheme_name}. Riskometer Classification: {risk}. "
        f"Benchmark Index: {benchmark}."
    )
    chunks.append({
        "text": chunk_3_text,
        "metadata": {
            "fund_name": scheme_name,
            "source_url": source_url,
            "chunk_type": "risk_and_benchmark",
            "last_updated": last_updated
        }
    })

    return chunks

def main():
    print("Starting Phase 2 Chunking & Persistence Pipeline...")
    
    # 1. Load Raw Funds Data
    if not os.path.exists(RAW_DATA_PATH):
        print(f"Error: Raw corpus file not found at {RAW_DATA_PATH}. Please run Phase 1 ingest.py first.")
        return
        
    with open(RAW_DATA_PATH, "r", encoding="utf-8") as f:
        funds = json.load(f)
        
    # 2. Build Chunks List
    all_chunks = []
    for fund in funds:
        chunks = create_semantic_chunks(fund)
        all_chunks.extend(chunks)
        
    # Append the generic procedural chunk
    all_chunks.append(PROCEDURAL_CHUNK)
    print(f"Semantic chunking complete. Generated {len(all_chunks)} chunks.")
    
    # 3. Load Embedding Model (BGE-small)
    print(f"Loading embedding model: {EMBEDDING_MODEL_NAME}...")
    # This will download the model locally to ~/.cache/huggingface/hub if not cached
    model = SentenceTransformer(EMBEDDING_MODEL_NAME)
    
    # 4. Generate Embeddings
    print("Generating vector embeddings for chunks...")
    texts = [chunk["text"] for chunk in all_chunks]
    # BGE-small embedding dimension is 384
    embeddings = model.encode(texts, show_progress_bar=True).tolist()
    
    # 5. Initialize ChromaDB
    print(f"Initializing local persistent ChromaDB at {CHROMA_DB_DIR}...")
    os.makedirs(CHROMA_DB_DIR, exist_ok=True)
    chroma_client = chromadb.PersistentClient(path=CHROMA_DB_DIR)
    
    # Create or Get collection
    # We specify cosine similarity for search distance metric
    collection = chroma_client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"}
    )
    
    # Prepare inputs for ChromaDB
    ids = [f"chunk_{i}" for i in range(len(all_chunks))]
    metadatas = [chunk["metadata"] for chunk in all_chunks]
    
    print(f"Upserting {len(all_chunks)} chunks into ChromaDB collection '{COLLECTION_NAME}'...")
    collection.upsert(
        ids=ids,
        embeddings=embeddings,
        documents=texts,
        metadatas=metadatas
    )
    
    # Save the chunk data and embeddings to a lightweight JSON file for Vercel/serverless compatibility
    json_path = os.path.join(os.path.dirname(CHROMA_DB_DIR), "chunk_embeddings.json")
    print(f"Saving lightweight JSON embeddings file to {json_path}...")
    serializable_chunks = []
    for i in range(len(all_chunks)):
        serializable_chunks.append({
            "id": ids[i],
            "text": texts[i],
            "metadata": metadatas[i],
            "embedding": embeddings[i]
        })
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(serializable_chunks, f, ensure_ascii=False, indent=2)
    
    print("Vector database setup and JSON backup complete! Embeddings successfully persisted.")

if __name__ == "__main__":
    main()
