import React, { useState } from "react";
import { motion } from "framer-motion";
import { PanelId } from "@/contexts/WorkspaceContext";
import { 
  BarChart4, 
  TrendingUp, 
  Users, 
  Activity,
  Share2,
  Download,
  Calendar,
  Filter
} from "lucide-react";
import { 
  Card, 
  CardContent, 
  CardHeader, 
  CardTitle, 
  CardDescription 
} from "@/components/ui/card";
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectTrigger,
  SelectValue
} from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { 
  ChartContainer, 
  ChartTooltip, 
  ChartTooltipContent 
} from "@/components/ui/chart";
import { 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  ResponsiveContainer,
  Legend,
  LineChart,
  Line,
  Tooltip,
  PieChart,
  Pie,
  Cell
} from "recharts";
import { ScrollArea } from "@/components/ui/scroll-area";

interface AnalyticsPanelProps {
  id: PanelId;
}

const weeklyEngagementData = [
  { name: "Mon", views: 420, engagement: 240 },
  { name: "Tue", views: 380, engagement: 180 },
  { name: "Wed", views: 650, engagement: 320 },
  { name: "Thu", views: 540, engagement: 280 },
  { name: "Fri", views: 760, engagement: 360 },
  { name: "Sat", views: 480, engagement: 220 },
  { name: "Sun", views: 380, engagement: 190 }
];

const socialChannelsData = [
  { name: "Twitter", value: 38 },
  { name: "LinkedIn", value: 24 },
  { name: "Facebook", value: 18 },
  { name: "Instagram", value: 12 },
  { name: "Others", value: 8 }
];

const weeklyVisitorsData = [
  { day: "Mon", visitors: 1240 },
  { day: "Tue", visitors: 1380 },
  { day: "Wed", visitors: 1520 },
  { day: "Thu", visitors: 1640 },
  { day: "Fri", visitors: 1820 },
  { day: "Sat", visitors: 1420 },
  { day: "Sun", visitors: 1380 }
];

const SOCIAL_COLORS = ["#6E59A5", "#7E69AB", "#9b87f5", "#D6BCFA", "#E9D8FD"];

