
# AI Studio OS Implementation Guide

This document provides detailed implementation guidance for maintaining and extending the AI Studio OS frontend with consistent design principles and integration patterns.

## Design System

### UI Design Principles

1. **Progressive Disclosure**: Start with a clean, simple interface that reveals complexity only when needed.
2. **Visual Consistency**: Maintain consistent styling across all components.
3. **Modular Architecture**: Every component is self-contained and reusable.
4. **Embedded Intelligence**: All panels can integrate with AI capabilities.
5. **Responsive Design**: All UI components adapt to different screen sizes.

### Core Design Elements

#### Rounded Elements

- **Border Radius**: Use the Tailwind `rounded-lg` class consistently for cards, panels, and containers.
- **Buttons**: Use `rounded-md` for standard buttons and `rounded-full` for icon buttons.
- **Input Fields**: Use `rounded-md` for consistent form elements.
- **Panels**: Use `rounded-lg` with `border border-studio-border` for panel containers.
- **Modals & Dialogs**: Use `rounded-xl` for a slightly more pronounced curve on overlays.

#### Color System

All colors are defined in the Tailwind config and CSS variables:

- **Background**: `bg-studio-background` (dark mode default)
- **Foreground**: `text-studio-foreground`
- **Primary**: `bg-studio-primary` for action elements
- **Secondary**: `bg-studio-secondary` for supporting elements
- **Accent**: `bg-studio-accent` for highlighting
- **Border**: `border-studio-border` for dividers
- **Highlight**: `bg-studio-highlight` for attention-grabbing elements
- **Status Colors**:
  - Success: `bg-studio-success`
  - Warning: `bg-studio-warning`
  - Error: `bg-studio-error`
  - Info: `bg-studio-info`

#### Shadow & Elevation

- Use `shadow-sm` for subtle elevation
- Use `shadow-md` for medium elevation
- Use `shadow-lg` for prominent elements
- For glass effects: `glass` utility class (defined in index.css)

#### Typography

- Headings: Use the font-weight system consistently (font-bold for headings)
- Body text: Use default font weight
- Use text size utilities consistently:
  - `text-xs` for small labels
  - `text-sm` for secondary text
  - `text-base` for body text
  - `text-lg`, `text-xl`, etc. for headings

### Animation Guidelines

- Use subtle motion with Framer Motion
- Ensure animations serve a purpose (feedback, focus, transition)
- Keep durations short (0.2-0.5s)
- Use consistent easing functions
- Common animation patterns:
  - Fade in/out for appearance/disappearance
  - Slide for panels and drawers
  - Scale for emphasis on interactions

## Component Integration

### Adding a New Panel

1. Create a new component in `src/components/panels/`
2. Register it within the workspace system
3. Ensure it follows the panel design pattern with consistent header/body/footer structure

Example panel structure:
```tsx
import React from "react";
import { motion } from "framer-motion";

export default function NewPanel() {
  return (
    <motion.div 
      className="flex flex-col h-full panel"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.3 }}
    >
      {/* Panel Header */}
      <div className="flex items-center justify-between p-4 border-b border-studio-border">
        <h2 className="text-xl font-bold">Panel Title</h2>
        <div className="flex items-center gap-2">
          {/* Action buttons */}
        </div>
      </div>
      
      {/* Panel Body */}
      <div className="flex-1 p-4 overflow-auto">
        {/* Panel content */}
      </div>
      
      {/* Optional Panel Footer */}
      <div className="flex items-center justify-between p-4 border-t border-studio-border">
        {/* Footer content */}
      </div>
    </motion.div>
  );
}
```

### Backend Integration

When integrating with backend systems:

1. Create appropriate data fetching hooks in `src/hooks/`
2. Use React Query for data fetching where appropriate
3. Implement real-time updates via WebSockets where needed
4. Add appropriate loading states and error handling

### State Management

- Use React Context for global state (themes, user preferences)
- Use local component state for UI-specific state
- Consider adding more specialized contexts as needed

## Module Integration Guidelines

### Prompt Laboratory

- Use split view layout with resizable panels
- Implement syntax highlighting for prompts
- Use tabs for multiple prompt sessions
- Implement visual history tree for prompt versions

### Analytics Dashboard

- Use responsive grid layout
- Implement chart components with Recharts
- Ensure all data visualizations are theme-aware
- Add filters and time range selectors

### Proxy Management

- Implement map visualization for proxy locations
- Use stats cards for metrics
- Implement filter sidebar for location/type filtering
- Add form panel for adding/editing proxies

### Memory Graph

- Implement interactive node graph visualization
- Add search/filter capabilities
- Implement node inspection panel
- Add annotation capabilities

### System Monitoring

- Use status cards for health metrics
- Implement real-time graph updates
- Add log viewer with search/filter
- Implement alert system with priorities

## Coding Standards

- Use TypeScript for all components
- Follow React best practices
- Use ESLint and Prettier for code formatting
- Write unit tests for critical components
- Document complex logic with comments
- Use meaningful component and function names

## Performance Considerations

- Lazy load panels and heavy components
- Use virtualization for long lists
- Optimize re-renders with memoization
- Monitor and optimize bundle size

## Accessibility

- Ensure proper keyboard navigation
- Use appropriate ARIA attributes
- Maintain sufficient color contrast
- Test with screen readers
- Support reduced motion preferences
