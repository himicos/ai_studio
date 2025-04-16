
import React, { useState } from "react";
import { motion } from "framer-motion";
import { PanelId } from "@/contexts/WorkspaceContext";
import { BookOpen, FileText, BrainCircuit, Code, Search, PlusCircle, X } from "lucide-react";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";

interface MemoryVaultPanelProps {
  id: PanelId;
}

export default function MemoryVaultPanel({ id }: MemoryVaultPanelProps) {
  const [activeTab, setActiveTab] = useState("docs");
  
  // Sample document data
  const documents = [
    { id: "doc1", title: "System Architecture Overview", category: "documentation", updated: "2025-04-10", size: "156 KB" },
    { id: "doc2", title: "Prompt Engineering Guide", category: "documentation", updated: "2025-04-09", size: "238 KB" },
    { id: "doc3", title: "Meeting Notes - Product Roadmap", category: "notes", updated: "2025-04-08", size: "42 KB" },
    { id: "doc4", title: "API Documentation", category: "reference", updated: "2025-04-05", size: "315 KB" },
    { id: "doc5", title: "Deployment Checklist", category: "reference", updated: "2025-04-01", size: "89 KB" },
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
          <div className="size-8 rounded-md bg-blue-500/10 flex items-center justify-center">
            <BookOpen className="size-4 text-blue-500" />
          </div>
          <h2 className="text-xl font-bold">Memory Vault</h2>
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
              <TabsTrigger value="docs">System Docs</TabsTrigger>
              <TabsTrigger value="autonotes">AutoNotes</TabsTrigger>
              <TabsTrigger value="codebase">Codebase Recall</TabsTrigger>
            </TabsList>
          </div>

          <TabsContent value="docs" className="flex-1 overflow-hidden p-4">
            <Card className="bg-studio-background-accent border-studio-border mb-4">
              <CardHeader className="pb-2">
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle className="text-base font-medium">Knowledge Base</CardTitle>
                    <CardDescription>
                      Internal documentation and reference materials
                    </CardDescription>
                  </div>
                  <div className="flex items-center gap-2">
                    <Button variant="outline" size="sm">
                      <Search className="size-4 mr-2" />
                      Search
                    </Button>
                    <Button size="sm">
                      <PlusCircle className="size-4 mr-2" />
                      Add Document
                    </Button>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <Input placeholder="Filter documents..." className="mb-4" />
                
                <div className="space-y-2">
                  {documents.map(doc => (
                    <Card key={doc.id} className="bg-studio-background border-studio-border">
                      <CardContent className="p-3 flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <div className="size-8 rounded-full bg-blue-500/10 flex items-center justify-center">
                            <FileText className="size-4 text-blue-500" />
                          </div>
                          <div>
                            <h4 className="text-sm font-medium">{doc.title}</h4>
                            <div className="flex items-center gap-2 mt-0.5">
                              <Badge variant="outline" className="text-xs">{doc.category}</Badge>
                              <span className="text-xs text-muted-foreground">Updated: {doc.updated}</span>
                            </div>
                          </div>
                        </div>
                        <div className="text-xs text-muted-foreground">{doc.size}</div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>
          
          <TabsContent value="autonotes" className="flex-1 overflow-hidden p-4">
            <div className="grid grid-cols-2 gap-4 h-full">
              <Card className="bg-studio-background-accent border-studio-border">
                <CardHeader className="pb-2">
                  <CardTitle className="text-base font-medium">AutoNotes</CardTitle>
                  <CardDescription>
                    AI-generated notes and summaries
                  </CardDescription>
                </CardHeader>
                <CardContent className="p-0">
                  <ScrollArea className="h-[400px]">
                    <div className="p-4 space-y-3">
                      <Card className="bg-studio-background border-studio-border">
                        <CardContent className="p-3">
                          <div className="flex items-center justify-between mb-2">
                            <h4 className="text-sm font-medium">Product Strategy Meeting</h4>
                            <Badge variant="outline" className="text-xs">Auto-generated</Badge>
                          </div>
                          <p className="text-xs text-muted-foreground mb-2">
                            Generated from meeting recording on April 10, 2025
                          </p>
                          <Button variant="outline" size="sm" className="w-full">View Summary</Button>
                        </CardContent>
                      </Card>
                      
                      <Card className="bg-studio-background border-studio-border">
                        <CardContent className="p-3">
                          <div className="flex items-center justify-between mb-2">
                            <h4 className="text-sm font-medium">Research Analysis</h4>
                            <Badge variant="outline" className="text-xs">Auto-generated</Badge>
                          </div>
                          <p className="text-xs text-muted-foreground mb-2">
                            Generated from document review on April 8, 2025
                          </p>
                          <Button variant="outline" size="sm" className="w-full">View Summary</Button>
                        </CardContent>
                      </Card>
                      
                      <Card className="bg-studio-background border-studio-border">
                        <CardContent className="p-3">
                          <div className="flex items-center justify-between mb-2">
                            <h4 className="text-sm font-medium">Client Call Notes</h4>
                            <Badge variant="outline" className="text-xs">Auto-generated</Badge>
                          </div>
                          <p className="text-xs text-muted-foreground mb-2">
                            Generated from call recording on April 5, 2025
                          </p>
                          <Button variant="outline" size="sm" className="w-full">View Summary</Button>
                        </CardContent>
                      </Card>
                    </div>
                  </ScrollArea>
                </CardContent>
              </Card>
              
              <Card className="bg-studio-background-accent border-studio-border">
                <CardHeader className="pb-2">
                  <CardTitle className="text-base font-medium">Generate New Notes</CardTitle>
                  <CardDescription>
                    Create new auto-notes from content
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="flex flex-col items-center justify-center h-[400px] text-center">
                    <div className="size-16 rounded-full bg-blue-500/10 mx-auto flex items-center justify-center mb-4">
                      <BrainCircuit className="size-8 text-blue-500" />
                    </div>
                    <h3 className="text-lg font-medium mb-2">AutoNotes Generator</h3>
                    <p className="text-muted-foreground mb-6 max-w-xs">
                      Upload content or connect a meeting to automatically generate structured notes
                    </p>
                    <div className="flex gap-2">
                      <Button>Record Meeting</Button>
                      <Button variant="outline">Upload Content</Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>
          
          <TabsContent value="codebase" className="flex-1 overflow-hidden p-4">
            <Card className="h-full bg-studio-background-accent border-studio-border">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle className="text-base font-medium">Codebase Recall</CardTitle>
                    <CardDescription>
                      Semantic search across your codebase
                    </CardDescription>
                  </div>
                  <Button variant="outline" size="sm">
                    <Code className="size-4 mr-2" />
                    Add Repository
                  </Button>
                </div>
              </CardHeader>
              <CardContent className="flex items-center justify-center h-[70%]">
                <div className="text-center max-w-md">
                  <div className="size-16 rounded-full bg-blue-500/10 mx-auto flex items-center justify-center mb-4">
                    <Code className="size-8 text-blue-500" />
                  </div>
                  <h3 className="text-lg font-medium mb-2">Codebase Memory</h3>
                  <p className="text-muted-foreground mb-6">
                    Connect your code repositories to enable semantic code search and intelligent context for your agents
                  </p>
                  <Button>
                    Connect First Repository
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
