import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useInView } from 'react-intersection-observer';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { toast } from 'sonner';
import { formatDistanceToNow } from 'date-fns';
import type { RedditFeedItem } from '@/lib/redditTypes';
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import { Sparkles, Loader2 as Spinner } from 'lucide-react';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";

// Type alias for sort order
type SortOrder = 'asc' | 'desc';

// Utility function for sentiment badge color
const getSentimentBadgeClass = (sentiment?: string | null): string => {
    if (!sentiment) return "border-transparent bg-gray-100 text-gray-600"; // Default/Unknown
    switch (sentiment.toUpperCase()) {
        case 'POSITIVE':
            return "border-transparent bg-green-100 text-green-800 hover:bg-green-200";
        case 'NEGATIVE':
            return "border-transparent bg-red-100 text-red-800 hover:bg-red-200";
        case 'NEUTRAL':
            return "border-transparent bg-yellow-100 text-yellow-800 hover:bg-yellow-200";
        default:
             return "border-transparent bg-gray-100 text-gray-600"; // Default for other cases
    }
};

// Individual post card component - Enhanced with AI display and Summarize button
const RedditFeedItemCard: React.FC<{ post: RedditFeedItem }> = ({ post }) => {
  const [showFullText, setShowFullText] = useState(false);
  const selfTextPreviewLength = 300;
  const [summary, setSummary] = useState<string | null>(null);
  const [isSummarizing, setIsSummarizing] = useState(false);
  const [summaryError, setSummaryError] = useState<string | null>(null);
  
  // Safely parse keywords (assuming they are stored as JSON string)
  let displayKeywords: string[] = [];
  if (typeof post.keywords === 'string') { // Check if it's a string before parsing
      try {
          const parsed = JSON.parse(post.keywords);
          if (Array.isArray(parsed)) {
              displayKeywords = parsed;
          }
      } catch (e) {
           console.error("Failed to parse keywords JSON:", e);
           // Keep displayKeywords as empty array
      }
  }

  const handleSummarize = async () => {
    if (isSummarizing) return;
    setIsSummarizing(true);
    setSummary(null); // Clear previous summary
    setSummaryError(null);
    toast.info(`Generating summary for post ${post.id}...`);

    try {
        const response = await fetch(`/api/reddit/agent/summarize_post/${post.id}`, {
            method: 'POST',
        });
        const result = await response.json();
        if (!response.ok) {
            throw new Error(result.detail || `HTTP error! status: ${response.status}`);
        }
        setSummary(result.summary);
        toast.success("Summary generated successfully.");
    } catch (err: any) {
        console.error("Failed to summarize post:", err);
        const errorMsg = err.message || "An unknown error occurred during summarization.";
        setSummaryError(errorMsg);
        toast.error(`Summarization failed: ${errorMsg}`);
    } finally {
        setIsSummarizing(false);
    }
  };

  return (
    <div className="p-4 border rounded-md mb-3 bg-card text-card-foreground shadow-sm transition-shadow hover:shadow-md">
       <div className="flex justify-between items-start mb-2 gap-2">
         <div className="flex flex-col flex-grow min-w-0"> {/* Ensure title wraps */}
             <a href={post.permalink} target="_blank" rel="noopener noreferrer" className="text-lg font-semibold hover:underline hover:text-primary transition-colors break-words">
                 {post.title}
             </a>
             <span className="text-sm text-muted-foreground">
                 Posted in <span className="font-medium">r/{post.subreddit}</span> by <span className="font-medium">u/{post.author || '[deleted]'}</span>
             </span>
         </div>
         <span className="text-xs text-muted-foreground whitespace-nowrap pl-2 flex-shrink-0">
             {formatDistanceToNow(new Date(post.created_utc), { addSuffix: true })}
         </span>
         <Tooltip>
            <TooltipTrigger asChild>
                <Button 
                    variant="ghost" 
                    size="icon" 
                    onClick={handleSummarize}
                    disabled={isSummarizing}
                    className="flex-shrink-0 text-muted-foreground hover:text-primary"
                >
                    {isSummarizing ? <Spinner className="size-4 animate-spin" /> : <Sparkles className="size-4" />}
                </Button>
            </TooltipTrigger>
            <TooltipContent><p>Summarize Post</p></TooltipContent>
         </Tooltip>
       </div>
       {post.selftext && (
           <div className="text-sm mb-2 break-words whitespace-pre-wrap">
            {showFullText ? post.selftext : post.selftext.substring(0, selfTextPreviewLength)}
            {post.selftext.length > selfTextPreviewLength && (
                 <Button 
                    variant="link"
                    className="text-xs p-0 h-auto ml-1"
                    onClick={() => setShowFullText(!showFullText)}
                 >
                     {showFullText ? 'Show less' : '... Show more'}
                 </Button>
             )}
            </div>
        )}
       {!post.is_self && post.url && (
            <a href={post.url} target="_blank" rel="noopener noreferrer" className="text-sm text-blue-500 hover:underline break-all block mb-2">
              {/* Display thumbnail or placeholder if available, else URL */}
              {post.url} 
            </a>
        )}
        {(post.sentiment || (displayKeywords && displayKeywords.length > 0)) && (
         <div className="flex flex-wrap items-center gap-2 mt-2 mb-2 pt-2 border-t border-border">
            {post.sentiment && (
                 <Badge variant="outline" className={cn("capitalize text-xs", getSentimentBadgeClass(post.sentiment))}>
                     {post.sentiment.toLowerCase()}
                 </Badge>
             )}
            {displayKeywords.map((keyword, index) => (
                <Badge key={`${keyword}-${index}`} variant="secondary" className="text-xs">
                     {keyword}
                 </Badge>
             ))}
         </div>
       )}
        <div className="flex justify-start items-center flex-wrap gap-x-4 gap-y-1 text-xs text-muted-foreground mt-auto pt-2 border-t border-border">
            <span>Score: <span className="font-medium">{post.score}</span></span>
            <span>Comments: <span className="font-medium">{post.num_comments}</span></span>
             <span>Upvote Ratio: <span className="font-medium">{(post.upvote_ratio * 100).toFixed(0)}%</span></span>
            {post.over_18 && <span className="text-red-500 text-xs font-semibold">(NSFW)</span>}
            {post.spoiler && <span className="text-yellow-600 text-xs font-semibold">(Spoiler)</span>}
         </div>
         {/* Add more details or actions (like summarization button) here later */}
         {summary && (
            <div className="mt-2 p-3 border rounded-md bg-muted/50 text-sm">
                <p className="font-semibold mb-1 text-primary">Summary:</p>
                <p className="whitespace-pre-wrap">{summary}</p>
            </div>
         )}
         {summaryError && (
            <div className="mt-2 p-3 border rounded-md bg-red-500/10 text-sm text-red-700">
                 <p><span className="font-semibold">Summarization Error:</span> {summaryError}</p>
            </div>
        )}
    </div>
  );
};