export default function AnalyticsPanel({ id }: AnalyticsPanelProps) {
  const [timeRange, setTimeRange] = useState<string>("week");
  
  return (
    <motion.div 
      className="flex flex-col h-full panel"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.3 }}
    >
      <div className="flex items-center justify-between p-4 border-b border-studio-border">
        <div className="flex items-center gap-2">
          <div className="size-8 rounded-md bg-studio-secondary/10 flex items-center justify-center">
            <BarChart4 className="size-4 text-studio-secondary" />
          </div>
          <h2 className="text-xl font-bold">Analytics Dashboard</h2>
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
                <SelectItem value="year">This Year</SelectItem>
              </SelectGroup>
            </SelectContent>
          </Select>
          <Button variant="outline" size="sm" className="h-8 px-2">
            <Download className="size-4 mr-1" />
            Export
          </Button>
        </div>
      </div>
      
      <ScrollArea className="flex-1" viewportClassName="p-4">
        <div className="space-y-6">
          <section>
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-lg font-medium">Key Insights</h3>
              <div className="flex items-center text-xs text-muted-foreground">
                <Calendar className="size-3.5 mr-1" />
                <span>Last updated: Today at 14:30</span>
              </div>
            </div>
            
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              <Card className="bg-studio-background-accent border-studio-border">
                <CardHeader className="pb-2">
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-sm font-medium">Total Views</CardTitle>
                    <div className="size-6 rounded bg-studio-primary/10 flex items-center justify-center">
                      <Activity className="size-3.5 text-studio-primary" />
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold mb-1">3,612</div>
                  <div className="flex items-center text-xs text-studio-success">
                    <TrendingUp className="size-3.5 mr-1" />
                    <span>+12.5% from last week</span>
                  </div>
                </CardContent>
              </Card>
              
              <Card className="bg-studio-background-accent border-studio-border">
                <CardHeader className="pb-2">
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-sm font-medium">Engagement Rate</CardTitle>
                    <div className="size-6 rounded bg-studio-secondary/10 flex items-center justify-center">
                      <Users className="size-3.5 text-studio-secondary" />
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold mb-1">48.2%</div>
                  <div className="flex items-center text-xs text-studio-success">
                    <TrendingUp className="size-3.5 mr-1" />
                    <span>+3.7% from last week</span>
                  </div>
                </CardContent>
              </Card>
              
              <Card className="bg-studio-background-accent border-studio-border">
                <CardHeader className="pb-2">
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-sm font-medium">Conversion Rate</CardTitle>
                    <div className="size-6 rounded bg-studio-accent/10 flex items-center justify-center">
                      <Share2 className="size-3.5 text-studio-accent" />
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold mb-1">5.7%</div>
                  <div className="flex items-center text-xs text-studio-success">
                    <TrendingUp className="size-3.5 mr-1" />
                    <span>+0.8% from last week</span>
                  </div>
                </CardContent>
              </Card>
            </div>
          </section>
          
          <section>
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-lg font-medium">Weekly Performance</h3>
              <Button variant="ghost" size="sm" className="h-8 px-2">
                <Filter className="size-3.5 mr-1" />
                Filter
              </Button>
            </div>
            
            <Card className="bg-studio-background-accent border-studio-border">
              <CardHeader>
                <CardTitle className="text-base font-medium">Views & Engagement</CardTitle>
                <CardDescription>Daily performance metrics for the past week</CardDescription>
              </CardHeader>
              <CardContent className="pt-0">
                <div className="w-full h-60 min-h-60 max-h-[35vh]">
                  <ChartContainer config={{
                    views: { color: "#8B5CF6" }, // Vivid Purple
                    engagement: { color: "#9b87f5" }, // Primary Purple
                  }}>
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={weeklyEngagementData} margin={{ top: 10, right: 30, left: 0, bottom: 20 }}>
                        <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="var(--studio-border)" />
                        <XAxis dataKey="name" stroke="var(--muted-foreground)" />
                        <YAxis stroke="var(--muted-foreground)" />
                        <ChartTooltip content={<ChartTooltipContent />} />
                        <Legend wrapperStyle={{ paddingTop: 10 }} />
                        <Bar dataKey="views" fill="#8B5CF6" radius={[4, 4, 0, 0]} />
                        <Bar dataKey="engagement" fill="#9b87f5" radius={[4, 4, 0, 0]} />
                      </BarChart>
                    </ResponsiveContainer>
                  </ChartContainer>
                </div>
              </CardContent>
            </Card>
          </section>
          
          <section>
            <h3 className="text-lg font-medium mb-3">Audience Insights</h3>
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
              <Card className="bg-studio-background-accent border-studio-border lg:col-span-2">
                <CardHeader>
                  <CardTitle className="text-base font-medium">Social Traffic Distribution</CardTitle>
                  <CardDescription>Traffic sources by social platform</CardDescription>
                </CardHeader>
                <CardContent className="pt-0">
                  <div className="w-full h-60 min-h-60 max-h-[35vh]">
                    <ChartContainer config={{
                      Twitter: { color: "#6E59A5" }, // Tertiary Purple
                      LinkedIn: { color: "#7E69AB" }, // Secondary Purple
                      Facebook: { color: "#9b87f5" }, // Primary Purple
                      Instagram: { color: "#D6BCFA" }, // Light Purple
                      Others: { color: "#E9D8FD" },
                    }}>
                      <ResponsiveContainer width="100%" height="100%">
                        <PieChart margin={{ top: 0, right: 0, left: 0, bottom: 0 }}>
                          <Pie
                            data={socialChannelsData}
                            cx="50%"
                            cy="50%"
                            labelLine={false}
                            outerRadius={80}
                            fill="#8884d8"
                            dataKey="value"
                            label={({name, percent}) => `${name}: ${(percent * 100).toFixed(0)}%`}
                          >
                            {socialChannelsData.map((entry, index) => (
                              <Cell key={`cell-${index}`} fill={SOCIAL_COLORS[index % SOCIAL_COLORS.length]} />
                            ))}
                          </Pie>
                          <ChartTooltip content={<ChartTooltipContent />} />
                        </PieChart>
                      </ResponsiveContainer>
                    </ChartContainer>
                  </div>
                </CardContent>
              </Card>
              
              <Card className="bg-studio-background-accent border-studio-border">
                <CardHeader>
                  <CardTitle className="text-base font-medium">Top Content</CardTitle>
                  <CardDescription>Highest performing</CardDescription>
                </CardHeader>
                <CardContent className="pt-0">
                  <div className="space-y-3">
                    <div className="flex items-start">
                      <div className="size-7 rounded bg-studio-primary/10 flex items-center justify-center mr-3 mt-0.5">
                        <span className="text-xs font-semibold text-studio-primary">01</span>
                      </div>
                      <div>
                        <p className="text-sm font-medium">Introduction to AI Models</p>
                        <p className="text-xs text-muted-foreground">1.2k views • 86% engagement</p>
                      </div>
                    </div>
                    <div className="flex items-start">
                      <div className="size-7 rounded bg-studio-primary/10 flex items-center justify-center mr-3 mt-0.5">
                        <span className="text-xs font-semibold text-studio-primary">02</span>
                      </div>
                      <div>
                        <p className="text-sm font-medium">Prompt Engineering Guide</p>
                        <p className="text-xs text-muted-foreground">945 views • 72% engagement</p>
                      </div>
                    </div>
                    <div className="flex items-start">
                      <div className="size-7 rounded bg-studio-primary/10 flex items-center justify-center mr-3 mt-0.5">
                        <span className="text-xs font-semibold text-studio-primary">03</span>
                      </div>
                      <div>
                        <p className="text-sm font-medium">Advanced RAG Techniques</p>
                        <p className="text-xs text-muted-foreground">742 views • 68% engagement</p>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </section>
          
          <section>
            <h3 className="text-lg font-medium mb-3">Visitors Trend</h3>
            <Card className="bg-studio-background-accent border-studio-border">
              <CardHeader>
                <CardTitle className="text-base font-medium">Weekly Visitors</CardTitle>
                <CardDescription>Total unique visitors over time</CardDescription>
              </CardHeader>
              <CardContent className="pt-0">
                <div className="w-full h-60 min-h-60 max-h-[35vh]">
                  <ChartContainer config={{
                    visitors: { color: "#6E59A5" }, // Tertiary Purple
                  }}>
                    <ResponsiveContainer width="100%" height="100%">
                      <LineChart data={weeklyVisitorsData} margin={{ top: 10, right: 20, left: 0, bottom: 20 }}>
                        <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="var(--studio-border)" />
                        <XAxis dataKey="day" stroke="var(--muted-foreground)" />
                        <YAxis stroke="var(--muted-foreground)" />
                        <ChartTooltip content={<ChartTooltipContent />} />
                        <Legend wrapperStyle={{ paddingTop: 10 }} />
                        <Line
                          type="monotone"
                          dataKey="visitors"
                          stroke="#6E59A5"
                          strokeWidth={2}
                          dot={{ stroke: '#6E59A5', strokeWidth: 2, r: 4 }}
                          activeDot={{ stroke: '#6E59A5', strokeWidth: 2, r: 6 }}
                        />
                      </LineChart>
                    </ResponsiveContainer>
                  </ChartContainer>
                </div>
              </CardContent>
            </Card>
          </section>
        </div>
      </ScrollArea>
    </motion.div>
  );
}
