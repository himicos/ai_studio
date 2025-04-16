import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useInView } from 'react-intersection-observer';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { toast } from 'sonner';
import { formatDistanceToNow } from 'date-fns';
import type { RedditFeedItem } from '@/lib/types/reddit'; // Assuming types defined

// Placeholder for the individual post card component
const RedditFeedItemCard: React.FC<{ post: RedditFeedItem }> = ({ post }) => {
  return (
    <div className="p-4 border rounded-md mb-3 bg-card text-card-foreground shadow-sm">
       <div className="flex justify-between items-start mb-2">
         <div className="flex flex-col">
             <a href={post.permalink} target="_blank" rel="noopener noreferrer" className="text-lg font-semibold hover:underline hover:text-primary transition-colors break-words">
                 {post.title}
             </a>
             <span className="text-sm text-muted-foreground">
                 Posted in r/{post.subreddit} by u/{post.author || '[deleted]'}
             </span>
         </div>
         <span className="text-xs text-muted-foreground whitespace-nowrap pl-2">
             {formatDistanceToNow(new Date(post.created_utc), { addSuffix: true })}
         </span>
       </div>
       {post.selftext && <p className="text-sm mb-2 break-words whitespace-pre-wrap">{post.selftext.substring(0, 300)}{post.selftext.length > 300 ? '...' : ''}</p>}
       {!post.is_self && post.url && (
            <a href={post.url} target="_blank" rel="noopener noreferrer" className="text-sm text-blue-500 hover:underline break-all">
              {post.url}
            </a>
        )}
        <div className="flex justify-start items-center space-x-4 text-xs text-muted-foreground mt-2">
            <span>Score: {post.score}</span>
            <span>Comments: {post.num_comments}</span>
             <span>Upvote Ratio: {(post.upvote_ratio * 100).toFixed(0)}%</span>
         </div>
         {/* Add more details or actions (like summarization button) here later */}
    </div>
  );
};

const RedditFeedList: React.FC = () => {
  const [feedItems, setFeedItems] = useState<RedditFeedItem[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [offset, setOffset] = useState(0);
  const [hasMore, setHasMore] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [sortBy, setSortBy] = useState('created_utc');
  const [sortOrder, setSortOrder] = useState('desc');
  const [subredditFilter, setSubredditFilter] = useState(''); // Optional: Filter by specific subreddit
  const limit = 20; // Number of items per fetch

  const { ref, inView } = useInView({
    threshold: 0.5,
  });

  const fetchFeed = useCallback(async (refresh = false) => {
    if (isLoading || (!refresh && !hasMore)) return;
    setIsLoading(true);
    if (refresh) {
        setOffset(0);
        setFeedItems([]); // Clear existing items on refresh
        setHasMore(true); // Reset hasMore on refresh
    }
    setError(null);

    const currentOffset = refresh ? 0 : offset;

    try {
        const params = new URLSearchParams({
            limit: String(limit),
            offset: String(currentOffset),
            sort_by: sortBy,
            sort_order: sortOrder,
        });
        if (searchTerm) params.append('search', searchTerm);
        if (subredditFilter) params.append('subreddit', subredditFilter);

      const response = await fetch(`/api/reddit/agent/feed?${params.toString()}`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const newItems: RedditFeedItem[] = await response.json();

       setFeedItems((prevItems) => refresh ? newItems : [...prevItems, ...newItems]);
       setOffset(currentOffset + newItems.length);
       setHasMore(newItems.length === limit);

    } catch (err: any) {
      console.error('Failed to fetch Reddit feed:', err);
      setError(err.message || 'Failed to load feed.');
      toast.error('Failed to load Reddit feed.');
      // Don't reset items on error during infinite scroll, only on refresh
    } finally {
      setIsLoading(false);
    }
  }, [isLoading, hasMore, offset, sortBy, sortOrder, searchTerm, subredditFilter, limit]);

  // Initial fetch and fetch on filter/sort changes
  useEffect(() => {
    fetchFeed(true); // Refresh = true for initial load or when filters change
  }, [sortBy, sortOrder, searchTerm, subredditFilter]); // Exclude fetchFeed from deps array

  // Fetch more on scroll
   useEffect(() => {
    if (inView && !isLoading && hasMore) {
        fetchFeed(); // Fetch next page (refresh = false)
    }
  }, [inView, isLoading, hasMore, fetchFeed]);

  const handleSearchChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setSearchTerm(event.target.value);
    // Debounce could be added here
  };

  const handleSubredditFilterChange = (event: React.ChangeEvent<HTMLInputElement>) => {
     setSubredditFilter(event.target.value);
   };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Reddit Feed</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Filter and Sort Controls */}
        <div className="flex flex-col md:flex-row gap-4 p-4 border rounded-md">
            <Input
                placeholder="Search title/text..."
                value={searchTerm}
                onChange={handleSearchChange}
                className="flex-grow"
            />
             <Input
                placeholder="Filter by r/... (optional)"
                value={subredditFilter}
                onChange={handleSubredditFilterChange}
                className="flex-grow"
            />
            <div className="flex gap-2 flex-wrap">
                <Select value={sortBy} onValueChange={setSortBy}>
                    <SelectTrigger className="w-[180px]">
                        <SelectValue placeholder="Sort by" />
                    </SelectTrigger>
                    <SelectContent>
                        <SelectItem value="created_utc">Date</SelectItem>
                        <SelectItem value="score">Score</SelectItem>
                        <SelectItem value="num_comments">Comments</SelectItem>
                        <SelectItem value="subreddit">Subreddit</SelectItem>
                        <SelectItem value="author">Author</SelectItem>
                    </SelectContent>
                </Select>
                 <Select value={sortOrder} onValueChange={setSortOrder}>
                    <SelectTrigger className="w-[120px]">
                        <SelectValue placeholder="Order" />
                    </SelectTrigger>
                    <SelectContent>
                        <SelectItem value="desc">Desc</SelectItem>
                        <SelectItem value="asc">Asc</SelectItem>
                    </SelectContent>
                </Select>
                 <Button onClick={() => fetchFeed(true)} disabled={isLoading} variant="secondary">Refresh</Button>
            </div>
        </div>

        {/* Feed Items List */}
        <div className="space-y-3">
          {feedItems.map((post) => (
            <RedditFeedItemCard key={post.id} post={post} />
          ))}
        </div>

        {/* Loading/End Indicator */}
         <div ref={ref} className="h-10 flex justify-center items-center">
             {isLoading && <p className="text-muted-foreground text-sm">Loading more posts...</p>}
             {!isLoading && !hasMore && feedItems.length > 0 && <p className="text-muted-foreground text-sm">End of feed.</p>}
             {!isLoading && !hasMore && feedItems.length === 0 && error && <p className="text-red-500 text-sm">Error: {error}</p>}
             {!isLoading && !hasMore && feedItems.length === 0 && !error && <p className="text-muted-foreground text-sm">No posts found matching your criteria.</p>}
         </div>
      </CardContent>
    </Card>
  );
};

export default RedditFeedList; 