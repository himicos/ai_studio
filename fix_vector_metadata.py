#!/usr/bin/env python3
"""
Fix the vector store metadata and id_to_node_id mapping
"""

import os
import json
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Constants
METADATA_PATH = "data/vector_store_metadata.json"

def fix_metadata():
    """Fix the vector store metadata file"""
    logger.info(f"Fixing vector store metadata at {METADATA_PATH}")
    
    if not os.path.exists(METADATA_PATH):
        logger.error(f"Metadata file not found: {METADATA_PATH}")
        return False
    
    # Load the current metadata
    try:
        with open(METADATA_PATH, 'r') as f:
            data = json.load(f)
        
        logger.info(f"Loaded metadata with keys: {list(data.keys())}")
        
        # Check if we need to add id_to_node_id mapping
        needs_id_mapping = 'id_to_node_id' not in data or not data['id_to_node_id']
        
        if needs_id_mapping:
            logger.info("Need to add id_to_node_id mapping")
            
            # Create the mapping from metadata
            id_to_node_id = {}
            metadata_entries = data.get('metadata', {})
            
            for index, entry in metadata_entries.items():
                if 'id' in entry:
                    node_id = entry['id']
                    id_to_node_id[index] = node_id
                    logger.info(f"Mapped index {index} to node ID {node_id}")
            
            # Add to the data
            data['id_to_node_id'] = id_to_node_id
            logger.info(f"Added {len(id_to_node_id)} entries to id_to_node_id mapping")
            
            # Make sure other required fields are present
            if 'next_id' not in data:
                # Calculate next_id as max index + 1
                next_id = 0
                for index in metadata_entries.keys():
                    try:
                        index_int = int(index)
                        next_id = max(next_id, index_int + 1)
                    except ValueError:
                        pass
                data['next_id'] = next_id
                logger.info(f"Added next_id: {next_id}")
            
            if 'dimensions' not in data:
                # Default for all-MiniLM-L6-v2
                data['dimensions'] = 384
                logger.info("Added dimensions: 384")
            
            if 'embedding_model' not in data:
                data['embedding_model'] = "all-MiniLM-L6-v2"
                logger.info("Added embedding_model: all-MiniLM-L6-v2")
            
            if 'updated_at' not in data:
                data['updated_at'] = int(datetime.now().timestamp())
                logger.info(f"Added updated_at: {data['updated_at']}")
            
            # Save the updated metadata
            with open(METADATA_PATH, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.info("Saved updated metadata file")
            return True
        else:
            logger.info("Metadata structure looks good, no changes needed")
            return False
        
    except Exception as e:
        logger.error(f"Error fixing metadata: {e}")
        return False

def main():
    """Main function"""
    print("\n========== VECTOR STORE METADATA FIX ==========\n")
    
    if fix_metadata():
        print("\nSuccessfully fixed vector store metadata!")
    else:
        print("\nNo changes needed or errors occurred.")
    
    return 0

if __name__ == "__main__":
    main() 