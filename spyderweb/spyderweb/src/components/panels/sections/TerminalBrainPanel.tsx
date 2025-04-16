import React, { useState } from "react";
import { motion } from "framer-motion";
import { PanelId } from "@/contexts/WorkspaceContext";
import { Terminal, Play, AlertTriangle, X } from "lucide-react";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";

interface TerminalBrainPanelProps {
  id: PanelId;
}

export default function TerminalBrainPanel({ id }: TerminalBrainPanelProps) {
  const [activeTab, setActiveTab] = useState("logs");
  const [command, setCommand] = useState("");
  
  const logs = [
    { level: "info", timestamp: "2025-04-12T10:15:32", message: "System initialized" },
    { level: "info", timestamp: "2025-04-12T10:15:35", message: "Agent runtime loaded successfully" },
    { level: "debug", timestamp: "2025-04-12T10:15:40", message: "Connecting to vector database..." },
    { level: "info", timestamp: "2025-04-12T10:15:42", message: "Vector database connected" },
    { level: "warning", timestamp: "2025-04-12T10:16:01", message: "Memory limit at 75% capacity" },
    { level: "error", timestamp: "2025-04-12T10:16:30", message: "Failed to connect to external API: rate limit exceeded" },
    { level: "info", timestamp: "2025-04-12T10:17:12", message: "Task scheduler initialized" },
    { level: "debug", timestamp: "2025-04-12T10:17:15", message: "Loading agent configurations..." },
    { level: "info", timestamp: "2025-04-12T10:17:20", message: "Agent configurations loaded" },
    { level: "info", timestamp: "2025-04-12T10:18:05", message: "User authentication successful" },
    { level: "debug", timestamp: "2025-04-12T10:18:10", message: "Session token generated" },
    { level: "info", timestamp: "2025-04-12T10:18:15", message: "User session established" },
    { level: "warning", timestamp: "2025-04-12T10:19:30", message: "API response latency exceeds threshold" },
  ];
  
  const getBadgeVariant = (level: string) => {
    switch (level) {
      case "error": return "destructive";
      case "warning": return "outline";
      case "info": return "default";
      case "debug": return "secondary";
      default: return "secondary";
    }
  };
  
  const handleRunCommand = () => {
    if (!command.trim()) return;
    console.log("Running command:", command);
    // In a real implementation, this would process the command
    setCommand("");
  };
  
  return (
    <motion.div 
      className="flex flex-col h-full panel"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.3 }}
    >
      <div className="flex items-center justify-between p-4 border-b border-studio-border">
        <div className="flex items-center gap-2">
          <div className="size-8 rounded-md bg-green-500/10 flex items-center justify-center">
            <Terminal className="size-4 text-green-500" />
          </div>
          <h2 className="text-xl font-bold">Terminal Brain</h2>
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
      
      <div className="flex-1 overflow-hidden">
        <Tabs value={activeTab} onValueChange={setActiveTab} className="h-full flex flex-col">
          <div className="px-4 pt-4">
            <TabsList className="grid w-full grid-cols-3">
              <TabsTrigger value="logs">Agent Logs</TabsTrigger>
              <TabsTrigger value="execute">Execute Task</TabsTrigger>
              <TabsTrigger value="chaos">Chaos Terminal</TabsTrigger>
            </TabsList>
          </div>

          <TabsContent value="logs" className="flex-1 overflow-hidden p-4">
            <Card className="h-full bg-studio-background-accent border-studio-border">
              <CardHeader className="pb-2">
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle className="text-base font-medium">System Logs</CardTitle>
                    <CardDescription>
                      Real-time agent and system activity
                    </CardDescription>
                  </div>
                  <div className="flex gap-2">
                    <Button variant="outline" size="sm">Clear</Button>
                    <Button variant="outline" size="sm">Filter</Button>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="h-[calc(100%-80px)] p-0">
                <ScrollArea className="h-full">
                  <div className="font-mono text-sm p-4 space-y-1">
                    {logs.map((log, index) => (
                      <div key={index} className="flex items-start gap-2 py-1">
                        <Badge variant={getBadgeVariant(log.level)} className="uppercase text-xs">
                          {log.level}
                        </Badge>
                        <span className="text-xs text-muted-foreground">
                          {new Date(log.timestamp).toLocaleTimeString()}
                        </span>
                        <span className="flex-1">{log.message}</span>
                      </div>
                    ))}
                  </div>
                </ScrollArea>
              </CardContent>
            </Card>
          </TabsContent>
          
          <TabsContent value="execute" className="flex-1 overflow-hidden p-4 flex flex-col">
            <Card className="bg-studio-background-accent border-studio-border mb-4">
              <CardHeader className="pb-2">
                <CardTitle className="text-base font-medium">Execute Command</CardTitle>
                <CardDescription>
                  Run commands directly in the agent runtime environment
                </CardDescription>
              </CardHeader>
              <CardContent>
                <Textarea 
                  className="font-mono bg-studio-background min-h-24"
                  placeholder="Enter command or task description..."
                  value={command}
                  onChange={(e) => setCommand(e.target.value)}
                />
                <div className="flex justify-end mt-2">
                  <Button onClick={handleRunCommand}>
                    <Play className="size-4 mr-2" />
                    Run
                  </Button>
                </div>
              </CardContent>
            </Card>
            
            <Card className="flex-1 bg-studio-background-accent border-studio-border">
              <CardHeader className="pb-2">
                <CardTitle className="text-base font-medium">Command Output</CardTitle>
              </CardHeader>
              <CardContent className="p-0">
                <div className="bg-studio-background font-mono text-sm p-4 h-[300px] overflow-auto">
                  <p className="text-muted-foreground">No output yet. Run a command to see results.</p>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
          
          <TabsContent value="chaos" className="flex-1 overflow-hidden p-4">
            <Card className="h-full bg-studio-background-accent border-studio-border">
              <CardHeader>
                <div className="flex items-center gap-2">
                  <AlertTriangle className="size-5 text-yellow-500" />
                  <CardTitle>Chaos Injection Terminal</CardTitle>
                </div>
                <CardDescription>
                  Advanced mode for system testing and resilience
                </CardDescription>
              </CardHeader>
              <CardContent className="flex items-center justify-center h-[70%]">
                <div className="text-center">
                  <div className="size-16 rounded-full bg-yellow-500/20 mx-auto flex items-center justify-center mb-4">
                    <AlertTriangle className="size-8 text-yellow-500" />
                  </div>
                  <h3 className="text-lg font-medium mb-2">Advanced Feature</h3>
                  <p className="text-muted-foreground mb-6 max-w-md">
                    The Chaos Terminal allows targeted disruption of system components
                    for resilience testing. This is an advanced feature that requires caution.
                  </p>
                  <Button variant="outline" className="border-yellow-500/50 text-yellow-500">
                    Unlock Chaos Terminal
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
