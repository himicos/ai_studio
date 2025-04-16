import React, { useState, useCallback } from "react";
import { motion } from "framer-motion";
import { PanelId } from "@/contexts/WorkspaceContext";
import { UserPlus, Megaphone, Copy, Calendar, Brain, Bot, Twitter } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { toast } from "sonner";
import { 
    AnalysisResult, 
    getTopRedditPosts, 
    getTopTwitterPosts,
    generateMarketingIdeas
} from "@/lib/api";

interface MarketingAgentPanelProps {
  id: PanelId;
}

export default function MarketingAgentPanel({ id }: MarketingAgentPanelProps) {
  const [promptText, setPromptText] = useState("");
  const [analysisResults, setAnalysisResults] = useState<AnalysisResult[]>([]);
  const [isLoadingReddit, setIsLoadingReddit] = useState(false);
  const [isLoadingTweets, setIsLoadingTweets] = useState(false);
  const [isLoadingIdeas, setIsLoadingIdeas] = useState(false);
  const [generatedIdeas, setGeneratedIdeas] = useState<string[]>([]);

  const handleFetchTopReddit = useCallback(async () => {
    setIsLoadingReddit(true);
    const toastId = toast.loading("Analyzing top Reddit posts...");
    try {
      const topPosts = await getTopRedditPosts(10, 'score');
      const formattedResults: AnalysisResult[] = topPosts.map(post => ({
        id: post.id,
        source: 'reddit',
        content: `${post.title}\n${post.selftext || ''}`.substring(0, 200) + '...',
        score: post.score,
        metadata: { url: post.permalink, author: post.author }
      }));
      setAnalysisResults(formattedResults);
      toast.success("Top Reddit posts analyzed.", { id: toastId });
    } catch (error) {
      console.error("Error fetching top Reddit posts:", error);
      toast.error("Failed to analyze Reddit posts", { id: toastId, description: String(error) });
    } finally {
      setIsLoadingReddit(false);
    }
  }, []);

  const handleFetchTopTweets = useCallback(async () => {
    setIsLoadingTweets(true);
    const toastId = toast.loading("Analyzing top Tweets...");
    try {
      const topTweets = await getTopTwitterPosts(10, 'retweet_count');
      const formattedResults: AnalysisResult[] = topTweets.map(tweet => ({
        id: tweet.tweet_id,
        source: 'twitter',
        content: tweet.content?.substring(0, 200) + '...' || '',
        score: tweet.retweet_count,
        metadata: { url: tweet.url, handle: tweet.user_handle }
      }));
      setAnalysisResults(formattedResults);
      toast.success("Top Tweets analyzed.", { id: toastId });
    } catch (error) {
      console.error("Error fetching top Tweets:", error);
      toast.error("Failed to analyze Tweets", { id: toastId, description: String(error) });
    } finally {
      setIsLoadingTweets(false);
    }
  }, []);

  const handleGenerateIdeas = useCallback(async () => {
    if (!promptText.trim() && analysisResults.length === 0) {
        toast.error("Please enter a prompt or analyze some content first.");
        return;
    }
    setIsLoadingIdeas(true);
    setGeneratedIdeas([]);
    const toastId = toast.loading("Generating content ideas...");
    
    try {
      console.log("Sending generation request with prompt:", promptText, "and context:", analysisResults);
      const response = await generateMarketingIdeas({
          goal_prompt: promptText,
          context: analysisResults
      });
      setGeneratedIdeas(response.ideas);
      toast.success("Content ideas generated!", { id: toastId });
      
    } catch (error) {
        console.error("Error generating ideas:", error);
        toast.error("Failed to generate ideas", { id: toastId, description: String(error) });
        setGeneratedIdeas([]);
    } finally {
        setIsLoadingIdeas(false);
    }
  }, [promptText, analysisResults]);

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
          <div className="size-8 rounded-md bg-studio-warning/10 flex items-center justify-center">
            <UserPlus className="size-4 text-studio-warning" />
          </div>
          <h2 className="text-xl font-bold">Marketing Agent</h2>
        </div>
        <div className="flex items-center gap-2">
          <button className="p-2 hover:bg-studio-background rounded-md">
            <Calendar className="size-4" />
          </button>
        </div>
      </div>
      
      {/* Panel Body - Modified Layout */}
      <div className="flex-1 p-4 overflow-y-auto flex flex-col gap-4"> 
          {/* User Prompt Section */}
          <Card className="bg-studio-background-accent">
            <CardHeader>
                <CardTitle className="flex items-center gap-2 text-lg">
                    <Megaphone className="size-5 text-studio-warning" />
                    Describe Your Goal
                </CardTitle>
            </CardHeader>
            <CardContent>
              <Textarea 
                className="w-full bg-studio-background border-studio-border outline-none resize-none h-24"
                placeholder="e.g., Generate blog post ideas about AI agents, create tweet thread about recent market news..."
                value={promptText}
                onChange={(e) => setPromptText(e.target.value)}
              />
            </CardContent>
          </Card>

          {/* Analysis Section */}
          <Card className="bg-studio-background-accent">
            <CardHeader>
                <CardTitle className="flex items-center gap-2 text-lg">
                    <Brain className="size-5 text-studio-accent" />
                    Gather Context
                </CardTitle>
            </CardHeader>
            <CardContent className="flex flex-col gap-4">
                <div className="flex items-center gap-2">
                    <Button onClick={handleFetchTopReddit} disabled={isLoadingReddit} variant="outline" size="sm">
                        {isLoadingReddit ? "Analyzing..." : "Analyze Top Reddit Posts"}
                    </Button>
                    <Button onClick={handleFetchTopTweets} disabled={isLoadingTweets} variant="outline" size="sm">
                        <Twitter className="size-4 mr-1"/>
                        {isLoadingTweets ? "Analyzing..." : "Analyze Top Tweets"}
                    </Button>
                </div>
                {analysisResults.length > 0 && (
                  <div className="border border-studio-border rounded-md p-2 bg-studio-background">
                    <h4 className="text-sm font-medium mb-2 text-muted-foreground">Analysis Context ({analysisResults.length} items)</h4>
                    <ScrollArea className="h-40">
                      <div className="space-y-2 pr-2">
                      {analysisResults.map((result) => (
                          <div key={result.id} className="text-xs border-b border-dashed border-studio-border last:border-b-0 pb-1 mb-1">
                              <span className={`font-medium ${result.source === 'reddit' ? 'text-orange-500' : 'text-blue-500'}`}>
                                  {result.source.toUpperCase()}:
                              </span>
                              <span className="text-muted-foreground ml-1 truncate block"> {result.content}</span>
                              <span className="text-muted-foreground/70 ml-1">(Score: {(result.score ?? 0).toFixed(0)})</span>
                          </div>
                      ))}
                      </div>
                    </ScrollArea>
                  </div>
                )}
            </CardContent>
          </Card>
          
          {/* Generation Section */}
          <Card className="bg-studio-background-accent">
             <CardHeader className="flex flex-row items-center justify-between">
                <CardTitle className="flex items-center gap-2 text-lg">
                    <Bot className="size-5 text-studio-primary" />
                    Generate Content Ideas
                </CardTitle>
                 <Button onClick={handleGenerateIdeas} disabled={isLoadingIdeas} size="sm">
                     {isLoadingIdeas ? "Generating..." : "Generate Ideas"}
                 </Button>
             </CardHeader>
             <CardContent>
                <div className="bg-studio-background p-3 rounded-md min-h-40 border border-studio-border">
                  {generatedIdeas.length === 0 && !isLoadingIdeas ? (
                    <p className="text-muted-foreground text-sm italic">
                      Generated content ideas will appear here...
                    </p>
                  ) : isLoadingIdeas ? (
                    <p className="text-muted-foreground text-sm italic">
                      Generating...
                    </p>
                  ) : (
                    <ScrollArea className="h-full max-h-60">
                      <ul className="list-disc list-inside space-y-1 text-sm">
                        {generatedIdeas.map((idea, index) => (
                          <li key={index}>{idea}</li>
                        ))}
                      </ul>
                    </ScrollArea>
                  )}
                </div>
             </CardContent>
          </Card>

      </div>
    </motion.div>
  );
}
