
import React, { useState } from "react";
import { motion } from "framer-motion";
import { PanelId } from "@/contexts/WorkspaceContext";
import { Search, PackagePlus, Zap, PlusCircle, X } from "lucide-react";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

interface VectorMinePanelProps {
  id: PanelId;
}

export default function VectorMinePanel({ id }: VectorMinePanelProps) {
  const [activeTab, setActiveTab] = useState("search");
  
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
          <div className="size-8 rounded-md bg-studio-primary/10 flex items-center justify-center">
            <Search className="size-4 text-studio-primary" />
          </div>
          <h2 className="text-xl font-bold">Vector Mine</h2>
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
              <TabsTrigger value="search">Search Corpus</TabsTrigger>
              <TabsTrigger value="insight">Latent Insight Agent</TabsTrigger>
              <TabsTrigger value="chaos">Chaos Simulator Inject</TabsTrigger>
            </TabsList>
          </div>

          <TabsContent value="search" className="flex-1 overflow-hidden p-4 flex flex-col">
            <Card className="bg-studio-background-accent border-studio-border mb-4">
              <CardHeader className="pb-2">
                <CardTitle className="text-base font-medium">Search Knowledge Base</CardTitle>
                <CardDescription>
                  Query your indexed documents with semantic search
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex gap-2">
                  <Input 
                    className="flex-1" 
                    placeholder="Search for concepts, ideas or specific information..." 
                  />
                  <Button>
                    <Search className="size-4 mr-2" />
                    Search
                  </Button>
                </div>
              </CardContent>
            </Card>
            
            <Card className="flex-1 bg-studio-background-accent border-studio-border">
              <CardHeader className="pb-2">
                <CardTitle className="text-base font-medium">Connected Sources</CardTitle>
                <CardDescription>
                  Data sources indexed for semantic search
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <Card className="bg-studio-background border-studio-border">
                    <CardContent className="p-4 flex items-center gap-3">
                      <div className="size-8 rounded-full bg-blue-500/20 flex items-center justify-center">
                        <span className="font-semibold text-blue-500">D</span>
                      </div>
                      <div className="flex-1">
                        <h4 className="text-sm font-medium">Demo Documents</h4>
                        <p className="text-xs text-muted-foreground">12 files · 2.3MB</p>
                      </div>
                    </CardContent>
                  </Card>
                  
                  <Card className="bg-studio-background border-studio-border">
                    <CardContent className="p-4 flex items-center justify-center text-center">
                      <Button variant="outline" size="sm" className="w-full">
                        <PlusCircle className="size-4 mr-2" />
                        Connect New Source
                      </Button>
                    </CardContent>
                  </Card>
                </div>
                
                <Card className="bg-studio-background border-studio-border p-4">
                  <div className="flex flex-col items-center justify-center py-8">
                    <PackagePlus className="size-12 text-muted-foreground mb-2" />
                    <h3 className="text-base font-medium mb-1">Add More Connectors</h3>
                    <p className="text-sm text-muted-foreground text-center max-w-md mb-4">
                      Connect to Notion, Google Drive, Slack and more with our premium connectors
                    </p>
                    <Button>
                      <Zap className="size-4 mr-2" />
                      Explore Connectors
                    </Button>
                  </div>
                </Card>
              </CardContent>
            </Card>
          </TabsContent>
          
          <TabsContent value="insight" className="flex-1 overflow-hidden p-4">
            <Card className="h-full bg-studio-background-accent border-studio-border">
              <CardHeader>
                <CardTitle>Latent Insight Agent</CardTitle>
                <CardDescription>
                  Discover hidden patterns and connections in your data
                </CardDescription>
              </CardHeader>
              <CardContent className="flex items-center justify-center h-[70%]">
                <div className="text-center">
                  <div className="size-16 rounded-full bg-studio-background/50 mx-auto flex items-center justify-center mb-4">
                    <Zap className="size-8 text-studio-primary" />
                  </div>
                  <h3 className="text-lg font-medium mb-2">Insight Agent Ready</h3>
                  <p className="text-muted-foreground mb-6 max-w-md">
                    Run this agent to analyze your connected data sources and extract insights
                  </p>
                  <Button>Run Insight Analysis</Button>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
          
          <TabsContent value="chaos" className="flex-1 overflow-hidden p-4">
            <Card className="h-full bg-studio-background-accent border-studio-border">
              <CardHeader>
                <CardTitle>Chaos Simulator Inject</CardTitle>
                <CardDescription>
                  Simulate unpredicted events and test system resilience
                </CardDescription>
              </CardHeader>
              <CardContent className="flex items-center justify-center h-[70%]">
                <div className="text-center">
                  <div className="size-16 rounded-full bg-red-500/20 mx-auto flex items-center justify-center mb-4">
                    <Zap className="size-8 text-red-500" />
                  </div>
                  <h3 className="text-lg font-medium mb-2">Chaos Simulator</h3>
                  <p className="text-muted-foreground mb-6 max-w-md">
                    This advanced module helps test your agents by introducing unexpected scenarios
                  </p>
                  <Button variant="destructive">Initialize Chaos Injection</Button>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </motion.div>
  );
}
