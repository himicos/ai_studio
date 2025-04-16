"""
Enhanced database module for AI Studio with memory vectorization support.
"""
import os
import json
import sqlite3
import numpy as np
from typing import Dict, Any, List, Optional
from datetime import datetime

# Database paths
DB_PATH = os.path.join("memory", "memory.sqlite")
VECTOR_DB_PATH = os.path.join("memory", "vectors.sqlite")

def init_db():
    """Initialize the databases with required tables."""
    # Ensure memory directory exists
    os.makedirs("memory", exist_ok=True)
    
    # Initialize main database
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create memory_nodes table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS memory_nodes (
        id TEXT PRIMARY KEY,
        type TEXT NOT NULL,
        content TEXT NOT NULL,
        tags TEXT,
        created_at INTEGER NOT NULL,
        source_id TEXT,
        source_type TEXT,
        metadata TEXT,
        has_embedding BOOLEAN DEFAULT 0
    )
    ''')
    
    # Create memory_edges table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS memory_edges (
        id TEXT PRIMARY KEY,
        from_node_id TEXT NOT NULL,
        to_node_id TEXT NOT NULL,
        relation_type TEXT NOT NULL,
        weight REAL DEFAULT 1.0,
        created_at INTEGER NOT NULL,
        metadata TEXT,
        FOREIGN KEY (from_node_id) REFERENCES memory_nodes (id),
        FOREIGN KEY (to_node_id) REFERENCES memory_nodes (id)
    )
    ''')
    
    # Initialize vector database
    vector_conn = sqlite3.connect(VECTOR_DB_PATH)
    vector_cursor = vector_conn.cursor()
    
    # Create embeddings table
    vector_cursor.execute('''
    CREATE TABLE IF NOT EXISTS embeddings (
        node_id TEXT PRIMARY KEY,
        embedding BLOB NOT NULL,
        model TEXT NOT NULL,
        dimensions INTEGER NOT NULL,
        created_at INTEGER NOT NULL,
        FOREIGN KEY (node_id) REFERENCES memory_nodes (id)
    )
    ''')
    
    conn.commit()
    vector_conn.commit()
    conn.close()
    vector_conn.close()

def create_memory_node(node: Dict[str, Any]) -> bool:
    """Create a new memory node."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Convert metadata to JSON if present
        metadata = json.dumps(node.get('metadata', {}))
        tags = json.dumps(node.get('tags', []))
        
        cursor.execute('''
        INSERT INTO memory_nodes (
            id, type, content, tags, created_at,
            source_id, source_type, metadata, has_embedding
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            node['id'],
            node['type'],
            node['content'],
            tags,
            node.get('created_at', int(datetime.now().timestamp())),
            node.get('source_id'),
            node.get('source_type'),
            metadata,
            0
        ))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error creating memory node: {e}")
        return False

def get_memory_node(node_id: str) -> Optional[Dict[str, Any]]:
    """Get a memory node by ID."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT * FROM memory_nodes WHERE id = ?
        ''', (node_id,))
        
        row = cursor.fetchone()
        if not row:
            return None
            
        # Convert row to dict
        columns = [col[0] for col in cursor.description]
        node = dict(zip(columns, row))
        
        # Parse JSON fields
        node['metadata'] = json.loads(node['metadata']) if node['metadata'] else {}
        node['tags'] = json.loads(node['tags']) if node['tags'] else []
        
        conn.close()
        return node
    except Exception as e:
        print(f"Error getting memory node: {e}")
        return None

def get_memory_nodes(
    node_type: Optional[str] = None,
    tags: Optional[List[str]] = None,
    start_date: Optional[int] = None,
    end_date: Optional[int] = None,
    search_query: Optional[str] = None,
    limit: int = 100,
    offset: int = 0
) -> List[Dict[str, Any]]:
    """Get memory nodes with filtering."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        query = "SELECT * FROM memory_nodes WHERE 1=1"
        params = []
        
        if node_type:
            query += " AND type = ?"
            params.append(node_type)
            
        if tags:
            # Search for any of the provided tags
            tags_json = json.dumps(tags)
            query += " AND tags LIKE ?"
            params.append(f"%{tags_json}%")
            
        if start_date:
            query += " AND created_at >= ?"
            params.append(start_date)
            
        if end_date:
            query += " AND created_at <= ?"
            params.append(end_date)
            
        if search_query:
            query += " AND content LIKE ?"
            params.append(f"%{search_query}%")
            
        query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        # Convert rows to dicts
        columns = [col[0] for col in cursor.description]
        nodes = []
        for row in rows:
            node = dict(zip(columns, row))
            node['metadata'] = json.loads(node['metadata']) if node['metadata'] else {}
            node['tags'] = json.loads(node['tags']) if node['tags'] else []
            nodes.append(node)
        
        conn.close()
        return nodes
    except Exception as e:
        print(f"Error getting memory nodes: {e}")
        return []

def create_memory_edge(edge: Dict[str, Any]) -> bool:
    """Create a new memory edge."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Convert metadata to JSON if present
        metadata = json.dumps(edge.get('metadata', {}))
        
        cursor.execute('''
        INSERT INTO memory_edges (
            id, from_node_id, to_node_id, relation_type,
            weight, created_at, metadata
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            edge['id'],
            edge['from_node_id'],
            edge['to_node_id'],
            edge['relation_type'],
            edge.get('weight', 1.0),
            edge.get('created_at', int(datetime.now().timestamp())),
            metadata
        ))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error creating memory edge: {e}")
        return False

