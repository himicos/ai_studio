import React, { useState, useCallback, useEffect } from 'react';
import { api } from '@/lib/api'; // Ensure general api is imported
import { toast } from "@/components/ui/use-toast"; // Ensure toast is imported
import { PanelId } from "@/contexts/WorkspaceContext";
import { Twitter, Search, Filter, RefreshCw, Hash, Users, List, Loader2 as Spinner, Play, Pause, Square, FileText, Sparkles } from "lucide-react"; 
import { useInView } from 'react-intersection-observer'; // <<< ADDED IMPORT
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { UserSearch } from '@/components/panels/agents/twitter/UserSearch';
import { TrackedUserIcon } from '@/components/panels/agents/twitter/TrackedUserIcon'; // Using renamed component
import { FilterPanel, SortOption as FilterSortOption } from '@/components/panels/agents/twitter/FilterPanel'; // Import only the component
import { FeedList, Tweet } from '@/components/panels/agents/twitter/FeedList';
import { UserAddDirect } from '@/components/panels/agents/twitter/UserAddDirect';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip"; // <<< ADD Tooltip imports
// Temporarily comment out NotificationContext import due to path issues
// import { useNotifications } from '../../../../contexts/NotificationContext'; 

// Minimal placeholder props - adjust if PanelId is needed immediately
// import { PanelId } from "@/contexts/WorkspaceContext";
interface TwitterAgentPanelProps {
  id?: string; // Make id optional for now
}

interface TrackedUserResponse {
  id: string;
  handle: string;
  tags: string[];
  date_added: string;
}

// <<< ADD SummarizeResponse Interface >>>
interface SummarizeResponse {
  summary: string;
}

// <<< ADD Individual Tweet Summary Response Interface >>>
interface TweetSummaryResponse {
  tweet_id: string;
  original_content?: string;
  summary: string;
  memory_node_id?: string;
}

// Use the imported type alias for clarity
type SortOrder = 'asc' | 'desc';

// Helper function to extract error messages (similar to useApi hook pattern)
const getErrorMsg = (error: any, defaultMessage: string): string => {
  if (error && error.response && error.response.data && error.response.data.detail) {
    return error.response.data.detail;
  }
  if (error instanceof Error) {
    return error.message;
  }
  return defaultMessage;
};

