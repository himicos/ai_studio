import React, { createContext, useContext, useState, useTransition, ReactNode, lazy, Suspense } from "react";
import { v4 as uuidv4 } from 'uuid';

// Re-introduce direct import
import { TwitterAgentPanel } from "@/components/panels/agents/TwitterAgentPanel"; 

// Basic panels
const WelcomePanel = lazy(() => import("@/components/panels/WelcomePanel"));
const PromptPanel = lazy(() => import("@/components/panels/PromptPanel"));
const CustomPanel = lazy(() => import("@/components/panels/CustomPanel"));
const SettingsPanel = lazy(() => import("@/components/panels/sections/SettingsPanel"));
const MemoryPanel = lazy(() => import("@/components/panels/MemoryPanel"));

// Original panels (renamed)
const AnalyticsPanel = lazy(() => import("@/components/panels/AnalyticsPanel"));
const StoragePanel = lazy(() => import("@/components/panels/StoragePanel"));

// Agent panels
// Use direct import for RedditAgentPanel for testing
import { RedditAgentPanel } from "@/components/panels/agents/reddit/RedditAgentPanel"; 
// const RedditAgentPanel = lazy(() => import("@/components/panels/agents/reddit/RedditAgentPanel"));

// Lazy load for TwitterAgentPanel remains commented out
// Re-introduce direct import for TwitterAgentPanel if lazy loading causes issues
// import { TwitterAgentPanel } from "@/components/panels/agents/TwitterAgentPanel";
const BuilderAgentPanel = lazy(() => import("@/components/panels/agents/BuilderAgentPanel"));
const MarketingAgentPanel = lazy(() => import("@/components/panels/agents/MarketingAgentPanel"));

// New section panels (to be created)
const VectorMinePanel = lazy(() => import("@/components/panels/sections/VectorMinePanel"));
const TerminalBrainPanel = lazy(() => import("@/components/panels/sections/TerminalBrainPanel"));
const LoadoutConfigPanel = lazy(() => import("@/components/panels/sections/LoadoutConfigPanel"));
const PromptForgePanel = lazy(() => import("@/components/panels/sections/PromptForgePanel"));
const MemoryVaultPanel = lazy(() => import("@/components/panels/sections/MemoryVaultPanel"));
const TelemetryPanel = lazy(() => import("@/components/panels/sections/TelemetryPanel"));
const ThoughtBankPanel = lazy(() => import("@/components/panels/sections/ThoughtBankPanel"));
const ThoughtWebPanel = lazy(() => import("@/components/panels/sections/ThoughtWebPanel"));

export type WorkspaceId = string;
export type PanelId = string;

interface Panel {
  id: PanelId;
  title: string;
  component: React.ComponentType<any>;
  isPinned?: boolean;
  isSection?: boolean;
}

interface Workspace {
  id: WorkspaceId;
  name: string;
  panels: PanelId[];
  active: PanelId | null;
  context: Record<string, any>;
  currentSectionPanel?: PanelId | null;
}

interface PanelOptions {
  createTab?: boolean;
}

interface WorkspaceContextType {
  activeWorkspace: WorkspaceId | null;
  workspaces: Record<WorkspaceId, Workspace>;
  panels: Record<PanelId, Panel>;
  createWorkspace: (name: string) => WorkspaceId;
  switchWorkspace: (id: WorkspaceId) => void;
  addPanel: (workspaceId: WorkspaceId, panelId: PanelId) => void;
  removePanel: (workspaceId: WorkspaceId, panelId: PanelId) => void;
  setActivePanel: (workspaceId: WorkspaceId, panelId: PanelId) => void;
  setWorkspaceContext: (workspaceId: WorkspaceId, context: Record<string, any>) => void;
  registerPanel: (panel: Panel) => void;
  createPanel: (workspaceId: WorkspaceId, panelType: string, options?: PanelOptions) => void;
  togglePinPanel: (panelId: PanelId) => void;
  closePanel: (workspaceId: WorkspaceId, panelId: PanelId) => void;
}

const WorkspaceContext = createContext<WorkspaceContextType | undefined>(undefined);

