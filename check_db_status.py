#!/usr/bin/env python
"""
Script to check the status of database and FAISS index
"""
import logging
import json
import sqlite3
from ai_studio_package.infra.vector_adapter import get_vector_store
from ai_studio_package.infra.db import get_db_connection

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("check_db")

def check_database():
    """Check database contents"""
    try:
        # Connect to SQLite DB
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get total count of memory nodes
        cursor.execute("SELECT COUNT(*) FROM memory_nodes")
        total_nodes = cursor.fetchone()[0]
        
        # Get count of memory nodes with embeddings
        cursor.execute("SELECT COUNT(*) FROM memory_nodes WHERE has_embedding = 1")
        nodes_with_embeddings = cursor.fetchone()[0]
        
        # Get count by type
        cursor.execute("SELECT type, COUNT(*) FROM memory_nodes GROUP BY type")
        type_counts = cursor.fetchall()
        
        # Get sample of each type
        samples = {}
        for type_row in type_counts:
            node_type = type_row[0]
            cursor.execute("SELECT id, title, has_embedding FROM memory_nodes WHERE type = ? LIMIT 1", (node_type,))
            sample = cursor.fetchone()
            if sample:
                samples[node_type] = {
                    "id": sample[0],
                    "title": sample[1],
                    "has_embedding": sample[2]
                }
        
        logger.info(f"Database contains {total_nodes} total memory nodes")
        logger.info(f"Database has {nodes_with_embeddings} nodes with embeddings")
        
        logger.info("Node counts by type:")
        for type_row in type_counts:
            logger.info(f"  {type_row[0]}: {type_row[1]}")
        
        logger.info("Sample nodes by type:")
        for node_type, sample in samples.items():
            logger.info(f"  {node_type}: {sample['title']} (has_embedding={sample['has_embedding']})")
        
        return {
            "total_nodes": total_nodes,
            "nodes_with_embeddings": nodes_with_embeddings,
            "type_counts": dict(type_counts),
            "samples": samples
        }
    except Exception as e:
        logger.error(f"Error checking database: {e}")
        return None

def check_faiss_index():
    """Check FAISS index contents"""
    try:
        # Get vector store
        vector_store = get_vector_store()
        
        # Check vector count
        vector_count = vector_store.index.ntotal if hasattr(vector_store.index, 'ntotal') else 0
        
        # Check metadata count
        metadata_count = len(vector_store.metadata) if hasattr(vector_store, 'metadata') else 0
        
        logger.info(f"FAISS index contains {vector_count} vectors")
        logger.info(f"FAISS index has {metadata_count} metadata entries")
        
        # Count by type in metadata
        type_counts = {}
        for idx, metadata in vector_store.metadata.items():
            node_type = metadata.get('type')
            if node_type:
                type_counts[node_type] = type_counts.get(node_type, 0) + 1
        
        logger.info("FAISS node counts by type:")
        for node_type, count in type_counts.items():
            logger.info(f"  {node_type}: {count}")
        
        # Check for test data
        test_data_count = sum(1 for m in vector_store.metadata.values() if m.get('type') == 'test_document')
        logger.info(f"FAISS index contains {test_data_count} test documents")
        
        # Get sample of each type
        samples = {}
        for node_type in type_counts:
            for idx, metadata in vector_store.metadata.items():
                if metadata.get('type') == node_type:
                    samples[node_type] = {
                        "id": metadata.get('id'),
                        "title": metadata.get('title', 'Unknown')
                    }
                    break
        
        logger.info("Sample nodes in FAISS by type:")
        for node_type, sample in samples.items():
            logger.info(f"  {node_type}: {sample.get('title')} (id={sample.get('id')})")
        
        # Check for database nodes missing from FAISS
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get nodes that should have embeddings
        cursor.execute("SELECT id FROM memory_nodes WHERE has_embedding = 1")
        db_nodes_with_embeddings = set(row[0] for row in cursor.fetchall())
        
        # Get nodes in FAISS
        faiss_node_ids = set(metadata.get('id') for metadata in vector_store.metadata.values())
        
        # Find missing nodes
        missing_in_faiss = db_nodes_with_embeddings - faiss_node_ids
        missing_in_db = faiss_node_ids - db_nodes_with_embeddings
        
        logger.info(f"{len(missing_in_faiss)} nodes marked as having embeddings in DB but missing from FAISS")
        logger.info(f"{len(missing_in_db)} nodes in FAISS but not marked as having embeddings in DB")
        
        # Sample of missing nodes
        if missing_in_faiss:
            sample_id = list(missing_in_faiss)[0] if missing_in_faiss else None
            if sample_id:
                cursor.execute("SELECT id, type, title FROM memory_nodes WHERE id = ?", (sample_id,))
                sample = cursor.fetchone()
                if sample:
                    logger.info(f"Sample missing node: {sample[2]} (type={sample[1]}, id={sample[0]})")
        
        return {
            "vector_count": vector_count,
            "metadata_count": metadata_count,
            "type_counts": type_counts,
            "test_data_count": test_data_count,
            "missing_in_faiss": len(missing_in_faiss),
            "missing_in_db": len(missing_in_db)
        }
    except Exception as e:
        logger.error(f"Error checking FAISS index: {e}")
        return None

def main():
    """Main entry point"""
    logger.info("Checking database and FAISS index status")
    
    # Check database
    db_status = check_database()
    
    # Check FAISS index
    faiss_status = check_faiss_index()
    
    # Overall status
    logger.info("\nOverall Status:")
    if db_status and faiss_status:
        # Database has nodes but FAISS is missing them
        if db_status["nodes_with_embeddings"] > 0 and faiss_status["missing_in_faiss"] > 0:
            logger.info("ISSUE: Database has nodes with embeddings, but they're missing from FAISS index")
            logger.info("SOLUTION: Run a migration to add database nodes to FAISS index")
        
        # FAISS has vectors but they're not in DB
        if faiss_status["metadata_count"] > db_status["nodes_with_embeddings"]:
            logger.info("ISSUE: FAISS has more nodes than database has nodes with embeddings")
            logger.info("SOLUTION: This may be due to test data; fix database nodes or clear FAISS index")
        
        # No embeddings anywhere
        if db_status["nodes_with_embeddings"] == 0 and faiss_status["vector_count"] == 0:
            logger.info("ISSUE: No nodes have embeddings")
            logger.info("SOLUTION: Run the embedding generation process for all nodes")
        
        # Everything looks good
        if db_status["nodes_with_embeddings"] > 0 and faiss_status["missing_in_faiss"] == 0:
            logger.info("Status OK: Database nodes with embeddings are properly stored in FAISS")
    else:
        logger.error("Could not determine status due to errors")

if __name__ == "__main__":
    main() 