import React, { useState } from "react";
import { motion } from "framer-motion";
import { PanelId } from "@/contexts/WorkspaceContext";
import { 
  Database, 
  BarChart, 
  Coins, 
  ExternalLink, 
  FileText,
  Download,
  Calendar,
  RefreshCw
} from "lucide-react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectTrigger,
  SelectValue
} from "@/components/ui/select";
import {
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent
} from "@/components/ui/chart";
import {
  LineChart,
  Line,
  BarChart as RechartsBarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  AreaChart,
  Area
} from "recharts";
import { ScrollArea } from "@/components/ui/scroll-area";

// Sample data for memory usage over time
const memoryUsageData = [
  { time: "00:00", usage: 128 },
  { time: "04:00", usage: 256 },
  { time: "08:00", usage: 512 },
  { time: "12:00", usage: 384 },
  { time: "16:00", usage: 640 },
  { time: "20:00", usage: 320 },
  { time: "24:00", usage: 192 }
];

// Sample data for token usage per model
const tokenUsageData = [
  { model: "GPT-3.5", prompt: 45, completion: 28 },
  { model: "GPT-4", prompt: 76, completion: 52 },
  { model: "Claude", prompt: 58, completion: 43 },
  { model: "Mistral", prompt: 33, completion: 17 }
];

// Sample data for API requests
const requestsData = [
  { day: "Mon", count: 24 },
  { day: "Tue", count: 18 },
  { day: "Wed", count: 32 },
  { day: "Thu", count: 27 },
  { day: "Fri", count: 42 },
  { day: "Sat", count: 15 },
  { day: "Sun", count: 12 }
];

interface StoragePanelProps {
  id: PanelId;
}