export function WorkspaceProvider({ children }: { children: React.ReactNode }) {
  const [activeWorkspace, setActiveWorkspace] = useState<WorkspaceId | null>(null);
  const [workspaces, setWorkspaces] = useState<Record<WorkspaceId, Workspace>>({});
  const [panels, setPanels] = useState<Record<PanelId, Panel>>({});
  const [isPending, startTransition] = useTransition();

  const createWorkspace = (name: string) => {
    const id = `workspace-${Date.now()}`;
    
    startTransition(() => {
      setWorkspaces((prev) => ({
        ...prev,
        [id]: { id, name, panels: [], active: null, context: {} },
      }));
      if (!activeWorkspace) {
        setActiveWorkspace(id);
      }
    });
    
    return id;
  };

  const switchWorkspace = (id: WorkspaceId) => {
    startTransition(() => {
      setActiveWorkspace(id);
    });
  };

  const addPanel = (workspaceId: WorkspaceId, panelId: PanelId) => {
    startTransition(() => {
      setWorkspaces((prev) => {
        if (!prev[workspaceId]) return prev;
        
        return {
          ...prev,
          [workspaceId]: {
            ...prev[workspaceId],
            panels: [...prev[workspaceId].panels, panelId],
            active: prev[workspaceId].active || panelId,
          },
        };
      });
    });
  };

  const removePanel = (workspaceId: WorkspaceId, panelId: PanelId) => {
    startTransition(() => {
      setWorkspaces((prev) => {
        if (!prev[workspaceId]) return prev;
        
        const updatedPanels = prev[workspaceId].panels.filter(id => id !== panelId);
        const active = prev[workspaceId].active === panelId
          ? (updatedPanels.length > 0 ? updatedPanels[0] : null)
          : prev[workspaceId].active;
        
        return {
          ...prev,
          [workspaceId]: {
            ...prev[workspaceId],
            panels: updatedPanels,
            active,
          },
        };
      });
    });
  };

  const setActivePanel = (workspaceId: WorkspaceId, panelId: PanelId) => {
    startTransition(() => {
      setWorkspaces((prev) => {
        if (!prev[workspaceId]) return prev;
        
        return {
          ...prev,
          [workspaceId]: {
            ...prev[workspaceId],
            active: panelId,
          },
        };
      });
    });
  };

  const setWorkspaceContext = (workspaceId: WorkspaceId, context: Record<string, any>) => {
    startTransition(() => {
      setWorkspaces((prev) => {
        if (!prev[workspaceId]) return prev;
        
        return {
          ...prev,
          [workspaceId]: {
            ...prev[workspaceId],
            context: { ...prev[workspaceId].context, ...context },
          },
        };
      });
    });
  };

  const registerPanel = (panel: Panel) => {
    startTransition(() => {
      setPanels((prev) => ({
        ...prev,
        [panel.id]: panel,
      }));
    });
  };
  
  const createPanel = (workspaceId: WorkspaceId, panelType: string, options: PanelOptions = { createTab: true }) => {
    console.log(`[WorkspaceContext] createPanel called with panelType: "${panelType}" for workspace: ${workspaceId}`);
    
    const panelId = `panel-${panelType}-${Date.now()}`;
    
    let newPanel: Panel | undefined;
    let isSection = false;
    
    switch (panelType) {
      case 'prompt':
        newPanel = {
          id: panelId,
          title: "Prompt Laboratory",
          component: PromptPanel
        };
        break;
      case 'analytics': 
        newPanel = {
          id: panelId,
          title: "Analytics Dashboard",
          component: AnalyticsPanel
        };
        break;
      case 'memory':
        newPanel = {
          id: panelId,
          title: "Memory Graph",
          component: MemoryPanel
        };
        break;
      case 'storage':
        newPanel = {
          id: panelId,
          title: "Storage",
          component: StoragePanel
        };
        break;
      case 'redditagent':
        newPanel = {
          id: panelId,
          title: "Reddit Agent",
          component: RedditAgentPanel
        };
        break;
      case 'twitter':
        newPanel = {
          id: panelId,
          title: "Twitter Tracker Agent",
          component: TwitterAgentPanel
        };
        break;
      case 'builder':
        newPanel = {
          id: panelId,
          title: "Builder Agent",
          component: BuilderAgentPanel
        };
        break;
      case 'marketing':
        newPanel = {
          id: panelId,
          title: "Marketing Agent",
          component: MarketingAgentPanel
        };
        break;
      case 'vectormine':
        newPanel = {
          id: panelId,
          title: "Vector Mine",
          component: VectorMinePanel,
          isSection: true
        };
        isSection = true;
        break;
      case 'terminalbrain':
        newPanel = {
          id: panelId,
          title: "Terminal Brain",
          component: TerminalBrainPanel,
          isSection: true
        };
        isSection = true;
        break;
      case 'loadoutconfig':
        newPanel = {
          id: panelId,
          title: "Loadout Config",
          component: LoadoutConfigPanel,
          isSection: true
        };
        isSection = true;
        break;
      case 'promptforge':
        newPanel = {
          id: panelId,
          title: "Prompt Forge",
          component: PromptForgePanel,
          isSection: true
        };
        isSection = true;
        break;
      case 'memoryvault':
        newPanel = {
          id: panelId,
          title: "Memory Vault",
          component: MemoryVaultPanel,
          isSection: true
        };
        isSection = true;
        break;
      case 'telemetry':
        newPanel = {
          id: panelId,
          title: "Telemetry",
          component: TelemetryPanel,
          isSection: true
        };
        isSection = true;
        break;
      case 'thoughtbank':
        newPanel = {
          id: panelId,
          title: "Thought Bank",
          component: ThoughtBankPanel,
          isSection: true
        };
        isSection = true;
        break;
      case 'thoughtweb':
        newPanel = {
          id: panelId,
          title: "Thought Web",
          component: ThoughtWebPanel,
          isSection: true
        };
        isSection = true;
        break;
      case 'settings':
        newPanel = {
          id: panelId,
          title: "Settings",
          component: SettingsPanel,
          isSection: true
        };
        isSection = true;
        break;
      case 'workspace':
      case 'custom':
      default:
        newPanel = {
          id: panelId,
          title: panelType === 'workspace' ? "Workspace" : "New Panel",
          component: panelType === 'workspace' ? WelcomePanel : CustomPanel
        };
    }
    
    if (newPanel) {
      startTransition(() => {
        registerPanel(newPanel as Panel);
        
        setWorkspaces(prev => {
          if (!prev[workspaceId]) return prev;
          
          const workspace = prev[workspaceId];
          
          if (isSection && !options.createTab) {
            return {
              ...prev,
              [workspaceId]: {
                ...workspace,
                currentSectionPanel: panelId,
                active: panelId
              }
            };
          } else {
            return {
              ...prev,
              [workspaceId]: {
                ...workspace,
                panels: [...workspace.panels, panelId],
                active: panelId
              }
            };
          }
        });
      });
      return panelId;
    } else {
      console.error(`Panel definition failed for type: ${panelType}`);
      return null;
    }
  };

  const togglePinPanel = (panelId: PanelId) => {
    startTransition(() => {
      setPanels((prev) => {
        if (!prev[panelId]) return prev;
        
        return {
          ...prev,
          [panelId]: {
            ...prev[panelId],
            isPinned: !prev[panelId].isPinned
          }
        };
      });
    });
  };
  
  const closePanel = (workspaceId: WorkspaceId, panelId: PanelId) => {
    if (panels[panelId]?.isPinned) return;
    
    removePanel(workspaceId, panelId);
  };

  return (
    <WorkspaceContext.Provider
      value={{
        activeWorkspace,
        workspaces,
        panels,
        createWorkspace,
        switchWorkspace,
        addPanel,
        removePanel,
        setActivePanel,
        setWorkspaceContext,
        registerPanel,
        createPanel,
        togglePinPanel,
        closePanel,
      }}
    >
      {children}
    </WorkspaceContext.Provider>
  );
}

export const useWorkspace = () => {
  const context = useContext(WorkspaceContext);
  if (!context) {
    throw new Error("useWorkspace must be used within a WorkspaceProvider");
  }
  return context;
};
