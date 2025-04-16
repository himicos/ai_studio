
# Design Elements Reference Guide

This document provides a reference for UI elements and components that match the AI Studio OS design aesthetic.

## Core UI Elements

### Cards & Panels

- **Panel Container**
  ```tsx
  <div className="panel rounded-lg border border-studio-border bg-studio-background-accent p-4">
    {/* Panel content */}
  </div>
  ```

- **Glass Panel**
  ```tsx
  <div className="glass rounded-lg p-4">
    {/* Glass panel content */}
  </div>
  ```

- **Card**
  ```tsx
  <div className="rounded-lg border border-studio-border bg-studio-background-accent p-4 shadow-sm">
    {/* Card content */}
  </div>
  ```

### Buttons

- **Primary Button**
  ```tsx
  <button className="rounded-md bg-studio-primary px-4 py-2 text-white hover:bg-studio-primary/90 transition-colors">
    Button Text
  </button>
  ```

- **Secondary Button**
  ```tsx
  <button className="rounded-md bg-studio-secondary px-4 py-2 text-white hover:bg-studio-secondary/90 transition-colors">
    Button Text
  </button>
  ```

- **Ghost Button**
  ```tsx
  <button className="rounded-md px-4 py-2 hover:bg-studio-background-accent transition-colors">
    Button Text
  </button>
  ```

- **Icon Button**
  ```tsx
  <button className="rounded-full p-2 hover:bg-studio-background-accent transition-colors">
    <Icon className="size-5" />
  </button>
  ```

### Inputs

- **Text Input**
  ```tsx
  <input 
    type="text" 
    className="rounded-md border border-studio-border bg-studio-background px-3 py-2 w-full focus:outline-none focus:ring-2 focus:ring-studio-primary"
  />
  ```

- **Select Input**
  ```tsx
  <select className="rounded-md border border-studio-border bg-studio-background px-3 py-2 w-full focus:outline-none focus:ring-2 focus:ring-studio-primary">
    <option>Option 1</option>
    <option>Option 2</option>
  </select>
  ```

### Navigation

- **Tab Bar**
  ```tsx
  <div className="flex border-b border-studio-border">
    <button className="px-4 py-2 border-b-2 border-studio-primary">Active Tab</button>
    <button className="px-4 py-2 border-b-2 border-transparent hover:border-studio-border/50">Inactive Tab</button>
  </div>
  ```

- **Sidebar Item**
  ```tsx
  <button className="flex items-center gap-3 px-3 py-2 rounded-md hover:bg-studio-background-accent w-full">
    <Icon className="size-5" />
    <span>Sidebar Item</span>
  </button>
  ```

### Data Display

- **Status Badge**
  ```tsx
  <span className="inline-flex items-center rounded-full bg-studio-success/20 px-2 py-1 text-xs text-studio-success">
    Online
  </span>
  ```

- **Info Card**
  ```tsx
  <div className="rounded-lg border border-studio-border bg-studio-background-accent p-4">
    <div className="flex items-center gap-3">
      <Icon className="size-8 text-studio-primary" />
      <div>
        <h3 className="font-medium">Card Title</h3>
        <p className="text-sm text-muted-foreground">Card description</p>
      </div>
    </div>
  </div>
  ```

- **Metric Card**
  ```tsx
  <div className="rounded-lg border border-studio-border bg-studio-background-accent p-4">
    <p className="text-sm text-muted-foreground">Metric Label</p>
    <h3 className="text-2xl font-bold mt-1">240</h3>
    <div className="flex items-center gap-1 mt-1 text-studio-success">
      <ArrowUpIcon className="size-4" />
      <span className="text-xs">2.5%</span>
    </div>
  </div>
  ```

### Modals & Overlays

- **Modal**
  ```tsx
  <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center">
    <div className="rounded-xl bg-studio-background p-6 shadow-xl max-w-md w-full">
      <h2 className="text-xl font-bold mb-4">Modal Title</h2>
      <div className="mb-6">Modal content</div>
      <div className="flex justify-end gap-3">
        <button className="rounded-md px-4 py-2 hover:bg-studio-background-accent">Cancel</button>
        <button className="rounded-md bg-studio-primary px-4 py-2 text-white">Confirm</button>
      </div>
    </div>
  </div>
  ```

- **Toast Notification**
  ```tsx
  <div className="rounded-lg border border-studio-border bg-studio-background-accent p-4 shadow-md">
    <div className="flex gap-3">
      <InfoIcon className="size-5 text-studio-info" />
      <div>
        <h4 className="font-medium">Notification Title</h4>
        <p className="text-sm text-muted-foreground">Notification message</p>
      </div>
    </div>
  </div>
  ```

## Specialized Components

### Analytics Elements

- **Chart Card**
  ```tsx
  <div className="rounded-lg border border-studio-border bg-studio-background-accent p-4">
    <h3 className="text-lg font-medium mb-4">Chart Title</h3>
    <div className="h-64">
      {/* Chart component goes here */}
    </div>
  </div>
  ```

