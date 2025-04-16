import React from 'react';
import { Input } from '@/components/ui/input';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Button } from '@/components/ui/button';

// Match the simplified SortOption from earlier rebuild steps
export type SortOption = 'date' | 'score' | 'likes' | 'retweets' | 'replies'; 

interface FilterPanelProps {
  keyword: string;
  sortOption: SortOption;
  sortOrder: 'asc' | 'desc'; // Added sortOrder back
  onKeywordChange: (keyword: string) => void;
  onSortChange: (sortOption: SortOption) => void;
  onSortOrderChange: (order: 'asc' | 'desc') => void; // Added handler back
}

export const FilterPanel: React.FC<FilterPanelProps> = ({
  keyword,
  sortOption,
  sortOrder, // Added back
  onKeywordChange,
  onSortChange,
  onSortOrderChange, // Added back
}) => {
  return (
    <div className="flex flex-col sm:flex-row gap-4">
      {/* Keyword Input */}
      <div className="flex-1">
        <Input
          type="text"
          placeholder="Filter by keyword..."
          value={keyword}
          onChange={(e) => onKeywordChange(e.target.value)}
          className="h-9"
        />
      </div>

      {/* Sort Select */}
      <div className="w-full sm:w-48">
        <Select value={sortOption} onValueChange={(value) => onSortChange(value as SortOption)}>
          <SelectTrigger className="h-9">
            <SelectValue placeholder="Sort by..." />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="date">Date</SelectItem>
            <SelectItem value="score">Score</SelectItem>
            <SelectItem value="likes">Likes</SelectItem>
            <SelectItem value="retweets">Retweets</SelectItem>
            <SelectItem value="replies">Replies</SelectItem>
          </SelectContent>
        </Select>
      </div>
      
      {/* Sort Order Toggle/Select (Example using simple buttons) */}
       <div className="flex items-center gap-2">
         <Button 
            variant={sortOrder === 'desc' ? 'default' : 'outline'} 
            size="sm" 
            className="h-9"
            onClick={() => onSortOrderChange('desc')}
         >
            Desc
         </Button>
         <Button 
            variant={sortOrder === 'asc' ? 'default' : 'outline'} 
            size="sm" 
            className="h-9"
            onClick={() => onSortOrderChange('asc')}
          >
            Asc
          </Button>
       </div>

    </div>
  );
}; 