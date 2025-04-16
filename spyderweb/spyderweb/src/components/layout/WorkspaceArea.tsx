
import React, { useState } from "react";
import { motion } from "framer-motion";
import { useWorkspace } from "@/contexts/WorkspaceContext";
import { PlusCircle, X, Pin, PinOff } from "lucide-react";
import EmptyWorkspace from "../workspace/EmptyWorkspace";
import PanelContainer from "../workspace/PanelContainer";
import CreatePanelModal from "../workspace/CreatePanelModal";

export default function WorkspaceArea() {
  const { activeWorkspace, workspaces, panels, setActivePanel, closePanel, togglePinPanel } = useWorkspace();
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  
  // If no workspace is active, or there are no workspaces
  if (!activeWorkspace || !workspaces[activeWorkspace]) {
    return <EmptyWorkspace />;
  }
  
  const currentWorkspace = workspaces[activeWorkspace];
  const activePanelId = currentWorkspace.active;
  
  // Check if the active panel is a tabbed panel or a section panel
  const isActivePanelTabbed = activePanelId && currentWorkspace.panels.includes(activePanelId);
  
  const handleOpenCreateModal = () => {
    setIsCreateModalOpen(true);
  };
  
  const handleCloseTab = (e: React.MouseEvent, panelId: string) => {
    e.stopPropagation(); // Prevent tab selection
    closePanel(activeWorkspace, panelId);
  };
  
  const handleTogglePin = (e: React.MouseEvent, panelId: string) => {
    e.stopPropagation(); // Prevent tab selection
    togglePinPanel(panelId);
  };
  
  // Sort panels to have pinned panels first
  const sortedPanels = [...currentWorkspace.panels].sort((a, b) => {
    const panelA = panels[a];
    const panelB = panels[b];
    
    if (panelA?.isPinned && !panelB?.isPinned) return -1;
    if (!panelA?.isPinned && panelB?.isPinned) return 1;
    return 0;
  });
  
  return (
    <div className="flex-1 flex flex-col overflow-hidden p-4">
      {/* Tabs Bar - Only show if we have tabs */}
      <div className="flex items-center h-10 mb-2">
        <div className="flex overflow-x-auto no-scrollbar">
          {sortedPanels.map((panelId) => {
            const panel = panels[panelId];
            const isActive = activePanelId === panelId;
            const isPinned = panel?.isPinned;
            
            if (!panel) return null;
            
            return (
              <motion.div
                key={panelId}
                className={`flex items-center px-4 py-2 mr-1 rounded-t-md ${
                  isActive 
                    ? "bg-studio-background-accent" 
                    : "bg-transparent hover:bg-studio-background-accent/50"
                }`}
                whileHover={{ y: -2 }}
                whileTap={{ y: 0 }}
                transition={{ duration: 0.2 }}
              >
                <button
                  className="flex items-center gap-2"
                  onClick={() => setActivePanel(activeWorkspace, panelId)}
                >
                  <span className={`text-sm ${isActive ? "font-medium" : "font-normal text-muted-foreground"}`}>
                    {panel.title}
                  </span>
                </button>
                
                <div className="flex items-center ml-2 space-x-1">
                  <motion.button
                    className="p-1 rounded-md hover:bg-studio-background transition-colors"
                    whileHover={{ scale: 1.1 }}
                    whileTap={{ scale: 0.9 }}
                    onClick={(e) => handleTogglePin(e, panelId)}
                    title={isPinned ? "Unpin tab" : "Pin tab"}
                  >
                    {isPinned ? (
                      <PinOff className="size-3 text-studio-primary" />
                    ) : (
                      <Pin className="size-3 text-muted-foreground" />
                    )}
                  </motion.button>
                  
                  <motion.button
                    className={`p-1 rounded-md hover:bg-studio-background transition-colors ${isPinned ? 'opacity-50 cursor-not-allowed' : ''}`}
                    whileHover={{ scale: isPinned ? 1 : 1.1 }}
                    whileTap={{ scale: isPinned ? 1 : 0.9 }}
                    onClick={(e) => handleCloseTab(e, panelId)}
                    disabled={isPinned}
                    title={isPinned ? "Unpin to close" : "Close tab"}
                  >
                    <X className="size-3 text-muted-foreground" />
                  </motion.button>
                </div>
              </motion.div>
            );
          })}
        </div>
        
        <motion.button
          className="ml-2 p-1 rounded-md hover:bg-studio-background-accent"
          whileHover={{ scale: 1.1 }}
          whileTap={{ scale: 0.95 }}
          onClick={handleOpenCreateModal}
        >
          <PlusCircle className="size-5" />
        </motion.button>
      </div>
      
      {/* Main Content Area */}
      <div className="flex-1 overflow-hidden panel">
        {activePanelId ? (
          <PanelContainer panelId={activePanelId} />
        ) : (
          <motion.div 
            className="h-full flex flex-col items-center justify-center glass rounded-lg p-8"
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.3 }}
          >
            <div className="size-16 rounded-full bg-studio-background-accent flex items-center justify-center mb-4">
              <PlusCircle className="size-8 text-studio-primary" />
            </div>
            <h3 className="text-xl font-medium mb-2">No Active Panel</h3>
            <p className="text-center text-muted-foreground mb-6 max-w-md">
              Create a new panel or select an existing one from the tabs above to get started.
            </p>
            <motion.button
              className="flex items-center gap-2 rounded-md bg-studio-primary px-4 py-2 text-white hover:bg-studio-primary/90 transition-colors"
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={handleOpenCreateModal}
            >
              <PlusCircle className="size-4" />
              <span>Create New Panel</span>
            </motion.button>
          </motion.div>
        )}
      </div>
      
      {/* Create Panel Modal */}
      <CreatePanelModal 
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        workspaceId={activeWorkspace}
      />
    </div>
  );
}
