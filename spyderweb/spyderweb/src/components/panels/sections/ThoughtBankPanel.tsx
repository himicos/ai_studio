
import React, { useState } from "react";
import { motion } from "framer-motion";
import { PanelId } from "@/contexts/WorkspaceContext";
import { Boxes, CloudUpload, Database, History, Filter, Search, X } from "lucide-react";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";

interface ThoughtBankPanelProps {
  id: PanelId;
}

export default function ThoughtBankPanel({ id }: ThoughtBankPanelProps) {
  const [activeTab, setActiveTab] = useState("logs");
  
  // Mock prompt log data
  const promptLogs = [
    { id: "log1", prompt: "Generate a strategy for improving team collaboration in remote work environments", 
      model: "gpt-4", timestamp: "2025-04-12T15:42:21", tokens: 428 },
    { id: "log2", prompt: "Analyze the following customer feedback and identify key issues", 
      model: "claude-3", timestamp: "2025-04-12T14:35:12", tokens: 756 },
    { id: "log3", prompt: "Create a step-by-step tutorial for implementing a GraphQL API", 
      model: "gpt-4", timestamp: "2025-04-12T12:15:42", tokens: 1043 },
    { id: "log4", prompt: "Summarize the main findings from the attached research paper", 
      model: "claude-3", timestamp: "2025-04-11T16:24:18", tokens: 892 },
    { id: "log5", prompt: "Generate ideas for a new product targeting Gen Z consumers", 
      model: "gpt-4", timestamp: "2025-04-11T10:08:57", tokens: 532 },
  ];
  
  // Mock vector snapshots data
  const vectorSnapshots = [
    { id: "vec1", name: "Customer Interview Analysis", timestamp: "2025-04-12", vectors: 256, size: "4.2 MB" },
    { id: "vec2", name: "Competitor Research", timestamp: "2025-04-10", vectors: 128, size: "2.8 MB" },
    { id: "vec3", name: "Product Requirements", timestamp: "2025-04-08", vectors: 192, size: "3.5 MB" },
    { id: "vec4", name: "Market Analysis", timestamp: "2025-04-05", vectors: 320, size: "5.1 MB" },
  ];
  
  // Mock agent memory data
  const agentMemories = [
    { id: "mem1", agent: "Research Assistant", timestamp: "2025-04-12T16:42:00", entries: 15, size: "1.8 MB" },
    { id: "mem2", agent: "Data Analyst", timestamp: "2025-04-12T14:15:32", entries: 8, size: "0.9 MB" },
    { id: "mem3", agent: "Project Manager", timestamp: "2025-04-11T18:22:45", entries: 23, size: "2.4 MB" },
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
          <div className="size-8 rounded-md bg-orange-500/10 flex items-center justify-center">
            <Boxes className="size-4 text-orange-500" />
          </div>
          <h2 className="text-xl font-bold">Thought Bank</h2>
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
              <TabsTrigger value="logs">Prompt Logs</TabsTrigger>
              <TabsTrigger value="vectors">Vector Snapshots</TabsTrigger>
              <TabsTrigger value="memory">Agent Memory Deltas</TabsTrigger>
            </TabsList>
          </div>

          <TabsContent value="logs" className="flex-1 overflow-hidden p-4">
            <Card className="bg-studio-background-accent border-studio-border mb-4">
              <CardHeader className="pb-2">
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle className="text-base font-medium">Prompt History</CardTitle>
                    <CardDescription>
                      Review and analyze previous prompts
                    </CardDescription>
                  </div>
                  <div className="flex items-center gap-2">
                    <Button variant="outline" size="sm">
                      <Filter className="size-4 mr-2" />
                      Filter
                    </Button>
                    <Button variant="outline" size="sm">
                      <History className="size-4 mr-2" />
                      Show All
                    </Button>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <Input placeholder="Search prompts..." className="mb-4" />
                
                <div className="space-y-2">
                  {promptLogs.map(log => (
                    <Card key={log.id} className="bg-studio-background border-studio-border">
                      <CardContent className="p-3">
                        <div className="flex justify-between items-start mb-2">
                          <div className="flex-1">
                            <p className="text-sm line-clamp-1">{log.prompt}</p>
                          </div>
                          <Badge variant="outline" className="ml-2 shrink-0">{log.model}</Badge>
                        </div>
                        <div className="flex items-center justify-between text-xs text-muted-foreground">
                          <div>
                            {new Date(log.timestamp).toLocaleString()}
                          </div>
                          <div>
                            {log.tokens} tokens
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>
          
          <TabsContent value="vectors" className="flex-1 overflow-hidden p-4">
            <div className="grid grid-cols-3 gap-4 mb-4">
              <Card className="bg-studio-background-accent border-studio-border">
                <CardContent className="p-4">
                  <div className="text-sm text-muted-foreground">Total Snapshots</div>
                  <div className="text-2xl font-bold mt-1">24</div>
                  <div className="text-xs text-muted-foreground mt-1">
                    <span>15.6 MB total</span>
                  </div>
                </CardContent>
              </Card>
              
              <Card className="bg-studio-background-accent border-studio-border">
                <CardContent className="p-4">
                  <div className="text-sm text-muted-foreground">Total Vectors</div>
                  <div className="text-2xl font-bold mt-1">4,128</div>
                  <div className="text-xs text-muted-foreground mt-1">
                    <span>Across all snapshots</span>
                  </div>
                </CardContent>
              </Card>
              
              <Card className="bg-studio-background-accent border-studio-border">
                <CardContent className="p-4">
                  <div className="text-sm text-muted-foreground">Average Dimension</div>
                  <div className="text-2xl font-bold mt-1">1,536</div>
                  <div className="text-xs text-muted-foreground mt-1">
                    <span>Embedding dimensions</span>
                  </div>
                </CardContent>
              </Card>
            </div>
            
            <Card className="bg-studio-background-accent border-studio-border">
              <CardHeader className="pb-2">
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle className="text-base font-medium">Vector Snapshots</CardTitle>
                    <CardDescription>
                      Stored vector embeddings and index snapshots
                    </CardDescription>
                  </div>
                  <div className="flex items-center gap-2">
                    <Button variant="outline" size="sm">
                      <Search className="size-4 mr-2" />
                      Search
                    </Button>
                    <Button size="sm">
                      <CloudUpload className="size-4 mr-2" />
                      Import
                    </Button>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {vectorSnapshots.map(snapshot => (
                    <Card key={snapshot.id} className="bg-studio-background border-studio-border">
                      <CardContent className="p-3 flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <div className="size-8 rounded-full bg-orange-500/10 flex items-center justify-center">
                            <Database className="size-4 text-orange-500" />
                          </div>
                          <div>
                            <h4 className="text-sm font-medium">{snapshot.name}</h4>
                            <div className="flex items-center gap-2 mt-0.5">
                              <span className="text-xs text-muted-foreground">{snapshot.timestamp}</span>
                              <span className="text-xs text-muted-foreground">•</span>
                              <span className="text-xs text-muted-foreground">{snapshot.vectors} vectors</span>
                              <span className="text-xs text-muted-foreground">•</span>
                              <span className="text-xs text-muted-foreground">{snapshot.size}</span>
                            </div>
                          </div>
                        </div>
                        <div className="flex gap-2">
                          <Button variant="ghost" size="sm">View</Button>
                          <Button variant="ghost" size="sm">Export</Button>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>
          
          <TabsContent value="memory" className="flex-1 overflow-hidden p-4">
            <Card className="bg-studio-background-accent border-studio-border mb-4">
              <CardHeader className="pb-2">
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle className="text-base font-medium">Agent Memory Deltas</CardTitle>
                    <CardDescription>
                      Track changes in agent memory over time
                    </CardDescription>
                  </div>
                  <Button size="sm">
                    Capture Current State
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                <ScrollArea className="h-[400px]">
                  <div className="space-y-4">
                    {agentMemories.map(memory => (
                      <Card key={memory.id} className="bg-studio-background border-studio-border">
                        <CardContent className="p-4">
                          <div className="flex items-center justify-between mb-3">
                            <h3 className="font-medium">{memory.agent}</h3>
                            <Badge variant="outline">{memory.entries} entries</Badge>
                          </div>
                          
                          <div className="space-y-2">
                            <div className="flex justify-between text-sm">
                              <span className="text-muted-foreground">Timestamp:</span>
                              <span>{new Date(memory.timestamp).toLocaleString()}</span>
                            </div>
                            <div className="flex justify-between text-sm">
                              <span className="text-muted-foreground">Size:</span>
                              <span>{memory.size}</span>
                            </div>
                            <div className="flex justify-between text-sm">
                              <span className="text-muted-foreground">Changes:</span>
                              <Badge variant="outline" className="bg-green-500/10 text-green-500">
                                +{Math.floor(Math.random() * 10) + 1} new
                              </Badge>
                            </div>
                          </div>
                          
                          <div className="flex justify-end mt-3">
                            <Button variant="outline" size="sm">View Details</Button>
                          </div>
                        </CardContent>
                      </Card>
                    ))}
                    
                    <div className="flex justify-center py-4">
                      <Button variant="outline">Load More</Button>
                    </div>
                  </div>
                </ScrollArea>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </motion.div>
  );
}
