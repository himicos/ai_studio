import React, { useState, useEffect, useRef, useCallback } from "react";
import { motion } from "framer-motion";
import ForceGraph2D from 'react-force-graph-2d';
import { PanelId } from "@/contexts/WorkspaceContext";
import { 
  Network, Link, Zap, FileCode, 
  Plug, ArrowRight, Plus, Search, 
  DatabaseBackup, FileJson, BrainCircuit
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
  MemoryNode,
  MemoryEdge
} from "../../lib/api";
import { Slider } from "@/components/ui/slider";
import { Label } from "@/components/ui/label";

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
  const [minSimilarity, setMinSimilarity] = useState<number>(0.5);

  const [isGeneratingGraph, setIsGeneratingGraph] = useState(false);

  const [graphNodes, setGraphNodes] = useState<MemoryNode[]>([]);
  const [graphEdges, setGraphEdges] = useState<MemoryEdge[]>([]);
  const [isLoadingGraph, setIsLoadingGraph] = useState(false);
  const [graphError, setGraphError] = useState<string | null>(null);

  const graphContainerRef = useRef<HTMLDivElement>(null);
  const [graphDimensions, setGraphDimensions] = useState({ width: 0, height: 0 });

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
      setGraphEdges(edgesResponse);
      if (nodesResponse.length > 0 || edgesResponse.length > 0) {
         toast.info(`Loaded ${nodesResponse.length} nodes and ${edgesResponse.length} edges.`);
      }
    } catch (error) {
      console.error("[DEBUG] Failed to fetch graph data inside fetchGraphData:", error);
      const errorMsg = error instanceof Error ? error.message : "Could not load graph data.";
      setGraphError(errorMsg);
      toast.error("Failed to load graph data", { description: errorMsg });
    } finally {
      setIsLoadingGraph(false);
    }
  }, []);

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
      const payload: SemanticSearchRequestPayload = { 
        query_text: semanticQuery,
        min_similarity: minSimilarity
      };
      const results = await searchMemoryNodes(payload);
      setSemanticResults(results);
      if (results.length === 0) {
         toast.info("No similar memory nodes found.");
      } else {
         toast.success(`Found ${results.length} similar node(s).`);
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

  const graphData = {
    nodes: graphNodes.map(node => ({
        id: node.id, 
        label: node.content.split('\n')[0].substring(0,30),
        fullContent: node.content,
        type: node.type,
    })),
    links: graphEdges.map(edge => ({ 
        source: edge.source_node_id,
        target: edge.target_node_id,
        label: edge.label,
    }))
  };

  console.log('[DEBUG] MemoryPanel State Check:', {
    activeTab,
    isLoadingGraph,
    graphError,
    graphNodesLength: graphNodes.length,
    graphEdgesLength: graphEdges.length,
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
                 <span className="text-xs font-medium w-10 text-right">{minSimilarity.toFixed(2)}</span>
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
                      {semanticResults.map(node => (
                        <Card key={node.id} className="bg-studio-background-accent mb-4">
                          <CardHeader className="pb-2">
                             <div className="flex justify-between items-start mb-1">
                                <Badge variant="outline">{node.type}</Badge>
                                <Badge variant="secondary" title="Similarity Score">
                                   {(node.similarity * 100).toFixed(1)}%
                                </Badge>
                             </div>
                             <CardTitle className="text-sm font-medium truncate" title={node.content}>
                                {node.content.split('\\n')[0].substring(0, 100)}{node.content.length > 100 ? '...' : ''}
                             </CardTitle>
                             <CardDescription className="text-xs">
                               ID: {node.id} | Created: {new Date(node.created_at * 1000).toLocaleDateString()}
                             </CardDescription>
                          </CardHeader>
                          <CardContent className="text-xs text-muted-foreground pt-1 pb-3">
                             <p className="line-clamp-3" title={node.content}> 
                                {node.content.split('\\n').slice(1).join('\\n') || node.content}
                             </p>
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
            {/* Compact Control Row - Moved higher and made more compact */}
            <div className="flex items-center gap-2 mb-2 p-1 bg-studio-background-accent rounded-md border border-studio-border">
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
            
            {/* Graph Container - Now taller with more space for visualization */}
            <div 
              ref={graphContainerRef} 
              className="flex-1 border border-studio-border rounded-lg overflow-hidden bg-studio-background-accent min-h-[350px] relative"
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
                  nodeLabel="label" // Show label on hover
                  backgroundColor="var(--graph-bg, #1a1a1a)" // Theme-sensitive background
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
                  // Customize appearance
                  nodeCanvasObject={(node, ctx, globalScale) => {
                    const label = node.label as string;
                    const fontSize = 12 / globalScale;
                    ctx.font = `${fontSize}px Sans-Serif`;
                    const textWidth = ctx.measureText(label).width;
                    const bgDimensions = [textWidth, fontSize].map(n => n + fontSize * 0.4); // Box padding
                    
                    // Node visualization (circle with gradient)
                    const nodeR = 5;
                    ctx.beginPath();
                    ctx.arc(node.x ?? 0, node.y ?? 0, nodeR, 0, 2 * Math.PI);
                    
                    // Create gradient for nodes based on type
                    const gradient = ctx.createRadialGradient(
                      node.x ?? 0, node.y ?? 0, 0,
                      node.x ?? 0, node.y ?? 0, nodeR
                    );
                    
                    // Use type to determine node color
                    const nodeType = (node as any).type;
                    if (nodeType === 'prompt') {
                      gradient.addColorStop(0, '#9333ea'); // Violet core
                      gradient.addColorStop(1, '#7e22ce'); // Darker violet edge
                    } else if (nodeType === 'document') {
                      gradient.addColorStop(0, '#3b82f6'); // Blue core
                      gradient.addColorStop(1, '#2563eb'); // Darker blue edge
                    } else {
                      gradient.addColorStop(0, '#10b981'); // Green core
                      gradient.addColorStop(1, '#059669'); // Darker green edge
                    }
                    
                    ctx.fillStyle = gradient;
                    ctx.fill();
                    
                    // Draw node border
                    ctx.strokeStyle = '#ffffff33';
                    ctx.lineWidth = 0.5;
                    ctx.stroke();

                    // Background rectangle for text
                    ctx.fillStyle = 'rgba(18, 18, 18, 0.85)'; // Dark background for text
                    ctx.fillRect((node.x ?? 0) - bgDimensions[0] / 2, (node.y ?? 0) - bgDimensions[1] / 2, bgDimensions[0], bgDimensions[1]);

                    // Text border
                    ctx.strokeStyle = '#ffffff22';
                    ctx.lineWidth = 0.5;
                    ctx.strokeRect((node.x ?? 0) - bgDimensions[0] / 2, (node.y ?? 0) - bgDimensions[1] / 2, bgDimensions[0], bgDimensions[1]);

                    // Text
                    ctx.textAlign = 'center';
                    ctx.textBaseline = 'middle';
                    ctx.fillStyle = '#ffffff'; // White text for better contrast
                    ctx.fillText(label, node.x ?? 0, node.y ?? 0);

                    node.__bckgDimensions = bgDimensions; // Cache dimensions for selection highlighting
                  }}
                  nodePointerAreaPaint={(node, color, ctx) => {
                     // Highlight area on hover
                     ctx.fillStyle = color;
                     const bckgDimensions = node.__bckgDimensions as number[] | undefined;
                     if (bckgDimensions) {
                       ctx.fillRect((node.x ?? 0) - bckgDimensions[0] / 2, (node.y ?? 0) - bckgDimensions[1] / 2, bckgDimensions[0], bckgDimensions[1]);
                     }
                  }}
                  // Link styling
                  linkLabel="label"
                  linkColor={() => "#ffffff33"} // Subtle link color
                  linkWidth={1}
                  linkDirectionalParticles={3} // More particles
                  linkDirectionalParticleWidth={2} // Slightly thicker particles
                  linkDirectionalParticleSpeed={0.006} // Slightly faster movement
                  linkDirectionalParticleColor={() => "#9333ea"} // Violet particles
                  linkCanvasObjectMode={() => "after"}
                  linkCanvasObject={(link, ctx) => {
                     const MAX_FONT_SIZE = 4;
                     const LABEL_NODE_MARGIN = 8; // Adjusted node size estimate
                     const start = link.source as any; // Cast to access x,y potentially
                     const end = link.target as any;

                     // Ignore unbound links
                     if (typeof start !== 'object' || typeof end !== 'object') return;

                     // Calculate label positioning
                     const textPos = Object.assign({}, ...['x', 'y'].map(c => ({
                       [c]: start[c] + (end[c] - start[c]) / 2 // Middle of line
                     })));

                     const relLink = { x: end.x - start.x, y: end.y - start.y };
                     const maxTextLength = Math.sqrt(Math.pow(relLink.x, 2) + Math.pow(relLink.y, 2)) - LABEL_NODE_MARGIN * 2;

                     let textAngle = Math.atan2(relLink.y, relLink.x);
                     // Maintain label upright node_orientation
                     if (textAngle > Math.PI / 2) textAngle = -(Math.PI - textAngle);
                     if (textAngle < -Math.PI / 2) textAngle = -(-Math.PI - textAngle);

                     const label = `${link.label}`;

                     // Estimate fontSize to fit in link length
                     ctx.font = '1px Sans-Serif';
                     const fontSize = Math.min(MAX_FONT_SIZE, maxTextLength / ctx.measureText(label).width);
                     ctx.font = `${fontSize}px Sans-Serif`;

                     // Draw text label with better visibility
                     ctx.save();
                     ctx.translate(textPos.x, textPos.y);
                     ctx.rotate(textAngle);
                     
                     // Background for text label (capsule shape)
                     const labelWidth = ctx.measureText(label).width;
                     const labelHeight = fontSize;
                     const labelBgHeight = labelHeight * 1.2;
                     const labelBgWidth = labelWidth * 1.2;
                     const labelBgRadius = labelBgHeight / 2;
                     
                     ctx.fillStyle = 'rgba(18, 18, 18, 0.7)';
                     // Draw rounded rectangle
                     ctx.beginPath();
                     ctx.moveTo(-labelBgWidth/2 + labelBgRadius, -labelBgHeight/2);
                     ctx.lineTo(labelBgWidth/2 - labelBgRadius, -labelBgHeight/2);
                     ctx.arc(labelBgWidth/2 - labelBgRadius, 0, labelBgRadius, -Math.PI/2, Math.PI/2);
                     ctx.lineTo(-labelBgWidth/2 + labelBgRadius, labelBgHeight/2);
                     ctx.arc(-labelBgWidth/2 + labelBgRadius, 0, labelBgRadius, Math.PI/2, -Math.PI/2);
                     ctx.closePath();
                     ctx.fill();
                     
                     // Text
                     ctx.textAlign = 'center';
                     ctx.textBaseline = 'middle';
                     ctx.fillStyle = '#ffffff'; // White text
                     ctx.fillText(label, 0, 0);
                     ctx.restore();
                  }}
                  // Other ForceGraph props
                  enableZoomInteraction={true}
                  enablePanInteraction={true}
                  cooldownTicks={100}
                  cooldownTime={3000} // Longer cooldown for better stabilization
                  nodeRelSize={4}
                  d3AlphaDecay={0.015} // Slower decay for smoother motion
                  d3VelocityDecay={0.2} // Less friction for more dynamic movement
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
    </motion.div>
  );
}
