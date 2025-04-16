
# Data Visualization Guide

This guide provides detailed information on implementing consistent, effective, and visually appealing data visualizations within the Spyderweb OS application.

## Table of Contents
1. [Chart Types and Usage](#chart-types-and-usage)
2. [Color Systems for Data](#color-systems-for-data)
3. [Responsive Charts](#responsive-charts)
4. [Accessibility in Data Visualization](#accessibility-in-data-visualization)
5. [Interactive Elements](#interactive-elements)
6. [Performance Considerations](#performance-considerations)
7. [Implementation Patterns](#implementation-patterns)

## Chart Types and Usage

Choose the appropriate chart type based on the data and the story you want to tell.

### Bar Charts

**When to use:**
- Comparing categorical data
- Showing values across different categories
- Displaying data changes over time (when categories are discrete)

**Implementation:**

```tsx
<ChartContainer config={{
  dataKey1: { color: "#9b87f5" },
  dataKey2: { color: "#7E69AB" },
}}>
  <ResponsiveContainer width="100%" height="100%">
    <BarChart data={data} margin={{ top: 10, right: 10, left: 0, bottom: 5 }}>
      <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="var(--studio-border)" />
      <XAxis dataKey="name" />
      <YAxis />
      <Tooltip content={<ChartTooltipContent />} />
      <Legend />
      <Bar dataKey="dataKey1" fill="#9b87f5" radius={[4, 4, 0, 0]} />
      <Bar dataKey="dataKey2" fill="#7E69AB" radius={[4, 4, 0, 0]} />
    </BarChart>
  </ResponsiveContainer>
</ChartContainer>
```

### Line Charts

**When to use:**
- Showing trends over time
- Displaying continuous data
- Comparing trends between different data series

**Implementation:**

```tsx
<ChartContainer config={{
  dataKey: { color: "#6E59A5" },
}}>
  <ResponsiveContainer width="100%" height="100%">
    <LineChart data={data} margin={{ top: 10, right: 10, left: 0, bottom: 5 }}>
      <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="var(--studio-border)" />
      <XAxis dataKey="xValue" />
      <YAxis />
      <Tooltip content={<ChartTooltipContent />} />
      <Legend />
      <Line
        type="monotone"
        dataKey="dataKey"
        stroke="#6E59A5"
        strokeWidth={2}
        dot={{ stroke: '#6E59A5', strokeWidth: 2, r: 4 }}
        activeDot={{ stroke: '#6E59A5', strokeWidth: 2, r: 6 }}
      />
    </LineChart>
  </ResponsiveContainer>
</ChartContainer>
```

### Pie/Donut Charts

**When to use:**
- Showing proportions of a whole
- Displaying percentage distribution
- Comparing parts of a total (limited to 6 or fewer categories for clarity)

**Implementation:**

```tsx
<ChartContainer config={{
  // Color configuration
}}>
  <ResponsiveContainer width="100%" height="100%">
    <PieChart margin={{ top: 0, right: 0, left: 0, bottom: 0 }}>
      <Pie
        data={data}
        cx="50%"
        cy="50%"
        labelLine={false}
        outerRadius={80}
        innerRadius={0}  // 0 for pie, >0 for donut
        fill="#8884d8"
        dataKey="value"
        label={({name, percent}) => `${name}: ${(percent * 100).toFixed(0)}%`}
      >
        {data.map((entry, index) => (
          <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
        ))}
      </Pie>
      <Tooltip content={<ChartTooltipContent />} />
    </PieChart>
  </ResponsiveContainer>
</ChartContainer>
```

### Area Charts

**When to use:**
- Emphasizing volume
- Showing cumulative values over time
- Highlighting the magnitude of trends

**Implementation:**

```tsx
<ChartContainer config={{
  dataKey: { color: "#9b87f5" },
}}>
  <ResponsiveContainer width="100%" height="100%">
    <AreaChart data={data} margin={{ top: 10, right: 10, left: 0, bottom: 5 }}>
      <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="var(--studio-border)" />
      <XAxis dataKey="xValue" />
      <YAxis />
      <Tooltip content={<ChartTooltipContent />} />
      <Legend />
      <Area 
        type="monotone" 
        dataKey="dataKey" 
        stroke="#9b87f5"
        fillOpacity={0.2}
        fill="#9b87f5" 
      />
    </AreaChart>
  </ResponsiveContainer>
</ChartContainer>
```

## Color Systems for Data

### Primary Chart Color Palette

Use the application's color system consistently for data visualizations:

- **Primary Purple:** `#9b87f5` - Main data series
- **Secondary Purple:** `#7E69AB` - Secondary data series
- **Tertiary Purple:** `#6E59A5` - Tertiary data series
- **Light Purple:** `#D6BCFA` - Quaternary data series
- **Pale Purple:** `#E9D8FD` - Additional data series

For extended color needs, use complementary colors that work well with the purple palette.

### Color Guidelines

1. **Consistency:** Use consistent colors for the same data series across different charts.
2. **Contrast:** Ensure sufficient contrast between adjacent colors in charts.
3. **Semantics:** Use color semantically (e.g., green for positive, red for negative).
4. **Accessibility:** Ensure colors are distinguishable for users with color vision deficiencies.
5. **Gradients:** Use gradients sparingly and ensure they don't interfere with data interpretation.

## Responsive Charts

### Implementation Strategies

1. **Container-Based Responsiveness:**

```tsx
<div className="w-full h-[220px] sm:h-[240px] md:h-[300px]">
  <ChartContainer config={...}>
    <ResponsiveContainer width="100%" height="100%">
      {/* Chart content */}
    </ResponsiveContainer>
  </ChartContainer>
</div>
```

2. **Dynamic Data Points:**
For smaller screens, consider reducing the number of data points displayed to avoid overcrowding.

```tsx
const visibleData = useResponsiveData(data, {
  sm: 5,  // Show 5 data points on small screens
  md: 7,  // Show 7 data points on medium screens
  lg: data.length  // Show all data points on large screens
});
```

3. **Adaptive Labels:**
Adjust label visibility and formatting based on screen size.

```tsx
<XAxis 
  dataKey="name"
  tick={{ fontSize: isMobile ? 10 : 12 }}
  interval={isMobile ? 1 : 0}  // Skip some labels on mobile
/>
```

4. **Layout Changes:**
Change chart layout or type based on screen size.

```tsx
{isMobile ? (
  <PieChart>{/* Simplified representation for mobile */}</PieChart>
) : (
  <BarChart>{/* Detailed representation for larger screens */}</BarChart>
)}
```

## Accessibility in Data Visualization

### Key Considerations

1. **Alternative Text:** Provide descriptive summaries of chart data for screen readers.

```tsx
<div aria-label="Bar chart showing monthly sales data. March has the highest sales at $10,000.">
  {/* Chart component */}
</div>
```

2. **Keyboard Navigation:** Ensure chart interactions are accessible via keyboard.

3. **Color Independence:** Don't rely solely on color to convey information; use patterns, labels, or other visual cues.

4. **Focus States:** Provide clear focus states for interactive chart elements.

5. **Screen Reader Announcements:** Update ARIA live regions when chart data changes.

## Interactive Elements

### Tooltips

Tooltips should be consistent across all charts and provide relevant information on hover/focus.

```tsx
<Tooltip 
  content={<ChartTooltipContent />} 
  cursor={{ fill: 'rgba(0, 0, 0, 0.1)' }}
/>
```

### Zoom and Pan

For complex or dense data sets, consider adding zoom and pan capabilities:

```tsx
<ReferenceArea 
  x1={refAreaLeft} 
  x2={refAreaRight} 
  strokeOpacity={0.3}
  fill="var(--studio-primary)"
  fillOpacity={0.3} 
/>
```

### Click Interactions

Handle click events for deep-dive analysis:

```tsx
<Bar 
  dataKey="value" 
  onClick={(data, index) => handleBarClick(data, index)} 
/>
```

## Performance Considerations

1. **Data Sampling:** For large datasets, consider sampling or aggregation.
2. **Lazy Loading:** Load charts only when they become visible in the viewport.
3. **Debouncing Window Resize:** Debounce resize handlers to prevent performance issues.
4. **Memoization:** Memoize chart components to prevent unnecessary re-renders.

```tsx
const MemoizedChart = React.memo(({ data }) => (
  <ResponsiveContainer>
    <BarChart data={data}>
      {/* Chart components */}
    </BarChart>
  </ResponsiveContainer>
));
```

## Implementation Patterns

### Chart with Loading State

```tsx
{isLoading ? (
  <div className="flex items-center justify-center h-[300px]">
    <Spinner />
  </div>
) : (
  <ChartContainer config={...}>
    <ResponsiveContainer>
      {/* Chart */}
    </ResponsiveContainer>
  </ChartContainer>
)}
```

### Error Handling

```tsx
{error ? (
  <div className="flex flex-col items-center justify-center h-[300px] text-center">
    <AlertTriangle className="text-studio-error mb-2" size={24} />
    <p className="text-studio-error font-medium">Failed to load chart data</p>
    <Button 
      variant="outline" 
      size="sm" 
      onClick={refetch} 
      className="mt-2"
    >
      Retry
    </Button>
  </div>
) : (
  <ChartContainer config={...}>
    <ResponsiveContainer>
      {/* Chart */}
    </ResponsiveContainer>
  </ChartContainer>
)}
```

### Empty State

```tsx
{data.length === 0 ? (
  <div className="flex flex-col items-center justify-center h-[300px] text-center">
    <Database className="text-muted-foreground mb-2" size={24} />
    <p className="text-muted-foreground">No data available</p>
  </div>
) : (
  <ChartContainer config={...}>
    <ResponsiveContainer>
      {/* Chart */}
    </ResponsiveContainer>
  </ChartContainer>
)}
```

### Chart with Time Period Selector

```tsx
<div className="space-y-4">
  <div className="flex justify-between items-center">
    <h3 className="font-medium">Sales Overview</h3>
    <Select 
      value={period} 
      onValueChange={setPeriod}
    >
      <SelectTrigger className="w-[120px] h-8">
        <SelectValue />
      </SelectTrigger>
      <SelectContent>
        <SelectItem value="day">Day</SelectItem>
        <SelectItem value="week">Week</SelectItem>
        <SelectItem value="month">Month</SelectItem>
        <SelectItem value="year">Year</SelectItem>
      </SelectContent>
    </Select>
  </div>
  <ChartContainer config={...}>
    <ResponsiveContainer>
      {/* Chart */}
    </ResponsiveContainer>
  </ChartContainer>
</div>
```