// Props for RedditFeedList, including filter/sort state
interface RedditFeedListProps {
  searchTerm: string;
  subredditFilter: string;
  sortBy: string;
  sortOrder: SortOrder;
}

export const RedditFeedList: React.FC<RedditFeedListProps> = ({
    searchTerm,
    subredditFilter,
    sortBy,
    sortOrder
}) => {
  const [feedItems, setFeedItems] = useState<RedditFeedItem[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [offset, setOffset] = useState(0);
  const [hasMore, setHasMore] = useState(true);
  const limit = 20; // Number of items per fetch
  const listRef = useRef<HTMLDivElement>(null);

  const { ref: intersectionRef, inView } = useInView({
    threshold: 0.5, // Trigger when 50% of the loading indicator is visible
    root: listRef.current, // Use the scrolling container as the root
  });

  const fetchFeed = useCallback(async (refresh = false) => {
    // Only set loading state, don't manage filters here
    if (isLoading || (!refresh && !hasMore)) return;
    setIsLoading(true);
    
    if (refresh) {
        setOffset(0);
        setHasMore(true); // Reset hasMore on refresh
    }
    setError(null);

    const currentOffset = refresh ? 0 : offset;

    try {
        // Use props for filter/sort parameters
        const params = new URLSearchParams({
            limit: String(limit),
            offset: String(currentOffset),
            sort_by: sortBy,
            sort_order: sortOrder,
        });
        if (searchTerm) params.append('search', searchTerm);
        if (subredditFilter) params.append('subreddit', subredditFilter.replace(/^r\//i, ''));

      const response = await fetch(`/api/reddit/agent/feed?${params.toString()}`);
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Failed to parse error response.'}));
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
      }
      const newItems: RedditFeedItem[] = await response.json();

       setFeedItems((prevItems) => refresh ? newItems : [...prevItems, ...newItems]);
       setOffset(currentOffset + newItems.length);
       setHasMore(newItems.length === limit);

    } catch (err: any) {
      console.error('Failed to fetch Reddit feed:', err);
      setError(err.message || 'Failed to load feed.');
      toast.error(`Failed to load Reddit feed: ${err.message}`);
      if (refresh) setFeedItems([]); // Clear items only if refresh failed
    } finally {
      setIsLoading(false);
    }
  }, [isLoading, hasMore, offset, limit, sortBy, sortOrder, searchTerm, subredditFilter]); // Added filter/sort props to deps

  // Trigger refresh when filter/sort props change
  useEffect(() => {
    fetchFeed(true); 
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sortBy, sortOrder, searchTerm, subredditFilter]); // Dependencies are the props

  // Fetch more on scroll (no change needed)
   useEffect(() => {
    if (inView && !isLoading && hasMore) {
        fetchFeed(); // Fetch next page (refresh = false)
    }
  }, [inView, isLoading, hasMore, fetchFeed]);

  return (
    // Removed outer Card, assuming parent component provides it
    // Removed filter/sort controls div
    <div ref={listRef} className="flex-grow space-y-3 overflow-y-auto pr-2"> {/* Scrollable container */}
        {feedItems.map((post) => (
            <TooltipProvider key={post.id}>
                 <RedditFeedItemCard post={post} />
             </TooltipProvider>
        ))}
        
        {/* Loading/End Indicator */}
        <div ref={intersectionRef} className="h-10 flex justify-center items-center">
            {isLoading && (
            <span className="animate-spin inline-block size-5 border-[3px] border-current border-t-transparent rounded-full text-muted-foreground" role="status" aria-label="loading"></span>
            )}
            {!isLoading && !hasMore && feedItems.length > 0 && <p className="text-muted-foreground text-sm">End of feed.</p>}
            {!isLoading && feedItems.length === 0 && error && <p className="text-red-500 text-sm">Error: {error}</p>}
            {!isLoading && feedItems.length === 0 && !error && <p className="text-muted-foreground text-sm">No posts found matching your criteria.</p>}
        </div>
    </div>
  );
};

// Export as named export if needed by panel
// export default RedditFeedList; 
