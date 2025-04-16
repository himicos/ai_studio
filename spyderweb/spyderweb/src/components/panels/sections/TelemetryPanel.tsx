
import React, { useState } from "react";
import { motion } from "framer-motion";
import { PanelId } from "@/contexts/WorkspaceContext";
import { Activity, Clock, Zap, BarChart2, TrendingUp, X } from "lucide-react";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectGroup, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";

interface TelemetryPanelProps {
  id: PanelId;
}

export default function TelemetryPanel({ id }: TelemetryPanelProps) {
  const [activeTab, setActiveTab] = useState("spend");
  
  // Mock data for visualization
  const timeSpentData = [
    { day: "Mon", hours: 1.5 },
    { day: "Tue", hours: 2.3 },
    { day: "Wed", hours: 1.2 },
    { day: "Thu", hours: 3.4 },
    { day: "Fri", hours: 2.8 },
    { day: "Sat", hours: 0.5 },
    { day: "Sun", hours: 0.2 },
  ];
  
  // Mock agent data
  const agents = [
    { name: "Research Assistant", usage: 42, performance: 87, timesSaved: 12.5 },
    { name: "Content Analyzer", usage: 28, performance: 92, timesSaved: 8.3 },
    { name: "Data Processor", usage: 36, performance: 78, timesSaved: 15.2 },
    { name: "Prompt Generator", usage: 19, performance: 83, timesSaved: 5.7 },
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
          <div className="size-8 rounded-md bg-green-500/10 flex items-center justify-center">
            <Activity className="size-4 text-green-500" />
          </div>
          <h2 className="text-xl font-bold">Telemetry</h2>
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
            <TabsList className="grid w-full grid-cols-4">
              <TabsTrigger value="spend">Token Spend</TabsTrigger>
              <TabsTrigger value="time">Time Saved</TabsTrigger>
              <TabsTrigger value="performance">Agent Performance</TabsTrigger>
              <TabsTrigger value="improve">Auto-Improve</TabsTrigger>
            </TabsList>
          </div>

          <TabsContent value="spend" className="flex-1 overflow-hidden p-4">
            <div className="flex mb-4 items-center justify-between">
              <div>
                <h3 className="text-lg font-medium">Token Usage Analytics</h3>
                <p className="text-sm text-muted-foreground">Track your token consumption over time</p>
              </div>
              <Select defaultValue="30days">
                <SelectTrigger className="w-[180px]">
                  <SelectValue placeholder="Time Period" />
                </SelectTrigger>
                <SelectContent>
                  <SelectGroup>
                    <SelectItem value="7days">Last 7 Days</SelectItem>
                    <SelectItem value="30days">Last 30 Days</SelectItem>
                    <SelectItem value="90days">Last 90 Days</SelectItem>
                    <SelectItem value="year">Last Year</SelectItem>
                  </SelectGroup>
                </SelectContent>
              </Select>
            </div>
            
            <div className="grid grid-cols-3 gap-4 mb-4">
              <Card className="bg-studio-background-accent border-studio-border">
                <CardContent className="p-4">
                  <div className="text-sm text-muted-foreground">Total Tokens Used</div>
                  <div className="text-2xl font-bold mt-1">1.28M</div>
                  <div className="flex items-center text-xs text-green-500 mt-1">
                    <TrendingUp className="size-3 mr-1" />
                    <span>12% increase</span>
                  </div>
                </CardContent>
              </Card>
              
              <Card className="bg-studio-background-accent border-studio-border">
                <CardContent className="p-4">
                  <div className="text-sm text-muted-foreground">Estimated Cost</div>
                  <div className="text-2xl font-bold mt-1">$34.56</div>
                  <div className="flex items-center text-xs text-muted-foreground mt-1">
                    <span>Last 30 days</span>
                  </div>
                </CardContent>
              </Card>
              
              <Card className="bg-studio-background-accent border-studio-border">
                <CardContent className="p-4">
                  <div className="text-sm text-muted-foreground">Cost per Task</div>
                  <div className="text-2xl font-bold mt-1">$0.057</div>
                  <div className="flex items-center text-xs text-green-500 mt-1">
                    <TrendingUp className="size-3 mr-1" />
                    <span>8% more efficient</span>
                  </div>
                </CardContent>
              </Card>
            </div>
            
            <Card className="bg-studio-background-accent border-studio-border">
              <CardHeader className="pb-2">
                <CardTitle className="text-base font-medium">Token Usage By Model</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="h-60">
                  <div className="h-full flex items-end gap-4">
                    <div className="flex-1 flex flex-col items-center">
                      <div className="w-full bg-blue-500 rounded-t-md" style={{ height: '60%' }}></div>
                      <div className="mt-2 text-sm">GPT-4</div>
                      <div className="text-xs text-muted-foreground">768K</div>
                    </div>
                    <div className="flex-1 flex flex-col items-center">
                      <div className="w-full bg-purple-500 rounded-t-md" style={{ height: '35%' }}></div>
                      <div className="mt-2 text-sm">Claude 3</div>
                      <div className="text-xs text-muted-foreground">448K</div>
                    </div>
                    <div className="flex-1 flex flex-col items-center">
                      <div className="w-full bg-green-500 rounded-t-md" style={{ height: '20%' }}></div>
                      <div className="mt-2 text-sm">Embeddings</div>
                      <div className="text-xs text-muted-foreground">256K</div>
                    </div>
                    <div className="flex-1 flex flex-col items-center">
                      <div className="w-full bg-yellow-500 rounded-t-md" style={{ height: '5%' }}></div>
                      <div className="mt-2 text-sm">Other</div>
                      <div className="text-xs text-muted-foreground">64K</div>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
          
          <TabsContent value="time" className="flex-1 overflow-hidden p-4">
            <div className="flex mb-4 items-center justify-between">
              <div>
                <h3 className="text-lg font-medium">Time Saved Analytics</h3>
                <p className="text-sm text-muted-foreground">Measure productivity gains from AI automation</p>
              </div>
              <Select defaultValue="week">
                <SelectTrigger className="w-[180px]">
                  <SelectValue placeholder="Time Period" />
                </SelectTrigger>
                <SelectContent>
                  <SelectGroup>
                    <SelectItem value="week">This Week</SelectItem>
                    <SelectItem value="month">This Month</SelectItem>
                    <SelectItem value="quarter">This Quarter</SelectItem>
                    <SelectItem value="year">This Year</SelectItem>
                  </SelectGroup>
                </SelectContent>
              </Select>
            </div>
            
            <div className="grid grid-cols-2 gap-4 mb-4">
              <Card className="bg-studio-background-accent border-studio-border">
                <CardContent className="p-4">
                  <div className="text-sm text-muted-foreground">Total Time Saved</div>
                  <div className="text-2xl font-bold mt-1">12.4 hours</div>
                  <div className="flex items-center text-xs text-green-500 mt-1">
                    <TrendingUp className="size-3 mr-1" />
                    <span>18% increase from last week</span>
                  </div>
                </CardContent>
              </Card>
              
              <Card className="bg-studio-background-accent border-studio-border">
                <CardContent className="p-4">
                  <div className="text-sm text-muted-foreground">Estimated Value</div>
                  <div className="text-2xl font-bold mt-1">$620.00</div>
                  <div className="flex items-center text-xs text-muted-foreground mt-1">
                    <span>Based on avg. hourly rate of $50</span>
                  </div>
                </CardContent>
              </Card>
            </div>
            
            <Card className="bg-studio-background-accent border-studio-border mb-4">
              <CardHeader className="pb-2">
                <CardTitle className="text-base font-medium">Time Saved This Week</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="h-40">
                  <div className="h-full flex items-end gap-2">
                    {timeSpentData.map((item, index) => (
                      <div key={index} className="flex-1 flex flex-col items-center">
                        <div 
                          className="w-full bg-studio-primary rounded-t-sm" 
                          style={{ height: `${item.hours * 30}px` }}
                        ></div>
                        <div className="mt-2 text-sm">{item.day}</div>
                        <div className="text-xs text-muted-foreground">{item.hours}h</div>
                      </div>
                    ))}
                  </div>
                </div>
              </CardContent>
            </Card>
            
            <Card className="bg-studio-background-accent border-studio-border">
              <CardHeader className="pb-2">
                <CardTitle className="text-base font-medium">Tasks Automated</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  <div className="flex justify-between items-center">
                    <span className="text-sm">Document Summarization</span>
                    <Badge>4.5 hours saved</Badge>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm">Data Analysis</span>
                    <Badge>3.2 hours saved</Badge>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm">Email Drafting</span>
                    <Badge>2.8 hours saved</Badge>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm">Research</span>
                    <Badge>1.9 hours saved</Badge>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
          
          <TabsContent value="performance" className="flex-1 overflow-hidden p-4">
            <Card className="bg-studio-background-accent border-studio-border mb-4">
              <CardHeader className="pb-2">
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle className="text-base font-medium">Agent Performance</CardTitle>
                    <CardDescription>
                      Evaluate and optimize your agent performance
                    </CardDescription>
                  </div>
                  <Button variant="outline" size="sm">
                    Export Data
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="grid grid-cols-5 gap-4 text-sm font-medium text-muted-foreground border-b border-studio-border pb-2">
                    <div>Agent Name</div>
                    <div>Usage</div>
                    <div>Performance</div>
                    <div>Time Saved</div>
                    <div></div>
                  </div>
                  
                  {agents.map((agent, index) => (
                    <div key={index} className="grid grid-cols-5 gap-4 items-center">
                      <div className="font-medium">{agent.name}</div>
                      <div>{agent.usage} tasks</div>
                      <div className="flex items-center gap-2">
                        <div className="h-2 w-16 bg-studio-background rounded-full">
                          <div 
                            className="h-full bg-green-500 rounded-full" 
                            style={{ width: `${agent.performance}%` }}
                          ></div>
                        </div>
                        <span className="text-sm">{agent.performance}%</span>
                      </div>
                      <div>{agent.timesSaved.toFixed(1)} hrs</div>
                      <div className="flex justify-end">
                        <Button variant="ghost" size="sm">Details</Button>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
            
            <div className="grid grid-cols-2 gap-4">
              <Card className="bg-studio-background-accent border-studio-border">
                <CardHeader className="pb-2">
                  <CardTitle className="text-base font-medium">Success Rate</CardTitle>
                  <CardDescription>
                    Task completion success metrics
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="flex flex-col items-center justify-center p-6">
                    <div className="relative size-32 mb-4">
                      <div className="absolute inset-0 border-8 border-studio-primary/20 rounded-full"></div>
                      <div 
                        className="absolute inset-0 border-8 border-studio-primary rounded-full"
                        style={{ clipPath: 'polygon(0 0, 100% 0, 100% 100%, 0% 100%)', transform: 'rotate(65deg)' }}
                      ></div>
                      <div className="absolute inset-0 flex items-center justify-center">
                        <div className="text-center">
                          <span className="text-3xl font-bold">82%</span>
                          <p className="text-xs text-muted-foreground">Success Rate</p>
                        </div>
                      </div>
                    </div>
                    <div className="space-y-2">
                      <div className="flex items-center gap-2">
                        <div className="size-3 bg-studio-primary rounded-full"></div>
                        <span className="text-sm">Successful: 82%</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <div className="size-3 bg-studio-primary/20 rounded-full"></div>
                        <span className="text-sm">Needs Improvement: 18%</span>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
              
              <Card className="bg-studio-background-accent border-studio-border">
                <CardHeader className="pb-2">
                  <CardTitle className="text-base font-medium">Optimization Opportunities</CardTitle>
                  <CardDescription>
                    Areas for agent improvement
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    <Card className="bg-studio-background border-studio-border">
                      <CardContent className="p-3 flex justify-between items-center">
                        <div>
                          <h4 className="text-sm font-medium">Prompt Optimization</h4>
                          <p className="text-xs text-muted-foreground">Improve prompting for better results</p>
                        </div>
                        <Button size="sm">Optimize</Button>
                      </CardContent>
                    </Card>
                    
                    <Card className="bg-studio-background border-studio-border">
                      <CardContent className="p-3 flex justify-between items-center">
                        <div>
                          <h4 className="text-sm font-medium">Model Selection</h4>
                          <p className="text-xs text-muted-foreground">Use more appropriate models</p>
                        </div>
                        <Button size="sm">Review</Button>
                      </CardContent>
                    </Card>
                    
                    <Card className="bg-studio-background border-studio-border">
                      <CardContent className="p-3 flex justify-between items-center">
                        <div>
                          <h4 className="text-sm font-medium">Knowledge Integration</h4>
                          <p className="text-xs text-muted-foreground">Add context from Memory Vault</p>
                        </div>
                        <Button size="sm">Integrate</Button>
                      </CardContent>
                    </Card>
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>
          
          <TabsContent value="improve" className="flex-1 overflow-hidden p-4">
            <Card className="h-full bg-studio-background-accent border-studio-border">
              <CardHeader>
                <CardTitle>Auto-Improve Candidates</CardTitle>
                <CardDescription>
                  Automatically optimize your agents and workflows
                </CardDescription>
              </CardHeader>
              <CardContent className="flex items-center justify-center h-[70%]">
                <div className="text-center max-w-md">
                  <div className="size-16 rounded-full bg-studio-primary/10 mx-auto flex items-center justify-center mb-4">
                    <Zap className="size-8 text-studio-primary" />
                  </div>
                  <h3 className="text-lg font-medium mb-2">Auto-Improve System</h3>
                  <p className="text-muted-foreground mb-6">
                    This premium feature uses AI to analyze your usage patterns and automatically
                    suggest optimizations for your agents and workflows
                  </p>
                  <Button>
                    Unlock Auto-Improve
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
