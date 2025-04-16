
# Spyderweb OS Design System Documentation

This document outlines the UI/UX principles, components, and patterns used throughout the Spyderweb OS application, with a focus on creating consistent, responsive, and visually appealing interfaces.

## Table of Contents
1. [Design Principles](#design-principles)
2. [Color System](#color-system)
3. [Typography](#typography)
4. [Spacing and Layout](#spacing-and-layout)
5. [Component Guidelines](#component-guidelines)
6. [Data Visualization](#data-visualization)
7. [Responsive Design](#responsive-design)
8. [Animation](#animation)
9. [Accessibility](#accessibility)

## Design Principles

### 1. Consistency
Maintain unified visual language and interaction patterns across all panels and components.

### 2. Hierarchy
Organize information with clear visual hierarchy to guide users through the interface.

### 3. Progressive Disclosure
Start with essential information and reveal complexity only when needed.

### 4. Responsive Design
Ensure interfaces adapt seamlessly across all screen sizes and devices.

### 5. Visual Clarity
Use clean layouts, appropriate spacing, and clear typography to enhance readability.

## Color System

The color system is designed to be balanced, accessible, and visually distinctive while maintaining a professional appearance.

### Primary Colors

- **Primary Purple:** `#9b87f5`
  - Used for primary buttons, key highlights, and important UI elements
  - Active states and focused elements
  
- **Secondary Purple:** `#7E69AB`
  - Used for secondary buttons and supporting elements
  - Complementary to primary purple
  
- **Tertiary Purple:** `#6E59A5`
  - Used for tertiary UI elements and data visualization
  - Provides depth when used alongside primary and secondary purples
  
- **Light Purple:** `#D6BCFA`
  - Used for subtle backgrounds, hover states, and accents
  - Provides visual contrast for light-themed elements

- **Background:** `bg-studio-background` (dark mode default)
- **Foreground:** `text-studio-foreground`
- **Accent:** `bg-studio-accent` for highlighting
- **Border:** `border-studio-border` for dividers

### Status Colors

- **Success:** `bg-studio-success` (green)
- **Warning:** `bg-studio-warning` (amber)
- **Error:** `bg-studio-error` (red)
- **Info:** `bg-studio-info` (blue)

### Color Usage Guidelines

1. **Consistent Application:** Use colors consistently across the application to reinforce meaning and hierarchy.
2. **Accessible Contrast:** Ensure text and interactive elements maintain sufficient contrast ratios (minimum 4.5:1 for normal text).
3. **Purposeful Accents:** Reserve accent colors for important actions or information.
4. **Data Visualization:** Use a consistent color palette for charts and graphs, with distinct colors for different data series.

## Typography

### Font Stack

```css
font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif
```

### Font Sizes

- **Extra Small:** `text-xs` (0.75rem) - Secondary information, captions
- **Small:** `text-sm` (0.875rem) - Body text alternative, secondary information
- **Base:** `text-base` (1rem) - Default body text
- **Large:** `text-lg` (1.125rem) - Subtitles, section headings
- **Extra Large:** `text-xl` (1.25rem) - Panel headings
- **2XL:** `text-2xl` (1.5rem) - Major headings, important numbers
- **3XL:** `text-3xl` (1.875rem) - Page titles, hero content

### Font Weights

- **Normal:** `font-normal` (400) - Default body text
- **Medium:** `font-medium` (500) - Emphasis, subtitles
- **Bold:** `font-bold` (700) - Headings, important information
- **Semi-Bold:** `font-semibold` (600) - Strong emphasis

## Spacing and Layout

### Grid System

The application uses a flexible grid system based on CSS Grid and Flexbox, with responsive breakpoints.

### Breakpoints

- **Small (sm):** 640px and above
- **Medium (md):** 768px and above
- **Large (lg):** 1024px and above
- **Extra Large (xl):** 1280px and above
- **2XL (2xl):** 1536px and above

### Spacing Scale

- **0:** 0px
- **0.5:** 0.125rem (2px)
- **1:** 0.25rem (4px)
- **1.5:** 0.375rem (6px)
- **2:** 0.5rem (8px)
- **3:** 0.75rem (12px)
- **4:** 1rem (16px)
- **5:** 1.25rem (20px)
- **6:** 1.5rem (24px)
- **8:** 2rem (32px)
- **10:** 2.5rem (40px)
- **12:** 3rem (48px)
- **16:** 4rem (64px)

### Layout Guidelines

1. **Consistent Margins:** Use consistent spacing between components and sections.
2. **Responsive Containers:** Use responsive containers that adapt to different screen sizes.
3. **Grid-Based Layouts:** Structure complex layouts using CSS Grid for two-dimensional layouts.
4. **Flexbox for Components:** Use Flexbox for one-dimensional layouts and component alignment.

## Component Guidelines

### Cards

Cards are a fundamental building block used throughout the application, particularly in dashboards. They provide a consistent container for related content.

```tsx
<Card className="bg-studio-background-accent border-studio-border">
  <CardHeader>
    <CardTitle className="text-base font-medium">Card Title</CardTitle>
    <CardDescription>Optional description</CardDescription>
  </CardHeader>
  <CardContent>
    {/* Card content */}
  </CardContent>
</Card>
```

### Buttons

Buttons follow a consistent style throughout the application with several variants.

```tsx
<Button>Primary Button</Button>
<Button variant="secondary">Secondary Button</Button>
<Button variant="outline">Outline Button</Button>
<Button variant="ghost">Ghost Button</Button>

// Size variants
<Button size="sm">Small Button</Button>
<Button size="default">Default Button</Button>
<Button size="lg">Large Button</Button>
```

### Form Elements

Form elements are styled consistently with clear focus states and accessible labels.

```tsx
<Select>
  <SelectTrigger>
    <SelectValue placeholder="Select option" />
  </SelectTrigger>
  <SelectContent>
    <SelectItem value="option1">Option 1</SelectItem>
    <SelectItem value="option2">Option 2</SelectItem>
  </SelectContent>
</Select>
```

## Data Visualization

Data visualization is a critical part of the application, particularly in dashboard panels. The following guidelines ensure consistent and effective data visualization.

### Charts

Charts are implemented using Recharts with consistent styling and responsive containers.

#### Best Practices

1. **Responsive Containers:** Always wrap charts in a `ResponsiveContainer` to ensure they resize properly.
   
   ```tsx
   <ResponsiveContainer width="100%" height={300}>
     <BarChart data={data}>
       {/* Chart components */}
     </BarChart>
   </ResponsiveContainer>
   ```

2. **Consistent Color Palette:** Use the application's color palette for chart elements, ensuring consistency with the overall design.

3. **Clear Labels and Tooltips:** Provide clear labels and tooltips for all chart elements to improve understanding.

4. **Accessibility:** Ensure charts are accessible with text alternatives and keyboard navigation where possible.

### Chart Types

#### Bar Charts
Used for comparing categorical data or showing changes over time.

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
      <ChartTooltip content={<ChartTooltipContent />} />
      <Legend />
      <Bar dataKey="dataKey1" fill="#9b87f5" radius={[4, 4, 0, 0]} />
      <Bar dataKey="dataKey2" fill="#7E69AB" radius={[4, 4, 0, 0]} />
    </BarChart>
  </ResponsiveContainer>
</ChartContainer>
```

#### Line Charts
Used for showing trends over continuous data, such as time series.

```tsx
<ChartContainer config={{
  dataKey: { color: "#6E59A5" },
}}>
  <ResponsiveContainer width="100%" height="100%">
    <LineChart data={data} margin={{ top: 10, right: 10, left: 0, bottom: 5 }}>
      <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="var(--studio-border)" />
      <XAxis dataKey="xValue" />
      <YAxis />
      <ChartTooltip content={<ChartTooltipContent />} />
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

#### Pie Charts
Used for showing proportions of a whole.

```tsx
<ChartContainer config={{
  // Configure colors for each segment
  segment1: { color: "#6E59A5" },
  segment2: { color: "#7E69AB" },
  segment3: { color: "#9b87f5" },
  segment4: { color: "#D6BCFA" },
}}>
  <ResponsiveContainer width="100%" height="100%">
    <PieChart margin={{ top: 0, right: 0, left: 0, bottom: 0 }}>
      <Pie
        data={data}
        cx="50%"
        cy="50%"
        labelLine={false}
        outerRadius={80}
        fill="#8884d8"
        dataKey="value"
        label={({name, percent}) => `${name}: ${(percent * 100).toFixed(0)}%`}
      >
        {data.map((entry, index) => (
          <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
        ))}
      </Pie>
      <ChartTooltip content={<ChartTooltipContent />} />
    </PieChart>
  </ResponsiveContainer>
</ChartContainer>
```

## Responsive Design

The application uses a mobile-first approach with responsive components that adapt to different screen sizes.

### Responsive Guidelines

1. **Mobile-First CSS:** Start with mobile styles and use media queries to enhance the experience on larger screens.

2. **Fluid Layouts:** Use percentage-based widths and flexible grid systems.

3. **Responsive Typography:** Use relative units (`rem`, `em`) for font sizes.

4. **Breakpoint-Based Layout Changes:** Adjust layout at appropriate breakpoints:

   ```tsx
   <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
     {/* Content */}
   </div>
   ```

5. **Component-Level Responsiveness:** Ensure individual components respond appropriately to their container size.

6. **Touch-Friendly UI:** Elements should be accessible via touch with appropriate sizing (minimum 44x44 pixels for interactive elements).

7. **Testing Across Devices:** Regularly test the interface at various screen sizes and on different devices.

## Animation

Animations should enhance the user experience without causing distraction. The application uses Framer Motion for animations.

### Animation Guidelines

1. **Purpose-Driven:** Animations should serve a purpose, such as providing feedback, guiding attention, or enhancing understanding.

2. **Consistent Timing:** Use consistent timing for similar animations throughout the application.
   - Fast animations (0.1s - 0.2s) for immediate feedback
   - Medium animations (0.3s - 0.5s) for transitions and state changes
   - Slow animations (0.5s - 1s) for emphasis or more complex transitions

3. **Subtle Effects:** Prefer subtle animations over dramatic ones for a professional appearance.

4. **Reduce Motion Option:** Respect user preferences for reduced motion.

### Common Animation Patterns

```tsx
// Fade in animation
<motion.div
  initial={{ opacity: 0 }}
  animate={{ opacity: 1 }}
  transition={{ duration: 0.3 }}
>
  {/* Content */}
</motion.div>

// Hover scale effect
<motion.button
  whileHover={{ scale: 1.05 }}
  whileTap={{ scale: 0.95 }}
  transition={{ type: "spring", stiffness: 400, damping: 10 }}
>
  Button Text
</motion.button>
```

## Accessibility

Accessibility is a core consideration in the application's design system.

### Accessibility Guidelines

1. **Color Contrast:** Ensure all text and interactive elements have sufficient color contrast (minimum 4.5:1 for normal text, 3:1 for large text).

2. **Keyboard Navigation:** All interactive elements should be accessible and usable via keyboard.

3. **Focus States:** Provide visible focus states for interactive elements.

4. **Screen Reader Support:** Use semantic HTML and ARIA attributes to enhance screen reader support.

5. **Text Alternatives:** Provide text alternatives for non-text content.

6. **Responsive Design:** Ensure the interface is usable at different zoom levels and on different devices.

7. **Form Labels:** All form controls should have associated labels.

8. **Reduced Motion:** Respect user preferences for reduced motion.

9. **Error Messages:** Provide clear, accessible error messages and instructions.

10. **Testing:** Regularly test the interface with accessibility tools and real users with disabilities.
