"""
Homeopathy Remedy Ingestion to Endee Vector Database
Using Official Endee Python SDK

This script:
1. Loads remedy chunks from remedy_chunks.json
2. Generates embeddings using all-MiniLM-L6-v2
3. Creates an index in Endee
4. Upserts vectors with metadata
"""

import json
from sentence_transformers import SentenceTransformer
from endee import Endee, Precision
from tqdm import tqdm
import os

# Configuration
CHUNKS_FILE = "data/remedy_chunks.json"
INDEX_NAME = "homeopathy_remedies"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
EMBEDDING_DIMENSION = 384
BATCH_SIZE = 50

print("="*80)
print("HOMEOPATHY REMEDY INGESTION TO ENDEE")
print("="*80)

# Step 1: Initialize Endee client
print("\n[1] Connecting to Endee...")
try:
    # client = Endee()  # Connects to localhost:8080 by default
    host = os.getenv("ENDEE_HOST", "localhost")
    port = os.getenv("ENDEE_PORT", "8080")
    client = Endee()
    client.base_url = f"http://{host}:{port}/api/v1"
    print(f"DEBUG: Targeted Endee URL: {client.base_url}")

    print("DONE: Connected to Endee server")
except Exception as e:
    print(f"ERROR: Failed to connect to Endee: {e}")
    print("  Make sure Endee server is running at http://localhost:8080")
    exit(1)

# Step 2: Load remedy chunks
print(f"\n[2] Loading remedy chunks from {CHUNKS_FILE}...")
try:
    with open(CHUNKS_FILE, 'r', encoding='utf-8') as f:
        chunks = json.load(f)
    print(f"DONE: Loaded {len(chunks)} remedy chunks")
except Exception as e:
    print(f"ERROR: Failed to load chunks: {e}")
    exit(1)

# Step 3: Initialize embedding model
print(f"\n[3] Loading embedding model: {EMBEDDING_MODEL}...")
try:
    model = SentenceTransformer(EMBEDDING_MODEL)
    print(f"DONE: Model loaded (dimension: {EMBEDDING_DIMENSION})")
except Exception as e:
    print(f"ERROR: Failed to load model: {e}")
    exit(1)

# Step 4: Create index in Endee
print(f"\n[4] Creating index '{INDEX_NAME}' in Endee...")
try:
    # Check if index already exists
    indexes_response = client.list_indexes()
    existing_indexes = indexes_response.get('indexes', [])
    existing_names = [idx['name'] for idx in existing_indexes]
    
    if INDEX_NAME in existing_names:
        print(f"  WARNING: Index '{INDEX_NAME}' already exists")
        user_input = input("  Delete and recreate? (y/n): ")
        if user_input.lower() == 'y':
            client.delete_index(name=INDEX_NAME)
            print(f"  DONE: Deleted existing index")
        else:
            print("  Using existing index")
    
    # Create new index if it doesn't exist
    indexes_response = client.list_indexes()
    existing_names = [idx['name'] for idx in indexes_response.get('indexes', [])]
    
    if INDEX_NAME not in existing_names:
        client.create_index(
            name=INDEX_NAME,
            dimension=EMBEDDING_DIMENSION,
            space_type="cosine",  # Cosine similarity for semantic search
            precision=Precision.INT8D  # Efficient quantization
        )
        print(f"DONE: Created index '{INDEX_NAME}'")
        print(f"  - Dimension: {EMBEDDING_DIMENSION}")
        print(f"  - Metric: cosine")
        print(f"  - Precision: INT8D")
    
    # Get index reference
    index = client.get_index(name=INDEX_NAME)
    print(f"DONE: Got index reference")
    
except Exception as e:
    print(f"ERROR: Failed to create index: {e}")
    exit(1)

# Step 5: Generate embeddings and prepare vectors
print(f"\n[5] Generating embeddings for {len(chunks)} hybrid chunks...")
vectors_to_upsert = []

try:
    for idx, chunk in enumerate(tqdm(chunks, desc="Generating embeddings")):
        # Generate embedding
        embedding = model.encode(chunk['text'], normalize_embeddings=True)
        
        # Prepare vector data for Endee
        # Use a unique ID: chunk_{idx} to prevent collisions
        vector_data = {
            "id": f"chunk_{idx}",
            "vector": embedding.tolist(),
            "meta": {
                "remedy_name": chunk['remedy_name'],
                "remedy_index": chunk.get('remedy_index', 0),
                "text_preview": chunk['text'][:300] + "...",
                "full_text": chunk['text']
            },
            "filter": {
                "remedy_name": chunk['remedy_name'],
                "chunk_type": chunk.get('chunk_type', "flat_window")
            }
        }
        
        vectors_to_upsert.append(vector_data)
    
    print(f"DONE: Generated {len(vectors_to_upsert)} embeddings")
    
except Exception as e:
    print(f"ERROR: Failed to generate embeddings: {e}")
    exit(1)

# Step 6: Upsert vectors to Endee in batches
print(f"\n[6] Upserting vectors to Endee (batch size: {BATCH_SIZE})...")
try:
    total_batches = (len(vectors_to_upsert) + BATCH_SIZE - 1) // BATCH_SIZE
    
    for i in range(0, len(vectors_to_upsert), BATCH_SIZE):
        batch = vectors_to_upsert[i:i + BATCH_SIZE]
        batch_num = (i // BATCH_SIZE) + 1
        
        print(f"  Batch {batch_num}/{total_batches}: Upserting {len(batch)} vectors...")
        index.upsert(batch)
        # No need to print "✓ Batch completed" every time for large uploads, looks cleaner
    
    print(f"DONE: Successfully upserted all {len(vectors_to_upsert)} vectors")
    
except Exception as e:
    print(f"ERROR: Failed to upsert vectors: {e}")
    exit(1)






# Step 7: Verify ingestion
print(f"\n[7] Verifying ingestion...")
try:
    # Test query with a sample remedy
    test_query = "headache with nausea and vomiting"
    print(f"  Test query: '{test_query}'")
    
    # Generate query embedding
    query_embedding = model.encode(test_query, normalize_embeddings=True)
    
    # Search
    results = index.query(
        vector=query_embedding.tolist(),
        top_k=3
    )
    
    print(f"\n  Top 3 Results:")
    for i, result in enumerate(results, 1):
        remedy_name = result.get('meta', {}).get('remedy_name', 'Unknown')
        similarity = result.get('similarity', 0)
        print(f"    {i}. {remedy_name} (similarity: {similarity:.4f})")
    
    print(f"\nDONE: Verification successful!")
    
except Exception as e:
    print(f"ERROR: Verification failed: {e}")

# Summary
print("\n" + "="*80)
print("INGESTION COMPLETE")
print("="*80)
print(f"Index Name: {INDEX_NAME}")
print(f"Total Remedies: {len(chunks)}")
print(f"Embedding Dimension: {EMBEDDING_DIMENSION}")
print(f"Metric: Cosine Similarity")
print(f"\nYour homeopathy RAG system is ready!")
print("="*80)