export default function StoragePanel({ id }: StoragePanelProps) {
  const [timeRange, setTimeRange] = useState<string>("day");
  
  const openLogViewer = () => {
    console.log("Opening log viewer...");
    // This would open a log viewer, e.g., in a modal
  };

  const refreshData = () => {
    console.log("Refreshing data...");
    // This would refresh the data from the API
  };

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
          <div className="size-8 rounded-md bg-studio-secondary/10 flex items-center justify-center">
            <Database className="size-4 text-studio-secondary" />
          </div>
          <h2 className="text-xl font-bold">Storage</h2>
        </div>
        <div className="flex items-center gap-2">
          <Select defaultValue={timeRange} onValueChange={setTimeRange}>
            <SelectTrigger className="w-[140px] h-8">
              <SelectValue placeholder="Select Range" />
            </SelectTrigger>
            <SelectContent>
              <SelectGroup>
                <SelectItem value="day">Today</SelectItem>
                <SelectItem value="week">This Week</SelectItem>
                <SelectItem value="month">This Month</SelectItem>
              </SelectGroup>
            </SelectContent>
          </Select>
          <Button variant="ghost" size="sm" onClick={refreshData} className="h-8 w-8 p-0">
            <RefreshCw className="size-4" />
          </Button>
          <Button variant="outline" size="sm" onClick={openLogViewer} className="h-8">
            <FileText className="size-4 mr-1" />
            View Logs
          </Button>
        </div>
      </div>
      
      {/* Panel Body with ScrollArea */}
      <ScrollArea className="flex-1" viewportClassName="p-4">
        <div className="space-y-6">
          <div className="flex items-center justify-between mb-1">
            <h3 className="text-lg font-medium">Resource Overview</h3>
            <div className="flex items-center text-xs text-muted-foreground">
              <Calendar className="size-3.5 mr-1" />
              <span>Last updated: Today at 15:45</span>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {/* Memory Usage Card */}
            <Card className="bg-studio-background-accent border-studio-border">
              <CardHeader className="pb-2">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-sm font-medium">RAM Usage</CardTitle>
                  <div className="size-6 rounded bg-studio-accent/10 flex items-center justify-center">
                    <BarChart className="size-3.5 text-studio-accent" />
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold mb-1">512 MB</div>
                <div className="flex items-center text-xs text-studio-success">
                  <span>64% of allocated memory</span>
                </div>
                <div className="mt-2 h-1.5 w-full rounded-full bg-studio-background">
                  <div className="h-full w-[64%] rounded-full bg-studio-accent"></div>
                </div>
              </CardContent>
            </Card>
            
            {/* Token Usage Card */}
            <Card className="bg-studio-background-accent border-studio-border">
              <CardHeader className="pb-2">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-sm font-medium">Token Usage</CardTitle>
                  <div className="size-6 rounded bg-studio-primary/10 flex items-center justify-center">
                    <Coins className="size-3.5 text-studio-primary" />
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold mb-1">5,436</div>
                <div className="flex items-center text-xs text-studio-info">
                  <span>Today's total consumption</span>
                </div>
                <div className="mt-2 flex justify-between text-xs text-muted-foreground">
                  <span>Prompt: 3,219</span>
                  <span>Completion: 2,217</span>
                </div>
              </CardContent>
            </Card>
            
            {/* API Requests Card */}
            <Card className="bg-studio-background-accent border-studio-border">
              <CardHeader className="pb-2">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-sm font-medium">API Requests</CardTitle>
                  <div className="size-6 rounded bg-studio-secondary/10 flex items-center justify-center">
                    <ExternalLink className="size-3.5 text-studio-secondary" />
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold mb-1">170</div>
                <div className="flex items-center text-xs text-studio-info">
                  <span>This week's total</span>
                </div>
                <div className="mt-2 flex justify-between text-xs text-muted-foreground">
                  <span>Success: 168</span>
                  <span>Failed: 2</span>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Memory Usage Graph with improved sizing */}
          <Card className="bg-studio-background-accent border-studio-border mb-6">
            <CardHeader>
              <CardTitle className="text-base font-medium">Memory Usage Over Time</CardTitle>
              <CardDescription>Last 24 hours memory consumption</CardDescription>
            </CardHeader>
            <CardContent className="pt-0">
              <div className="w-full h-60 min-h-60 max-h-[35vh]">
                <ChartContainer config={{
                  usage: { color: "#8B5CF6" }, // Vivid Purple
                }}>
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={memoryUsageData} margin={{ top: 10, right: 30, left: 0, bottom: 20 }}>
                      <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="var(--studio-border)" />
                      <XAxis dataKey="time" stroke="var(--muted-foreground)" />
                      <YAxis stroke="var(--muted-foreground)" />
                      <ChartTooltip content={<ChartTooltipContent />} />
                      <Legend wrapperStyle={{ paddingTop: 10 }} />
                      <Area 
                        type="monotone" 
                        dataKey="usage" 
                        name="Memory Usage (MB)"
                        stroke="#8B5CF6"
                        fill="#8B5CF6"
                        fillOpacity={0.2}
                      />
                    </AreaChart>
                  </ResponsiveContainer>
                </ChartContainer>
              </div>
            </CardContent>
          </Card>

          {/* Token Usage Graph with improved sizing */}
          <Card className="bg-studio-background-accent border-studio-border mb-6">
            <CardHeader>
              <CardTitle className="text-base font-medium">Token Usage by Model</CardTitle>
              <CardDescription>Breakdown of token usage per model</CardDescription>
            </CardHeader>
            <CardContent className="pt-0">
              <div className="w-full h-60 min-h-60 max-h-[35vh]">
                <ChartContainer config={{
                  prompt: { color: "#9b87f5" }, // Primary Purple
                  completion: { color: "#7E69AB" }, // Secondary Purple
                }}>
                  <ResponsiveContainer width="100%" height="100%">
                    <RechartsBarChart data={tokenUsageData} margin={{ top: 10, right: 30, left: 0, bottom: 20 }}>
                      <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="var(--studio-border)" />
                      <XAxis dataKey="model" stroke="var(--muted-foreground)" />
                      <YAxis stroke="var(--muted-foreground)" />
                      <ChartTooltip content={<ChartTooltipContent />} />
                      <Legend wrapperStyle={{ paddingTop: 10 }} />
                      <Bar dataKey="prompt" fill="#9b87f5" radius={[4, 4, 0, 0]} name="Prompt Tokens" />
                      <Bar dataKey="completion" fill="#7E69AB" radius={[4, 4, 0, 0]} name="Completion Tokens" />
                    </RechartsBarChart>
                  </ResponsiveContainer>
                </ChartContainer>
              </div>
            </CardContent>
          </Card>

          {/* API Requests Graph with improved sizing */}
          <Card className="bg-studio-background-accent border-studio-border mb-6">
            <CardHeader>
              <div className="flex justify-between items-center">
                <div>
                  <CardTitle className="text-base font-medium">API Requests per Day</CardTitle>
                  <CardDescription>Daily API call frequency</CardDescription>
                </div>
                <Button variant="outline" size="sm" className="h-8">
                  <Download className="size-4 mr-1" />
                  Export Data
                </Button>
              </div>
            </CardHeader>
            <CardContent className="pt-0">
              <div className="w-full h-60 min-h-60 max-h-[35vh]">
                <ChartContainer config={{
                  count: { color: "#6E59A5" }, // Tertiary Purple
                }}>
                  <ResponsiveContainer width="100%" height="100%">
                    <RechartsBarChart data={requestsData} margin={{ top: 10, right: 30, left: 0, bottom: 20 }}>
                      <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="var(--studio-border)" />
                      <XAxis dataKey="day" stroke="var(--muted-foreground)" />
                      <YAxis stroke="var(--muted-foreground)" />
                      <ChartTooltip content={<ChartTooltipContent />} />
                      <Legend wrapperStyle={{ paddingTop: 10 }} />
                      <Bar dataKey="count" fill="#6E59A5" radius={[4, 4, 0, 0]} name="API Calls" />
                    </RechartsBarChart>
                  </ResponsiveContainer>
                </ChartContainer>
              </div>
            </CardContent>
          </Card>

          {/* Share Section */}
          <Card className="bg-studio-background-accent border-studio-border">
            <CardHeader>
              <CardTitle className="text-base font-medium">Share Your Insights</CardTitle>
              <CardDescription>Export analytics or share with your team</CardDescription>
            </CardHeader>
            <CardContent className="pt-0">
              <div className="flex flex-wrap gap-3">
                <Button variant="outline" size="sm" className="bg-[#1DA1F2]/10 hover:bg-[#1DA1F2]/20 text-[#1DA1F2]">
                  Twitter
                </Button>
                <Button variant="outline" size="sm" className="bg-[#0077B5]/10 hover:bg-[#0077B5]/20 text-[#0077B5]">
                  LinkedIn
                </Button>
                <Button variant="outline" size="sm" className="bg-[#4267B2]/10 hover:bg-[#4267B2]/20 text-[#4267B2]">
                  Facebook
                </Button>
                <Button variant="outline" size="sm" className="bg-studio-primary/10 hover:bg-studio-primary/20 text-studio-primary">
                  Copy Link
                </Button>
                <Button variant="outline" size="sm" className="ml-auto">
                  <Download className="size-4 mr-1" />
                  PDF Report
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      </ScrollArea>
    </motion.div>
  );
}
