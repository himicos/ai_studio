
import React, { useState, useRef, useEffect } from "react";
import { motion } from "framer-motion";
import { PanelId } from "@/contexts/WorkspaceContext";
import { BrainCircuit, Search, Filter, ZoomIn, ZoomOut, GitBranch, X } from "lucide-react";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";
import { Select, SelectContent, SelectGroup, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

interface ThoughtWebPanelProps {
  id: PanelId;
}

export default function ThoughtWebPanel({ id }: ThoughtWebPanelProps) {
  const [activeTab, setActiveTab] = useState("mindmap");
  const [scale, setScale] = useState(1);
  const canvasRef = useRef<HTMLDivElement>(null);
  
  const handleZoomIn = () => {
    setScale(prev => Math.min(prev + 0.1, 2));
  };
  
  const handleZoomOut = () => {
    setScale(prev => Math.max(prev - 0.1, 0.5));
  };
  
  // Sample node data for visualization
  const nodes = [
    { id: 'node1', label: 'Project Overview', type: 'document', x: 400, y: 150, connections: ['node2', 'node3'] },
    { id: 'node2', label: 'User Research', type: 'document', x: 200, y: 250, connections: ['node4'] },
    { id: 'node3', label: 'Design System', type: 'document', x: 600, y: 250, connections: ['node5'] },
    { id: 'node4', label: 'Persona: Maria', type: 'entity', x: 150, y: 400, connections: [] },
    { id: 'node5', label: 'Color Palette', type: 'resource', x: 550, y: 400, connections: [] },
    { id: 'node6', label: 'Competitive Analysis', type: 'document', x: 400, y: 350, connections: [] },
  ];
  
  // Sample agents for the network view
  const agents = [
    { id: 'agent1', name: 'Research Assistant', type: 'autonomous', connections: ['agent2', 'agent4'] },
    { id: 'agent2', name: 'Content Writer', type: 'tool', connections: ['agent3'] },
    { id: 'agent3', name: 'Fact Checker', type: 'tool', connections: [] },
    { id: 'agent4', name: 'Data Analyst', type: 'autonomous', connections: ['agent5'] },
    { id: 'agent5', name: 'Report Generator', type: 'tool', connections: [] },
  ];

  return (
    <motion.div 
      className="flex flex-col h-full panel"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.3 }}
    >
      {/* Panel Header */}
      <div className="flex items-center justify-between p-4 border-b border-studio-border">
        <div className="flex items-center gap-2">
          <div className="size-8 rounded-md bg-purple-500/10 flex items-center justify-center">
            <BrainCircuit className="size-4 text-purple-500" />
          </div>
          <h2 className="text-xl font-bold">Thought Web</h2>
        </div>
        <div className="flex items-center gap-2">
          <motion.button
            className="rounded-full p-1.5 border border-studio-border hover:bg-studio-background-accent"
            whileHover={{ scale: 1.1 }}
            whileTap={{ scale: 0.95 }}
          >
            <X className="size-4" />
          </motion.button>
        </div>
      </div>
      
      {/* Panel Body */}
      <div className="flex-1 overflow-hidden">
        <Tabs value={activeTab} onValueChange={setActiveTab} className="h-full flex flex-col">
          <div className="px-4 pt-4">
            <TabsList className="grid w-full grid-cols-3">
              <TabsTrigger value="mindmap">Live Mindmap</TabsTrigger>
              <TabsTrigger value="network">Agent Network View</TabsTrigger>
              <TabsTrigger value="traceback">Chain Traceback</TabsTrigger>
            </TabsList>
          </div>

          <TabsContent value="mindmap" className="flex-1 overflow-hidden p-4">
            <div className="flex-1 h-full flex flex-col">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                  <Select defaultValue="all">
                    <SelectTrigger className="w-[140px]">
                      <SelectValue placeholder="Filter Nodes" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectGroup>
                        <SelectItem value="all">All Nodes</SelectItem>
                        <SelectItem value="document">Documents</SelectItem>
                        <SelectItem value="entity">Entities</SelectItem>
                        <SelectItem value="resource">Resources</SelectItem>
                      </SelectGroup>
                    </SelectContent>
                  </Select>
                  
                  <Button variant="outline" size="sm">
                    <Search className="size-4 mr-2" />
                    Search
                  </Button>
                </div>
                
                <div className="flex items-center gap-2">
                  <Button variant="outline" size="icon" onClick={handleZoomOut}>
                    <ZoomOut className="size-4" />
                  </Button>
                  <span className="text-sm w-12 text-center">{Math.round(scale * 100)}%</span>
                  <Button variant="outline" size="icon" onClick={handleZoomIn}>
                    <ZoomIn className="size-4" />
                  </Button>
                </div>
              </div>
              
              <Card className="bg-studio-background-accent border-studio-border flex-1 relative overflow-hidden">
                <div 
                  className="absolute inset-0 overflow-hidden" 
                  ref={canvasRef}
                >
                  <div 
                    className="relative w-full h-full" 
                    style={{transform: `scale(${scale})`, transformOrigin: 'center', transition: 'transform 0.2s'}}
                  >
                    {/* Render the connections first */}
                    <svg className="absolute inset-0 w-full h-full pointer-events-none">
                      {nodes.map(node => 
                        node.connections.map(targetId => {
                          const target = nodes.find(n => n.id === targetId);
                          if (!target) return null;
                          return (
                            <line 
                              key={`${node.id}-${targetId}`}
                              x1={node.x}
                              y1={node.y}
                              x2={target.x}
                              y2={target.y}
                              stroke="#6E59A5"
                              strokeWidth="1.5"
                              strokeOpacity="0.6"
                            />
                          );
                        })
                      )}
                    </svg>
                    
                    {/* Render the nodes */}
                    {nodes.map(node => (
                      <div
                        key={node.id}
                        className="absolute bg-studio-background-accent border border-studio-border rounded-md p-2 shadow-md cursor-pointer hover:border-studio-primary transition-colors"
                        style={{
                          left: node.x - 60,
                          top: node.y - 25,
                          width: 120,
                        }}
                      >
                        <div className="text-center">
                          <div className="text-xs font-medium mb-1 truncate">{node.label}</div>
                          <Badge variant="outline" className="text-[10px] py-0">
                            {node.type}
                          </Badge>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </Card>
            </div>
          </TabsContent>
          
          <TabsContent value="network" className="flex-1 overflow-hidden p-4">
            <Card className="bg-studio-background-accent border-studio-border mb-4">
              <CardHeader className="pb-2">
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle className="text-base font-medium">Agent Network</CardTitle>
                    <CardDescription>
                      Visualize how agents connect and collaborate
                    </CardDescription>
                  </div>
                  <Button variant="outline" size="sm">
                    <Filter className="size-4 mr-2" />
                    Filter
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-5 gap-4 mb-4">
                  {agents.map((agent, index) => (
                    <Card key={agent.id} className="bg-studio-background border-studio-border">
                      <CardContent className="p-3 text-center">
                        <div className="size-10 mx-auto rounded-full bg-purple-500/10 flex items-center justify-center mb-2">
                          <BrainCircuit className={`size-5 ${agent.type === 'autonomous' ? 'text-purple-500' : 'text-blue-500'}`} />
                        </div>
                        <h4 className="text-sm font-medium line-clamp-1">{agent.name}</h4>
                        <Badge variant="outline" className="text-xs mt-1">
                          {agent.type}
                        </Badge>
                      </CardContent>
                    </Card>
                  ))}
                </div>
                
                <div className="h-64 relative border border-studio-border rounded-md bg-studio-background">
                  <div className="absolute inset-0 flex items-center justify-center">
                    <div className="text-center">
                      <p className="text-muted-foreground mb-2">Interactive graph visualization</p>
                      <Button>Generate Network View</Button>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
          
          <TabsContent value="traceback" className="flex-1 overflow-hidden p-4">
            <Card className="h-full bg-studio-background-accent border-studio-border">
              <CardHeader>
                <div className="flex items-center gap-2">
                  <GitBranch className="size-5 text-purple-500" />
                  <CardTitle>Chain Traceback</CardTitle>
                </div>
                <CardDescription>
                  Track the lineage and connections between thinking chains
                </CardDescription>
              </CardHeader>
              <CardContent className="flex items-center justify-center h-[70%]">
                <div className="text-center">
                  <div className="size-16 rounded-full bg-purple-500/10 mx-auto flex items-center justify-center mb-4">
                    <GitBranch className="size-8 text-purple-500" />
                  </div>
                  <h3 className="text-lg font-medium mb-2">Chain Visualization</h3>
                  <p className="text-muted-foreground mb-6 max-w-md">
                    Track how agents and thoughts connect together over time to form complex reasoning chains
                  </p>
                  <Button>
                    Create New Trace
                  </Button>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </motion.div>
  );
}
