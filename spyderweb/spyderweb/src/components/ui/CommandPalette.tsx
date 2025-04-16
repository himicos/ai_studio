
import React, { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Search, X } from "lucide-react";
import { useApp } from "@/contexts/AppContext";

type CommandItem = {
  id: string;
  title: string;
  keywords: string[];
  category: string;
  action: () => void;
};

// Example commands
const commands: CommandItem[] = [
  {
    id: "new-workspace",
    title: "Create New Workspace",
    keywords: ["create", "workspace", "new", "project"],
    category: "Workspace",
    action: () => console.log("Create new workspace"),
  },
  {
    id: "new-panel",
    title: "Add New Panel",
    keywords: ["add", "panel", "new", "component"],
    category: "Panels",
    action: () => console.log("Add new panel"),
  },
  {
    id: "toggle-theme",
    title: "Toggle Dark/Light Theme",
    keywords: ["theme", "dark", "light", "toggle", "mode"],
    category: "Appearance",
    action: () => console.log("Toggle theme"),
  },
  {
    id: "system-status",
    title: "Check System Status",
    keywords: ["system", "status", "health", "check"],
    category: "System",
    action: () => console.log("Check system status"),
  },
];

export default function CommandPalette() {
  const { toggleCommandPalette } = useApp();
  const [search, setSearch] = useState("");
  const [filteredCommands, setFilteredCommands] = useState<CommandItem[]>(commands);
  const [selectedIndex, setSelectedIndex] = useState(0);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        toggleCommandPalette();
      } else if (e.key === "ArrowDown") {
        e.preventDefault();
        setSelectedIndex((prev) => 
          prev < filteredCommands.length - 1 ? prev + 1 : prev
        );
      } else if (e.key === "ArrowUp") {
        e.preventDefault();
        setSelectedIndex((prev) => (prev > 0 ? prev - 1 : prev));
      } else if (e.key === "Enter" && filteredCommands[selectedIndex]) {
        e.preventDefault();
        executeCommand(filteredCommands[selectedIndex]);
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [filteredCommands, selectedIndex, toggleCommandPalette]);

  useEffect(() => {
    if (search.trim() === "") {
      setFilteredCommands(commands);
    } else {
      const filtered = commands.filter((command) => {
        const searchLower = search.toLowerCase();
        return (
          command.title.toLowerCase().includes(searchLower) ||
          command.keywords.some((k) => k.toLowerCase().includes(searchLower)) ||
          command.category.toLowerCase().includes(searchLower)
        );
      });
      setFilteredCommands(filtered);
    }
    setSelectedIndex(0);
  }, [search]);

  const executeCommand = (command: CommandItem) => {
    command.action();
    toggleCommandPalette();
  };

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-start justify-center pt-[15vh]">
      <motion.div
        className="w-full max-w-xl bg-studio-background-accent shadow-xl rounded-lg overflow-hidden border border-studio-border"
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -20 }}
      >
        <div className="flex items-center p-4 border-b border-studio-border">
          <Search className="size-5 text-muted-foreground mr-2" />
          <input
            type="text"
            placeholder="Search commands..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="flex-1 bg-transparent border-none focus:outline-none"
            autoFocus
          />
          <button
            onClick={toggleCommandPalette}
            className="size-7 flex items-center justify-center rounded-md hover:bg-studio-border"
          >
            <X className="size-4" />
          </button>
        </div>

        <div className="max-h-[70vh] overflow-y-auto">
          {filteredCommands.length === 0 ? (
            <div className="p-4 text-center text-muted-foreground">
              No commands found
            </div>
          ) : (
            <div className="p-2">
              {filteredCommands.map((command, index) => (
                <motion.div
                  key={command.id}
                  className={`p-3 rounded-md cursor-pointer ${
                    index === selectedIndex
                      ? "bg-studio-primary/20"
                      : "hover:bg-studio-background"
                  }`}
                  onClick={() => executeCommand(command)}
                  initial={{ opacity: 0, y: 5 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.05 }}
                >
                  <div className="flex justify-between items-center">
                    <div className="font-medium">{command.title}</div>
                    <div className="text-xs text-muted-foreground">
                      {command.category}
                    </div>
                  </div>
                </motion.div>
              ))}
            </div>
          )}
        </div>
      </motion.div>
    </div>
  );
}
