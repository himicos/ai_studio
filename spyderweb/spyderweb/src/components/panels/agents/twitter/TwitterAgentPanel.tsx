import React, { useState, useEffect, useCallback, createContext, useContext } from 'react';
import { PanelId } from "@/contexts/WorkspaceContext";
import { Twitter, Search, Filter, RefreshCw, Hash, Users, List, Loader2 as Spinner, Play, Pause, Square } from "lucide-react"; 
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { api } from '@/lib/api';
import debounce from 'lodash/debounce';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { toast } from "@/components/ui/use-toast";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { UserAddDirect } from '@/components/panels/agents/twitter/UserAddDirect';
import { TrackedUserIcon } from '@/components/panels/agents/twitter/TrackedUserIcon';
import { FilterPanel, SortOption } from '@/components/panels/agents/twitter/FilterPanel';
import { FeedList, Tweet } from '@/components/panels/agents/twitter/FeedList';

interface TwitterAgentPanelProps {
  id: PanelId;
}

interface TrackedUser {
  id: string;
  handle: string;
  tags: string[];
  date_added: string;
}

interface TrackingStatus {
    is_running: boolean;
    tracked_users_count: number;
    tracked_tweets_count: number;
}

// --- Define Context ---
interface TwitterAgentContextType {
  refreshTrackedUsers: () => Promise<void>;
}

const TwitterAgentContext = createContext<TwitterAgentContextType | undefined>(undefined);

export const useTwitterAgent = () => {
  const context = useContext(TwitterAgentContext);
  if (!context) {
    throw new Error('useTwitterAgent must be used within a TwitterAgentProvider');
  }
  return context;
};
// --- End Context Definition ---

