"""
Memory Router

This module provides API endpoints for managing memory nodes and edges.
Handles querying, filtering, and visualization of the knowledge graph.
"""

import logging
from typing import Dict, List, Optional, Any, Union
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from datetime import datetime

# Import controllers
# In a real implementation, these would be imported from actual controller modules
# For now, we'll create placeholder classes
class MemoryController:
    """Controller for memory operations"""
    
    def __init__(self):
        # Placeholder for memory nodes and edges
        self.nodes = [
            {
                "id": "node1",
                "type": "post",
                "content": "This is a sample Reddit post",
                "tags": ["reddit", "sample"],
                "created_at": datetime.now().timestamp() - 3600
            },
            {
                "id": "node2",
                "type": "tweet",
                "content": "This is a sample tweet",
                "tags": ["twitter", "sample"],
                "created_at": datetime.now().timestamp() - 7200
            },
            {
                "id": "node3",
                "type": "prompt",
                "content": "What is the meaning of life?",
                "tags": ["prompt", "philosophy"],
                "created_at": datetime.now().timestamp() - 10800
            }
        ]
        
        self.edges = [
            {
                "id": "edge1",
                "from_node_id": "node1",
                "to_node_id": "node2",
                "relation_type": "references"
            },
            {
                "id": "edge2",
                "from_node_id": "node2",
                "to_node_id": "node3",
                "relation_type": "inspires"
            }
        ]
        
    def get_nodes(self, 
                  node_type: Optional[str] = None, 
                  tags: Optional[List[str]] = None,
                  start_date: Optional[float] = None,
                  end_date: Optional[float] = None,
                  search_query: Optional[str] = None,
                  limit: int = 100,
                  offset: int = 0) -> List[Dict[str, Any]]:
        """Get memory nodes with filtering"""
        # This would normally query the database with filters
        # For now, apply simple filtering to our placeholder data
        filtered_nodes = self.nodes
        
        if node_type:
            filtered_nodes = [node for node in filtered_nodes if node["type"] == node_type]
            
        if tags:
            filtered_nodes = [node for node in filtered_nodes if any(tag in node["tags"] for tag in tags)]
            
        if start_date:
            filtered_nodes = [node for node in filtered_nodes if node["created_at"] >= start_date]
            
        if end_date:
            filtered_nodes = [node for node in filtered_nodes if node["created_at"] <= end_date]
            
        if search_query:
            filtered_nodes = [node for node in filtered_nodes if search_query.lower() in node["content"].lower()]
            
        # Apply pagination
        paginated_nodes = filtered_nodes[offset:offset + limit]
        
        return paginated_nodes
        
    def get_edges(self,
                  from_node_id: Optional[str] = None,
                  to_node_id: Optional[str] = None,
                  relation_type: Optional[str] = None,
                  limit: int = 100,
                  offset: int = 0) -> List[Dict[str, Any]]:
        """Get memory edges with filtering"""
        # This would normally query the database with filters
        # For now, apply simple filtering to our placeholder data
        filtered_edges = self.edges
        
        if from_node_id:
            filtered_edges = [edge for edge in filtered_edges if edge["from_node_id"] == from_node_id]
            
        if to_node_id:
            filtered_edges = [edge for edge in filtered_edges if edge["to_node_id"] == to_node_id]
            
        if relation_type:
            filtered_edges = [edge for edge in filtered_edges if edge["relation_type"] == relation_type]
            
        # Apply pagination
        paginated_edges = filtered_edges[offset:offset + limit]
        
        return paginated_edges
        
    def get_node_by_id(self, node_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific memory node by ID"""
        for node in self.nodes:
            if node["id"] == node_id:
                return node
        return None
        
    def get_edge_by_id(self, edge_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific memory edge by ID"""
        for edge in self.edges:
            if edge["id"] == edge_id:
                return edge
        return None
        
    def add_node(self, node_data: Dict[str, Any]) -> Dict[str, Any]:
        """Add a new memory node"""
        # This would normally insert into the database
        # For now, just add to our placeholder data
        node_id = f"node{len(self.nodes) + 1}"
        node = {
            "id": node_id,
            **node_data,
            "created_at": datetime.now().timestamp()
        }
        self.nodes.append(node)
        return node
        
    def add_edge(self, edge_data: Dict[str, Any]) -> Dict[str, Any]:
        """Add a new memory edge"""
        # This would normally insert into the database
        # For now, just add to our placeholder data
        edge_id = f"edge{len(self.edges) + 1}"
        edge = {
            "id": edge_id,
            **edge_data
        }
        self.edges.append(edge)
        return edge
        
    def get_graph(self, 
                  node_types: Optional[List[str]] = None,
                  tags: Optional[List[str]] = None,
                  start_date: Optional[float] = None,
                  end_date: Optional[float] = None,
                  search_query: Optional[str] = None,
                  limit: int = 100) -> Dict[str, Any]:
        """Get a subgraph of the memory graph"""
        # Get filtered nodes
        nodes = self.get_nodes(
            node_type=node_types[0] if node_types and len(node_types) > 0 else None,
            tags=tags,
            start_date=start_date,
            end_date=end_date,
            search_query=search_query,
            limit=limit
        )
        
        # Get edges between these nodes
        node_ids = [node["id"] for node in nodes]
        edges = [edge for edge in self.edges 
                if edge["from_node_id"] in node_ids and edge["to_node_id"] in node_ids]
        
        return {
            "nodes": nodes,
            "edges": edges
        }
        
    def get_stats(self) -> Dict[str, Any]:
        """Get memory statistics"""
        node_types = {}
        for node in self.nodes:
            node_type = node["type"]
            if node_type in node_types:
                node_types[node_type] += 1
            else:
                node_types[node_type] = 1
                
        relation_types = {}
        for edge in self.edges:
            relation_type = edge["relation_type"]
            if relation_type in relation_types:
                relation_types[relation_type] += 1
            else:
                relation_types[relation_type] = 1
                
        return {
            "total_nodes": len(self.nodes),
            "total_edges": len(self.edges),
            "node_types": node_types,
            "relation_types": relation_types
        }

# Configure logging
logger = logging.getLogger("ai_studio.memory")

# Create router
router = APIRouter()

# Models
class NodeBase(BaseModel):
    """Base model for memory nodes"""
    type: str = Field(..., description="Type of node (post, tweet, prompt, etc.)")
    content: str = Field(..., description="Content of the node")
    tags: List[str] = Field(default_factory=list, description="Tags associated with the node")

class NodeCreate(NodeBase):
    """Model for creating a new node"""
    pass

class Node(NodeBase):
    """Complete node model"""
    id: str
    created_at: float

class EdgeBase(BaseModel):
    """Base model for memory edges"""
    from_node_id: str = Field(..., description="ID of the source node")
    to_node_id: str = Field(..., description="ID of the target node")
    relation_type: str = Field(..., description="Type of relation between nodes")

class EdgeCreate(EdgeBase):
    """Model for creating a new edge"""
    pass

class Edge(EdgeBase):
    """Complete edge model"""
    id: str

class MemoryGraph(BaseModel):
    """Memory graph model"""
    nodes: List[Node]
    edges: List[Edge]

class MemoryStats(BaseModel):
    """Memory statistics model"""
    total_nodes: int
    total_edges: int
    node_types: Dict[str, int]
    relation_types: Dict[str, int]

class MemoryQuery(BaseModel):
    """Memory query model"""
    node_types: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    start_date: Optional[float] = None
    end_date: Optional[float] = None
    search_query: Optional[str] = None
    limit: int = 100

# Dependency to get controller
def get_memory_controller():
    """Dependency to get the memory controller"""
    # In a real implementation, this would be a singleton or retrieved from a dependency injection system
    return MemoryController()

# Routes
@router.get("/nodes", response_model=List[Node])
async def get_nodes(
    node_type: Optional[str] = None,
    tags: Optional[List[str]] = Query(None),
    start_date: Optional[float] = None,
    end_date: Optional[float] = None,
    search_query: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    controller: MemoryController = Depends(get_memory_controller)
):
    """
    Get memory nodes with filtering
    
    Args:
        node_type: Filter by node type
        tags: Filter by tags
        start_date: Filter by start date (timestamp)
        end_date: Filter by end date (timestamp)
        search_query: Filter by content search
        limit: Maximum number of nodes to return
        offset: Number of nodes to skip
        
    Returns:
        List[Node]: List of memory nodes
    """
    try:
        nodes = controller.get_nodes(
            node_type=node_type,
            tags=tags,
            start_date=start_date,
            end_date=end_date,
            search_query=search_query,
            limit=limit,
            offset=offset
        )
        return nodes
    except Exception as e:
        logger.error(f"Error getting memory nodes: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting memory nodes: {str(e)}")

@router.get("/edges", response_model=List[Edge])
async def get_edges(
    from_node_id: Optional[str] = None,
    to_node_id: Optional[str] = None,
    relation_type: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    controller: MemoryController = Depends(get_memory_controller)
):
    """
    Get memory edges with filtering
    
    Args:
        from_node_id: Filter by source node ID
        to_node_id: Filter by target node ID
        relation_type: Filter by relation type
        limit: Maximum number of edges to return
        offset: Number of edges to skip
        
    Returns:
        List[Edge]: List of memory edges
    """
    try:
        edges = controller.get_edges(
            from_node_id=from_node_id,
            to_node_id=to_node_id,
            relation_type=relation_type,
            limit=limit,
            offset=offset
        )
        return edges
    except Exception as e:
        logger.error(f"Error getting memory edges: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting memory edges: {str(e)}")

@router.get("/nodes/{node_id}", response_model=Node)
async def get_node(
    node_id: str,
    controller: MemoryController = Depends(get_memory_controller)
):
    """
    Get a specific memory node by ID
    
    Args:
        node_id: Node ID
        
    Returns:
        Node: Memory node
    """
    try:
        node = controller.get_node_by_id(node_id)
        if not node:
            raise HTTPException(status_code=404, detail=f"Node not found: {node_id}")
        return node
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting memory node: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting memory node: {str(e)}")

@router.get("/edges/{edge_id}", response_model=Edge)
async def get_edge(
    edge_id: str,
    controller: MemoryController = Depends(get_memory_controller)
):
    """
    Get a specific memory edge by ID
    
    Args:
        edge_id: Edge ID
        
    Returns:
        Edge: Memory edge
    """
    try:
        edge = controller.get_edge_by_id(edge_id)
        if not edge:
            raise HTTPException(status_code=404, detail=f"Edge not found: {edge_id}")
        return edge
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting memory edge: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting memory edge: {str(e)}")

@router.post("/nodes", response_model=Node)
async def add_node(
    node: NodeCreate,
    controller: MemoryController = Depends(get_memory_controller)
):
    """
    Add a new memory node
    
    Args:
        node: Node data
        
    Returns:
        Node: Created memory node
    """
    try:
        created_node = controller.add_node(node.dict())
        logger.info(f"Added new memory node: {created_node['id']}")
        return created_node
    except Exception as e:
        logger.error(f"Error adding memory node: {e}")
        raise HTTPException(status_code=500, detail=f"Error adding memory node: {str(e)}")

@router.post("/edges", response_model=Edge)
async def add_edge(
    edge: EdgeCreate,
    controller: MemoryController = Depends(get_memory_controller)
):
    """
    Add a new memory edge
    
    Args:
        edge: Edge data
        
    Returns:
        Edge: Created memory edge
    """
    try:
        # Validate that nodes exist
        from_node = controller.get_node_by_id(edge.from_node_id)
        if not from_node:
            raise HTTPException(status_code=404, detail=f"Source node not found: {edge.from_node_id}")
            
        to_node = controller.get_node_by_id(edge.to_node_id)
        if not to_node:
            raise HTTPException(status_code=404, detail=f"Target node not found: {edge.to_node_id}")
        
        created_edge = controller.add_edge(edge.dict())
        logger.info(f"Added new memory edge: {created_edge['id']}")
        return created_edge
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding memory edge: {e}")
        raise HTTPException(status_code=500, detail=f"Error adding memory edge: {str(e)}")

@router.post("/query", response_model=MemoryGraph)
async def query_memory(
    query: MemoryQuery,
    controller: MemoryController = Depends(get_memory_controller)
):
    """
    Query the memory graph
    
    Args:
        query: Memory query parameters
        
    Returns:
        MemoryGraph: Subgraph matching the query
    """
    try:
        graph = controller.get_graph(
            node_types=query.node_types,
            tags=query.tags,
            start_date=query.start_date,
            end_date=query.end_date,
            search_query=query.search_query,
            limit=query.limit
        )
        return graph
    except Exception as e:
        logger.error(f"Error querying memory: {e}")
        raise HTTPException(status_code=500, detail=f"Error querying memory: {str(e)}")

@router.get("/stats", response_model=MemoryStats)
async def get_stats(controller: MemoryController = Depends(get_memory_controller)):
    """
    Get memory statistics
    
    Returns:
        MemoryStats: Memory statistics
    """
    try:
        stats = controller.get_stats()
        return stats
    except Exception as e:
        logger.error(f"Error getting memory stats: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting memory stats: {str(e)}")
