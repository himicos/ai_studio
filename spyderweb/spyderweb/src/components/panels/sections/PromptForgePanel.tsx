
import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { PanelId } from "@/contexts/WorkspaceContext";
import { FlaskConical, History, Copy, PlayCircle, ArrowRight, GitBranch, X, ChevronDown, ChevronUp } from "lucide-react";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Select, SelectContent, SelectGroup, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

interface PromptForgePanelProps {
  id: PanelId;
}

export default function PromptForgePanel({ id }: PromptForgePanelProps) {
  const [activeTab, setActiveTab] = useState("bump");
  const [prompt, setPrompt] = useState("Create a detailed marketing strategy for a new eco-friendly product targeting environmentally conscious consumers.");
  const [showHistory, setShowHistory] = useState(false);
  
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
            <FlaskConical className="size-4 text-studio-primary" />
          </div>
          <h2 className="text-xl font-bold">Prompt Forge</h2>
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
              <TabsTrigger value="bump">Prompt Bump Test</TabsTrigger>
              <TabsTrigger value="builder">Chain Builder</TabsTrigger>
              <TabsTrigger value="rerunner">Prompt Rerunner</TabsTrigger>
            </TabsList>
          </div>

          <TabsContent value="bump" className="flex-1 overflow-hidden p-4">
            <div className="grid grid-cols-2 gap-4 h-full">
              <div className="flex flex-col h-full">
                <Card className="bg-studio-background-accent border-studio-border mb-4">
                  <CardHeader className="pb-2">
                    <CardTitle className="text-base font-medium">Base Prompt</CardTitle>
                    <CardDescription>
                      Enter your original prompt
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <Textarea 
                      className="min-h-[150px]" 
                      placeholder="Enter your prompt..."
                      value={prompt}
                      onChange={(e) => setPrompt(e.target.value)}
                    />
                  </CardContent>
                </Card>
                
                <Card className="flex-1 bg-studio-background-accent border-studio-border">
                  <CardHeader className="pb-2">
                    <CardTitle className="text-base font-medium">Variation Parameters</CardTitle>
                    <CardDescription>
                      Configure how to improve your prompt
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <label className="text-sm font-medium block mb-1">Model</label>
                          <Select defaultValue="gpt4">
                            <SelectTrigger>
                              <SelectValue placeholder="Select Model" />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectGroup>
                                <SelectItem value="gpt4">GPT-4 Turbo</SelectItem>
                                <SelectItem value="claude">Claude 3 Opus</SelectItem>
                                <SelectItem value="gemini">Gemini Pro</SelectItem>
                              </SelectGroup>
                            </SelectContent>
                          </Select>
                        </div>
                        
                        <div>
                          <label className="text-sm font-medium block mb-1">Optimization Goal</label>
                          <Select defaultValue="clarity">
                            <SelectTrigger>
                              <SelectValue placeholder="Select Goal" />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectGroup>
                                <SelectItem value="clarity">Clarity</SelectItem>
                                <SelectItem value="creativity">Creativity</SelectItem>
                                <SelectItem value="specificity">Specificity</SelectItem>
                                <SelectItem value="brevity">Brevity</SelectItem>
                              </SelectGroup>
                            </SelectContent>
                          </Select>
                        </div>
                      </div>
                      
                      <div>
                        <label className="text-sm font-medium block mb-1">Bump Direction</label>
                        <Select defaultValue="enhance">
                          <SelectTrigger>
                            <SelectValue placeholder="Select Direction" />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectGroup>
                              <SelectItem value="enhance">Enhance & Elaborate</SelectItem>
                              <SelectItem value="refine">Refine & Focus</SelectItem>
                              <SelectItem value="simplify">Simplify</SelectItem>
                              <SelectItem value="expert">Expert-Level</SelectItem>
                            </SelectGroup>
                          </SelectContent>
                        </Select>
                      </div>
                      
                      <div className="pt-2">
                        <Button className="w-full">
                          <PlayCircle className="size-4 mr-2" />
                          Generate Variations
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>
              
              <Card className="h-full bg-studio-background-accent border-studio-border">
                <CardHeader className="pb-2">
                  <div className="flex items-center justify-between">
                    <div>
                      <CardTitle className="text-base font-medium">Generated Variations</CardTitle>
                      <CardDescription>
                        Compare different prompt variations
                      </CardDescription>
                    </div>
                    <Button 
                      variant="outline" 
                      size="sm" 
                      onClick={() => setShowHistory(!showHistory)}
                      className="flex items-center gap-1"
                    >
                      <History className="size-4" />
                      History
                      {showHistory ? <ChevronUp className="size-3" /> : <ChevronDown className="size-3" />}
                    </Button>
                  </div>
                </CardHeader>
                <CardContent className="p-0">
                  <AnimatePresence>
                    {showHistory && (
                      <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: "auto", opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        transition={{ duration: 0.2 }}
                        className="border-b border-studio-border"
                      >
                        <ScrollArea className="h-[150px]">
                          <div className="py-3 space-y-3 px-4">
                            <Card className="border border-studio-border bg-studio-background p-3">
                              <div className="flex items-center justify-between mb-2">
                                <span className="text-xs font-medium">Yesterday, 3:45 PM</span>
                                <Button variant="ghost" size="sm" className="h-6">
                                  <Copy className="size-3 mr-1" />
                                  Copy
                                </Button>
                              </div>
                              <p className="text-xs text-muted-foreground">Original prompt: Create a marketing strategy...</p>
                              <p className="text-sm mt-1">Create a targeted marketing strategy for a new eco-friendly product...</p>
                            </Card>
                            <Card className="border border-studio-border bg-studio-background p-3">
                              <div className="flex items-center justify-between mb-2">
                                <span className="text-xs font-medium">Yesterday, 2:12 PM</span>
                                <Button variant="ghost" size="sm" className="h-6">
                                  <Copy className="size-3 mr-1" />
                                  Copy
                                </Button>
                              </div>
                              <p className="text-xs text-muted-foreground">Original prompt: Design a social media...</p>
                              <p className="text-sm mt-1">Design a comprehensive social media campaign focusing on...</p>
                            </Card>
                          </div>
                        </ScrollArea>
                      </motion.div>
                    )}
                  </AnimatePresence>
                  
                  <ScrollArea className="h-[calc(100%-60px)]" viewportClassName="px-4 py-4">
                    <div className="space-y-4">
                      <Card className="border border-studio-border bg-studio-background p-4 hover:border-studio-primary/30 transition-colors duration-200">
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-sm font-medium">Variation 1 - Enhanced</span>
                          <Button variant="ghost" size="sm" className="hover:bg-studio-background-accent">
                            <Copy className="size-3.5 mr-1" />
                            Copy
                          </Button>
                        </div>
                        <p className="text-sm">
                          Develop a comprehensive, multi-channel marketing strategy for a new eco-friendly product 
                          targeting environmentally conscious consumers. Include detailed audience segmentation, 
                          competitive positioning, key messaging pillars, channel-specific tactics, and measurable KPIs 
                          that align with sustainability goals. Incorporate specific recommendations for leveraging 
                          the product's environmental credentials while avoiding greenwashing.
                        </p>
                      </Card>
                      
                      <Card className="border border-studio-border bg-studio-background p-4 hover:border-studio-primary/30 transition-colors duration-200">
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-sm font-medium">Variation 2 - Focused</span>
                          <Button variant="ghost" size="sm" className="hover:bg-studio-background-accent">
                            <Copy className="size-3.5 mr-1" />
                            Copy
                          </Button>
                        </div>
                        <p className="text-sm">
                          Create a targeted marketing strategy for a new eco-friendly product. Focus on:
                          1) Primary eco-conscious consumer segments
                          2) Three key differentiators from competitors
                          3) Sustainability messaging framework
                          4) Digital-first channel approach
                          5) Conversion metrics that track both sales and environmental impact
                        </p>
                      </Card>
                      
                      <Card className="border border-studio-border bg-studio-background p-4 hover:border-studio-primary/30 transition-colors duration-200">
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-sm font-medium">Variation 3 - Expert</span>
                          <Button variant="ghost" size="sm" className="hover:bg-studio-background-accent">
                            <Copy className="size-3.5 mr-1" />
                            Copy
                          </Button>
                        </div>
                        <p className="text-sm">
                          Craft a strategic marketing plan for a sustainable product launch targeting LOHAS 
                          (Lifestyles of Health and Sustainability) consumers. Detail psychographic profiling of 
                          primary and secondary segments, positioning strategy against greenwashed competitors, 
                          and implementation of the 5Ps of green marketing. Include B Corp certification leverage points, 
                          sustainability storytelling framework, eco-influencer partnership criteria, and carbon 
                          impact transparency metrics.
                        </p>
                      </Card>
                      
                      <Card className="border border-studio-border bg-studio-background p-4 hover:border-studio-primary/30 transition-colors duration-200">
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-sm font-medium">Variation 4 - Technical</span>
                          <Button variant="ghost" size="sm" className="hover:bg-studio-background-accent">
                            <Copy className="size-3.5 mr-1" />
                            Copy
                          </Button>
                        </div>
                        <p className="text-sm">
                          Construct a data-driven marketing strategy for an eco-friendly product with emphasis on 
                          sustainability metrics verification. Include carbon footprint calculation methodology, 
                          material sourcing transparency documentation, and third-party certification process. 
                          Develop technical comparison matrix against conventional alternatives with quantifiable 
                          environmental impact reduction metrics displayed through interactive data visualization 
                          for consumer education.
                        </p>
                      </Card>
                      
                      <Card className="border border-studio-border bg-studio-background p-4 hover:border-studio-primary/30 transition-colors duration-200">
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-sm font-medium">Variation 5 - Conversational</span>
                          <Button variant="ghost" size="sm" className="hover:bg-studio-background-accent">
                            <Copy className="size-3.5 mr-1" />
                            Copy
                          </Button>
                        </div>
                        <p className="text-sm">
                          Design a marketing strategy for an eco-friendly product that speaks directly to environmentally 
                          conscious consumers through authentic, conversational messaging. Create a campaign that feels 
                          like friendly advice rather than corporate marketing, emphasizing real-world benefits and 
                          emotional connection. Include social proof elements featuring actual customers and their 
                          experiences, alongside transparent information about your sustainable practices.
                        </p>
                      </Card>
                      
                      <Card className="border border-studio-border bg-studio-background p-4 hover:border-studio-primary/30 transition-colors duration-200">
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-sm font-medium">Variation 6 - Visual-Focused</span>
                          <Button variant="ghost" size="sm" className="hover:bg-studio-background-accent">
                            <Copy className="size-3.5 mr-1" />
                            Copy
                          </Button>
                        </div>
                        <p className="text-sm">
                          Develop a visually-driven marketing strategy for an eco-friendly product that leverages 
                          powerful imagery and minimal text to communicate sustainability values. Emphasize nature-inspired 
                          color palettes, authentic photography showing the product's environmental benefits in action, 
                          and infographics that visualize impact metrics. Include guidelines for consistent visual 
                          storytelling across Instagram, Pinterest, and TikTok to reach environmentally conscious audiences.
                        </p>
                      </Card>
                    </div>
                  </ScrollArea>
                </CardContent>
              </Card>
            </div>
          </TabsContent>
          
          <TabsContent value="builder" className="flex-1 overflow-hidden p-4">
            <Card className="h-full bg-studio-background-accent border-studio-border">
              <CardHeader>
                <CardTitle className="text-base font-medium">Chain Builder</CardTitle>
                <CardDescription>
                  Construct multi-step prompt chains and workflows
                </CardDescription>
              </CardHeader>
              <CardContent className="h-[80%]">
                <div className="h-full flex flex-col items-center justify-center">
                  <div className="text-center max-w-md">
                    <div className="size-16 rounded-full bg-studio-background/50 mx-auto flex items-center justify-center mb-4">
                      <GitBranch className="size-8 text-studio-primary" />
                    </div>
                    <h3 className="text-lg font-medium mb-2">Chain Builder</h3>
                    <p className="text-muted-foreground mb-6">
                      Design complex prompt chains that feed into each other for sophisticated AI workflows
                    </p>
                    <Button>
                      Create New Chain
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
          
          <TabsContent value="rerunner" className="flex-1 overflow-hidden p-4">
            <Card className="h-full bg-studio-background-accent border-studio-border">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle className="text-base font-medium">Prompt Rerunner</CardTitle>
                    <CardDescription>
                      Track results across multiple prompt runs
                    </CardDescription>
                  </div>
                  <div className="flex items-center gap-2">
                    <Button variant="outline" size="sm">
                      <History className="size-4 mr-2" />
                      History
                    </Button>
                    <Button variant="outline" size="sm">New Run</Button>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="h-[80%]">
                <div className="h-full flex flex-col items-center justify-center">
                  <div className="text-center max-w-md">
                    <div className="size-16 rounded-full bg-studio-primary/10 mx-auto flex items-center justify-center mb-4">
                      <ArrowRight className="size-8 text-studio-primary" />
                    </div>
                    <h3 className="text-lg font-medium mb-2">No Recent Runs</h3>
                    <p className="text-muted-foreground mb-6">
                      Track the performance and results of your prompts over time with different parameters and models
                    </p>
                    <Button>
                      Start First Run
                    </Button>
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
