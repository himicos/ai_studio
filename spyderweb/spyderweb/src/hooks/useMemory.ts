/**
 * useMemory.ts
 * 
 * Hook for managing memory nodes and edges.
 * Provides functionality to query, filter, and visualize the knowledge graph.
 */

import { useApiQuery, useApiMutation } from './useApi';
import { useWebSocketEvent } from './useWebSocket';
import { useCallback, useState } from 'react';

// Memory interfaces
export interface NodeBase {
  type: string;
  content: string;
  tags: string[];
  metadata?: Record<string, any>;
  has_embedding?: boolean;
  similarity_score?: number;
}

export interface NodeCreate extends NodeBase {}

export interface Node extends NodeBase {
  id: string;
  created_at: number;
}

export interface EdgeBase {
  from_node_id: string;
  to_node_id: string;
  relation_type: string;
}

export interface EdgeCreate extends EdgeBase {}

export interface Edge extends EdgeBase {
  id: string;
}

export interface MemoryGraph {
  nodes: Node[];
  edges: Edge[];
}

export interface MemoryStats {
  total_nodes: number;
  total_edges: number;
  node_types: Record<string, number>;
  relation_types: Record<string, number>;
}

export interface MemoryQuery {
  node_types?: string[];
  tags?: string[];
  start_date?: number;
  end_date?: number;
  search_query?: string;
  limit?: number;
  semantic_search?: boolean;
}

/**
 * Hook for retrieving memory nodes
 */
export const useGetNodes = (
  nodeType?: string,
  tags?: string[],
  startDate?: number,
  endDate?: number,
  searchQuery?: string,
  limit: number = 100,
  offset: number = 0
) => {
  const queryParams = new URLSearchParams();
  if (nodeType) queryParams.append('node_type', nodeType);
  if (tags) tags.forEach(tag => queryParams.append('tags', tag));
  if (startDate) queryParams.append('start_date', startDate.toString());
  if (endDate) queryParams.append('end_date', endDate.toString());
  if (searchQuery) queryParams.append('search_query', searchQuery);
  queryParams.append('limit', limit.toString());
  queryParams.append('offset', offset.toString());
  
  return useApiQuery<Node[]>(`/memory/nodes?${queryParams.toString()}`);
};

/**
 * Hook for retrieving memory edges
 */
export const useGetEdges = (
  fromNodeId?: string,
  toNodeId?: string,
  relationType?: string,
  limit: number = 100,
  offset: number = 0
) => {
  const queryParams = new URLSearchParams();
  if (fromNodeId) queryParams.append('from_node_id', fromNodeId);
  if (toNodeId) queryParams.append('to_node_id', toNodeId);
  if (relationType) queryParams.append('relation_type', relationType);
  queryParams.append('limit', limit.toString());
  queryParams.append('offset', offset.toString());
  
  return useApiQuery<Edge[]>(`/memory/edges?${queryParams.toString()}`);
};

/**
 * Hook for retrieving a specific node
 */
export const useGetNode = (nodeId: string) => {
  return useApiQuery<Node>(`/memory/nodes/${nodeId}`);
};

/**
 * Hook for retrieving a specific edge
 */
export const useGetEdge = (edgeId: string) => {
  return useApiQuery<Edge>(`/memory/edges/${edgeId}`);
};

/**
 * Hook for adding a new node
 */
export const useAddNode = () => {
  return useApiMutation<Node, NodeCreate>('/memory/nodes');
};

/**
 * Hook for adding a new edge
 */
export const useAddEdge = () => {
  return useApiMutation<Edge, EdgeCreate>('/memory/edges');
};

/**
 * Hook for querying the memory graph
 */
export const useQueryMemory = () => {
  return useApiMutation<MemoryGraph, MemoryQuery>('/memory/query');
};

/**
 * Hook for retrieving memory statistics
 */
export const useMemoryStats = () => {
  return useApiQuery<MemoryStats>('/memory/stats');
};

/**
 * Combined hook for memory operations with vector embedding support
 */
