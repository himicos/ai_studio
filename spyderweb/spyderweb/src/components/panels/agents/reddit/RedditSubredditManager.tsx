import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { toast } from 'sonner';
import { Trash2, PlusCircle } from 'lucide-react';
import type { SubredditResponse } from '@/lib/redditTypes';

const RedditSubredditManager: React.FC = () => {
  const [trackedSubreddits, setTrackedSubreddits] = useState<SubredditResponse[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [newSubreddit, setNewSubreddit] = useState('');
  const [isAdding, setIsAdding] = useState(false);
  const [isRemoving, setIsRemoving] = useState<string | null>(null); // Store name of subreddit being removed

  const fetchTrackedSubreddits = useCallback(async () => {
    setIsLoading(true);
    try {
      const response = await fetch('/api/reddit/agent/tracked');
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data: SubredditResponse[] = await response.json();
      setTrackedSubreddits(data);
    } catch (error) {
      console.error('Failed to fetch tracked subreddits:', error);
      toast.error('Failed to load tracked subreddits.');
      setTrackedSubreddits([]);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchTrackedSubreddits();
  }, [fetchTrackedSubreddits]);

  const handleAddSubreddit = async () => {
    const subredditToAdd = newSubreddit.trim();
    if (!subredditToAdd) {
      toast.warning('Please enter a subreddit name.');
      return;
    }

    // Basic validation: only letters, numbers, underscores
    if (!/^[a-zA-Z0-9_]+$/.test(subredditToAdd)) {
      toast.error('Invalid subreddit name. Use only letters, numbers, and underscores.');
      return;
    }

    setIsAdding(true);
    try {
      const response = await fetch('/api/reddit/agent/tracked', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ subreddit_name: subredditToAdd }),
      });
      const result = await response.json();
       if (!response.ok) {
        throw new Error(result.detail || `HTTP error! status: ${response.status}`);
      }
      toast.success(result.message || `Subreddit r/${subredditToAdd} added.`);
      setNewSubreddit('');
      fetchTrackedSubreddits(); // Refresh the list
    } catch (error: any) {
      console.error('Failed to add subreddit:', error);
       toast.error(`Failed to add r/${subredditToAdd}: ${error.message}`);
    } finally {
      setIsAdding(false);
    }
  };

  const handleRemoveSubreddit = async (subredditName: string) => {
    setIsRemoving(subredditName);
    try {
      const response = await fetch(`/api/reddit/agent/tracked/${subredditName}`, {
        method: 'DELETE',
      });
       const result = await response.json();
      if (!response.ok) {
        throw new Error(result.detail || `HTTP error! status: ${response.status}`);
      }
      toast.success(result.message || `Subreddit r/${subredditName} removed.`);
      fetchTrackedSubreddits(); // Refresh the list
    } catch (error: any) {
      console.error('Failed to remove subreddit:', error);
      toast.error(`Failed to remove r/${subredditName}: ${error.message}`);
    } finally {
      setIsRemoving(null);
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Tracked Subreddits</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Add Subreddit Input */}
        <div className="flex space-x-2">
          <Input
            type="text"
            placeholder="Enter subreddit name (e.g., python)"
            value={newSubreddit}
            onChange={(e) => setNewSubreddit(e.target.value)}
            disabled={isAdding || isRemoving !== null}
            className="flex-grow"
            maxLength={21} // Reddit subreddit name limit
          />
          <Button
            onClick={handleAddSubreddit}
            disabled={isAdding || isRemoving !== null || !newSubreddit.trim()}
            size="icon"
            aria-label="Add Subreddit"
          >
            {isAdding ? (
                <span className="animate-spin inline-block size-4 border-[2px] border-current border-t-transparent rounded-full" role="status" aria-label="loading"></span>
            ) : (
                 <PlusCircle className="h-4 w-4" />
            )}

          </Button>
        </div>

        {/* List of Tracked Subreddits */}
        {isLoading ? (
          <div className="flex justify-center items-center p-4">
             <span className="animate-spin inline-block size-5 border-[3px] border-current border-t-transparent rounded-full text-muted-foreground" role="status" aria-label="loading"></span>
          </div>
        ) : (
          <div className="space-y-2 max-h-60 overflow-y-auto pr-2">
            {trackedSubreddits.length === 0 ? (
              <p className="text-muted-foreground text-sm text-center py-4">No subreddits are currently being tracked.</p>
            ) : (
              trackedSubreddits.map((sub) => (
                <div key={sub.name} className="flex items-center justify-between p-2 border rounded-md bg-muted/50 hover:bg-muted/80 transition-colors">
                  <span className="font-medium text-sm">r/{sub.name}</span>
                  <Button
                    onClick={() => handleRemoveSubreddit(sub.name)}
                    disabled={isRemoving === sub.name || isAdding}
                    variant="ghost"
                    size="icon"
                    className="text-muted-foreground hover:text-destructive hover:bg-destructive/10"
                    aria-label={`Remove r/${sub.name}`}
                  >
                   {isRemoving === sub.name ? (
                       <span className="animate-spin inline-block size-4 border-[2px] border-current border-t-transparent rounded-full" role="status" aria-label="loading"></span>
                   ) : (
                       <Trash2 className="h-4 w-4" />
                   )}
                  </Button>
                </div>
              ))
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default RedditSubredditManager; // Ensure default export
