import React from 'react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"

// Type alias for sort order
type SortOrder = 'asc' | 'desc';

interface RedditFilterPanelProps {
  searchTerm: string;
  onSearchTermChange: (value: string) => void;
  subredditFilter: string;
  onSubredditFilterChange: (value: string) => void;
  sortBy: string;
  onSortByChange: (value: string) => void;
  sortOrder: SortOrder;
  onSortOrderChange: (value: SortOrder) => void;
  onRefresh: () => void;
  isLoading: boolean;
}

export const RedditFilterPanel: React.FC<RedditFilterPanelProps> = ({
  searchTerm,
  onSearchTermChange,
  subredditFilter,
  onSubredditFilterChange,
  sortBy,
  onSortByChange,
  sortOrder,
  onSortOrderChange,
  onRefresh,
  isLoading,
}) => {
  return (
    <div className="flex flex-col md:flex-row gap-2 p-3 border rounded-md bg-muted/50 flex-shrink-0 mb-4">
        <Input
            placeholder="Search title/text..."
            value={searchTerm}
            onChange={(e) => onSearchTermChange(e.target.value)}
            className="flex-grow md:max-w-xs"
            disabled={isLoading}
        />
          <Input
            placeholder="Filter by r/... (optional)"
            value={subredditFilter}
            onChange={(e) => onSubredditFilterChange(e.target.value)}
            className="flex-grow md:max-w-xs"
            disabled={isLoading}
        />
        <div className="flex gap-2 flex-wrap items-center flex-grow justify-end">
            <Select value={sortBy} onValueChange={onSortByChange} disabled={isLoading}>
                <SelectTrigger className="w-auto md:w-[140px]">
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
              <Select value={sortOrder} onValueChange={(v) => onSortOrderChange(v as SortOrder)} disabled={isLoading}>
                <SelectTrigger className="w-auto md:w-[100px]">
                    <SelectValue placeholder="Order" />
                </SelectTrigger>
                <SelectContent>
                    <SelectItem value="desc">Desc</SelectItem>
                    <SelectItem value="asc">Asc</SelectItem>
                </SelectContent>
            </Select>
              <Button onClick={onRefresh} disabled={isLoading} variant="secondary" size="sm">Refresh</Button>
        </div>
    </div>
  );
}; 