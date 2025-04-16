import React from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription, CardFooter } from "@/components/ui/card";
import { formatDistanceToNow } from 'date-fns';
import { Link, Sparkles, Loader2 as Spinner } from 'lucide-react';
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";

// Restore full Tweet interface
export interface Tweet {
  id: string;
  user_id: string;
  content: string;
  date_posted: string;
  engagement: {
    replies: number;
    retweets: number;
    likes: number;
  };
  keywords: string[];
  handle?: string;
  url?: string;
  sentiment?: string;
}

interface FeedListProps {
  tweets: Tweet[];
  onSummarizeTweet: (tweetId: string) => void;
  isSummarizingTweet: Record<string, boolean>;
}

// Restore original FeedList component logic
export const FeedList: React.FC<FeedListProps> = ({ tweets, onSummarizeTweet, isSummarizingTweet }) => {
  console.log("FeedList received tweets:", JSON.stringify(tweets, null, 2));

  if (!tweets || !Array.isArray(tweets)) {
    console.error('Invalid tweets prop:', tweets);
    return (
      <Card>
        <CardContent className="p-4 text-center text-destructive">
          Invalid feed data
        </CardContent>
      </Card>
    );
  }

  if (tweets.length === 0) {
    return (
      <Card>
        <CardContent className="p-4 text-center text-muted-foreground">
          No tweets found in feed
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      {tweets.map((tweet) => {
        const isLoadingSummary = isSummarizingTweet[tweet.id] || false;
        
        return (
          <Card key={tweet.id} className="w-full text-sm">
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Avatar className="h-8 w-8">
                    <AvatarFallback>{tweet.handle ? tweet.handle.substring(0, 2).toUpperCase() : '??'}</AvatarFallback>
                  </Avatar>
                  <span className="font-semibold">@{tweet.handle || 'unknown'}</span>
                  {tweet.url && (
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <a href={tweet.url} target="_blank" rel="noopener noreferrer">
                          <Link className="h-4 w-4 text-muted-foreground hover:text-foreground" />
                        </a>
                      </TooltipTrigger>
                      <TooltipContent>View on Nitter</TooltipContent>
                    </Tooltip>
                  )}
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <Button 
                        variant="ghost" 
                        size="icon" 
                        className="h-6 w-6" 
                        onClick={() => onSummarizeTweet(tweet.id)}
                        disabled={isLoadingSummary}
                      >
                        {isLoadingSummary ? (
                          <Spinner className="h-4 w-4 animate-spin" />
                        ) : (
                          <Sparkles className="h-4 w-4 text-muted-foreground hover:text-primary" />
                        )}
                      </Button>
                    </TooltipTrigger>
                    <TooltipContent>Summarize Tweet</TooltipContent>
                  </Tooltip>
                </div>
                <CardDescription className="text-xs pt-1">
                  {tweet.date_posted ? formatDistanceToNow(new Date(tweet.date_posted), { addSuffix: true }) : "Date unknown"}
                </CardDescription>
              </div>
            </CardHeader>
            <CardContent className="py-2">
              <p className="whitespace-pre-wrap break-words">
                {tweet.content || '[No Content]'}
              </p>
            </CardContent>
            <CardFooter className="pt-2 pb-3 flex justify-between items-center text-muted-foreground">
              <div className="flex items-center gap-4 text-xs">
                <span>Replies: {tweet.engagement.replies}</span>
                <span>Retweets: {tweet.engagement.retweets}</span>
                <span>Likes: {tweet.engagement.likes}</span>
                {tweet.sentiment && (
                  <span 
                    className={`
                      px-2 py-0.5 rounded-full text-xs font-medium
                      ${tweet.sentiment === 'positive' ? 'bg-green-100 text-green-800' :
                        tweet.sentiment === 'negative' ? 'bg-red-100 text-red-800' :
                        tweet.sentiment === 'neutral' ? 'bg-yellow-100 text-yellow-800' : 'bg-gray-100 text-gray-800'
                      }
                    `}
                  >
                    {tweet.sentiment.charAt(0).toUpperCase() + tweet.sentiment.slice(1)}
                  </span>
                )}
              </div>
              {tweet.keywords && tweet.keywords.length > 0 && (
                <div className="mt-2 flex flex-wrap gap-1">
                  {tweet.keywords.map((keyword) => (
                    <span
                      key={keyword}
                      className="px-2 py-1 text-xs bg-secondary rounded-full"
                    >
                      {keyword}
                    </span>
                  ))}
                </div>
              )}
            </CardFooter>
          </Card>
        );
      })}
    </div>
  );
}; 