export const useMemory = () => {
  const [graphData, setGraphData] = useState<MemoryGraph | null>(null);
  const [semanticResults, setSemanticResults] = useState<Node[]>([]);
  
  // API queries and mutations
  const statsQuery = useMemoryStats();
  const addNodeMutation = useAddNode();
  const addEdgeMutation = useAddEdge();
  const queryMemoryMutation = useQueryMemory();
  
  // WebSocket events for real-time updates
  useWebSocketEvent<{ node: Node }>('prompt_result', (event) => {
    const { node } = event.payload;
    if (graphData) {
      setGraphData({
        ...graphData,
        nodes: [...graphData.nodes, node]
      });
    }
    setSemanticResults(prev => [node, ...prev]);
  });
  
  // WebSocket events
  const memoryAddedEvent = useWebSocketEvent<{ node: Node }>('memory_added', (event) => {
    // Update graph data if available
    if (graphData) {
      setGraphData({
        ...graphData,
        nodes: [...graphData.nodes, event.payload.node],
      });
    }
    
    // Refetch stats to ensure consistency
    statsQuery.refetch();
  });
  
  const memoryGraphUpdateEvent = useWebSocketEvent<{ graph: MemoryGraph }>('memory_graph_update', (event) => {
    // Update graph data
    setGraphData(event.payload.graph);
  });
  
  // Add node
  const addNode = useCallback((node: NodeCreate) => {
    return addNodeMutation.mutateAsync(node, {
      onSuccess: (newNode) => {
        // Update graph data if available
        if (graphData) {
          setGraphData({
            ...graphData,
            nodes: [...graphData.nodes, newNode],
          });
        }
        
        // Refetch stats to ensure consistency
        statsQuery.refetch();
        
        return newNode;
      },
    });
  }, [addNodeMutation, graphData, statsQuery]);
  
  // Add edge
  const addEdge = useCallback((edge: EdgeCreate) => {
    return addEdgeMutation.mutateAsync(edge, {
      onSuccess: (newEdge) => {
        // Update graph data if available
        if (graphData) {
          setGraphData({
            ...graphData,
            edges: [...graphData.edges, newEdge],
          });
        }
        
        // Refetch stats to ensure consistency
        statsQuery.refetch();
        
        return newEdge;
      },
    });
  }, [addEdgeMutation, graphData, statsQuery]);
  
  // Query memory with semantic search support
  const queryMemory = useCallback((query: MemoryQuery) => {
    return queryMemoryMutation.mutateAsync(query, {
      onSuccess: (result) => {
        // Update graph data
        setGraphData(result);
        
        // Update semantic results if using semantic search
        if (query.semantic_search && result.nodes.length > 0) {
          setSemanticResults(result.nodes.sort((a, b) => 
            (b.similarity_score || 0) - (a.similarity_score || 0)
          ));
        }
        
        return result;
      },
    });
  }, [queryMemoryMutation]);
  
  // Get node types from stats
  const nodeTypes = Object.keys(statsQuery.data?.node_types || {});
  
  // Get relation types from stats
  const relationTypes = Object.keys(statsQuery.data?.relation_types || {});
  
  return {
    // Graph data
    graph: graphData,
    stats: statsQuery.data,
    nodeTypes,
    relationTypes,
    semanticResults,
    
    // Loading states
    isLoading: statsQuery.isLoading || queryMemoryMutation.isPending,
    isAddingNode: addNodeMutation.isPending,
    isAddingEdge: addEdgeMutation.isPending,
    isQuerying: queryMemoryMutation.isPending,
    
    // Error states
    isError: statsQuery.isError || addNodeMutation.isError || addEdgeMutation.isError || queryMemoryMutation.isError,
    error: statsQuery.error || addNodeMutation.error || addEdgeMutation.error || queryMemoryMutation.error,
    
    // Actions
    addNode,
    addEdge,
    queryMemory,
    
    // Semantic search helpers
    findSimilarNodes: (searchQuery: string, limit = 10) => {
      return queryMemory({
        search_query: searchQuery,
        semantic_search: true,
        limit
      });
    },
    
    // Refetch
    refetchStats: statsQuery.refetch,
    
    // Utility hooks
    useGetNodes,
    useGetEdges,
    useGetNode,
    useGetEdge,
  };
};

export default useMemory;