export function TwitterAgentPanel({ id }: TwitterAgentPanelProps) {
  const [trackedUsers, setTrackedUsers] = useState<TrackedUser[]>([]);
  const [feedTweets, setFeedTweets] = useState<Tweet[]>([]);
  const [isLoadingUsers, setIsLoadingUsers] = useState(false);
  const [isLoadingFeed, setIsLoadingFeed] = useState(false);
  const [isTracking, setIsTracking] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [keyword, setKeyword] = useState('');
  const [sortOption, setSortOption] = useState<SortOption>('date');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');
  const [isLoadingTrackingStatus, setIsLoadingTrackingStatus] = useState(true);
  const [isScanning, setIsScanning] = useState(false);

  const fetchTrackedUsers = useCallback(async () => {
    setIsLoadingUsers(true);
    setError(null);
    try {
      const response = await api.get<TrackedUser[]>('/api/twitter-agent/tracked_users');
      const users = Array.isArray(response.data) ? response.data : [];
      console.log("[TwitterAgentPanel] Fetched trackedUsers:", users);
      users.forEach((user, index) => {
          if (user.id === null || user.id === undefined) {
              console.warn(`[TwitterAgentPanel] Tracked user at index ${index} has null/undefined ID:`, user);
          }
      });
      setTrackedUsers(users);
    } catch (err) {
      setError('Failed to fetch tracked users');
      console.error('Error fetching users:', err);
      setTrackedUsers([]);
    } finally {
      setIsLoadingUsers(false);
    }
  }, []);

  const fetchFeed = useCallback(async () => {
    setIsLoadingFeed(true);
    setError(null);
    try {
      const params = {
         keyword: keyword || undefined,
         sort_by: sortOption,
         sort_order: sortOrder
       };
      const response = await api.get('/api/twitter-agent/feed', { params });
      setFeedTweets(Array.isArray(response.data) ? response.data : []);
    } catch (err) {
      setError('Failed to fetch feed');
      console.error('Error fetching feed:', err);
      setFeedTweets([]);
    } finally {
      setIsLoadingFeed(false);
    }
  }, [keyword, sortOption, sortOrder]);

  const debouncedFetchFeed = useCallback(debounce(fetchFeed, 500), [fetchFeed]);

  const handleRemoveUser = useCallback(async (userId: string) => {
    try {
      await api.delete(`/api/twitter-agent/remove_user/${userId}`);
      await fetchTrackedUsers();
      toast({ title: "User removed", description: `User removed successfully.` });
    } catch (err) {
      setError('Failed to remove user');
      console.error('Error removing user:', err);
      toast({ title: "Error", description: "Failed to remove user.", variant: "destructive" });
    }
  }, [fetchTrackedUsers]);

  const fetchTrackingStatus = useCallback(async () => {
    setIsLoadingTrackingStatus(true);
    try {
      const response = await api.get<TrackingStatus>('/api/twitter-agent/tracking_status');
      const serverState = response.data.is_running;
      setIsTracking(serverState);
      return serverState;
    } catch (err) {
      console.error('Error checking tracking status:', err);
      toast({ title: "Error", description: "Failed to fetch tracking status.", variant: "destructive" });
      setIsTracking(false);
      return false;
    } finally {
       setIsLoadingTrackingStatus(false);
    }
  }, [setIsTracking, setIsLoadingTrackingStatus]);

  const handleTrackingToggle = useCallback(async () => {
    const action = isTracking ? 'stop' : 'start';
    const endpoint = action === 'stop' ? '/api/twitter-agent/stop_tracking' : '/api/twitter-agent/start_tracking';
    const successMessage = action === 'stop' ? 'Tracking stopped' : 'Tracking started';
    const errorMessage = `Failed to ${action} tracking`;
    
    setIsLoadingTrackingStatus(true);
    setError(null);

    try {
      await api.post(endpoint);
      toast({ title: successMessage });
      await fetchTrackingStatus(); 
    } catch (err) {
      setError(errorMessage);
      console.error(`Error ${action}ing tracking:`, err);
      toast({ title: "Error", description: errorMessage, variant: "destructive" });
      await fetchTrackingStatus(); 
    } finally {
    }
  }, [isTracking, fetchTrackingStatus]);

  const handleRunScan = async () => {
    try {
      setIsScanning(true);
      setError(null);
      const statusResponse = await api.get<TrackingStatus>('/api/twitter-agent/tracking_status');
      if (!statusResponse.data.is_running) {
        await handleTrackingToggle(); 
        await new Promise(resolve => setTimeout(resolve, 1000)); 
        const updatedStatus = await api.get<TrackingStatus>('/api/twitter-agent/tracking_status');
        if (!updatedStatus.data.is_running) {
           throw new Error("Tracking could not be started for scan.");
        }
      }
      await fetchFeed();
      toast({ title: "Scan Requested", description: "Twitter scan initiated." });
    } catch (error: any) {
      console.error('Error running scan:', error);
      setError('Failed to run scan');
      toast({ title: "Error", description: error.message || "Failed to run scan.", variant: "destructive" });
    } finally {
      setIsScanning(false);
    }
  };

  useEffect(() => {
    fetchTrackedUsers();
    fetchTrackingStatus();
    debouncedFetchFeed();
    return () => debouncedFetchFeed.cancel();
  }, [fetchTrackedUsers, fetchTrackingStatus, debouncedFetchFeed]);

  useEffect(() => {
    debouncedFetchFeed();
  }, [keyword, sortOption, sortOrder, debouncedFetchFeed]);

  // Log the callback function just before rendering
  console.log("[TwitterAgentPanel] fetchTrackedUsers type just before render:", typeof fetchTrackedUsers, fetchTrackedUsers);

  // Context value
  const contextValue = {
    refreshTrackedUsers: fetchTrackedUsers
  };

  return (
    // Wrap the component tree in the Provider
    <TwitterAgentContext.Provider value={contextValue}>
        <div className="flex flex-col h-full">
            <div className="flex items-center justify-between p-4 border-b">
                <div className="flex items-center gap-2">
                    <h2 className="text-lg font-semibold">Twitter Agent</h2>
                    <Badge variant={isTracking ? "default" : "secondary"}>
                        {isTracking ? "Tracking Active" : "Tracking Inactive"}
                    </Badge>
                </div>
                <div className="flex gap-2">
                    <Button
                        variant="outline"
                        size="sm"
                        onClick={handleRunScan}
                        disabled={isLoadingUsers || isScanning || isLoadingTrackingStatus}
                    >
                        <RefreshCw className={`h-4 w-4 mr-2 ${isScanning ? 'animate-spin' : ''}`} />
                        {isScanning ? 'Scanning...' : 'Run Scan'}
                    </Button>
                    <Button
                        variant={isTracking ? "destructive" : "default"}
                        size="sm"
                        onClick={handleTrackingToggle}
                        disabled={isLoadingTrackingStatus}
                    >
                        {isTracking ? (
                            <><Square className="h-4 w-4 mr-2" />Stop Tracking</>
                        ) : (
                            <><Play className="h-4 w-4 mr-2" />Start Tracking</>
                        )}
                    </Button>
                </div>
            </div>

            <div className="flex-1 overflow-hidden">
                <div className="h-full flex flex-col">
                    <div className="p-4 border-b">
                        <UserAddDirect />
                    </div>

                    <div className="flex-1 overflow-hidden">
                        <div className="h-full flex">
                            <div className="w-64 border-r p-4 overflow-y-auto">
                                <h3 className="font-medium mb-2">Tracked Users</h3>
                                {isLoadingUsers ? (
                                    <div className="flex justify-center items-center h-full"><Spinner className="h-5 w-5 animate-spin" /></div>
                                ) : (
                                    <div className="space-y-2">
                                        {trackedUsers.filter(user => user && user.id != null).map(user => (
                                            <TrackedUserIcon
                                                key={user.id}
                                                userId={user.id}
                                                handle={user.handle}
                                                tags={user.tags}
                                                onRemove={() => handleRemoveUser(user.id)}
                                            />
                                        ))}
                                        {trackedUsers.filter(user => user && user.id != null).length === 0 && (
                                            <p className="text-sm text-muted-foreground">
                                                No users tracked yet
                                            </p>
                                        )}
                                    </div>
                                )}
                            </div>

                            <div className="flex-1 flex flex-col overflow-hidden">
                                <div className="p-4 border-b">
                                    <FilterPanel 
                                        keyword={keyword}
                                        sortOption={sortOption}
                                        onKeywordChange={setKeyword}
                                        onSortChange={(value) => setSortOption(value as SortOption)}
                                        sortOrder={sortOrder}
                                        onSortOrderChange={setSortOrder}
                                    />
                                </div>
                                <div className="flex-1 overflow-y-auto p-4">
                                    {isLoadingFeed ? (
                                        <div className="flex justify-center items-center h-full">
                                            <Spinner className="h-6 w-6 animate-spin" />
                                        </div>
                                    ) : (
                                        <FeedList tweets={feedTweets} /> 
                                    )}
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </TwitterAgentContext.Provider>
  );
} 