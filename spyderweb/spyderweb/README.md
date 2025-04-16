
# AI Studio OS

## Overview

AI Studio OS is a modular and futuristic frontend for AI operations, built with React, TypeScript, Tailwind CSS, and Framer Motion. The system provides a unified interface for managing AI workflows, prompts, analytics, and system monitoring with a focus on progressive disclosure and embedded intelligence.

## Key Features

- **Modular Design**: Every component is decoupled, allowing for easy extension and customization
- **Progressive Disclosure UX**: Simple surfaces that reveal depth and complexity when needed
- **Embedded Intelligence**: Every panel/component supports GPT-wired functionality
- **Dynamic Panel Loading**: Asynchronous panel loading through a registry system
- **Workspace Router**: Supports tabbed views, docked tools, and slideouts
- **Persistent Context**: Maintains state across workspace sessions
- **WebSocket Layer**: Real-time updates and notifications
- **Command Palette & Shortcuts**: Global command access and keyboard navigation
- **Theme & State Management**: Comprehensive dark/light mode and global state

## Tech Stack

- **Frontend**: React, TypeScript, Tailwind CSS, Framer Motion
- **UI Components**: shadcn/ui with custom component registry
- **State Management**: React Context API
- **Icons**: Lucide React
- **Animation**: Framer Motion
- **Styling**: Tailwind CSS

## Getting Started

1. Install dependencies:

```bash
npm install
```

2. Start the development server:

```bash
npm run dev
```

3. Access the application at: http://localhost:5173

## Component Structure

```
src/
├── App.tsx                 # Main application entry point
├── components/
│   ├── layout/             # Core layout components
│   │   ├── AppShell.tsx    # Main application shell
│   │   ├── FloatingSidebar.tsx # Left sidebar navigation
│   │   ├── HeaderBar.tsx   # Top navigation bar
│   │   └── WorkspaceArea.tsx # Main content area
│   ├── panels/             # Content panels
│   │   └── WelcomePanel.tsx # Initial welcome panel
│   ├── ui/                 # Reusable UI components
│   │   └── ...
│   └── workspace/          # Workspace-specific components
│       ├── EmptyWorkspace.tsx # Empty state for workspaces
│       └── PanelContainer.tsx # Container for panels
├── contexts/               # React context providers
│   ├── AppContext.tsx      # Application-level state
│   ├── ThemeContext.tsx    # Theme management
│   └── WorkspaceContext.tsx # Workspace state management
├── hooks/                  # Custom React hooks
│   ├── use-mobile.tsx      # Mobile detection hook
│   └── use-toast.ts        # Toast notification hook
└── lib/                    # Utility functions
    └── utils.ts            # Common utilities
```

## Future Enhancements

- Integration with backend services (prompt router, action executor, etc.)
- Advanced analytics dashboard
- Real-time data visualization
- Memory graph for knowledge mapping
- Proxy management systems
- Complete workspace persistence

## License

MIT License