- **Data Table**
  ```tsx
  <div className="rounded-lg border border-studio-border overflow-hidden">
    <table className="w-full">
      <thead className="bg-studio-background-accent border-b border-studio-border">
        <tr>
          <th className="px-4 py-3 text-left">Column 1</th>
          <th className="px-4 py-3 text-left">Column 2</th>
        </tr>
      </thead>
      <tbody>
        <tr className="border-b border-studio-border">
          <td className="px-4 py-3">Value 1</td>
          <td className="px-4 py-3">Value 2</td>
        </tr>
      </tbody>
    </table>
  </div>
  ```

### Prompt Laboratory Elements

- **Prompt Editor**
  ```tsx
  <div className="rounded-lg border border-studio-border bg-studio-background p-4">
    <div className="flex items-center justify-between mb-2">
      <h3 className="font-medium">Original Prompt</h3>
      <button className="rounded-full p-1 hover:bg-studio-background-accent">
        <EditIcon className="size-4" />
      </button>
    </div>
    <textarea 
      className="w-full bg-studio-background-accent rounded-md p-3 font-mono text-sm"
      rows={6}
    ></textarea>
  </div>
  ```

- **Split View Container**
  ```tsx
  <div className="flex gap-4 h-full">
    <div className="flex-1 rounded-lg border border-studio-border bg-studio-background p-4">
      {/* Left panel */}
    </div>
    <div className="flex-1 rounded-lg border border-studio-border bg-studio-background p-4">
      {/* Right panel */}
    </div>
  </div>
  ```

### Memory Graph Elements

- **Node Detail Card**
  ```tsx
  <div className="rounded-lg border border-studio-border bg-studio-background-accent p-4">
    <h3 className="font-medium mb-2">Node Title</h3>
    <div className="space-y-2">
      <div className="flex justify-between text-sm">
        <span className="text-muted-foreground">Type:</span>
        <span>Entity</span>
      </div>
      <div className="flex justify-between text-sm">
        <span className="text-muted-foreground">Created:</span>
        <span>2023-04-10</span>
      </div>
      <div className="flex justify-between text-sm">
        <span className="text-muted-foreground">Relations:</span>
        <span>5</span>
      </div>
    </div>
    <div className="mt-4 flex gap-2">
      <button className="rounded-md bg-studio-background px-3 py-1 text-xs hover:bg-studio-background-accent">Edit</button>
      <button className="rounded-md bg-studio-background px-3 py-1 text-xs hover:bg-studio-background-accent">View Relations</button>
    </div>
  </div>
  ```

### System Monitoring Elements

- **Health Status Card**
  ```tsx
  <div className="rounded-lg border border-studio-border bg-studio-background-accent p-4">
    <div className="flex items-center gap-3">
      <div className="size-3 rounded-full bg-studio-success"></div>
      <h3 className="font-medium">System Health</h3>
    </div>
    <div className="mt-2 space-y-2">
      <div className="flex justify-between">
        <span className="text-sm text-muted-foreground">CPU Usage</span>
        <span className="text-sm">24%</span>
      </div>
      <div className="h-1.5 w-full rounded-full bg-studio-background">
        <div className="h-full w-1/4 rounded-full bg-studio-success"></div>
      </div>
    </div>
  </div>
  ```

- **Log Entry**
  ```tsx
  <div className="border-l-4 border-studio-info bg-studio-background-accent p-3">
    <div className="flex items-center justify-between">
      <span className="text-xs text-muted-foreground">2023-04-11 14:30:45</span>
      <span className="rounded-full bg-studio-info/20 px-2 py-0.5 text-xs text-studio-info">INFO</span>
    </div>
    <p className="mt-1 font-mono text-sm">System initialized successfully</p>
  </div>
  ```

## Animation Patterns

- **Fade In**
  ```tsx
  <motion.div
    initial={{ opacity: 0 }}
    animate={{ opacity: 1 }}
    transition={{ duration: 0.3 }}
  >
    {/* Content */}
  </motion.div>
  ```

- **Slide In**
  ```tsx
  <motion.div
    initial={{ x: -20, opacity: 0 }}
    animate={{ x: 0, opacity: 1 }}
    transition={{ duration: 0.3 }}
  >
    {/* Content */}
  </motion.div>
  ```

- **Scale**
  ```tsx
  <motion.div
    initial={{ scale: 0.95, opacity: 0 }}
    animate={{ scale: 1, opacity: 1 }}
    transition={{ duration: 0.3 }}
  >
    {/* Content */}
  </motion.div>
  ```

- **Hover Scale**
  ```tsx
  <motion.div
    whileHover={{ scale: 1.05 }}
    transition={{ type: "spring", stiffness: 400, damping: 10 }}
  >
    {/* Content */}
  </motion.div>
  ```
