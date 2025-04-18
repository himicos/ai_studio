import React, { useState, useEffect, useRef, useCallback, useMemo } from "react";
import { motion } from "framer-motion";
import ForceGraph2D from 'react-force-graph-2d';
import { PanelId } from "@/contexts/WorkspaceContext";
import { 
  Network, Link, Zap, FileCode, 
  Plug, ArrowRight, Plus, Search, 
  DatabaseBackup, FileJson, BrainCircuit, X,
  BarChart, Clock, Activity, Filter, 
  Brain, CheckIcon, Settings
} from "lucide-react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
  CardFooter
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { toast } from "sonner";
import { 
  searchMemoryNodes, 
  MemoryNodeSearchResult, 
  SemanticSearchRequestPayload,
  generateKnowledgeGraph,
  getMemoryNodes,
  getMemoryEdges,
  getNodeWeights,
  trackNodeAccess
} from "../../lib/api";
import { Slider } from "@/components/ui/slider";
import { Label } from "@/components/ui/label";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { 
  AlertDialog, 
  AlertDialogAction, 
  AlertDialogCancel, 
  AlertDialogContent, 
  AlertDialogDescription, 
  AlertDialogFooter, 
  AlertDialogHeader, 
  AlertDialogTitle 
} from "@/components/ui/alert-dialog";
import ContextMenu from "@/components/graph/ContextMenu";
import * as contextActions from "@/lib/actions/contextActions";
import { useDispatch, useSelector } from 'react-redux';
import { Virtuoso } from 'react-virtuoso';
import { Disclosure, Menu, Transition } from '@headlessui/react';
import { useMediaQuery } from 'react-responsive';
import { DotLottiePlayer } from '@dotlottie/react-player';
import { ClipLoader } from 'react-spinners';
import { RootState } from '../../redux/store';
import { MemoryNode, MemoryEdge, PanelVisualizationType, setSelectedVisualization, setSelectedMemoryNode, VisualizationOptions, setVisualizationOptions } from '../../redux/slices/appSlice';
import { type MemoryNode as ApiMemoryNode, type MemoryEdge as ApiMemoryEdge } from '../../lib/api';

const sampleNodes = [
  { id: 'node1', label: 'Project Overview', type: 'document', connections: ['node2', 'node3'] },
  { id: 'node2', label: 'User Research', type: 'document', connections: ['node4'] },
  { id: 'node3', label: 'Design System', type: 'prompt', connections: ['node5'] },
  { id: 'node4', label: 'Persona Definition', type: 'prompt', connections: [] },
  { id: 'node5', label: 'Component Library', type: 'prompt', connections: [] },
];

interface MemoryPanelProps {
  id: PanelId;
}

// Define node sizing modes
type NodeSizingMode = 'uniform' | 'importance' | 'recency' | 'frequency';

// Add parameters for improved visualization
const NODE_SIZE = {
  MIN: 4,        // Minimum node size 
  MAX: 15,       // Maximum node size (increased for better visibility)
  HIGHLIGHT_FACTOR: 1.3  // How much bigger highlighted nodes should be
};

// Define relationship colors for better visibility  
const RELATION_COLORS = {
  uses: "#ff6b6b",       // Red for "uses" relationships
  follows: "#4ecdc4",    // Teal for "follows" relationships
  implements: "#f9c74f", // Yellow for "implements" relationships
  stores: "#43aa8b",     // Green for "stores" relationships
  informs: "#6a0dad",    // Purple for "informs" relationships
  guides: "#fb8500",     // Orange for "guides" relationships
  powers: "#023e8a",     // Dark blue for "powers" relationships
  defines: "#d62828",    // Dark red for "defines" relationships
  applies: "#9381ff",    // Light purple for "applies" relationships
  serves: "#14746f",     // Dark teal for "serves" relationships
  default: "#9333ea"     // Default purple
};

// Add this new interface for relationship focus
interface RelationshipView {
  source: ApiMemoryNode;
  target: ApiMemoryNode;
  edge: ApiMemoryEdge;
}

// Force Graph node object interface
interface FGNodeObject {
  id: string;
  x?: number;
  y?: number;
  [key: string]: any;
}

// Define the types we need
interface GraphNode {
  id: string;
  color?: string;
  val?: number;
  x?: number;
  y?: number;
  __bckgDimensions?: number[];
  // Add other properties as needed
}

interface GraphLink {
  source: string;
  target: string;
  color?: string;
  label?: string;
  highlighted?: boolean;
}

// Define the NodeMetadata interface
interface NodeMetadata {
  [key: string]: any;
}

