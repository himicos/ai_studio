"""
Vector Database Benchmark Script

This script evaluates performance of FAISS and ChromaDB for the SpyderWeb AI Studio
by measuring insertion and query times on a sample dataset.
"""

import time
import numpy as np
import sqlite3
import os
import faiss
import chromadb
from tqdm import tqdm
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("vector_db_benchmark")

# Configuration
NUM_SAMPLE_VECTORS = 10000  # Number of sample vectors to create
VECTOR_DIM = 768  # Dimension of each vector (768 is typical for BERT-based models)
NUM_QUERIES = 100  # Number of queries to execute for benchmarking
TOP_K = 10  # Number of results to retrieve per query

class BenchmarkResult:
    def __init__(self, name):
        self.name = name
        self.insertion_time = 0
        self.query_time = 0
        self.total_time = 0
        self.queries_per_second = 0
    
    def __str__(self):
        return (f"{self.name} Results:\n"
                f"  Insertion Time: {self.insertion_time:.4f} sec\n"
                f"  Query Time: {self.query_time:.4f} sec\n"
                f"  Avg Query Speed: {self.queries_per_second:.2f} queries/sec\n"
                f"  Total Processing Time: {self.total_time:.4f} sec")

def generate_sample_data(num_vectors, dim):
    """Generate random vectors to simulate embeddings."""
    logger.info(f"Generating {num_vectors} sample vectors with {dim} dimensions")
    
    # Generate random vectors normalized to unit length (cosine similarity ready)
    vectors = np.random.random((num_vectors, dim)).astype('float32')
    
    # Normalize each vector to unit length
    faiss.normalize_L2(vectors)
    
    # Generate sample IDs and metadata
    ids = [f"node_{i}" for i in range(num_vectors)]
    
    # Create sample queries (just take some of the vectors and add noise)
    query_indices = np.random.choice(num_vectors, NUM_QUERIES, replace=False)
    query_vectors = vectors[query_indices].copy()
    
    # Add a small amount of noise to make queries realistic
    noise = np.random.random(query_vectors.shape).astype('float32') * 0.1
    query_vectors += noise
    faiss.normalize_L2(query_vectors)
    
    return vectors, ids, query_vectors

def benchmark_sqlite(vectors, ids, query_vectors):
    """Benchmark SQLite-based vector search (current approach)."""
    result = BenchmarkResult("SQLite Vector Search")
    logger.info(f"Benchmarking SQLite-based vector search...")

    # Create a temporary SQLite database
    db_path = "vector_benchmark.db"
    if os.path.exists(db_path):
        os.remove(db_path)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create memory_nodes table with embedding column
    cursor.execute("""
    CREATE TABLE memory_nodes (
        id TEXT PRIMARY KEY,
        content TEXT,
        embeddings BLOB
    )
    """)
    
    # Insert the vectors
    start_time = time.time()
    for i, (id, vector) in enumerate(tqdm(zip(ids, vectors), total=len(ids), desc="Inserting into SQLite")):
        # Store vector as binary blob
        vector_blob = vector.tobytes()
        cursor.execute(
            "INSERT INTO memory_nodes (id, content, embeddings) VALUES (?, ?, ?)",
            (id, f"Sample content {i}", vector_blob)
        )
    
    conn.commit()
    insertion_time = time.time() - start_time
    result.insertion_time = insertion_time
    
    # Perform queries (brute force comparison in Python)
    start_time = time.time()
    
    # This is extremely slow with SQLite, so we'll limit to fewer queries
    sample_queries = query_vectors[:min(10, NUM_QUERIES)]
    
    for i, query_vector in enumerate(tqdm(sample_queries, desc="Querying SQLite")):
        # For each query, we need to load all vectors from SQLite and compare
        cursor.execute("SELECT id, embeddings FROM memory_nodes")
        rows = cursor.fetchall()
        
        similarities = []
        for row_id, embedding_blob in rows:
            # Convert blob back to numpy array
            stored_vector = np.frombuffer(embedding_blob, dtype=np.float32)
            
            # Calculate cosine similarity (dot product of normalized vectors)
            similarity = np.dot(query_vector, stored_vector)
            similarities.append((row_id, similarity))
        
        # Sort by similarity (descending)
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        # Get top K results
        top_results = similarities[:TOP_K]
    
    query_time = time.time() - start_time
    # Scale the query time to represent what it would be for all queries
    query_time = query_time * (NUM_QUERIES / len(sample_queries))
    
    result.query_time = query_time
    result.total_time = insertion_time + query_time
    result.queries_per_second = NUM_QUERIES / query_time if query_time > 0 else 0
    
    # Clean up
    conn.close()
    if os.path.exists(db_path):
        os.remove(db_path)
    
    return result

