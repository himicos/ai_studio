import React, { useState } from "react";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils";
import { useWorkspace } from "@/contexts/WorkspaceContext";
import { 
  Home, Activity, Settings, Database, 
  Search, FlaskConical, BookOpen, Terminal, ChevronLeft, ChevronRight,
  Network, Server, Box, BrainCircuit, CircuitBoard, Boxes, ArrowUpDown, MessageSquare
} from "lucide-react";

interface NavItemProps {
  icon: React.ElementType;
  label: string;
  active?: boolean;
  badge?: number;
  onClick?: () => void;
}

const NavItem = ({ icon: Icon, label, active, badge, onClick }: NavItemProps) => {
  return (
    <motion.div
      className={cn(
        "flex items-center px-4 py-3 rounded-lg cursor-pointer group",
        active ? "bg-studio-primary/20" : "hover:bg-studio-background-accent"
      )}
      onClick={onClick}
      whileHover={{ x: 5 }}
      transition={{ duration: 0.2 }}
    >
      <Icon 
        className={cn(
          "size-5",
          active ? "text-studio-primary" : "text-muted-foreground group-hover:text-studio-foreground"
        )} 
      />
      <span className={cn(
        "ml-3 truncate text-sm",
        active ? "font-medium" : "font-normal"
      )}>{label}</span>
      {badge !== undefined && (
        <div className="ml-auto px-1.5 py-0.5 text-xs font-medium rounded-full bg-studio-primary text-white">
          {badge}
        </div>
      )}
    </motion.div>
  );
};

interface NavSectionProps {
  title: string;
  children: React.ReactNode;
  expanded: boolean;
}

const NavSection = ({ title, children, expanded }: NavSectionProps) => {
  return (
    <div className="mb-6">
      {expanded && (
        <h3 className="text-xs font-medium uppercase text-muted-foreground px-4 mb-2">
          {title}
        </h3>
      )}
      <div className="space-y-1">{children}</div>
    </div>
  );
};

export default function FloatingSidebar() {
  const [expanded, setExpanded] = useState(true);
  const [activeItem, setActiveItem] = useState("workspace");
  const { activeWorkspace, createPanel } = useWorkspace();

  const handleNavClick = (id: string) => {
    setActiveItem(id);
    
    // Only proceed if we have an active workspace
    if (!activeWorkspace) return;
    
    // Logic to determine if a tab should be created
    // Assuming 'workspace', 'redditagent', etc. should create tabs
    const shouldCreateTab = ["workspace", "redditagent", /* other IDs that need tabs */ ].includes(id);
    
    createPanel(activeWorkspace, id, { createTab: shouldCreateTab });
    
    // Original logic - keeping commented for reference 
    // // Only create a panel for the workspace section
    // if (id === "workspace") {
    //   createPanel(activeWorkspace, id);
    // } else {
    //   // For other sections, just navigate to their content
    //   // without creating a new tab
    //   createPanel(activeWorkspace, id, {createTab: false});
    // }
  };

  const sidebarVariants = {
    expanded: { width: 220 },
    collapsed: { width: 60 }
  };

  return (
    <motion.div
      className="panel h-full relative z-10 border-r border-studio-border"
      variants={sidebarVariants}
      initial={expanded ? "expanded" : "collapsed"}
      animate={expanded ? "expanded" : "collapsed"}
      transition={{ duration: 0.3, ease: "easeInOut" }}
    >
      <div className="h-full flex flex-col p-2">
        <div className="flex justify-between items-center py-3 px-4 mb-4">
          {expanded && (
            <motion.div 
              className="text-lg font-semibold"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
            >
              Spyderweb OS
            </motion.div>
          )}
          <motion.button 
            onClick={() => setExpanded(!expanded)}
            className="flex items-center justify-center size-6 rounded hover:bg-studio-background-accent"
            whileHover={{ scale: 1.1 }}
            whileTap={{ scale: 0.95 }}
          >
            {expanded ? <ChevronLeft size={16} /> : <ChevronRight size={16} />}
          </motion.button>
        </div>
        
        <div className="flex-1 overflow-y-auto overflow-x-hidden">
          <NavSection title="Operate" expanded={expanded}>
            <NavItem 
              icon={Home} 
              label="Workspace" 
              active={activeItem === "workspace"} 
              onClick={() => handleNavClick("workspace")} 
            />
            <NavItem 
              icon={Search} 
              label="Vector Mine" 
              active={activeItem === "vectormine"} 
              onClick={() => handleNavClick("vectormine")} 
            />
            <NavItem 
              icon={Terminal} 
              label="Terminal Brain" 
              active={activeItem === "terminalbrain"} 
              onClick={() => handleNavClick("terminalbrain")} 
              badge={3} 
            />
          </NavSection>
          
          <NavSection title="Build" expanded={expanded}>
            <NavItem 
              icon={Server} 
              label="Loadout Config" 
              active={activeItem === "loadoutconfig"} 
              onClick={() => handleNavClick("loadoutconfig")} 
            />
            <NavItem 
              icon={FlaskConical} 
              label="Prompt Forge" 
              active={activeItem === "promptforge"} 
              onClick={() => handleNavClick("promptforge")} 
            />
            <NavItem 
              icon={BookOpen} 
              label="Memory Vault" 
              active={activeItem === "memoryvault"} 
              onClick={() => handleNavClick("memoryvault")} 
            />
          </NavSection>
          
          <NavSection title="Monitor" expanded={expanded}>
            <NavItem 
              icon={Activity} 
              label="Telemetry" 
              active={activeItem === "telemetry"} 
              onClick={() => handleNavClick("telemetry")} 
            />
            <NavItem 
              icon={Boxes} 
              label="Thought Bank" 
              active={activeItem === "thoughtbank"} 
              onClick={() => handleNavClick("thoughtbank")} 
            />
            <NavItem 
              icon={BrainCircuit} 
              label="Thought Web" 
              active={activeItem === "thoughtweb"} 
              onClick={() => handleNavClick("thoughtweb")} 
            />
          </NavSection>
        </div>
        
        <div className="mt-auto border-t border-studio-border pt-2">
          <NavItem 
            icon={Settings} 
            label="Settings" 
            active={activeItem === "settings"} 
            onClick={() => handleNavClick("settings")} 
          />
        </div>
      </div>
    </motion.div>
  );
}