export default function MemoryPanel({ id }: MemoryPanelProps) {
  const [activeTab, setActiveTab] = useState("connections");
  const [promptText, setPromptText] = useState("");
  const [sourceNode, setSourceNode] = useState<string | null>(null);
  const [targetNode, setTargetNode] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [sqlQuery, setSqlQuery] = useState("SELECT * FROM memory_graph\nWHERE node_type = 'prompt'\nORDER BY created_at DESC\nLIMIT 10;");

  const [semanticQuery, setSemanticQuery] = useState("");
  const [semanticResults, setSemanticResults] = useState<MemoryNodeSearchResult[]>([]);
  const [isLoadingSemanticSearch, setIsLoadingSemanticSearch] = useState(false);
  const [semanticSearchError, setSemanticSearchError] = useState<string | null>(null);
  const [minSimilarity, setMinSimilarity] = useState<number>(0.3);

  const [isGeneratingGraph, setIsGeneratingGraph] = useState(false);

  const [graphRef, setGraphRef] = useState<any>(null);
  const [graphNodes, setGraphNodes] = useState<GraphNode[]>([]);
  const [graphLinks, setGraphLinks] = useState<GraphLink[]>([]);
  const [isLoadingGraph, setIsLoadingGraph] = useState(false);
  const [graphError, setGraphError] = useState<string | null>(null);

  // Add state for semantic highlighting
  const [graphQuery, setGraphQuery] = useState("");
  const [highlightedNodes, setHighlightedNodes] = useState<Set<string>>(new Set());
  const [isSearchingGraph, setIsSearchingGraph] = useState(false);
  const [highlightIntensity, setHighlightIntensity] = useState<number>(0.7);
  const [nodeSimilarities, setNodeSimilarities] = useState<Record<string, number>>({});
  
  // Add state for node weight/attention encoding
  const [nodeWeights, setNodeWeights] = useState<Record<string, NodeMetadata>>({});
  const [isLoadingWeights, setIsLoadingWeights] = useState(false);
  const [nodeSizingMode, setNodeSizingMode] = useState<NodeSizingMode>('uniform');

  const graphContainerRef = useRef<HTMLDivElement>(null);
  const [graphDimensions, setGraphDimensions] = useState({ width: 0, height: 0 });

  // Add state for relationship filtering
  const [relationshipFilter, setRelationshipFilter] = useState<string | null>(null);
  const [nodeTypeFilter, setNodeTypeFilter] = useState<string | null>(null);
  const [showRelationshipsView, setShowRelationshipsView] = useState(false);

  // --- New State for Context Menu ---
  const [contextMenuVisible, setContextMenuVisible] = useState<boolean>(false);
  const [contextMenuPosition, setContextMenuPosition] = useState<{ x: number; y: number } | null>(null);
  const [contextMenuNode, setContextMenuNode] = useState<ApiMemoryNode | null>(null);

  // --- State for Confirmation Dialog ---
  const [confirmDialogState, setConfirmDialogState] = useState<{
    isOpen: boolean;
    title: string;
    description: string;
    onConfirm: () => void;
  } | null>(null);

  const filteredNodes = sampleNodes.filter(node => 
    node.label.toLowerCase().includes(searchQuery.toLowerCase()) ||
    node.type.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const updateGraphDimensions = useCallback(() => {
    if (graphContainerRef.current) {
      const width = graphContainerRef.current.offsetWidth;
      const height = graphContainerRef.current.offsetHeight;
      console.log(`[DEBUG] updateGraphDimensions Attempt: Measured width=${width}, height=${height}`, graphContainerRef.current);
      setGraphDimensions({ width, height });
    } else {
      console.log("[DEBUG] updateGraphDimensions Attempt: graphContainerRef.current is null");
    }
  }, []);

  // Setup ResizeObserver to handle panel resize events
  useEffect(() => {
    if (graphContainerRef.current && activeTab === 'knowledge') {
      console.log("[DEBUG] Setting up ResizeObserver for graph container");
      const resizeObserver = new ResizeObserver(() => {
        console.log("[DEBUG] ResizeObserver triggered - container dimensions changed");
        updateGraphDimensions();
      });
      
      resizeObserver.observe(graphContainerRef.current);
      
      return () => {
        console.log("[DEBUG] Cleaning up ResizeObserver");
        resizeObserver.disconnect();
      };
    }
    return undefined;
  }, [graphContainerRef, activeTab, updateGraphDimensions]);

  // Add function to fetch node weights
  const fetchNodeWeights = useCallback(async () => {
    setIsLoadingWeights(true);
    try {
      const weights = await getNodeWeights();
      setNodeWeights(weights);
      console.log('[DEBUG] Fetched Node Weights:', weights);
    } catch (error) {
      console.error("Failed to fetch node weights:", error);
      // Don't show a toast here to avoid annoying users if this is a background operation
    } finally {
      setIsLoadingWeights(false);
    }
  }, []);

  // Modify the existing fetchGraphData function to also fetch weights
  const fetchGraphData = useCallback(async () => {
    setIsLoadingGraph(true);
    setGraphError(null);
    try {
      const [nodesResponse, edgesResponse] = await Promise.all([
        getMemoryNodes(),
        getMemoryEdges()
      ]);
      console.log('[DEBUG] Fetched Nodes:', nodesResponse);
      console.log('[DEBUG] Fetched Edges:', edgesResponse);
      setGraphNodes(nodesResponse);
      setGraphLinks(edgesResponse);
      if (nodesResponse.length > 0 || edgesResponse.length > 0) {
         toast.info(`Loaded ${nodesResponse.length} nodes and ${edgesResponse.length} edges.`);
         
         // Fetch node weights after graph data is loaded
         fetchNodeWeights();
      }
    } catch (error) {
      console.error("[DEBUG] Failed to fetch graph data inside fetchGraphData:", error);
      const errorMsg = error instanceof Error ? error.message : "Could not load graph data.";
      setGraphError(errorMsg);
      toast.error("Failed to load graph data", { description: errorMsg });
    } finally {
      setIsLoadingGraph(false);
    }
  }, [fetchNodeWeights]);

  useEffect(() => {
    if (activeTab === 'knowledge') {
      console.log("[DEBUG] Knowledge tab active. Fetching data and scheduling dimension update via rAF.");
      fetchGraphData();
      
      // Add a small delay to ensure DOM is fully rendered before measuring
      const timer = setTimeout(() => {
        console.log('[DEBUG] Delayed measurement: Running updateGraphDimensions after DOM render');
        updateGraphDimensions();
        
        // As a fallback, try one more time after all content has loaded
        window.requestAnimationFrame(() => {
          window.requestAnimationFrame(() => {
          updateGraphDimensions();
      });
        });
      }, 100);

      return () => {
        clearTimeout(timer);
      };
    }
    
    return undefined; 
  }, [activeTab, fetchGraphData, updateGraphDimensions]);

  const handleConnect = () => {
    if (sourceNode && targetNode) {
      toast.success("Connection created successfully!", {
        description: `Created link between "${sourceNode}" and "${targetNode}"`
      });
      setSourceNode(null);
      setTargetNode(null);
    } else {
      toast.error("Cannot create connection", {
        description: "Please select both source and target nodes"
      });
    }
  };

  const handleCreateFromPrompt = async () => {
    if (!promptText.trim()) {
      toast.error("Cannot create graph", {
        description: "Please enter a prompt or text to analyze."
      });
      return;
    }
    
    setIsGeneratingGraph(true);
    const toastId = toast.loading("Generating knowledge graph from text...", {
      description: "This may take a moment depending on the text length and model response time.",
    });

    try {
      const response = await generateKnowledgeGraph({ text: promptText });

      if (response.status === 'success') {
         toast.success("Knowledge graph generated!", {
           id: toastId,
           description: response.message || `Created ${response.nodes_created} nodes and ${response.edges_created} edges.`,
         });
         setPromptText(""); 
         await fetchGraphData();
      } else {
         throw new Error(response.message || "Graph generation failed on the backend.");
      }

    } catch (error) {
      console.error("Graph generation failed:", error);
      const errorMsg = error instanceof Error ? error.message : "An unknown error occurred.";
      toast.error("Graph generation failed", { 
        id: toastId,
        description: errorMsg 
      });
    } finally {
      setIsGeneratingGraph(false);
    }
  };

  const handleExportSQL = () => {
    toast.success("SQL query executed!", {
      description: "Results have been exported to your clipboard"
    });
  };

  const handleSemanticSearch = async () => {
    if (!semanticQuery.trim()) {
      toast.error("Please enter a search query.");
      return;
    }
    setIsLoadingSemanticSearch(true);
    setSemanticSearchError(null);
    setSemanticResults([]);

    try {
      // Clean the query by removing trailing ellipses and whitespace
      const cleanedQuery = semanticQuery.trim().replace(/\.{3,}$/, '').replace(/\s+/g, ' ');
      
      const payload: SemanticSearchRequestPayload = { 
        query_text: cleanedQuery,
        min_similarity: minSimilarity
      };
      console.log('Cleaned search query:', cleanedQuery, 'Min similarity:', minSimilarity);
      const results = await searchMemoryNodes(payload);
      setSemanticResults(results);
      
      if (results.length === 0) {
        if (minSimilarity > 0.4) {
          toast.info("No results found. Try lowering the minimum similarity threshold.", {
            description: "Current threshold: " + (minSimilarity * 100).toFixed(0) + "%"
          });
        } else {
          toast.info("No similar memory nodes found.", {
            description: "Try a different search query."
          });
        }
      } else {
        const avgSimilarity = results.reduce((sum, node) => sum + node.similarity, 0) / results.length;
        toast.success(`Found ${results.length} similar node(s).`, {
          description: `Average similarity: ${(avgSimilarity * 100).toFixed(0)}%`
        });
      }
    } catch (error) {
      console.error("Semantic search failed:", error);
      const errorMsg = error instanceof Error ? error.message : "An unknown error occurred.";
      setSemanticSearchError(`Search failed: ${errorMsg}`);
      toast.error("Semantic search failed", { description: errorMsg });
    } finally {
      setIsLoadingSemanticSearch(false);
    }
  };

  // Add a function to determine if an edge should be highlighted
  const isEdgeHighlighted = useCallback((source: string, target: string): boolean => {
    // If we're not in highlight mode, don't highlight any edges
    if (highlightedNodes.size === 0) return false;
    
    // Highlight edges where both source and target are highlighted
    return highlightedNodes.has(source) && highlightedNodes.has(target);
  }, [highlightedNodes]);

  // Update the handleGraphSearch function to improve highlighting
  const handleGraphSearch = async () => {
    if (!graphQuery.trim() || graphNodes.length === 0) return;
    
    setIsSearchingGraph(true);
    try {
      // Clean the query by removing trailing ellipses and whitespace
      const cleanedQuery = graphQuery.trim().replace(/\.{3,}$/, '');
      
      // Use the same API as semantic search panel but with lower threshold for more results
      const payload: SemanticSearchRequestPayload = { 
        query_text: cleanedQuery,
        limit: 50, // Increase limit to get more nodes for highlighting
        min_similarity: 0.15 // Lower threshold for more comprehensive highlighting
      };
      
      // Try to use the API, fall back to client-side search if it fails
      try {
        const results = await searchMemoryNodes(payload);
        
        if (results.length === 0) {
          toast.info("No similar nodes found in the graph.");
          setHighlightedNodes(new Set());
          return;
        }
        
        // Create a mapping of node IDs to similarity scores
        const similarityMap: Record<string, number> = {};
        const nodeIds = new Set<string>();
        
        results.forEach(result => {
          nodeIds.add(result.id);
          similarityMap[result.id] = result.similarity || 0;
        });
        
        // Update highlighted nodes
        setHighlightedNodes(nodeIds);
        
        // Store similarity scores for visualization
        setNodeSimilarities(similarityMap);
        
        // Update node colors and sizes based on similarity scores
        updateNodeVisualization(similarityMap);
        
        toast.success(`Found ${results.length} related node(s) in the graph.`);
        
        // Zoom to fit highlighted nodes if any found
        if (graphRef && nodeIds.size > 0) {
          setTimeout(() => {
            const nodesToFit = graphNodes.filter(node => nodeIds.has(node.id));
            if (nodesToFit.length > 0) {
              graphRef.zoomToFit(500, 50, node => nodeIds.has(node.id));
            }
          }, 500);
        }
        
        // Try to track nodes (but don't fail if API returns 405)
        results.forEach(node => {
          trackNodeAccess({
            node_id: node.id,
            access_type: 'search_result',
            access_weight: node.similarity // Weight by similarity
          }).catch(error => {
            console.error(`Failed to track search result for node ${node.id}:`, error);
            // Silently continue on error
          });
        });
      } catch (error) {
        console.warn("API search failed, falling back to client-side search:", error);
        
        // Perform a basic client-side search
        const queryTerms = cleanedQuery.toLowerCase().split(/\s+/);
        const matchingNodes = graphNodes.filter(node => {
          // Cast to ApiMemoryNode to access content property safely
          const apiNode = node as unknown as ApiMemoryNode;
          if (!apiNode.content) return false;
          const nodeContent = apiNode.content.toLowerCase();
          return queryTerms.some(term => nodeContent.includes(term));
        });
        
        // Create a set of highlighted node IDs and approximate similarity scores
        const nodeIds = new Set<string>();
        const similarityMap: Record<string, number> = {};
        
        matchingNodes.forEach(node => {
          nodeIds.add(node.id);
          // Assign approximate similarity of 0.6 for exact matches
          similarityMap[node.id] = 0.6;
        });
        
        // Update highlighted nodes
        setHighlightedNodes(nodeIds);
        
        // Store similarity scores for visualization
        setNodeSimilarities(similarityMap);
        
        // Update node colors and sizes based on similarity scores
        updateNodeVisualization(similarityMap);
        
        if (matchingNodes.length === 0) {
          toast.info("No similar nodes found in the graph.");
        } else {
          toast.success(`Found ${matchingNodes.length} related node(s) in the graph.`);
          
          // Zoom to fit highlighted nodes
          if (graphRef && nodeIds.size > 0) {
            setTimeout(() => {
              graphRef.zoomToFit(500, 50, node => nodeIds.has(node.id));
            }, 500);
          }
        }
      }
    } catch (error) {
      console.error("Graph search failed:", error);
      const errorMsg = error instanceof Error ? error.message : "An unknown error occurred.";
      toast.error("Graph search failed", { description: errorMsg });
      setHighlightedNodes(new Set());
    } finally {
      setIsSearchingGraph(false);
    }
  };
  
  // Add a function to update node visualization based on similarity scores
  const updateNodeVisualization = (similarityScores: Record<string, number>) => {
    // Create a copy of the current graph nodes
    const updatedNodes = [...graphNodes];
    
    // Update colors and sizes based on similarity scores
    updatedNodes.forEach(node => {
      const similarity = similarityScores[node.id];
      if (similarity !== undefined) {
        // Update node color based on similarity score
        const hue = Math.max(0, Math.min(240, 240 - (similarity * 240))); // 240 (blue) to 0 (red)
        node.color = `hsl(${hue}, 70%, 50%)`;
        
        // Update node size based on similarity
        const baseSize = NODE_SIZE.MIN;
        const maxSize = NODE_SIZE.MAX;
        node.val = baseSize + ((maxSize - baseSize) * similarity);
      }
    });
    
    // Update graph nodes
    setGraphNodes(updatedNodes);
  };

  // Clear highlights function
  const clearHighlights = () => {
    setHighlightedNodes(new Set());
    setGraphQuery("");
  };

  // Function to get relationship color
  const getRelationshipColor = useCallback((label: string, isHighlighted: boolean): string => {
    const baseColor = RELATION_COLORS[label as keyof typeof RELATION_COLORS] || RELATION_COLORS.default;
    return isHighlighted ? baseColor : `${baseColor}77`; // Add transparency if not highlighted
  }, []);

  // Modify the calculateNodeSize function to make size differences more dramatic
  const calculateNodeSize = useCallback((nodeId: string, isHighlighted: boolean = false): number => {
    const baseSize = NODE_SIZE.MIN; 
    const minSize = NODE_SIZE.MIN;
    const maxSize = NODE_SIZE.MAX; 
    
    if (nodeSizingMode === 'uniform') {
      return isHighlighted ? baseSize * NODE_SIZE.HIGHLIGHT_FACTOR : baseSize;
    }
    
    const metadata = nodeWeights[nodeId];
    if (!metadata) {
      return isHighlighted ? baseSize * NODE_SIZE.HIGHLIGHT_FACTOR : baseSize;
    }
    
    let sizeFactor = 1;
    
    switch (nodeSizingMode) {
      case 'importance':
        // More dramatic scaling for importance
        sizeFactor = metadata.importance !== undefined ? metadata.importance : 1;
        // Apply stronger non-linear scaling for more visible differences
        sizeFactor = Math.pow(sizeFactor, 2); 
        break;
      case 'recency': {
        // Calculate recency factor based on last accessed time
        // More recent = larger with faster decay
        if (metadata.last_accessed) {
          const now = Date.now() / 1000; // current time in seconds
          const hoursSinceAccess = (now - metadata.last_accessed) / (60 * 60);
          // Much steeper decay over time (1.0 to 0.1 over 24 hours instead of 48)
          sizeFactor = Math.max(0.1, Math.exp(-hoursSinceAccess / 6));
          // Apply stronger non-linear scaling
          sizeFactor = Math.pow(sizeFactor, 1.5);
        }
        break;
      }
      case 'frequency':
        // More dramatic scaling by access count
        sizeFactor = metadata.access_count !== undefined ? 
          Math.min(4.0, 0.5 + (metadata.access_count / 3)) : 1;
        break;
    }
    
    // Apply size factor and clamp to min/max range
    const calculatedSize = Math.max(minSize, Math.min(maxSize, baseSize * sizeFactor));
    
    // If highlighted, make it even larger
    return isHighlighted ? calculatedSize * NODE_SIZE.HIGHLIGHT_FACTOR : calculatedSize;
  }, [nodeSizingMode, nodeWeights]);

  // Handle node click to update access tracking
  const handleNodeClick = useCallback((node: FGNodeObject, event: MouseEvent) => {
    if (contextMenuVisible) {
        setContextMenuVisible(false);
        setContextMenuNode(null);
        setContextMenuPosition(null);
    }
    
    console.log("Node clicked:", node);
    const nodeId = node.id as string;
    const graphNode = node as GraphNode;
    toast.info(`Node Clicked: ${nodeId}`, {
        description: `Type: ${graphNode.type}, Label: ${graphNode.label}`
    });

    trackNodeAccess({
        node_id: nodeId,
        access_type: 'view',
        access_weight: 1.0 
    }).catch(error => {
        console.warn(`Failed to track view access for node ${nodeId}:`, error);
    });

  }, [contextMenuVisible]);

  // Modify the graphData object to include filtering
  const graphData = useMemo<{ nodes: GraphNode[], links: GraphLink[] }>(() => {
    // Filter nodes based on node type filter
    const filteredNodes = graphNodes.filter(node => 
      !nodeTypeFilter || node.type === nodeTypeFilter
    );
    
    // Get IDs of filtered nodes for edge filtering
    const filteredNodeIds = new Set(filteredNodes.map(node => node.id));
    
    // Filter edges based on relationship filter and filtered nodes
    const filteredEdges = graphLinks.filter(edge => 
      (!relationshipFilter || edge.label === relationshipFilter) && 
      filteredNodeIds.has(edge.source) && 
      filteredNodeIds.has(edge.target)
    );
    
    const filteredNodesTyped: GraphNode[] = filteredNodes.map(node => {
       const isHighlighted = highlightedNodes.has(node.id);
       return {
          // Ensure all fields required by ForceGraph2D and ContextMenu are here
          ...(node as ApiMemoryNode), // Spread the original node data
          id: node.id,
          label: node.content.split('\n')[0].substring(0, 30),
          fullContent: node.content,
          type: node.type,
          highlighted: isHighlighted,
          // Apply color based on highlight/type
          color: isHighlighted ? (node.type === 'prompt' ? '#9333ea' : node.type === 'document' ? '#3b82f6' : '#10b981') : undefined,
          // Calculate size based on mode and weights
          size: calculateNodeSize(node.id, isHighlighted),
          // Ensure metadata is passed if needed by actions
          metadata: (node as ApiMemoryNode).metadata 
      };
    });
    
    const filteredEdgesTyped = filteredEdges.map(edge => {
      const isEdgeHighlit = isEdgeHighlighted(edge.source, edge.target);
      return { 
        source: edge.source,
        target: edge.target,
        label: edge.label,
        highlighted: isEdgeHighlit,
        color: getRelationshipColor(edge.label, isEdgeHighlit)
      };
    });
    
    const graphDataResult = {
      nodes: filteredNodesTyped,
      links: filteredEdgesTyped
    };
    
    // --- DEBUG LOG FOR GRAPH RENDER CONDITION (moved here) ---
    console.log('[DEBUG] Graph Render Check (inside useMemo):', {
      width: graphDimensions.width,
      height: graphDimensions.height,
      nodesLength: graphNodes.length, // Use graphNodes directly here
      isLoading: isLoadingGraph,
      error: graphError,
      shouldRender: graphDimensions.width > 0 && graphDimensions.height > 0 && graphNodes.length > 0 && !isLoadingGraph && !graphError
    });
    // --- END DEBUG LOG ---
    
    return graphDataResult; // Return the calculated data
  }, [graphNodes, graphLinks, highlightedNodes, nodeTypeFilter, relationshipFilter, isEdgeHighlighted, getRelationshipColor, calculateNodeSize, graphDimensions, isLoadingGraph, graphError]); // Add dependencies

  // Calculate relationships for the relationships view
  const relationships: RelationshipView[] = useMemo(() => {
    if (graphNodes.length === 0 || graphLinks.length === 0) return [];
    
    // Create a map for faster node lookup
    const nodeMap = new Map<string, ApiMemoryNode>();
    graphNodes.forEach(node => nodeMap.set(node.id, node));
    
    // Build relationship objects
    return graphLinks
      .filter(edge => {
        // Apply relationship filter if present
        if (relationshipFilter && edge.label !== relationshipFilter) return false;
        
        // Apply node type filter if present
        if (nodeTypeFilter) {
          const source = nodeMap.get(edge.source);
          const target = nodeMap.get(edge.target);
          if (!source || !target) return false;
          if (source.type !== nodeTypeFilter && target.type !== nodeTypeFilter) return false;
        }
        
        return true;
      })
      .map(edge => {
        const source = nodeMap.get(edge.source);
        const target = nodeMap.get(edge.target);
        
        // Skip invalid relationships
        if (!source || !target) return null;
        
        return {
          source,
          target,
          edge
        };
      })
      .filter((item): item is RelationshipView => item !== null);
  }, [graphNodes, graphLinks, relationshipFilter, nodeTypeFilter]);

  // Find all unique relationship types
  const relationshipTypes = useMemo(() => {
    const types = new Set<string>();
    graphLinks.forEach(edge => types.add(edge.label));
    return Array.from(types).sort();
  }, [graphLinks]);
  
  // Find all unique node types
  const nodeTypes = useMemo(() => {
    const types = new Set<string>();
    graphNodes.forEach(node => types.add(node.type));
    return Array.from(types).sort();
  }, [graphNodes]);

  console.log('[DEBUG] MemoryPanel State Check:', {
    activeTab,
    isLoadingGraph,
    graphError,
    graphNodesLength: graphNodes.length,
    graphEdgesLength: graphLinks.length,
    graphDimensions
  });

  useEffect(() => {
    // Set CSS variable based on current theme
    const updateThemeColors = () => {
      const isDarkTheme = document.documentElement.classList.contains('dark');
      if (isDarkTheme) {
        document.documentElement.style.setProperty('--graph-bg', '#1a1a1a');
        document.documentElement.style.setProperty('--node-text-color', '#ffffff');
        document.documentElement.style.setProperty('--node-bg-color', 'rgba(18, 18, 18, 0.85)');
        document.documentElement.style.setProperty('--link-color', '#ffffff33');
      } else {
        document.documentElement.style.setProperty('--graph-bg', '#ffffff');
        document.documentElement.style.setProperty('--node-text-color', '#000000');
        document.documentElement.style.setProperty('--node-bg-color', 'rgba(255, 255, 255, 0.85)');
        document.documentElement.style.setProperty('--link-color', '#00000033');
      }
    };
    
    // Initial call
    updateThemeColors();
    
    // Setup theme change detection
    const observer = new MutationObserver((mutations) => {
      mutations.forEach((mutation) => {
        if (mutation.attributeName === 'class') {
          updateThemeColors();
        }
      });
    });
    
    observer.observe(document.documentElement, { attributes: true });
    
    return () => {
      observer.disconnect();
    };
  }, []);

  // --- NEW Context Menu Handlers ---
  const handleNodeRightClick = useCallback((node: FGNodeObject, event: MouseEvent) => {
    event.preventDefault();
    console.log("Node right-clicked:", node);
    
    const fullNodeData = graphNodes.find(n => n.id === node.id);
    
    if (fullNodeData) {
        setContextMenuNode(fullNodeData);
        setContextMenuPosition({ x: event.pageX, y: event.pageY });
        setContextMenuVisible(true);
        
        // TODO: Update backend NodeAccessPayload to allow 'context_menu' type for specific tracking.
        // Using 'view' temporarily to avoid frontend error.
        trackNodeAccess({
            node_id: fullNodeData.id,
            access_type: 'view', // Changed from 'context_menu' temporarily
            access_weight: 0.5 
        }).catch(error => {
            console.warn(`Failed to track context menu access (as view) for node ${fullNodeData.id}:`, error);
        });
    } else {
        console.warn(`Could not find full data for right-clicked node ID: ${node.id}`);
        toast.error("Could not get node details for context menu.");
        setContextMenuVisible(false);
    }
  }, [graphNodes]);

  const handleCloseContextMenu = useCallback(() => {
    setContextMenuVisible(false);
    setContextMenuNode(null);
    setContextMenuPosition(null);
  }, []);

  const showConfirmation = useCallback((options: { title: string, description: string, onConfirm: () => void }) => {
    setConfirmDialogState({ ...options, isOpen: true });
  }, []);

  const handleContextMenuAction = useCallback(async (actionKey: string, node: ApiMemoryNode) => {
    console.log(`Context Action Triggered: ${actionKey} on node ${node.id}`);
    handleCloseContextMenu(); // Close menu immediately

    switch (actionKey) {
      case 'summarize':
        await contextActions.handleSummarize(node);
        break;
      case 'findSimilar':
        await contextActions.handleFindSimilar(node);
        // TODO: How to display results? Highlight nodes? Open side panel?
        break;
      case 'copyContent':
        contextActions.handleCopyContent(node);
        break;
      case 'copyNodeId':
        contextActions.handleCopyNodeId(node);
        break;
      case 'delete':
        // Pass the showConfirmation function to the handler
        await contextActions.handleDelete(node, showConfirmation);
        break;
      case 'viewOnX':
        contextActions.handleViewOnX(node);
        break;
      case 'generateReply':
        await contextActions.handleGenerateReply(node);
        break;
      case 'viewOnReddit':
        contextActions.handleViewOnReddit(node);
        break;
      case 'summarizeComments':
        await contextActions.handleSummarizeComments(node);
        break;
      default:
        console.warn(`Unknown context menu action: ${actionKey}`);
        toast.warning(`Action "${actionKey}" not implemented yet.`);
    }
  }, [handleCloseContextMenu, showConfirmation]); // Add dependencies

  // --- Effect for closing menu on outside click ---
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      // Check if the click is outside the context menu
      // A simple check might be enough if the menu is the only thing that should prevent closing
      // More robust: check if event.target is not within the menu DOM element
      if (contextMenuVisible) {
         // Check if the click target is outside the menu element (requires ref on menu)
         // For now, let's just close it on any click when visible
         // We might need a ref on the ContextMenu component itself for better checking
         console.log('Global click while menu visible - closing');
         handleCloseContextMenu();
      }
    };

    if (contextMenuVisible) {
      document.addEventListener('click', handleClickOutside);
    } else {
      document.removeEventListener('click', handleClickOutside);
    }

    // Cleanup
    return () => {
      document.removeEventListener('click', handleClickOutside);
    };
  }, [contextMenuVisible, handleCloseContextMenu]);

  return (
    <motion.div 
      className="flex flex-col h-full panel"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.3 }}
    >
      <div className="flex items-center justify-between p-4 border-b border-studio-border">
        <div className="flex items-center gap-2">
          <div className="size-8 rounded-md bg-studio-accent/10 flex items-center justify-center">
            <Network className="size-4 text-studio-accent" />
          </div>
          <h2 className="text-xl font-bold">Memory Graph</h2>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" className="flex gap-1">
            <DatabaseBackup className="size-4" />
            Import Data
          </Button>
          <Button variant="outline" size="sm" className="flex gap-1">
            <FileJson className="size-4" />
            Export Graph
          </Button>
        </div>
      </div>
      
      <div className="flex-1 overflow-hidden relative">
        <Tabs value={activeTab} onValueChange={setActiveTab} className="h-full flex flex-col">
          <div className="px-4 pt-4">
            <TabsList className="grid w-full grid-cols-4">
              <TabsTrigger value="connections" className="flex items-center gap-2">
                <Link className="size-4" /> Connections
              </TabsTrigger>
              <TabsTrigger value="semantic_search" className="flex items-center gap-2">
                <BrainCircuit className="size-4" /> Semantic Search
              </TabsTrigger>
              <TabsTrigger value="knowledge" className="flex items-center gap-2">
                <Zap className="size-4" /> Knowledge Graph
              </TabsTrigger>
              <TabsTrigger value="export" className="flex items-center gap-2">
                <FileCode className="size-4" /> SQL Export
              </TabsTrigger>
            </TabsList>
          </div>

          <TabsContent value="connections" className="flex-1 overflow-hidden flex flex-col p-4 relative z-10">
            <Card className="bg-studio-background-accent border-studio-border mb-4">
              <CardHeader className="pb-2">
                <CardTitle className="text-base font-medium">Create Connection</CardTitle>
                <CardDescription>Link two nodes together to build your memory graph</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-7 gap-4 items-center">
                  <div className="col-span-3">
                    <label className="text-xs text-muted-foreground mb-1 block">Source Node</label>
                    <select 
                      className="w-full rounded-md border border-studio-border bg-studio-background px-3 py-2 text-sm"
                      value={sourceNode || ""}
                      onChange={(e) => setSourceNode(e.target.value)}
                    >
                      <option value="">Select source node...</option>
                      {sampleNodes.map(node => (
                        <option key={`source-${node.id}`} value={node.label}>
                          {node.label} ({node.type})
                        </option>
                      ))}
                    </select>
                  </div>
                  
                  <div className="flex justify-center items-center">
                    <ArrowRight className="size-5 text-studio-accent" />
                  </div>
                  
                  <div className="col-span-3">
                    <label className="text-xs text-muted-foreground mb-1 block">Target Node</label>
                    <select 
                      className="w-full rounded-md border border-studio-border bg-studio-background px-3 py-2 text-sm"
                      value={targetNode || ""}
                      onChange={(e) => setTargetNode(e.target.value)}
                    >
                      <option value="">Select target node...</option>
                      {sampleNodes.map(node => (
                        <option key={`target-${node.id}`} value={node.label}>
                          {node.label} ({node.type})
                        </option>
                      ))}
                    </select>
                  </div>
                </div>
              </CardContent>
              <CardFooter className="relative z-20">
                <Button 
                  onClick={handleConnect}
                  className="ml-auto flex items-center gap-2 bg-studio-accent hover:bg-studio-accent/90"
                >
                  <Plug className="size-4" />
                  Connect Nodes
                </Button>
              </CardFooter>
            </Card>
            
            <div className="flex-1 flex flex-col border border-studio-border rounded-lg overflow-hidden">
              <div className="p-4 border-b border-studio-border flex items-center justify-between bg-studio-background-accent">
                <h3 className="text-sm font-medium">Nodes Explorer</h3>
                <div className="relative w-64">
                  <Search className="absolute left-2 top-1/2 transform -translate-y-1/2 size-4 text-muted-foreground" />
                  <Input 
                    placeholder="Search nodes..." 
                    className="pl-8 w-full bg-studio-background"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                  />
                </div>
              </div>
              
              <ScrollArea className="flex-1 p-4 bg-studio-background">
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                  {filteredNodes.map(node => (
                    <Card key={node.id} className="bg-studio-background-accent hover:bg-studio-background-accent/80 transition-colors cursor-pointer">
                      <CardHeader className="pb-2">
                        <div className="flex justify-between items-start">
                          <Badge variant={node.type === 'prompt' ? 'secondary' : 'outline'} className="mb-2">
                            {node.type}
                          </Badge>
                          <span className="text-xs text-muted-foreground">{node.connections.length} connections</span>
                        </div>
                        <CardTitle className="text-sm font-medium">{node.label}</CardTitle>
                      </CardHeader>
                      <CardFooter className="pt-0">
                        <div className="flex gap-2 text-xs text-muted-foreground">
                          <span>ID: {node.id}</span>
                        </div>
                      </CardFooter>
                    </Card>
                  ))}
                  
                  <Card className="bg-studio-background border-dashed border-2 border-studio-border flex items-center justify-center p-6 hover:bg-studio-background-accent/10 transition-colors cursor-pointer">
                    <div className="text-center">
                      <div className="mx-auto size-10 rounded-full bg-studio-accent/10 flex items-center justify-center mb-2">
                        <Plus className="size-5 text-studio-accent" />
                      </div>
                      <h3 className="text-sm font-medium">Create New Node</h3>
                      <p className="text-xs text-muted-foreground mt-1">Add a new entry to your graph</p>
                    </div>
                  </Card>
                </div>
              </ScrollArea>
            </div>
          </TabsContent>

          <TabsContent value="semantic_search" className="grow overflow-hidden flex flex-col relative z-10">
            <div className="px-4 py-3 border-b border-studio-border bg-studio-background-accent">
              <p className="text-xs text-muted-foreground">
                Semantic search finds results based on meaning and context, not just exact keyword matches. 
                Enter a phrase, topic, or question to find related memory nodes across your tracked content.
              </p>
            </div>

            <div className="flex gap-2 mb-2 px-4 pt-4">
              <Input 
                placeholder="Enter semantic query..." 
                className="flex-grow bg-studio-background"
                value={semanticQuery}
                onChange={(e) => setSemanticQuery(e.target.value)}
                onKeyDown={(e) => { if (e.key === 'Enter') handleSemanticSearch(); }}
                disabled={isLoadingSemanticSearch}
              />
              <Button 
                onClick={handleSemanticSearch}
                disabled={isLoadingSemanticSearch || !semanticQuery.trim()}
                className="flex items-center gap-2 bg-studio-accent hover:bg-studio-accent/90"
              >
                <Search className="size-4" />
                {isLoadingSemanticSearch ? "Searching..." : "Search"}
              </Button>
            </div>

            {semanticSearchError && (
              <div className="mb-2 px-4">
                <div className="p-3 rounded-md bg-red-100 border border-red-300 text-red-800 text-sm">
                  {semanticSearchError}
                </div>
              </div>
            )}

            <div className="px-4 pt-1 pb-3 flex flex-wrap items-center justify-start gap-x-4 gap-y-2 border-b border-studio-border">
              <div className="flex items-center gap-2">
                <Button variant="outline" size="sm" className="text-xs">Filter</Button>
                <Button variant="outline" size="sm" className="text-xs">Sort</Button>
              </div>
              <div className="flex flex-col w-full">
                <div className="flex items-center gap-2 flex-grow min-w-[150px]">
                  <Label htmlFor="similarity-slider" className="text-xs whitespace-nowrap">Min Similarity:</Label>
                  <Slider 
                    id="similarity-slider"
                    min={0.1} 
                    max={1.0} 
                    step={0.05} 
                    value={[minSimilarity]}
                    onValueChange={(value) => setMinSimilarity(value[0])}
                    className="flex-grow"
                    disabled={isLoadingSemanticSearch}
                  />
                  <Badge variant="outline" className="text-xs font-medium w-16 text-right">
                    {(minSimilarity * 100).toFixed(0)}%
                  </Badge>
                </div>
                <p className="text-xs text-muted-foreground mt-1 pl-2">
                  Recommended: 30-40% for broad results, 60%+ for high precision
                </p>
              </div>
            </div>

            <div className="flex-1 overflow-auto">
              <ScrollArea className="h-full min-h-[300px]">
              <div className="p-4">
                {isLoadingSemanticSearch && (
                  <p className="text-sm text-muted-foreground text-center py-4">Loading results...</p>
                )}
                 {!isLoadingSemanticSearch && semanticResults.length === 0 && (
                   <p className="text-sm text-muted-foreground text-center py-4">
                     {semanticQuery ? 'No results found.' : 'Enter a query to start semantic search.'}
                   </p>
                )}
                {semanticResults.length > 0 && (
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <div className="col-span-full mb-2">
                      <p className="text-sm text-muted-foreground">
                        Found {semanticResults.length} result{semanticResults.length !== 1 ? 's' : ''} with average similarity of {
                          (semanticResults.reduce((sum, node) => sum + node.similarity, 0) / semanticResults.length * 100).toFixed(0)
                        }%
                      </p>
                    </div>
                    {semanticResults.map(node => (
                      <Card key={node.id} className="bg-studio-background-accent mb-4 hover:bg-studio-background-accent/90 transition-colors">
                        <CardHeader className="pb-2">
                           <div className="flex justify-between items-start mb-1">
                              <Badge variant="outline" className="capitalize">{node.type}</Badge>
                              <Badge 
                                variant={node.similarity >= 0.6 ? "default" : 
                                         node.similarity >= 0.4 ? "secondary" : 
                                         "outline"} 
                                className={
                                  node.similarity >= 0.6 ? "bg-green-100 text-green-800 hover:bg-green-200" :
                                  node.similarity >= 0.4 ? "bg-amber-100 text-amber-800 hover:bg-amber-200" :
                                  "bg-gray-100 text-gray-800 hover:bg-gray-200"
                                }
                                title="Similarity Score"
                              >
                                 {(node.similarity * 100).toFixed(0)}%
                              </Badge>
                           </div>
                           <CardTitle className="text-sm font-medium" title={node.content}>
                              {/* Show more content and enhance the display */}
                              {node.content ? (
                                node.content.split('\n')[0].substring(0, 100) + (node.content.length > 100 ? '...' : '')
                              ) : (
                                <span className="text-muted-foreground italic">No content available</span>
                              )}
                           </CardTitle>
                           <CardDescription className="text-xs mt-1 flex items-center justify-between">
                             <span>ID: {node.id.substring(0, 12)}{node.id.length > 12 ? '...' : ''}</span>
                             <span>{new Date(node.created_at * 1000).toLocaleDateString()}</span>
                           </CardDescription>
                        </CardHeader>
                        <CardContent className="text-xs text-muted-foreground pt-2 pb-3">
                           {node.content ? (
                             <div>
                               <p className="line-clamp-3 pb-1 border-b border-studio-border mb-2"> 
                                 {node.content.split('\n').slice(1).join('\n').substring(0, 150) + 
                                 (node.content.length > 150 ? '...' : '')}
                               </p>
                               <div className="flex flex-wrap gap-1 mt-1">
                                 {node.tags && node.tags.length > 0 ? (
                                   node.tags.map((tag, idx) => (
                                     <Badge key={idx} variant="outline" className="text-[10px] px-1 py-0">{tag}</Badge>
                                   ))
                                 ) : (
                                   <span className="text-[10px] italic">No tags</span>
                                 )}
                               </div>
                             </div>
                           ) : (
                             <p className="italic">No additional content</p>
                           )}
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                )}
              </div>
            </ScrollArea>
            </div>
          </TabsContent>

          <TabsContent value="knowledge" className="grow shrink-0 overflow-hidden flex flex-col relative z-10 p-2">
            {/* Compact Control Row */}
            <div className="flex flex-col gap-2 mb-2">
              <div className="flex items-center gap-2 p-1 bg-studio-background-accent rounded-md border border-studio-border">
                <Input 
                  placeholder="Enter text to generate graph..."
                  className="flex-grow bg-studio-background h-8 text-sm"
                  value={promptText}
                  onChange={(e) => setPromptText(e.target.value)}
                  onKeyDown={(e) => { if (e.key === 'Enter' && !isGeneratingGraph && promptText.trim()) handleCreateFromPrompt(); }}
                  disabled={isGeneratingGraph}
                />
                <Button 
                  onClick={handleCreateFromPrompt}
                  disabled={isGeneratingGraph || !promptText.trim()}
                  className="flex items-center gap-1 bg-studio-primary hover:bg-studio-primary/90 whitespace-nowrap h-8"
                  size="sm"
                >
                  <Zap className="size-3.5" />
                  {isGeneratingGraph ? "Creating..." : "Create & Visualize"} 
                </Button>
            </div>
            
              {/* Add semantic search controls for the graph */}
              <div className="flex items-center gap-2 p-1 bg-studio-background-accent rounded-md border border-studio-border">
                <Input 
                  placeholder="Search within graph..."
                  className="flex-grow bg-studio-background h-8 text-sm"
                  value={graphQuery}
                  onChange={(e) => setGraphQuery(e.target.value)}
                  onKeyDown={(e) => { if (e.key === 'Enter' && !isSearchingGraph && graphQuery.trim()) handleGraphSearch(); }}
                  disabled={isSearchingGraph || graphNodes.length === 0}
                />
                <Button 
                  onClick={handleGraphSearch}
                  disabled={isSearchingGraph || !graphQuery.trim() || graphNodes.length === 0}
                  className="flex items-center gap-1 bg-studio-accent hover:bg-studio-accent/90 whitespace-nowrap h-8"
                  size="sm"
                >
                  <Search className="size-3.5" />
                  {isSearchingGraph ? "Searching..." : "Find Similar"} 
                </Button>
                {highlightedNodes.size > 0 && (
                  <Button 
                    onClick={clearHighlights}
                    className="flex items-center gap-1 bg-transparent border-studio-border hover:bg-studio-background whitespace-nowrap h-8"
                    size="sm"
                    variant="outline"
                  >
                    <X className="size-3.5" />
                    Clear 
                  </Button>
                )}
              </div>
              
              {/* Add Node Weight/Attention control */}
              <div className="flex items-center justify-between gap-2 p-1 bg-studio-background-accent rounded-md border border-studio-border">
                <div className="flex items-center gap-2">
                  <span className="text-xs text-muted-foreground whitespace-nowrap">Node Sizing:</span>
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button 
                        variant="outline" 
                        size="sm" 
                        className="h-8 bg-studio-background flex items-center gap-1"
                      >
                        {nodeSizingMode === 'uniform' && <Filter className="size-3.5" />}
                        {nodeSizingMode === 'importance' && <BarChart className="size-3.5" />}
                        {nodeSizingMode === 'recency' && <Clock className="size-3.5" />}
                        {nodeSizingMode === 'frequency' && <Activity className="size-3.5" />}
                        <span className="capitalize">{nodeSizingMode}</span>
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="start">
                      <DropdownMenuLabel>Size Nodes By</DropdownMenuLabel>
                      <DropdownMenuSeparator />
                      <DropdownMenuItem onClick={() => setNodeSizingMode('uniform')}>
                        <Filter className="size-4 mr-2" />
                        <span>Uniform (Default)</span>
                      </DropdownMenuItem>
                      <DropdownMenuItem onClick={() => setNodeSizingMode('importance')}>
                        <BarChart className="size-4 mr-2" />
                        <span>Importance</span>
                      </DropdownMenuItem>
                      <DropdownMenuItem onClick={() => setNodeSizingMode('recency')}>
                        <Clock className="size-4 mr-2" />
                        <span>Recency</span>
                      </DropdownMenuItem>
                      <DropdownMenuItem onClick={() => setNodeSizingMode('frequency')}>
                        <Activity className="size-4 mr-2" />
                        <span>Access Frequency</span>
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </div>
                
                {highlightedNodes.size > 0 && (
                  <div className="flex items-center gap-2 flex-grow">
                    <Label htmlFor="highlight-intensity" className="text-xs whitespace-nowrap">Highlight Intensity:</Label>
                    <Slider 
                      id="highlight-intensity"
                      min={0.3} 
                      max={1.0} 
                      step={0.05} 
                      value={[highlightIntensity]}
                      onValueChange={(value) => setHighlightIntensity(value[0])}
                      className="flex-grow"
                    />
                    <span className="text-xs font-medium w-10 text-right">{(highlightIntensity * 100).toFixed(0)}%</span>
                  </div>
                )}
              </div>
            </div>
            
            {/* Add filters right after the search bar */}
            {graphNodes.length > 0 && (
              <div className="flex flex-wrap items-center gap-2 p-2 bg-studio-background-accent rounded-md border border-studio-border mt-2">
                <div className="flex items-center gap-2 mr-2">
                  <span className="text-xs text-muted-foreground whitespace-nowrap">Filters:</span>
                  
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button 
                        variant="outline" 
                        size="sm" 
                        className="h-8 bg-studio-background flex items-center gap-1"
                      >
                        <Filter className="size-3.5" />
                        <span>{nodeTypeFilter || 'All Node Types'}</span>
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="start">
                      <DropdownMenuItem onClick={() => setNodeTypeFilter(null)}>
                        <span>All Types</span>
                      </DropdownMenuItem>
                      <DropdownMenuSeparator />
                      {nodeTypes.map(type => (
                        <DropdownMenuItem key={type} onClick={() => setNodeTypeFilter(type)}>
                          <div className="flex items-center gap-2">
                            <div 
                              className="w-3 h-3 rounded-full" 
                              style={{ 
                                backgroundColor: type === 'prompt' ? '#9333ea' : 
                                               type === 'document' ? '#3b82f6' : '#10b981'
                              }}
                            ></div>
                            <span className="capitalize">{type}</span>
                          </div>
                        </DropdownMenuItem>
                      ))}
                    </DropdownMenuContent>
                  </DropdownMenu>
                </div>
                
                <div className="flex items-center gap-2 mr-2">
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button 
                        variant="outline" 
                        size="sm" 
                        className="h-8 bg-studio-background flex items-center gap-1"
                      >
                        <Link className="size-3.5" />
                        <span>{relationshipFilter || 'All Relationships'}</span>
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="start">
                      <DropdownMenuItem onClick={() => setRelationshipFilter(null)}>
                        <span>All Relationships</span>
                      </DropdownMenuItem>
                      <DropdownMenuSeparator />
                      {relationshipTypes.map(type => (
                        <DropdownMenuItem key={type} onClick={() => setRelationshipFilter(type)}>
                          <div className="flex items-center gap-2">
                            <div 
                              className="w-3 h-3 rounded-full" 
                              style={{ backgroundColor: RELATION_COLORS[type as keyof typeof RELATION_COLORS] || RELATION_COLORS.default }}
                            ></div>
                            <span className="capitalize">{type}</span>
                          </div>
                        </DropdownMenuItem>
                      ))}
                    </DropdownMenuContent>
                  </DropdownMenu>
                  
                  {(nodeTypeFilter || relationshipFilter) && (
                    <Button 
                      variant="ghost"
                      size="sm" 
                      onClick={() => {
                        setNodeTypeFilter(null);
                        setRelationshipFilter(null);
                      }}
                      className="h-8 px-2"
                    >
                      <X className="size-3.5" />
                      <span className="ml-1">Clear</span>
                    </Button>
                  )}
                </div>
                
                <Button 
                  variant={showRelationshipsView ? "default" : "outline"}
                  size="sm" 
                  className="h-8 ml-auto"
                  onClick={() => setShowRelationshipsView(!showRelationshipsView)}
                >
                  <Link className="size-3.5 mr-1" />
                  {showRelationshipsView ? 'Hide Connections' : 'Show Connections'}
                </Button>
              </div>
            )}

            {/* Relationship list view - improved styling */}
            {showRelationshipsView && graphNodes.length > 0 && (
              <div className="mt-2 border border-studio-border rounded-md bg-studio-background overflow-hidden">
                <div className="p-2 border-b border-studio-border flex justify-between items-center bg-studio-background-accent">
                  <h3 className="text-sm font-medium">Connections View</h3>
                  <Badge variant="outline" className="text-xs">
                    {relationships.length} connection{relationships.length !== 1 ? 's' : ''}
                  </Badge>
                </div>
                
                <ScrollArea className="h-[200px]">
                  {relationships.length === 0 ? (
                    <div className="flex flex-col items-center justify-center h-[180px] text-center">
                      <div className="w-10 h-10 rounded-full bg-studio-accent/10 flex items-center justify-center mb-2">
                        <Link className="text-studio-accent size-5" />
                      </div>
                      <p className="text-sm text-muted-foreground max-w-[250px]">
                        {relationshipFilter || nodeTypeFilter ? 
                          'No connections match the current filters.' : 
                          'No connections available.'}
                      </p>
                      {(relationshipFilter || nodeTypeFilter) && (
                        <Button 
                          variant="ghost" 
                          size="sm" 
                          onClick={() => {
                            setNodeTypeFilter(null);
                            setRelationshipFilter(null);
                          }}
                          className="mt-2"
                        >
                          Clear Filters
                        </Button>
                      )}
                    </div>
                  ) : (
                    <div className="p-2 space-y-2">
                      {relationships.map((rel) => (
                        <div 
                          key={rel.edge.id}
                          className="p-3 bg-studio-background-accent rounded-md border border-studio-border transition-colors hover:bg-studio-background-accent/80"
                        >
                          <div className="flex flex-col sm:flex-row sm:items-center gap-2 text-sm">
                            <div className="flex items-center gap-1 min-w-0">
                              <Badge 
                                variant="outline" 
                                className="text-xs capitalize shrink-0"
                                style={{ backgroundColor: rel.source.type === 'prompt' ? '#9333ea33' : rel.source.type === 'document' ? '#3b82f633' : '#10b98133' }}
                              >
                                {rel.source.type}
                              </Badge>
                              <span className="font-medium truncate">{rel.source.content.split('\n')[0].substring(0, 30)}</span>
                            </div>
                            
                            <div className="flex items-center gap-1 px-2 shrink-0 self-center">
                              <ArrowRight className="size-3.5" />
                              <Badge 
                                className="text-xs whitespace-nowrap"
                                style={{ 
                                  backgroundColor: RELATION_COLORS[rel.edge.label as keyof typeof RELATION_COLORS] || RELATION_COLORS.default,
                                  color: 'white'
                                }}
                              >
                                {rel.edge.label}
                              </Badge>
                              <ArrowRight className="size-3.5" />
                            </div>
                            
                            <div className="flex items-center gap-1 min-w-0">
                              <Badge 
                                variant="outline" 
                                className="text-xs capitalize shrink-0"
                                style={{ backgroundColor: rel.target.type === 'prompt' ? '#9333ea33' : rel.target.type === 'document' ? '#3b82f633' : '#10b98133' }}
                              >
                                {rel.target.type}
                              </Badge>
                              <span className="font-medium truncate">{rel.target.content.split('\n')[0].substring(0, 30)}</span>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </ScrollArea>
              </div>
            )}

            {/* Graph Container */}
            <div 
              ref={graphContainerRef} 
              className={`flex-1 border border-studio-border rounded-lg overflow-hidden bg-studio-background-accent min-h-[350px] relative ${showRelationshipsView ? 'mt-2' : 'mt-0'}`}
            >
              {/* Loading indicator */}
              {isLoadingGraph && (
                <div className="absolute inset-0 flex items-center justify-center bg-studio-background/50">
                  <div className="text-sm text-center">
                    <div className="animate-spin size-5 border-2 border-studio-accent border-t-transparent rounded-full mx-auto mb-2"></div>
                    <p>Loading graph data...</p>
                  </div>
                </div>
              )}
              
              {/* Error message */}
              {graphError && !isLoadingGraph && (
                <div className="absolute inset-0 flex items-center justify-center">
                  <div className="bg-red-50 text-red-800 rounded-md p-4 max-w-md text-sm">
                    <p className="font-medium mb-1">Error loading graph</p>
                    <p>{graphError}</p>
                  </div>
                </div>
              )}
              
              {/* Empty state */}
              {!isLoadingGraph && !graphError && graphNodes.length === 0 && (
                <div className="absolute inset-0 flex items-center justify-center">
                  <div className="text-center max-w-md p-4">
                    <div className="size-12 rounded-full bg-studio-accent/10 flex items-center justify-center mx-auto mb-3">
                      <Zap className="size-6 text-studio-accent" />
                    </div>
                    <h3 className="text-lg font-medium mb-2">No Knowledge Graph Yet</h3>
                    <p className="text-muted-foreground text-sm mb-4">
                      Generate a knowledge graph by entering text in the field above. The AI will extract concepts and relationships.
                    </p>
                  </div>
                </div>
              )}

              {/* Render ForceGraph if dimensions are ready and data exists */}
              {graphDimensions.width > 0 && graphDimensions.height > 0 && graphNodes.length > 0 && !isLoadingGraph && !graphError && (
                <ForceGraph2D
                  graphData={graphData}
                  width={graphDimensions.width}
                  height={graphDimensions.height}
                  nodeLabel="label"
                  backgroundColor="var(--graph-bg, #1a1a1a)"
                  backgroundImageUrl={`data:image/svg+xml,${encodeURIComponent(`
                    <svg width="100%" height="100%" xmlns="http://www.w3.org/2000/svg">
                      <defs>
                        <linearGradient id="darkGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                          <stop offset="0%" stop-color="#151515" />
                          <stop offset="50%" stop-color="#1a1a1a" />
                          <stop offset="100%" stop-color="#151515" />
                        </linearGradient>
                        <linearGradient id="lightGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                          <stop offset="0%" stop-color="#f8f8f8" />
                          <stop offset="50%" stop-color="#ffffff" />
                          <stop offset="100%" stop-color="#f8f8f8" />
                        </linearGradient>
                        <pattern id="darkGrid" width="20" height="20" patternUnits="userSpaceOnUse">
                          <path d="M 20 0 L 0 0 0 20" fill="none" stroke="#222222" stroke-width="0.5"/>
                        </pattern>
                        <pattern id="lightGrid" width="20" height="20" patternUnits="userSpaceOnUse">
                          <path d="M 20 0 L 0 0 0 20" fill="none" stroke="#e0e0e0" stroke-width="0.5"/>
                        </pattern>
                      </defs>
                      <!-- This script detects the theme and sets the appropriate gradient -->
                      <script type="text/javascript"><![CDATA[
                        function updateTheme() {
                          var isDark = document.documentElement.classList.contains('dark');
                          var bgRect = document.getElementById('bgRect');
                          var gridRect = document.getElementById('gridRect');
                          
                          if (isDark) {
                            bgRect.setAttribute('fill', 'url(#darkGrad)');
                            gridRect.setAttribute('fill', 'url(#darkGrid)');
                          } else {
                            bgRect.setAttribute('fill', 'url(#lightGrad)');
                            gridRect.setAttribute('fill', 'url(#lightGrid)');
                          }
                        }
                        
                        // Initial theme setting
                        updateTheme();
                        
                        // Watch for theme changes
                        var observer = new MutationObserver(function(mutations) {
                          mutations.forEach(function(mutation) {
                            if (mutation.attributeName === 'class') {
                              updateTheme();
                            }
                          });
                        });
                        
                        observer.observe(document.documentElement, { attributes: true });
                      ]]></script>
                      
                      <rect id="bgRect" width="100%" height="100%" fill="url(#darkGrad)"/>
                      <rect id="gridRect" width="100%" height="100%" fill="url(#darkGrid)"/>
                    </svg>
                  `)}`}
                  
                  // Node sizing and interaction
                  nodeRelSize={nodeSizingMode === 'uniform' ? 4 : 1}
                  onNodeClick={handleNodeClick}
                  onNodeRightClick={handleNodeRightClick}
                  
                  // Link styling - ENHANCED with directional particles and arrows
                  linkLabel="label"
                  linkWidth={(link) => (link as GraphLink).highlighted ? 3 : 1}
                  linkColor={(link) => (link as GraphLink).color}
                  linkDirectionalParticles={(link) => {
                    // @ts-ignore - more particles on highlighted links
                    return (link as GraphLink).highlighted ? 8 : 3;
                  }}
                  linkDirectionalParticleWidth={(link) => {
                    // @ts-ignore - wider particles on highlighted links
                    return (link as GraphLink).highlighted ? 4 : 2;
                  }}
                  linkDirectionalParticleSpeed={(link) => {
                    // @ts-ignore - faster particles on highlighted links
                    return (link as GraphLink).highlighted ? 0.015 : 0.006;
                  }}
                  linkDirectionalParticleColor={(link) => {
                    // @ts-ignore - use relationship-specific colors for particles
                    return (link as GraphLink).color;
                  }}
                  // Add directional arrows
                  linkDirectionalArrowLength={5}
                  linkDirectionalArrowRelPos={0.8}
                  linkDirectionalArrowColor={(link) => {
                    // @ts-ignore
                    return (link as GraphLink).color;
                  }}
                  
                  // Node appearance customization
                  nodeCanvasObject={(node, ctx, globalScale) => {
                    const graphNode = node as GraphNode;
                    const label = graphNode.label || '';
                    const fontSize = 12 / globalScale;
                    ctx.font = `${fontSize}px Sans-Serif`;
                    const textWidth = ctx.measureText(label).width;
                    const bgDimensions = [textWidth, fontSize].map(n => n + fontSize * 0.4);

                    const nodeR = graphNode.size || 5;
                    ctx.beginPath();
                    ctx.arc(node.x || 0, node.y || 0, nodeR, 0, 2 * Math.PI); 
                    
                    const isHighlighted = graphNode.highlighted;
                    const nodeType = graphNode.type;
                    
                    if (highlightedNodes.size > 0) {
                      if (isHighlighted) {
                        const gradient = ctx.createRadialGradient(
                          node.x || 0, node.y || 0, 0,
                          node.x || 0, node.y || 0, nodeR * 1.3
                        );
                        
                        if (nodeType === 'prompt') {
                          gradient.addColorStop(0, '#be2eff');
                          gradient.addColorStop(1, '#9333ea');
                        } else if (nodeType === 'document') {
                          gradient.addColorStop(0, '#60a9ff');
                          gradient.addColorStop(1, '#3b82f6');
                        } else {
                          gradient.addColorStop(0, '#34eaa3');
                          gradient.addColorStop(1, '#10b981');
                        }
                        
                        ctx.fillStyle = gradient;
                        ctx.shadowColor = nodeType === 'prompt' ? '#9333ea' : nodeType === 'document' ? '#3b82f6' : '#10b981';
                        ctx.shadowBlur = 12 * highlightIntensity;
                      } else {
                        const gradient = ctx.createRadialGradient(
                          node.x || 0, node.y || 0, 0,
                          node.x || 0, node.y || 0, nodeR
                        );
                        
                        if (nodeType === 'prompt') {
                          gradient.addColorStop(0, '#9333ea33');
                          gradient.addColorStop(1, '#7e22ce22');
                        } else if (nodeType === 'document') {
                          gradient.addColorStop(0, '#3b82f633');
                          gradient.addColorStop(1, '#2563eb22');
                        } else {
                          gradient.addColorStop(0, '#10b98133');
                          gradient.addColorStop(1, '#05966922');
                        }
                        
                        ctx.fillStyle = gradient;
                        ctx.shadowBlur = 0;
                      }
                    } else {
                      const gradient = ctx.createRadialGradient(
                        node.x || 0, node.y || 0, 0,
                        node.x || 0, node.y || 0, nodeR
                      );
                      
                      if (nodeType === 'prompt') {
                        gradient.addColorStop(0, '#9333ea');
                        gradient.addColorStop(1, '#7e22ce');
                      } else if (nodeType === 'document') {
                        gradient.addColorStop(0, '#3b82f6');
                        gradient.addColorStop(1, '#2563eb');
                      } else {
                        gradient.addColorStop(0, '#10b981');
                        gradient.addColorStop(1, '#059669');
                      }
                      
                      ctx.fillStyle = gradient;
                      ctx.shadowBlur = 0;
                    }
                    
                    ctx.fill();
                    
                    ctx.shadowBlur = 0;
                    ctx.strokeStyle = '#ffffff33';
                    ctx.lineWidth = 0.5;
                    ctx.stroke();

                    ctx.fillStyle = 'rgba(18, 18, 18, 0.85)';
                    ctx.fillRect((node.x || 0) - bgDimensions[0] / 2, (node.y || 0) - bgDimensions[1] / 2, bgDimensions[0], bgDimensions[1]);

                    ctx.strokeStyle = '#ffffff22';
                    ctx.lineWidth = 0.5;
                    ctx.strokeRect((node.x || 0) - bgDimensions[0] / 2, (node.y || 0) - bgDimensions[1] / 2, bgDimensions[0], bgDimensions[1]);

                    ctx.textAlign = 'center';
                    ctx.textBaseline = 'middle';
                    ctx.fillStyle = '#ffffff';
                    ctx.fillText(label, node.x || 0, node.y || 0);

                    // Use a type assertion to avoid TypeScript error
                    (node as any).__bckgDimensions = bgDimensions;
                  }}
                  
                  // Improved graph physics for better layout
                  cooldownTicks={150}
                  cooldownTime={5000}
                  d3AlphaDecay={0.01}
                  d3VelocityDecay={0.15}
                  d3Force="charge"
                  d3ForceStrength={-120}
                />
              )} 
            </div>
          </TabsContent>

          <TabsContent value="export" className="flex-1 overflow-hidden flex flex-col p-4 relative z-10">
            <Card className="bg-studio-background-accent border-studio-border mb-4">
              <CardHeader className="pb-2">
                <CardTitle className="text-base font-medium">SQL Query</CardTitle>
                <CardDescription>Write custom SQL to extract data from your memory graph</CardDescription>
              </CardHeader>
              <CardContent>
                <Textarea 
                  className="h-32 resize-none font-mono bg-studio-background"
                  value={sqlQuery}
                  onChange={(e) => setSqlQuery(e.target.value)}
                />
              </CardContent>
              <CardFooter>
                <Button 
                  onClick={handleExportSQL}
                  className="ml-auto flex items-center gap-2 bg-studio-primary hover:bg-studio-primary/90"
                >
                  <FileCode className="size-4" />
                  Execute & Export
                </Button>
              </CardFooter>
            </Card>
            
            <Card className="flex-1 bg-studio-background border-studio-border overflow-hidden flex flex-col">
              <CardHeader className="pb-2">
                <CardTitle className="text-base font-medium">Query Results</CardTitle>
              </CardHeader>
              <CardContent className="flex-1 overflow-hidden">
                <div className="border border-studio-border rounded-md overflow-hidden">
                  <div className="bg-studio-background-accent p-3 border-b border-studio-border">
                    <div className="grid grid-cols-4 gap-4 text-sm font-medium">
                      <div>ID</div>
                      <div>Label</div>
                      <div>Type</div>
                      <div>Connections</div>
                    </div>
                  </div>
                  <ScrollArea className="h-64">
                    <div className="p-3">
                      {sampleNodes.map((node, index) => (
                        <div 
                          key={node.id} 
                          className={`grid grid-cols-4 gap-4 text-sm py-2 ${
                            index !== sampleNodes.length - 1 ? 'border-b border-studio-border' : ''
                          }`}
                        >
                          <div className="text-muted-foreground">{node.id}</div>
                          <div>{node.label}</div>
                          <div>
                            <Badge variant={node.type === 'prompt' ? 'secondary' : 'outline'} className="text-xs">
                              {node.type}
                            </Badge>
                          </div>
                          <div>{node.connections.length}</div>
                        </div>
                      ))}
                    </div>
                  </ScrollArea>
                </div>
              </CardContent>
              <CardFooter className="border-t border-studio-border">
                <div className="flex items-center justify-between w-full text-xs text-muted-foreground">
                  <span>5 rows returned in 0.03s</span>
                  <Button 
                    variant="outline" 
                    size="sm"
                    className="flex items-center gap-1"
                  >
                    <FileJson className="size-3" />
                    Save as JSON
                  </Button>
                </div>
              </CardFooter>
            </Card>
          </TabsContent>
        </Tabs>
      </div>

      {/* Render Context Menu (Outside the main card flow, positioned absolutely) */}
      <ContextMenu
        node={contextMenuNode}
        position={contextMenuPosition}
        isVisible={contextMenuVisible}
        onClose={handleCloseContextMenu}
        onAction={handleContextMenuAction}
      />

      {/* Render Confirmation Dialog */} 
      {confirmDialogState?.isOpen && (
          <AlertDialog open={confirmDialogState.isOpen} onOpenChange={(open) => !open && setConfirmDialogState(null)}>
              <AlertDialogContent>
                  <AlertDialogHeader>
                      <AlertDialogTitle>{confirmDialogState.title}</AlertDialogTitle>
                      <AlertDialogDescription>
                          {confirmDialogState.description}
                      </AlertDialogDescription>
                  </AlertDialogHeader>
                  <AlertDialogFooter>
                      <AlertDialogCancel onClick={() => setConfirmDialogState(null)}>Cancel</AlertDialogCancel>
                      <AlertDialogAction 
                        onClick={() => {
                            confirmDialogState.onConfirm();
                            setConfirmDialogState(null); // Close dialog after confirmation
                        }}
                        className="bg-red-600 hover:bg-red-700 text-white" // Style confirm for destructive action
                      >
                        Confirm
                      </AlertDialogAction>
                  </AlertDialogFooter>
              </AlertDialogContent>
          </AlertDialog>
      )}

    </motion.div>
  );
}