def get_memory_edge(edge_id: str) -> Optional[Dict[str, Any]]:
    """Get a memory edge by ID."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT * FROM memory_edges WHERE id = ?
        ''', (edge_id,))
        
        row = cursor.fetchone()
        if not row:
            return None
            
        # Convert row to dict
        columns = [col[0] for col in cursor.description]
        edge = dict(zip(columns, row))
        
        # Parse JSON fields
        edge['metadata'] = json.loads(edge['metadata']) if edge['metadata'] else {}
        
        conn.close()
        return edge
    except Exception as e:
        print(f"Error getting memory edge: {e}")
        return None

def get_memory_edges(
    from_node_id: Optional[str] = None,
    to_node_id: Optional[str] = None,
    relation_type: Optional[str] = None,
    limit: int = 100,
    offset: int = 0
) -> List[Dict[str, Any]]:
    """Get memory edges with filtering."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        query = "SELECT * FROM memory_edges WHERE 1=1"
        params = []
        
        if from_node_id:
            query += " AND from_node_id = ?"
            params.append(from_node_id)
            
        if to_node_id:
            query += " AND to_node_id = ?"
            params.append(to_node_id)
            
        if relation_type:
            query += " AND relation_type = ?"
            params.append(relation_type)
            
        query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        # Convert rows to dicts
        columns = [col[0] for col in cursor.description]
        edges = []
        for row in rows:
            edge = dict(zip(columns, row))
            edge['metadata'] = json.loads(edge['metadata']) if edge['metadata'] else {}
            edges.append(edge)
        
        conn.close()
        return edges
    except Exception as e:
        print(f"Error getting memory edges: {e}")
        return []

def get_memory_graph(
    node_types: Optional[List[str]] = None,
    tags: Optional[List[str]] = None,
    start_date: Optional[int] = None,
    end_date: Optional[int] = None,
    search_query: Optional[str] = None,
    limit: int = 100
) -> Dict[str, Any]:
    """Get a subgraph of the memory graph."""
    try:
        # Get nodes
        nodes = get_memory_nodes(
            node_type=node_types[0] if node_types else None,
            tags=tags,
            start_date=start_date,
            end_date=end_date,
            search_query=search_query,
            limit=limit
        )
        
        # Get edges between these nodes
        node_ids = [node['id'] for node in nodes]
        edges = []
        for node_id in node_ids:
            # Get outgoing edges
            outgoing = get_memory_edges(from_node_id=node_id)
            # Get incoming edges
            incoming = get_memory_edges(to_node_id=node_id)
            edges.extend(outgoing + incoming)
        
        return {
            'nodes': nodes,
            'edges': edges
        }
    except Exception as e:
        print(f"Error getting memory graph: {e}")
        return {'nodes': [], 'edges': []}

def get_memory_stats() -> Dict[str, Any]:
    """Get memory statistics."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Get total nodes
        cursor.execute("SELECT COUNT(*) FROM memory_nodes")
        total_nodes = cursor.fetchone()[0]
        
        # Get total edges
        cursor.execute("SELECT COUNT(*) FROM memory_edges")
        total_edges = cursor.fetchone()[0]
        
        # Get node types and counts
        cursor.execute("SELECT type, COUNT(*) FROM memory_nodes GROUP BY type")
        node_types = dict(cursor.fetchall())
        
        # Get edge types and counts
        cursor.execute("SELECT relation_type, COUNT(*) FROM memory_edges GROUP BY relation_type")
        edge_types = dict(cursor.fetchall())
        
        # Get recent activity
        cursor.execute('''
        SELECT created_at, type, id FROM memory_nodes 
        ORDER BY created_at DESC LIMIT 10
        ''')
        recent_nodes = cursor.fetchall()
        
        conn.close()
        
        return {
            'total_nodes': total_nodes,
            'total_edges': total_edges,
            'node_types': node_types,
            'edge_types': edge_types,
            'recent_activity': [
                {
                    'timestamp': ts,
                    'type': t,
                    'id': i
                } for ts, t, i in recent_nodes
            ]
        }
    except Exception as e:
        print(f"Error getting memory stats: {e}")
        return {
            'total_nodes': 0,
            'total_edges': 0,
            'node_types': {},
            'edge_types': {},
            'recent_activity': []
        }

# Initialize database on module import
init_db()
