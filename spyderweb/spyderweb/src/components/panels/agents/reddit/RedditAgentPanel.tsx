import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { toast } from 'sonner';
// Use default import for Manager, named for List and Filter
import RedditSubredditManager from './RedditSubredditManager';
import { RedditFeedList } from './RedditFeedList';
import { RedditFilterPanel } from './RedditFilterPanel';
import type { RedditAgentStatus } from '@/lib/redditTypes';
import { MessageSquare, RefreshCw, Play, Pause, Loader2 as Spinner } from 'lucide-react';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";

// Type alias for sort order
type SortOrder = 'asc' | 'desc';

// Renaming the main component to follow the likely export convention
export function RedditAgentPanel() {
  const [status, setStatus] = useState<RedditAgentStatus | null>(null);
  const [isLoadingStatus, setIsLoadingStatus] = useState(false);
  const [isStartingTracking, setIsStartingTracking] = useState(false);
  const [isStoppingTracking, setIsStoppingTracking] = useState(false);
  const [isScanning, setIsScanning] = useState(false);

  // State for filters (managed by this parent component)
  const [searchTerm, setSearchTerm] = useState('');
  const [sortBy, setSortBy] = useState('created_utc');
  const [sortOrder, setSortOrder] = useState<SortOrder>('desc');
  const [subredditFilter, setSubredditFilter] = useState('');
  // State to trigger feed refresh manually (passed to FilterPanel)
  const [refreshFeedKey, setRefreshFeedKey] = useState(0);

  const fetchStatus = useCallback(async () => {
    setIsLoadingStatus(true);
    try {
      const response = await fetch('/api/reddit/agent/status');
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data: RedditAgentStatus = await response.json();
      setStatus(data);
    } catch (error) {
      console.error('Failed to fetch Reddit Agent status:', error);
      toast.error('Failed to fetch Reddit Agent status.');
      setStatus(null); // Reset status on error
    } finally {
      setIsLoadingStatus(false);
    }
  }, []);

  // Fetch status on mount and periodically
  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, 30000);
    return () => clearInterval(interval);
  }, [fetchStatus]);

  const handleStartTracking = async () => {
    setIsStartingTracking(true);
    try {
      const response = await fetch('/api/reddit/agent/start_tracking', { method: 'POST' });
      const result = await response.json();
      if (!response.ok) throw new Error(result.detail || `HTTP error! status: ${response.status}`);
      toast.success(result.message || 'Reddit tracking started.');
      fetchStatus();
    } catch (error: any) { toast.error(`Failed to start tracking: ${error.message}`); }
    finally { setIsStartingTracking(false); }
  };

  const handleStopTracking = async () => {
    setIsStoppingTracking(true);
    try {
      const response = await fetch('/api/reddit/agent/stop_tracking', { method: 'POST' });
      const result = await response.json();
      if (!response.ok && response.status !== 409) throw new Error(result.detail || `HTTP error! status: ${response.status}`);
      toast.success(result.message || 'Reddit tracking stopped.');
      fetchStatus();
    } catch (error: any) { toast.error(`Failed to stop tracking: ${error.message}`); }
    finally { setIsStoppingTracking(false); }
  };

 const handleRunScan = async () => {
    setIsScanning(true);
    toast.info('Initiating Reddit scan...');
    try {
      const response = await fetch('/api/reddit/agent/scan', { method: 'POST' });
      const result = await response.json();
      if (!response.ok) throw new Error(result.detail || `HTTP error! status: ${response.status}`);
      toast.success(result.message || 'Reddit scan completed successfully.');
      // Trigger feed refresh after scan
      setRefreshFeedKey(prev => prev + 1);
    } catch (error: any) { toast.error(`Reddit scan failed: ${error.message}`); }
    finally { setIsScanning(false); }
  };

  const handleRefreshFeed = () => {
      setRefreshFeedKey(prev => prev + 1); // Increment key to trigger fetchFeed(true) in RedditFeedList via FilterPanel
  };

  const isRunning = status?.is_running ?? false;
  const isClientInitialized = status?.client_initialized ?? false;
  const isLoadingControls = isStartingTracking || isStoppingTracking || isScanning;

  return (
    <TooltipProvider>
        <div className="panel flex flex-col h-full">
        {/* Header - mirroring TwitterAgentPanel structure */}
        <div className="flex items-center justify-between p-4 border-b border-studio-border flex-shrink-0">
            <div className="flex items-center gap-2">
                <div className="size-8 rounded-md bg-orange-500/10 flex items-center justify-center">
                    {/* Using MessageSquare, could use a Reddit-specific icon if available */}
                    <MessageSquare className="size-4 text-orange-500" /> 
                </div>
                <h2 className="text-lg font-semibold">Reddit Agent</h2>
            </div>
            <div className="flex items-center gap-1">
                {/* Scan Button */}
                <Tooltip>
                    <TooltipTrigger asChild>
                        <Button 
                            variant="ghost" 
                            size="icon" 
                            onClick={handleRunScan}
                            disabled={!isClientInitialized || isLoadingControls}
                        >
                             {isScanning ? <Spinner className="size-4 animate-spin" /> : <RefreshCw className="size-4" />}
                        </Button>
                    </TooltipTrigger>
                    <TooltipContent><p>Run Scan Now</p></TooltipContent>
                </Tooltip>

                {/* Start/Stop Button */}
                <Tooltip>
                    <TooltipTrigger asChild>
                        <Button 
                            variant="ghost" 
                            size="icon" 
                            onClick={isRunning ? handleStopTracking : handleStartTracking}
                            disabled={!isClientInitialized || isLoadingControls}
                        >
                            {isLoadingControls && (isStartingTracking || isStoppingTracking) ? <Spinner className="size-4 animate-spin" /> : (isRunning ? <Pause className="size-4"/> : <Play className="size-4"/>)}
                        </Button>
                    </TooltipTrigger>
                    <TooltipContent><p>{isRunning ? 'Stop Background Tracking' : 'Start Background Tracking'}</p></TooltipContent>
                </Tooltip>
                 {/* Add other header buttons if needed */}
            </div>
        </div>

        {/* Main Content Area */}
        {/* Using simple vertical stack for Reddit, adjust if two-column needed */}
        <div className="flex-1 p-4 space-y-4 overflow-y-auto">
            
            {/* Status/Warning Area */}
            {isLoadingStatus && <p>Loading status...</p>}
            {!isClientInitialized && status !== null && (
                 <Card className="border-red-500/50 bg-red-500/5">
                     <CardHeader><CardTitle className="text-red-700">Client Error</CardTitle></CardHeader>
                     <CardContent><p className="text-red-600">PRAW client failed to initialize. Check backend logs and .env credentials. Agent functionality is disabled.</p></CardContent>
                 </Card>
            )}
            {isClientInitialized && status && (
                <div className="text-sm text-muted-foreground">
                    Status: {isRunning ? <span className="text-green-600 font-semibold">Running</span> : <span className="text-yellow-600 font-semibold">Idle</span>} (Interval: {status.scan_interval_seconds}s)
                </div>
            )}

            {/* Control Card (Subreddit Manager) - Conditionally rendered */}            
            {isClientInitialized && <RedditSubredditManager />}

            {/* Feed Area - Conditionally rendered */}            
            {isClientInitialized && (
                <Card className="flex flex-col h-full"> {/* Enclose feed list in a Card */} 
                    <CardHeader>
                        <CardTitle>Feed</CardTitle>
                    </CardHeader>
                    <CardContent className="flex-grow flex flex-col overflow-hidden">
                        <RedditFilterPanel 
                            searchTerm={searchTerm}
                            onSearchTermChange={setSearchTerm}
                            subredditFilter={subredditFilter}
                            onSubredditFilterChange={setSubredditFilter}
                            sortBy={sortBy}
                            onSortByChange={setSortBy}
                            sortOrder={sortOrder}
                            onSortOrderChange={setSortOrder}
                            onRefresh={handleRefreshFeed} // Pass refresh handler
                            isLoading={isLoadingControls} // Disable filters while controls are busy
                        />
                        <RedditFeedList 
                            key={refreshFeedKey} // Use key to force remount/refresh on demand
                            searchTerm={searchTerm}
                            subredditFilter={subredditFilter}
                            sortBy={sortBy}
                            sortOrder={sortOrder}
                        />
                    </CardContent>
                </Card>
             )}
        </div>
        </div>
    </TooltipProvider>
  );
};

// Use default export if WorkspaceContext expects it, otherwise keep named
// export default RedditAgentPanel; 
