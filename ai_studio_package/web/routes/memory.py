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
import openai
import numpy as np
import json
import uuid # For generating temporary IDs if needed or using DB IDs directly

# Import controllers and database functions
from ai_studio_package.infra.db_enhanced import (
    get_memory_nodes, create_memory_node, get_db_connection, get_vector_db_connection,
    init_db, init_vector_db, create_memory_edge, get_memory_edges, get_memory_node, get_memory_edge, get_memory_stats
)

class MemoryController:
    """Controller for memory operations"""
    
    def __init__(self):
        # Initialize vector store
        init_vector_db()
        
    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding vector for text using OpenAI API"""
        try:
            response = await openai.Embedding.acreate(
                input=text,
                model="text-embedding-ada-002"
            )
            return response["data"][0]["embedding"]
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            raise HTTPException(status_code=500, detail=f"Error generating embedding: {str(e)}")
        
    def get_nodes(self, 
                  node_type: Optional[str] = None, 
                  tags: Optional[List[str]] = None,
                  start_date: Optional[float] = None,
                  end_date: Optional[float] = None,
                  search_query: Optional[str] = None,
                  limit: int = 100,
                  offset: int = 0) -> List[Dict[str, Any]]:
        """Get memory nodes with filtering"""
        return get_memory_nodes(
            node_type=node_type,
            tags=tags,
            start_date=int(start_date) if start_date else None,
            end_date=int(end_date) if end_date else None,
            search_query=search_query,
            limit=limit,
            offset=offset
        )
        
    def get_edges(self,
                  source_node_id: Optional[str] = None,
                  target_node_id: Optional[str] = None,
                  label: Optional[str] = None,
                  limit: int = 100,
                  offset: int = 0) -> List[Dict[str, Any]]:
        """Get memory edges with filtering"""
        return get_memory_edges(
            source_node_id=source_node_id,
            target_node_id=target_node_id,
            label=label,
            limit=limit,
            offset=offset
        )
        
    def get_node_by_id(self, node_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific memory node by ID"""
        return get_memory_node(node_id)
        
    def get_edge_by_id(self, edge_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific memory edge by ID"""
        return get_memory_edge(edge_id)
        
    async def add_node(self, node_data: Dict[str, Any]) -> Dict[str, Any]:
        """Add a new memory node"""
        try:
            # Add timestamp if not provided
            if "created_at" not in node_data:
                node_data["created_at"] = int(datetime.now().timestamp())
                
            if "content" not in node_data:
                raise ValueError("Node data must contain 'content' field")
                
            # Create the node and check for failure
            node_id = create_memory_node(node_data)
            if node_id is None:
                # Log error (already logged in create_memory_node)
                # Raise exception to be caught by the caller (e.g., reddit scanner) or the main exception handler
                raise Exception("Failed to create memory node in database.")
            
            # Add ID to response
            node_data["id"] = node_id
            
            return node_data
        except Exception as e:
            logger.error(f"Error in MemoryController.add_node: {e}")
            # Re-raise the original exception or a specific HTTPException
            # The caller (RedditController) already has error handling, so just re-raising might be okay.
            # Let's keep the HTTPException for broader coverage.
            raise HTTPException(status_code=500, detail=f"Error adding memory node: {str(e)}")
            
    async def store_memory_node(self, content: str, node_type: str, tags: List[str], metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Store a memory node with content and metadata"""
        try:
            # Create node data
            node_data = {
                "content": content,
                "type": node_type,
                "tags": tags,
                "metadata": metadata,
                "created_at": int(datetime.now().timestamp())
            }
            
            # Create node
            return await self.add_node(node_data)
        except Exception as e:
            logger.error(f"Error storing memory node: {e}")
            raise HTTPException(status_code=500, detail=f"Error storing memory node: {str(e)}")
        
    def add_edge(self, edge_data: Dict[str, Any]) -> Dict[str, Any]:
        """Add a new memory edge"""
        # Create the edge
        success = create_memory_edge(edge_data)
        if success:
            return edge_data
        raise Exception("Failed to create memory edge")
        
    async def get_graph(self, 
                  node_types: Optional[List[str]] = None,
                  tags: Optional[List[str]] = None,
                  start_date: Optional[float] = None,
                  end_date: Optional[float] = None,
                  search_query: Optional[str] = None,
                  limit: int = 100) -> Dict[str, Any]:
        """Get a subgraph of the memory graph with semantic search"""
        try:
            # If search query provided, use vector similarity
            if search_query:
                # Generate query embedding
                query_embedding = await self.generate_embedding(search_query)
                
                # Find similar nodes
                similar_nodes = search_embeddings(query_embedding, limit)
                node_ids = [node_id for node_id, _ in similar_nodes]
                
                # Get graph centered on these nodes
                return get_memory_graph(
                    node_ids=node_ids,
                    node_types=node_types,
                    tags=tags,
                    start_date=int(start_date) if start_date else None,
                    end_date=int(end_date) if end_date else None,
                    limit=limit
                )
            
            # Otherwise use standard filtering
            return get_memory_graph(
                node_types=node_types,
                tags=tags,
                start_date=int(start_date) if start_date else None,
                end_date=int(end_date) if end_date else None,
                search_query=search_query,
                limit=limit
            )
        except Exception as e:
            logger.error(f"Error getting memory graph: {e}")
            raise HTTPException(status_code=500, detail=f"Error getting memory graph: {str(e)}")
        
    def get_stats(self) -> Dict[str, Any]:
        """Get memory statistics"""
        return get_memory_stats()

# Configure logging
logger = logging.getLogger("ai_studio.memory")

# Create router
router = APIRouter()

# Create memory controller instance
memory_controller = MemoryController()

# Export functions
async def store_memory_node(content: str, node_type: str, tags: List[str], metadata: Dict[str, Any]) -> Dict[str, Any]:
    """Store a memory node with content and metadata"""
    return await memory_controller.store_memory_node(content, node_type, tags, metadata)

async def search_memory(query_text: str, node_type: Optional[str] = None, limit: int = 50, offset: int = 0, semantic_search: bool = True) -> List[Dict[str, Any]]:
    """Search memory nodes with semantic search"""
    return memory_controller.get_nodes(
        node_type=node_type,
        search_query=query_text if semantic_search else None,
        limit=limit,
        offset=offset
    )

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
    source_node_id: str = Field(..., description="ID of the source node")
    target_node_id: str = Field(..., description="ID of the target node")
    label: str = Field(..., description="Type of relation/label between nodes")

class EdgeCreate(EdgeBase):
    """Model for creating a new edge"""
    pass

class Edge(EdgeBase):
    """Complete edge model"""
    id: str
    created_at: Optional[int] = None
    weight: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None

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
            source_node_id=from_node_id,
            target_node_id=to_node_id,
            label=relation_type,
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

# --- Add Request/Response Models for Graph Generation ---
class GenerateGraphRequest(BaseModel):
    text: str = Field(..., description="The text content to generate a knowledge graph from.")
    # Add optional model choice later if needed

class GenerateGraphResponse(BaseModel):
    nodes_created: int = Field(..., description="Number of new memory nodes created.")
    edges_created: int = Field(..., description="Number of new memory edges created.")
    status: str = Field("success", description="Status of the operation.")
    message: Optional[str] = Field(None, description="Optional message detailing success or failure.")

# --- Add Route for Graph Generation ---
@router.post(
    "/generate-graph", 
    response_model=GenerateGraphResponse,
    summary="Generate Knowledge Graph from Text",
    description="Uses an LLM (e.g., OpenAI) to extract nodes and edges from the provided text and stores them in the memory graph."
)
async def generate_knowledge_graph(
    request: GenerateGraphRequest,
    # Could add dependency injection for controller if needed later
):
    """
    Generates a knowledge graph from input text using an LLM.
    """
    logger.info(f"Received request to generate knowledge graph from text: '{request.text[:100]}...'")
    nodes_created_count = 0
    edges_created_count = 0
    
    try:
        # 1. Initialize OpenAI Client (Ensure OPENAI_API_KEY is set in .env)
        # Consider initializing this once globally or in controller __init__
        try:
            client = openai.AsyncOpenAI() 
        except Exception as client_err:
             logger.error(f"Failed to initialize OpenAI client: {client_err}", exc_info=True)
             raise HTTPException(status_code=500, detail="Failed to initialize OpenAI client. Check API key.")

        # 2. Define System Prompt for LLM
        system_prompt = """
You are an AI assistant tasked with extracting structured knowledge from text. 
Analyze the provided text and identify key entities (people, places, organizations, concepts, technologies, etc.) as nodes, and the relationships between them as edges.
Return the output ONLY as a JSON object containing two keys: "nodes" and "edges".

- "nodes": An array of objects, where each object represents a node and has the following keys:
    - "id": A unique temporary identifier string for this node (e.g., "node_1", "node_2").
    - "label": A concise name or label for the entity/concept (e.g., "OpenAI", "Python Language").
    - "type": A suggested category for the node (e.g., "Organization", "Technology", "Concept", "Person").
- "edges": An array of objects, where each object represents a directed relationship and has the following keys:
    - "source_id": The temporary "id" of the source node from the "nodes" array.
    - "target_id": The temporary "id" of the target node from the "nodes" array.
    - "label": A short phrase describing the relationship (e.g., "develops", "uses", "located_in", "is_a").

Example Input Text: "Acme Corp announced a new partnership with Globex Inc. to develop AI tools using Python."
Example JSON Output:
{
  "nodes": [
    {"id": "node_1", "label": "Acme Corp", "type": "Organization"},
    {"id": "node_2", "label": "Globex Inc", "type": "Organization"},
    {"id": "node_3", "label": "AI tools", "type": "Concept"},
    {"id": "node_4", "label": "Python", "type": "Technology"},
    {"id": "node_5", "label": "Partnership", "type": "Concept"}
  ],
  "edges": [
    {"source_id": "node_1", "target_id": "node_5", "label": "announced"},
    {"source_id": "node_1", "target_id": "node_2", "label": "partnered_with"},
    {"source_id": "node_5", "target_id": "node_3", "label": "to_develop"},
    {"source_id": "node_3", "target_id": "node_4", "label": "uses"}
  ]
}

Ensure the output is valid JSON. Do not include any explanations or text outside the JSON object.
"""

        # 3. Call OpenAI API
        logger.debug("Calling OpenAI API for graph extraction...")
        try:
            response = await client.chat.completions.create(
                model="gpt-3.5-turbo", # Or another suitable model
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": request.text}
                ],
                response_format={"type": "json_object"}, # Request JSON output if model supports it
                temperature=0.2, # Lower temperature for more deterministic structure extraction
            )
            llm_output_content = response.choices[0].message.content
            logger.debug(f"LLM raw response content: {llm_output_content}")
        except Exception as api_err:
            logger.error(f"OpenAI API call failed: {api_err}", exc_info=True)
            raise HTTPException(status_code=502, detail=f"OpenAI API call failed: {str(api_err)}")

        # 4. Parse LLM JSON Response
        try:
            if not llm_output_content:
                 raise ValueError("LLM returned empty content.")
            graph_data = json.loads(llm_output_content)
            if "nodes" not in graph_data or "edges" not in graph_data:
                raise ValueError("LLM JSON response missing 'nodes' or 'edges' key.")
            logger.info(f"Successfully parsed graph data from LLM. Found {len(graph_data.get('nodes',[]))} potential nodes, {len(graph_data.get('edges',[]))} potential edges.")
        except json.JSONDecodeError as json_err:
            logger.error(f"Failed to parse JSON from LLM response: {json_err}", exc_info=True)
            logger.error(f"LLM Raw Content causing error: {llm_output_content}")
            raise HTTPException(status_code=500, detail="Failed to parse structured data from LLM response.")
        except ValueError as val_err:
             logger.error(f"Invalid graph data structure from LLM: {val_err}")
             raise HTTPException(status_code=500, detail=f"Invalid graph data structure received from LLM: {val_err}")


        # 5. Create Nodes in DB and Map IDs
        temp_to_permanent_id_map = {}
        llm_nodes = graph_data.get("nodes", [])
        
        logger.info(f"Attempting to create {len(llm_nodes)} nodes in database...")
        for node_info in llm_nodes:
            temp_id = node_info.get("id")
            label = node_info.get("label")
            node_type = node_info.get("type", "Unknown") # Default type if missing
            
            if not temp_id or not label:
                logger.warning(f"Skipping node due to missing 'id' or 'label': {node_info}")
                continue

            # Node content can be the label, or maybe link back to original text later?
            node_content = label 
            
            node_payload = {
                # Let create_memory_node generate the ID if needed, or generate one here
                # 'id': f"graph_node_{uuid.uuid4()}", # Example explicit ID generation
                'type': f"graph_{node_type}", # Prefix type for clarity
                'content': node_content, 
                'tags': ["generated_graph", node_type],
                'created_at': int(datetime.now().timestamp()),
                'source_type': 'llm_graph_generation',
                'metadata': {'original_label': label} # Store original label if needed
            }
            
            try:
                # Assuming create_memory_node returns the permanent ID
                permanent_id = create_memory_node(node_payload)
                if permanent_id:
                    temp_to_permanent_id_map[temp_id] = permanent_id
                    nodes_created_count += 1
                    logger.debug(f"Created node: Temp ID '{temp_id}' -> Permanent ID '{permanent_id}' (Label: {label})")
                else:
                     logger.error(f"Failed to create node for temp_id {temp_id} (Label: {label}). Database function returned None.")
            except Exception as node_db_err:
                 logger.error(f"Database error creating node for temp_id {temp_id} (Label: {label}): {node_db_err}", exc_info=True)
                 # Decide whether to continue or fail the whole operation

        # 6. Create Edges in DB using Mapped IDs
        llm_edges = graph_data.get("edges", [])
        logger.info(f"Attempting to create {len(llm_edges)} edges in database...")
        for edge_info in llm_edges:
            source_temp_id = edge_info.get("source_id")
            target_temp_id = edge_info.get("target_id")
            label = edge_info.get("label", "related_to") # Default label

            if not source_temp_id or not target_temp_id:
                logger.warning(f"Skipping edge due to missing source/target ID: {edge_info}")
                continue

            # Look up permanent IDs
            source_perm_id = temp_to_permanent_id_map.get(source_temp_id)
            target_perm_id = temp_to_permanent_id_map.get(target_temp_id)

            if not source_perm_id or not target_perm_id:
                logger.warning(f"Skipping edge '{label}' because source ('{source_temp_id}' -> {source_perm_id}) or target ('{target_temp_id}' -> {target_perm_id}) node was not created successfully.")
                continue

            edge_payload = {
                # Let create_memory_edge generate the ID
                'source_node_id': source_perm_id,
                'target_node_id': target_perm_id,
                'label': label,
                'created_at': int(datetime.now().timestamp()),
                 'metadata': {'source': 'llm_graph_generation'}
            }
            
            try:
                success = create_memory_edge(edge_payload)
                if success:
                    edges_created_count += 1
                    logger.debug(f"Created edge: {source_perm_id} -[{label}]-> {target_perm_id}")
                else:
                     logger.error(f"Failed to create edge: {source_perm_id} -[{label}]-> {target_perm_id}. Database function returned False.")
            except Exception as edge_db_err:
                logger.error(f"Database error creating edge: {source_perm_id} -[{label}]-> {target_perm_id}: {edge_db_err}", exc_info=True)
                # Decide whether to continue or fail the whole operation

        logger.info(f"Knowledge graph generation finished. Nodes created: {nodes_created_count}, Edges created: {edges_created_count}")
        return GenerateGraphResponse(
            nodes_created=nodes_created_count,
            edges_created=edges_created_count,
            status="success",
            message=f"Successfully generated graph with {nodes_created_count} nodes and {edges_created_count} edges."
        )

    except HTTPException as http_exc:
        # Re-raise HTTP exceptions
        raise http_exc
    except Exception as e:
        logger.error(f"Unexpected error during knowledge graph generation: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="An unexpected error occurred during graph generation.")