def benchmark_faiss(vectors, ids, query_vectors):
    """Benchmark FAISS vector database."""
    result = BenchmarkResult("FAISS Vector Search")
    logger.info(f"Benchmarking FAISS vector search...")
    
    # Create an IndexFlatIP for inner product (cosine similarity with normalized vectors)
    index = faiss.IndexFlatIP(VECTOR_DIM)
    
    # Insert the vectors
    start_time = time.time()
    index.add(vectors)
    insertion_time = time.time() - start_time
    result.insertion_time = insertion_time
    
    # Perform queries
    start_time = time.time()
    for query_vector in tqdm(query_vectors, desc="Querying FAISS"):
        # Reshape to 2D array (FAISS expects batch of queries)
        query_vector_2d = query_vector.reshape(1, -1)
        
        # Search the index
        similarities, indices = index.search(query_vector_2d, TOP_K)
        
        # Get the corresponding IDs
        result_ids = [ids[idx] for idx in indices[0] if idx >= 0 and idx < len(ids)]
    
    query_time = time.time() - start_time
    result.query_time = query_time
    result.total_time = insertion_time + query_time
    result.queries_per_second = NUM_QUERIES / query_time if query_time > 0 else 0
    
    return result

def benchmark_chroma(vectors, ids, query_vectors):
    """Benchmark ChromaDB vector database."""
    result = BenchmarkResult("ChromaDB Vector Search")
    logger.info(f"Benchmarking ChromaDB vector search...")
    
    # Initialize ChromaDB (in-memory for benchmark)
    client = chromadb.Client()
    collection = client.create_collection("benchmark_collection")
    
    # Prepare documents for batch insertion (Chroma works best with batches)
    documents = [f"Sample content {i}" for i in range(len(vectors))]
    metadatas = [{"source": "benchmark"} for _ in range(len(vectors))]
    
    # Insert vectors
    start_time = time.time()
    
    # Use batching for faster insertion (typical batch size 1000)
    batch_size = 1000
    for i in tqdm(range(0, len(vectors), batch_size), desc="Inserting into ChromaDB"):
        end_idx = min(i + batch_size, len(vectors))
        batch_ids = ids[i:end_idx]
        batch_embeddings = vectors[i:end_idx].tolist()
        batch_documents = documents[i:end_idx]
        batch_metadatas = metadatas[i:end_idx]
        
        collection.add(
            ids=batch_ids,
            embeddings=batch_embeddings,
            documents=batch_documents,
            metadatas=batch_metadatas
        )
    
    insertion_time = time.time() - start_time
    result.insertion_time = insertion_time
    
    # Perform queries
    start_time = time.time()
    for i, query_vector in enumerate(tqdm(query_vectors, desc="Querying ChromaDB")):
        # Convert numpy array to list for ChromaDB
        query_embedding = query_vector.tolist()
        
        # Query the collection
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=TOP_K
        )
    
    query_time = time.time() - start_time
    result.query_time = query_time
    result.total_time = insertion_time + query_time
    result.queries_per_second = NUM_QUERIES / query_time if query_time > 0 else 0
    
    return result

def run_benchmarks():
    """Run all benchmarks and display results."""
    logger.info(f"Starting vector database benchmarks")
    
    # Generate sample data
    vectors, ids, query_vectors = generate_sample_data(NUM_SAMPLE_VECTORS, VECTOR_DIM)
    
    # Run benchmarks
    results = []
    
    # Always benchmark FAISS and ChromaDB
    results.append(benchmark_faiss(vectors, ids, query_vectors))
    results.append(benchmark_chroma(vectors, ids, query_vectors))
    
    # Optionally benchmark SQLite (much slower)
    sqlite_result = benchmark_sqlite(vectors, ids, query_vectors)
    results.append(sqlite_result)
    
    # Print results
    logger.info("==== Benchmark Results ====")
    for result in results:
        logger.info(f"\n{result}")
    
    # Calculate relative performance improvements
    if sqlite_result.query_time > 0:
        for result in results:
            if result.name != "SQLite Vector Search":
                speedup = sqlite_result.query_time / result.query_time
                logger.info(f"{result.name} is {speedup:.1f}x faster than SQLite for queries")
    
    # Recommend the best option
    fastest = min(results, key=lambda x: x.query_time)
    lowest_overhead = min(results, key=lambda x: x.insertion_time)
    
    logger.info(f"\nFastest query performance: {fastest.name}")
    logger.info(f"Lowest insertion overhead: {lowest_overhead.name}")
    
    # Give specific recommendation
    if fastest.name == "FAISS Vector Search":
        logger.info("\nRecommendation: Use FAISS for high-performance vector search")
        logger.info("FAISS excels at pure vector search speed but requires custom code for metadata")
    else:
        logger.info("\nRecommendation: Use ChromaDB for balanced performance and features")
        logger.info("ChromaDB provides good performance with built-in metadata and persistence")

if __name__ == "__main__":
    run_benchmarks() 