import React from "react";
import { motion } from "framer-motion";
import { X, Pencil, Layout, BarChart4, Network, MessageSquare, Twitter, Github, UserPlus } from "lucide-react";
import { useWorkspace } from "@/contexts/WorkspaceContext";
import { 
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle 
} from "@/components/ui/card";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";

interface CreatePanelModalProps {
  isOpen: boolean;
  onClose: () => void;
  workspaceId: string;
}

const panelTypes = [
  {
    id: "prompt",
    title: "Prompt Laboratory",
    description: "Create and test prompts with real-time feedback",
    icon: Pencil,
    color: "text-studio-primary",
    bgColor: "bg-studio-primary/10",
  },
  {
    id: "analytics",
    title: "Analytics Dashboard",
    description: "Visualize data with charts and metrics",
    icon: BarChart4,
    color: "text-studio-secondary",
    bgColor: "bg-studio-secondary/10",
  },
  {
    id: "memory",
    title: "Memory Graph",
    description: "Create and visualize knowledge graphs",
    icon: Network,
    color: "text-studio-accent",
    bgColor: "bg-studio-accent/10",
  },
  {
    id: "redditagent",
    title: "Reddit Research Agent",
    description: "Analyze and extract insights from Reddit data",
    icon: MessageSquare,
    color: "text-studio-error",
    bgColor: "bg-studio-error/10",
  },
  {
    id: "twitter",
    title: "Twitter Tracker Agent",
    description: "Track users, view real-time feeds, and analyze engagement",
    icon: Twitter,
    color: "text-studio-info",
    bgColor: "bg-studio-info/10",
  },
  {
    id: "builder",
    title: "Builder Agent",
    description: "Automate development workflows and code generation",
    icon: Github,
    color: "text-studio-success",
    bgColor: "bg-studio-success/10",
  },
  {
    id: "marketing",
    title: "Marketing Agent",
    description: "AI-powered content creation and campaign management",
    icon: UserPlus,
    color: "text-studio-warning",
    bgColor: "bg-studio-warning/10",
  },
  {
    id: "custom",
    title: "Custom Panel",
    description: "Create a blank panel with custom content",
    icon: Layout,
    color: "text-studio-info",
    bgColor: "bg-studio-info/10",
  },
];

export default function CreatePanelModal({ isOpen, onClose, workspaceId }: CreatePanelModalProps) {
  const { createPanel } = useWorkspace();
  
  if (!isOpen) return null;

  const handleCreatePanel = (typeId: string) => {
    createPanel(workspaceId, typeId);
    onClose();
  };
  
  return (
    <motion.div
      className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      onClick={onClose}
    >
      <motion.div 
        className="w-full max-w-3xl"
        initial={{ scale: 0.95, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        exit={{ scale: 0.95, opacity: 0 }}
        transition={{ duration: 0.2 }}
        onClick={(e) => e.stopPropagation()}
      >
        <Card className="glass border-studio-border">
          <CardHeader className="border-b border-studio-border">
            <div className="flex items-center justify-between">
              <CardTitle>Create New Panel</CardTitle>
              <button 
                onClick={onClose}
                className="rounded-full p-1 hover:bg-studio-background-accent transition-colors"
              >
                <X className="size-5" />
              </button>
            </div>
            <CardDescription>
              Select a panel type to add to your workspace
            </CardDescription>
          </CardHeader>
          <CardContent className="pt-6">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {panelTypes.map((type) => (
                <motion.button
                  key={type.id}
                  className="flex items-start gap-4 p-4 rounded-lg border border-studio-border hover:bg-studio-background-accent text-left transition-colors"
                  onClick={() => handleCreatePanel(type.id)}
                  whileHover={{ y: -2 }}
                  whileTap={{ y: 0 }}
                >
                  <div className={`size-12 rounded-lg ${type.bgColor} flex items-center justify-center`}>
                    <type.icon className={`size-6 ${type.color}`} />
                  </div>
                  <div className="flex-1">
                    <h3 className="font-medium mb-1">{type.title}</h3>
                    <p className="text-sm text-muted-foreground">{type.description}</p>
                  </div>
                </motion.button>
              ))}
            </div>
          </CardContent>
          <CardFooter className="border-t border-studio-border pt-4">
            <p className="text-sm text-muted-foreground">
              You can customize the panel after creation
            </p>
          </CardFooter>
        </Card>
      </motion.div>
    </motion.div>
  );
}
