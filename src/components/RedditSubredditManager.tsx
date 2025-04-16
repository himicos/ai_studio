import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { toast } from 'sonner';
import { Trash2, PlusCircle } from 'lucide-react';
import type { SubredditResponse } from '@/lib/types/reddit'; // Assuming types are defined here

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
            disabled={isAdding}
            className="flex-grow"
          />
          <Button
            onClick={handleAddSubreddit}
            disabled={isAdding || !newSubreddit.trim()}
            size="icon"
            aria-label="Add Subreddit"
          >
            {isAdding ? (
                <span className="loading loading-spinner loading-xs"></span>
            ) : (
                 <PlusCircle className="h-4 w-4" />
            )}

          </Button>
        </div>

        {/* List of Tracked Subreddits */}
        {isLoading ? (
          <p>Loading tracked subreddits...</p>
        ) : (
          <div className="space-y-2">
            {trackedSubreddits.length === 0 ? (
              <p className="text-muted-foreground text-sm">No subreddits are currently being tracked.</p>
            ) : (
              trackedSubreddits.map((sub) => (
                <div key={sub.name} className="flex items-center justify-between p-2 border rounded-md bg-muted/50">
                  <span className="font-medium">r/{sub.name}</span>
                  <Button
                    onClick={() => handleRemoveSubreddit(sub.name)}
                    disabled={isRemoving === sub.name}
                    variant="ghost"
                    size="icon"
                    aria-label={`Remove r/${sub.name}`}
                  >
                   {isRemoving === sub.name ? (
                       <span className="loading loading-spinner loading-xs"></span>
                   ) : (
                       <Trash2 className="h-4 w-4 text-destructive" />
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

export default RedditSubredditManager; 