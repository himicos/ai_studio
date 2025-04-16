
import React, { useState } from "react";
import { motion } from "framer-motion";
import { PanelId } from "@/contexts/WorkspaceContext";
import { Server, BarChart3, DollarSign, PlusCircle, X, Zap } from "lucide-react";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";

interface LoadoutConfigPanelProps {
  id: PanelId;
}

export default function LoadoutConfigPanel({ id }: LoadoutConfigPanelProps) {
  const [activeTab, setActiveTab] = useState("router");
  
  // Mock model data
  const models = [
    { name: "GPT-4 Turbo", provider: "OpenAI", status: "active", type: "completion", cost: "high", performance: 95 },
    { name: "Claude 3 Opus", provider: "Anthropic", status: "active", type: "completion", cost: "high", performance: 92 },
    { name: "Gemini Pro", provider: "Google", status: "disabled", type: "completion", cost: "medium", performance: 89 },
    { name: "Llama 3", provider: "Meta", status: "active", type: "completion", cost: "low", performance: 82 },
    { name: "Whisper v3", provider: "OpenAI", status: "active", type: "audio", cost: "medium", performance: 97 },
    { name: "DALL-E 3", provider: "OpenAI", status: "active", type: "image", cost: "high", performance: 90 },
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
            <Server className="size-4 text-purple-500" />
          </div>
          <h2 className="text-xl font-bold">Loadout Config</h2>
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
              <TabsTrigger value="router">LLM Router</TabsTrigger>
              <TabsTrigger value="benchmarks">Model Benchmarks</TabsTrigger>
              <TabsTrigger value="cost">Cost View</TabsTrigger>
            </TabsList>
          </div>

          <TabsContent value="router" className="flex-1 overflow-hidden p-4">
            <Card className="bg-studio-background-accent border-studio-border mb-4">
              <CardHeader className="pb-2">
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle className="text-base font-medium">Model Configuration</CardTitle>
                    <CardDescription>
                      Configure and route requests to different models
                    </CardDescription>
                  </div>
                  <Button size="sm">
                    <PlusCircle className="size-4 mr-2" />
                    Add Model
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="grid grid-cols-6 gap-4 text-sm font-medium text-muted-foreground border-b border-studio-border pb-2">
                    <div>Model</div>
                    <div>Provider</div>
                    <div>Type</div>
                    <div>Cost</div>
                    <div>Status</div>
                    <div></div>
                  </div>
                  
                  {models.map((model, index) => (
                    <div key={index} className="grid grid-cols-6 gap-4 items-center text-sm">
                      <div className="font-medium">{model.name}</div>
                      <div>{model.provider}</div>
                      <div>{model.type}</div>
                      <div>
                        {model.cost === "high" && <Badge variant="outline" className="bg-red-500/10 text-red-500">High</Badge>}
                        {model.cost === "medium" && <Badge variant="outline" className="bg-yellow-500/10 text-yellow-500">Medium</Badge>}
                        {model.cost === "low" && <Badge variant="outline" className="bg-green-500/10 text-green-500">Low</Badge>}
                      </div>
                      <div>
                        {model.status === "active" ? (
                          <Badge variant="outline" className="bg-green-500/10 text-green-500">Active</Badge>
                        ) : (
                          <Badge variant="outline" className="bg-gray-500/10 text-gray-500">Disabled</Badge>
                        )}
                      </div>
                      <div className="flex justify-end">
                        <Button variant="ghost" size="sm">Configure</Button>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
            
            <Card className="bg-studio-background-accent border-studio-border">
              <CardHeader className="pb-2">
                <CardTitle className="text-base font-medium">Upgrade Options</CardTitle>
                <CardDescription>
                  Expand your model capabilities with premium options
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 gap-4">
                  <Card className="bg-studio-background border-studio-border">
                    <CardContent className="p-6">
                      <div className="flex flex-col items-center text-center">
                        <Zap className="size-8 text-studio-primary mb-2" />
                        <h3 className="text-lg font-medium mb-1">Premium Models</h3>
                        <p className="text-sm text-muted-foreground mb-4">
                          Get access to specialized models for specific tasks
                        </p>
                        <Button>Explore Premium</Button>
                      </div>
                    </CardContent>
                  </Card>
                  
                  <Card className="bg-studio-background border-studio-border">
                    <CardContent className="p-6">
                      <div className="flex flex-col items-center text-center">
                        <Server className="size-8 text-studio-primary mb-2" />
                        <h3 className="text-lg font-medium mb-1">Self-Hosting</h3>
                        <p className="text-sm text-muted-foreground mb-4">
                          Configure your own model deployments
                        </p>
                        <Button variant="outline">Learn More</Button>
                      </div>
                    </CardContent>
                  </Card>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
          
          <TabsContent value="benchmarks" className="flex-1 overflow-hidden p-4">
            <Card className="h-full bg-studio-background-accent border-studio-border">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle className="text-base font-medium">Model Performance</CardTitle>
                    <CardDescription>
                      Benchmark results across different tasks
                    </CardDescription>
                  </div>
                  <Button variant="outline" size="sm">
                    Run New Benchmark
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-6">
                  {models.filter(m => m.type === "completion").map((model, index) => (
                    <div key={index} className="space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="font-medium">{model.name}</span>
                        <span className="text-sm">{model.performance}%</span>
                      </div>
                      <Progress value={model.performance} className="h-2" />
                      <div className="grid grid-cols-4 gap-2 text-xs text-muted-foreground">
                        <div>Reasoning: {Math.round(model.performance * 0.9)}%</div>
                        <div>Creative: {Math.round(model.performance * 1.1)}%</div>
                        <div>Factual: {Math.round(model.performance * 0.95)}%</div>
                        <div>Speed: {Math.round(model.performance * 0.85)}%</div>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>
          
          <TabsContent value="cost" className="flex-1 overflow-hidden p-4">
            <Card className="bg-studio-background-accent border-studio-border mb-4">
              <CardHeader className="pb-2">
                <div className="flex items-center gap-2">
                  <DollarSign className="size-5 text-green-500" />
                  <CardTitle>Usage & Costs</CardTitle>
                </div>
                <CardDescription>
                  Track your model usage and associated costs
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-3 gap-4">
                  <Card className="bg-studio-background border-studio-border">
                    <CardContent className="p-4">
                      <div className="text-sm text-muted-foreground">Current Month Spend</div>
                      <div className="text-2xl font-bold mt-1">$42.38</div>
                      <div className="flex items-center text-xs text-green-500 mt-1">
                        <span>Under budget</span>
                      </div>
                    </CardContent>
                  </Card>
                  
                  <Card className="bg-studio-background border-studio-border">
                    <CardContent className="p-4">
                      <div className="text-sm text-muted-foreground">Token Usage</div>
                      <div className="text-2xl font-bold mt-1">1.2M</div>
                      <div className="flex items-center text-xs text-muted-foreground mt-1">
                        <span>Last 30 days</span>
                      </div>
                    </CardContent>
                  </Card>
                  
                  <Card className="bg-studio-background border-studio-border">
                    <CardContent className="p-4">
                      <div className="text-sm text-muted-foreground">Avg Cost per Request</div>
                      <div className="text-2xl font-bold mt-1">$0.021</div>
                      <div className="flex items-center text-xs text-muted-foreground mt-1">
                        <span>All models</span>
                      </div>
                    </CardContent>
                  </Card>
                </div>
                
                <div className="mt-6">
                  <div className="flex items-center justify-between mb-2">
                    <h4 className="font-medium">Cost Distribution</h4>
                    <div className="text-xs text-muted-foreground">Last 30 days</div>
                  </div>
                  <div className="h-40 flex items-end gap-1">
                    {/* Mock bar chart */}
                    {Array.from({ length: 10 }).map((_, i) => (
                      <div key={i} className="flex-1 flex flex-col items-center">
                        <div 
                          className="w-full bg-studio-primary rounded-sm" 
                          style={{ height: `${20 + Math.random() * 80}px` }}
                        ></div>
                        <div className="text-xs mt-1">{i + 1}</div>
                      </div>
                    ))}
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </motion.div>
  );
}