// Using NAMED export for now as it was the last stable state before deletion
export function TwitterAgentPanel({ id }: TwitterAgentPanelProps) {
  // console.log("Rendering TwitterAgentPanel - Step 12: Full JSX Restored"); // REMOVE LOG

  // Restore State Hooks
  const [trackedUsers, setTrackedUsers] = useState<TrackedUserResponse[]>([]);
  const [feedTweets, setFeedTweets] = useState<Tweet[]>([]);
  const [isLoadingUsers, setIsLoadingUsers] = useState(false);
  const [isLoadingFeed, setIsLoadingFeed] = useState(false);
  const [isTracking, setIsTracking] = useState(false);
  const [isLoadingTrackingStatus, setIsLoadingTrackingStatus] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [keyword, setKeyword] = useState('');
  const [sortOption, setSortOption] = useState('date_posted');
  const [sortOrder, setSortOrder] = useState<SortOrder>('desc');
  const [isScanning, setIsScanning] = useState(false);
  const [offset, setOffset] = useState(0);
  const [limit] = useState(20); // Keep limit constant for now
  const [hasMoreTweets, setHasMoreTweets] = useState(true);
  const [isLoadingMore, setIsLoadingMore] = useState(false); // Optional: for a specific "load more" spinner
  const [isSummarizing, setIsSummarizing] = useState(false); // <<< ADDED: State for summarization loading
  const [summaryFocus, setSummaryFocus] = useState<string>('general'); // <<< ADDED: State for summary focus
  // <<< ADD State for individual tweet summarization loading >>>
  const [isSummarizingTweet, setIsSummarizingTweet] = useState<Record<string, boolean>>({});

  // <<< ADD Intersection Observer Hook >>>
  const { ref: feedEndRef, inView: feedEndInView } = useInView({
    threshold: 0, 
    triggerOnce: false
  });

  // Temporarily comment out useNotifications hook
  // const { showNotification } = useNotifications(); 

  // Restore Callback Shells (logic still commented)
  const fetchTrackedUsers = useCallback(async () => {
    // console.log("fetchTrackedUsers called - Running logic"); // REMOVE LOG
    setIsLoadingUsers(true); // Restore logic
    setError(null);         // Restore logic
    try {
      const response = await api.get('/api/twitter-agent/tracked_users'); // Restore logic (using general api)
      setTrackedUsers(Array.isArray(response.data) ? response.data : []); // Restore logic
    } catch (err) {
      setError('Failed to fetch tracked users'); // Restore logic
      console.error('Error fetching users:', err);   // Restore logic
      setTrackedUsers([]);                         // Restore logic
    } finally {
      setIsLoadingUsers(false); // Restore logic
    }
  }, []);

  // <<< PAGINATION AWARE fetchFeed >>>
  const fetchFeed = useCallback(async (isLoadMore = false) => {
    // <<< Add Logging >>>
    console.log(`>>> fetchFeed called: isLoadMore=${isLoadMore}, currentOffset=${offset}, hasMoreTweets=${hasMoreTweets}, isLoadingMore=${isLoadingMore}`);
    
    const currentOffset = isLoadMore ? offset : 0;

    // Reset state only on initial load/filter change
    if (!isLoadMore) {
      console.log("   >>> Resetting state for initial load/filter change");
      setOffset(0);
      setFeedTweets([]);
      setHasMoreTweets(true); // Assume more might exist
      setIsLoadingFeed(true); // Use main loader for initial load
    } else {
      // Don't fetch if no more tweets or already loading more
      if (!hasMoreTweets || isLoadingMore) {
          console.log("   >>> Skipping load more (no more tweets or already loading)");
          return; 
      }
      console.log("   >>> Setting isLoadingMore = true");
      setIsLoadingMore(true); // Use specific loader for load more
    }
    
    setError(null);

    try {
      console.log(`   >>> Fetching API: limit=${limit}, offset=${currentOffset}, keyword=${keyword}, sort_by=${sortOption}, sort_order=${sortOrder}`);
      const response = await api.get<Tweet[]>('/api/twitter-agent/feed', {
        params: {
          limit: limit,
          offset: currentOffset,
          keyword: keyword,
          sort_by: sortOption,
          sort_order: sortOrder
        }
      });

      setFeedTweets(prevTweets =>
        isLoadMore ? [...prevTweets, ...response.data] : response.data
      );

      // Update offset for the *next* fetch
      setOffset(currentOffset + response.data.length);
      setHasMoreTweets(response.data.length === limit); // More exist if we received a full page

    } catch (err) {
      setError(getErrorMsg(err, 'Failed to fetch feed'));
      // Keep existing tweets on load more error
      if (!isLoadMore) {
          setFeedTweets([]);
      }
    } finally {
      if (!isLoadMore) {
        setIsLoadingFeed(false);
      } else {
        setIsLoadingMore(false);
      }
    }
  // Ensure all relevant dependencies are included
  }, [keyword, sortOption, sortOrder, limit, offset, hasMoreTweets, isLoadingMore, getErrorMsg]); // Added dependencies

  // Helper to map backend sort value to FilterPanel sort value
  const mapBackendToSortOption = (backendValue: string): FilterSortOption => {
      switch (backendValue) {
          case 'date_posted': return 'date';
          case 'engagement_likes': return 'likes';
          case 'engagement_retweets': return 'retweets';
          case 'engagement_replies': return 'replies';
          case 'score': return 'score'; // <<< ADD score mapping
          default: return 'date'; // Fallback
      }
  };

  // Simpler handlers assuming FilterPanel has separate callbacks
  const handleKeywordChange = useCallback((newKeyword: string) => {
    setKeyword(newKeyword); 
  }, []);

  const handleSortOptionChange = useCallback((newSortOption: string) => { // Assume string for now
      setSortOption(newSortOption);
  }, []);
  
  const handleSortOrderChange = useCallback((newSortOrder: SortOrder) => {
      setSortOrder(newSortOrder);
  }, []);
  // ------------------------------------

  interface UserSearchResult { id: string; handle: string; name: string; }
  const handleUserSelect = useCallback(async (user: UserSearchResult) => {
    // console.log("handleUserSelect called - Running logic"); // REMOVE LOG
    // Prevent adding if already tracked (logic restored)
    if (trackedUsers.some(u => u.handle === user.handle)) { 
      toast({ title: "User already tracked", description: `@${user.handle} is already being tracked.` });
      return; 
    }
    try {
      // Revert to api.post (logic restored)
      await api.post('/api/twitter-agent/add_user', { handle: user.handle, tags: [] });
      await fetchTrackedUsers(); // Refresh users (logic restored)
      toast({ title: "User added", description: `@${user.handle} added successfully.` });
    } catch (err) {
      setError('Failed to add user'); // Restore logic
      console.error('Error adding user:', err); // Restore logic
      toast({ title: "Error", description: "Failed to add user.", variant: "destructive" }); // Restore logic
    }
  }, [fetchTrackedUsers, trackedUsers]); // Restore dependencies

  const handleRemoveUser = useCallback(async (userId: string) => {
    // console.log(">>> handleRemoveUser called for ID:", userId); // Keep commented out
    try {
      await api.delete(`/api/twitter-agent/remove_user/${userId}`);
      await fetchTrackedUsers(); 
      await fetchFeed(); // <<< ADDED: Refetch feed after successful user removal
      // Use toast for success notification
      toast({ title: "User removed", description: `User removed successfully.` }); 
    } catch (err) {
      setError('Failed to remove user'); 
      console.error('Error removing user:', err); // Keep console.error for debugging
      // Use toast for error notification
      toast({ title: "Error", description: "Failed to remove user.", variant: "destructive" });
    }
  }, [fetchTrackedUsers, fetchFeed]); 

  const handleTrackingToggle = useCallback(async () => {
    // console.log("handleTrackingToggle called - Running logic"); // Keep commented
    setIsLoadingTrackingStatus(true);
    setError(null);
    const endpoint = isTracking ? '/api/twitter-agent/stop_tracking' : '/api/twitter-agent/start_tracking';
    const action = isTracking ? 'stop' : 'start';
    
    try {
      const response = await api.post<{ message: string }>(endpoint);
      const newStatus = !isTracking;
      setIsTracking(newStatus);
      toast({ title: `Tracking ${action}ed`, description: response.data.message });
    } catch (err: any) {
      const errorMsg = getErrorMsg(err, `Failed to ${action} tracking`);
      setError(errorMsg);
      toast({ title: "Error", description: errorMsg, variant: "destructive" });
      // If action failed, revert optimistic UI update?
      // Or refetch status to be sure?
      // For now, just log the error and show toast.
      console.error(`Error during ${action}_tracking:`, err);
    } finally {
      setIsLoadingTrackingStatus(false);
      // Consider refetching status after action attempt
      // checkTrackingStatus(); 
    }
  }, [isTracking, toast, getErrorMsg]); // Correct dependencies: isTracking, toast, getErrorMsg

  const handleRunScan = useCallback(async () => {
    // console.log("handleRunScan called - Running logic"); // Keep commented
    setIsScanning(true); // Use separate loading state for scan
    setError(null);
    
    try {
      const response = await api.post<{ message: string }>('/api/twitter-agent/run_scan');
      toast({ title: "Scan Triggered", description: response.data.message });
      fetchFeed(); // Refetch feed immediately after triggering scan
    } catch (err: any) {
      const errorMsg = getErrorMsg(err, "Failed to run scan");
      setError(errorMsg);
      toast({ title: "Error", description: errorMsg, variant: "destructive" });
      console.error("Error running scan:", err);
    } finally {
      setIsScanning(false);
    }
  }, [toast, getErrorMsg, fetchFeed]); // Add fetchFeed to dependencies

  const handleSummarizeFeed = useCallback(async () => {
    if (feedTweets.length === 0) {
        toast({ title: "No tweets", description: "Cannot summarize an empty feed.", variant: "destructive" });
        return;
    }
    // console.log("Summarizing feed...", feedTweets);
    setIsSummarizing(true);
    setError(null);
    
    try {
        // Prepare payload, including focus if not 'general'
        const payload: { tweets: Tweet[]; focus?: string } = { tweets: feedTweets };
        if (summaryFocus !== 'general') {
            payload.focus = summaryFocus;
        }
        
        const response = await api.post<SummarizeResponse>('/api/twitter-agent/summarize_feed', payload);
        
        // Display the summary (currently placeholder) in a toast
        toast({ 
            title: "Feed Summary", 
            // Use a larger description area in toast for summary if needed
            description: response.data.summary, 
            duration: 9000 // Longer duration for summary
        });
        
    } catch (err: any) {
        const errorMsg = getErrorMsg(err, "Failed to summarize feed");
        setError(errorMsg);
        toast({ title: "Summarization Error", description: errorMsg, variant: "destructive" });
        console.error("Error summarizing feed:", err);
    } finally {
        setIsSummarizing(false);
    }
  // Add summaryFocus to dependency array
  }, [feedTweets, toast, getErrorMsg, summaryFocus]); 

  // <<< ADD Handler for summarizing a single tweet >>>
  const handleSummarizeTweet = useCallback(async (tweetId: string) => {
    console.log(`handleSummarizeTweet called for ID: ${tweetId}`);
    // Set loading state for this specific tweet
    setIsSummarizingTweet(prev => ({ ...prev, [tweetId]: true }));
    setError(null);

    try {
      const response = await api.post<TweetSummaryResponse>(`/api/twitter-agent/summarize_tweet/${tweetId}`);
      
      // Display the summary in a toast
      toast({
        title: `Summary for Tweet ${tweetId.substring(0, 6)}...`,
        description: response.data.summary,
        duration: 9000 // Longer duration for summary
      });
      if (response.data.memory_node_id) {
        console.log(`Individual summary saved to memory node: ${response.data.memory_node_id}`);
      }

    } catch (err: any) {
      const errorMsg = getErrorMsg(err, `Failed to summarize tweet ${tweetId}`);
      setError(errorMsg); // Maybe set a specific error state?
      toast({ title: "Summarization Error", description: errorMsg, variant: "destructive" });
      console.error(`Error summarizing tweet ${tweetId}:`, err);
    } finally {
      // Set loading state back to false for this tweet
      setIsSummarizingTweet(prev => ({ ...prev, [tweetId]: false }));
    }
  }, [toast, getErrorMsg]); // Dependencies: toast, getErrorMsg

  // useEffect Hooks 
  useEffect(() => {
    // Fetch initial feed (offset 0) when component mounts or filters change
    fetchTrackedUsers(); // Keep fetching users here
    fetchFeed(false); 
  }, [fetchTrackedUsers, keyword, sortOption, sortOrder]); // REMOVED fetchFeed from deps

  useEffect(() => {
    // console.log("Effect 2 triggered - Running checkTrackingStatus logic"); // REMOVE LOG
    const checkTrackingStatus = async () => {
      // Using general api object as per previous reverts
      // console.log("checkTrackingStatus called - Running logic"); // REMOVE LOG
      setIsLoadingTrackingStatus(true); // Restore logic
      try {
        const status = await api.get<{ is_running: boolean }>('/api/twitter-agent/tracking_status'); // Restore logic
        setIsTracking(status.data.is_running); // Restore logic
      } catch (err) {
        console.error('Error checking tracking status:', err); // Restore logic
        setIsTracking(false); // Restore logic (fallback)
      } finally {
         setIsLoadingTrackingStatus(false); // Restore logic
      }
    };
    checkTrackingStatus(); // Restore logic
  }, []); // Restore empty dependency array

  // <<< ADD useEffect for Infinite Scroll Trigger >>>
  useEffect(() => {
    if (feedEndInView && !isLoadingMore && hasMoreTweets) {
      fetchFeed(true); // Fetch the next page
    }
  }, [feedEndInView, isLoadingMore, hasMoreTweets, fetchFeed]); // Dependencies for the trigger

  return (
    // Wrap with TooltipProvider
    <TooltipProvider>
      <div className="h-full flex flex-col bg-card text-card-foreground shadow-sm rounded-lg overflow-hidden">

        {/* === REMOVE TEMPORARY CODE FROM TOP === */}
        
        {/* Panel Header */}
        <div className="p-4 border-b flex justify-between items-center">
          <div className="flex items-center gap-2">
            <h2 className="text-lg font-semibold">Twitter Agent</h2>
            <Badge variant={isTracking ? "default" : "secondary"}>
              {isTracking ? "Tracking Active" : "Tracking Inactive"}
            </Badge>
          </div>
          <div className="flex gap-2">
            <Button onClick={handleRunScan} disabled={isScanning || isLoadingTrackingStatus} size="sm" variant="outline">
              {isScanning ? <Spinner className="mr-2 h-4 w-4 animate-spin" /> : <Search className="mr-2 h-4 w-4" />}
              Run Scan Now
            </Button>
            {/* <<< ADD Summarize Button >>> */}
            <Button onClick={handleSummarizeFeed} disabled={isSummarizing || isLoadingFeed || feedTweets.length === 0} size="sm" variant="outline">
              {isSummarizing ? <Spinner className="mr-2 h-4 w-4 animate-spin" /> : <FileText className="mr-2 h-4 w-4" />} 
              Summarize Feed
            </Button>
            {/* <<< END Summarize Button >>> */}
            <Button onClick={handleTrackingToggle} disabled={isLoadingTrackingStatus} variant={isTracking ? "destructive" : "default"} size="sm">
              {isLoadingTrackingStatus ? <Spinner className="mr-2 h-4 w-4 animate-spin" /> : (isTracking ? <Square className="mr-2 h-4 w-4" /> : <Play className="mr-2 h-4 w-4" />)}
              {isTracking ? 'Stop Tracking' : 'Start Tracking'}
            </Button>
          </div>
        </div>

        {/* Main Content Area */}
        <div className="flex-1 overflow-hidden flex flex-col">
          <div className="h-full flex flex-col">

            {/* User Search Section - REMAINS COMMENTED OUT */}
            {/* 
            <div className="p-4 border-b">
              <UserSearch onUserSelect={handleUserSelect} />
            </div>
            */}

            {/* Main content split */}
            <div className="flex-1 flex overflow-hidden">
              {/* Tracked Users List */}
              <div className="w-1/3 border-r overflow-y-auto p-4 space-y-2">
                <h3 className="font-medium mb-2">Tracked Users</h3>
                {isLoadingUsers ? (
                   <div className="flex justify-center items-center h-full"><Spinner className="h-5 w-5 animate-spin" /></div>
                ) : error && trackedUsers.length === 0 ? ( // Show error if loading failed and no users shown
                   <div className="text-destructive text-center text-sm">{error}</div>
                ) : (
                  <div className="space-y-2">
                    {trackedUsers.map(user => (
                      <TrackedUserIcon // Use renamed component
                        key={user.id}
                        userId={user.id}
                        handle={user.handle}
                        tags={user.tags}
                        onRemove={() => handleRemoveUser(user.id)} 
                      />
                    ))}
                    {trackedUsers.length === 0 && !error && (
                      <p className="text-sm text-muted-foreground">
                        No users tracked yet.
                      </p>
                    )}
                  </div>
                )}
              </div>

              {/* Feed Display */}
              <div className="flex-1 overflow-y-auto p-4 flex flex-col"> {/* Added flex flex-col */}
                {/* === ADD Focus Select Dropdown === */}
                <div className="mb-4 p-4 border-b flex items-center space-x-2">
                   <label htmlFor="summary-focus" className="text-sm font-medium text-muted-foreground whitespace-nowrap">Summary Focus:</label>
                   <Select value={summaryFocus} onValueChange={setSummaryFocus}>
                      <SelectTrigger id="summary-focus" className="w-[200px]">
                         <SelectValue placeholder="Select focus" />
                      </SelectTrigger>
                      <SelectContent>
                         <SelectItem value="general">General Summary</SelectItem>
                         <SelectItem value="efficiency">Focus: Efficiency</SelectItem>
                         <SelectItem value="development">Focus: Development</SelectItem>
                         <SelectItem value="finance">Focus: Finance</SelectItem>
                         {/* Add more focus options here as needed */}
                      </SelectContent>
                   </Select>
                </div>
                {/* === END Focus Select Dropdown === */}
                
                {/* Filter Panel */}
                <div className="p-4 border-b">
                  <FilterPanel 
                    keyword={keyword} 
                    sortOption={mapBackendToSortOption(sortOption)} 
                    sortOrder={sortOrder}
                    onKeywordChange={handleKeywordChange}
                    onSortChange={(newOptionFromPanel: FilterSortOption) => { 
                      let backendOption: string = newOptionFromPanel;
                      // Perform mapping to backend string value
                      if (newOptionFromPanel === 'date') backendOption = 'date_posted';
                      if (newOptionFromPanel === 'likes') backendOption = 'engagement_likes';
                      if (newOptionFromPanel === 'retweets') backendOption = 'engagement_retweets';
                      if (newOptionFromPanel === 'replies') backendOption = 'engagement_replies';
                      // if (newOptionFromPanel === 'score') backendOption = 'score'; // Keep backend value same as frontend for score
                      // Since backendOption defaults to newOptionFromPanel, 
                      // if it's 'score', it will correctly pass 'score' to the handler.
                      handleSortOptionChange(backendOption); // Update state with the backend string
                    }}
                    onSortOrderChange={handleSortOrderChange}
                  />
                </div>

                {/* Feed List */}
                <div className="flex-1 overflow-y-auto p-4 space-y-4">
                  {isLoadingFeed && !isLoadingMore ? ( // Show main loader only on initial load
                    <div className="flex justify-center items-center h-32">
                      <Spinner className="h-8 w-8 animate-spin text-muted-foreground" />
                    </div>
                  ) : feedTweets.length > 0 ? (
                    <>
                      <FeedList 
                        tweets={feedTweets} 
                        onSummarizeTweet={handleSummarizeTweet} // <<< Pass handler
                        isSummarizingTweet={isSummarizingTweet} // <<< Pass loading state
                      />
                      {/* Sentinel Element for Infinite Scroll Trigger */}
                      <div ref={feedEndRef} style={{ height: '1px' }} /> 
                    </>
                  ) : (
                     // Show error or "No tweets" message when not loading and no tweets exist
                     <Card>
                       <CardContent className="p-4 text-center text-muted-foreground">
                         {error ? `Error: ${error}` : "No tweets found"}
                       </CardContent>
                     </Card>
                  )}
                  {/* Optional: Show loading indicator specifically for "load more" */}
                  {isLoadingMore && (
                    <div className="flex justify-center items-center py-4">
                        <Spinner className="h-6 w-6 animate-spin text-muted-foreground" />
                    </div>
                  )}
                  {/* Optional: Show message when no more tweets exist */}
                  {!isLoadingFeed && !isLoadingMore && !hasMoreTweets && feedTweets.length > 0 && (
                       <p className="text-center text-muted-foreground text-sm py-4">No more tweets to load.</p>
                  )}
                </div>
              </div>
            </div>

            {/* Direct Add User Component - RESTORED TO ORIGINAL POSITION */}
            <UserAddDirect 
              onUserAdded={fetchTrackedUsers} // Pass the function directly 
            />
          </div>
        </div>
      </div>
    </TooltipProvider>
  );
} 