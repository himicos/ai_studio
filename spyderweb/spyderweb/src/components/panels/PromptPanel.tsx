
import React, { useState } from "react";
import { motion } from "framer-motion";
import { PanelId } from "@/contexts/WorkspaceContext";
import { Pencil, Copy, CheckCircle, X } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { ResizablePanelGroup, ResizablePanel, ResizableHandle } from "@/components/ui/resizable";
import { ScrollArea } from "@/components/ui/scroll-area";

interface PromptPanelProps {
  id: PanelId;
}

export default function PromptPanel({ id }: PromptPanelProps) {
  const [input, setInput] = useState("");
  const [output, setOutput] = useState("");
  const [copying, setCopying] = useState(false);

  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value);
  };

  const handleSubmit = () => {
    // This is where we would handle API calls to get responses
    // For now, we'll just echo the input as output
    setOutput(input);
  };

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(output);
      setCopying(true);
      setTimeout(() => setCopying(false), 2000);
    } catch (err) {
      console.error("Failed to copy: ", err);
    }
  };

  const handleClear = () => {
    setInput("");
    setOutput("");
  };

  return (
    <motion.div 
      className="flex flex-col h-full panel"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.3 }}
    >
      {/* Panel Header */}
      <div className="flex items-center justify-between p-4 border-b border-studio-border">
        <div className="flex items-center gap-2">
          <div className="size-8 rounded-md bg-studio-primary/10 flex items-center justify-center">
            <Pencil className="size-4 text-studio-primary" />
          </div>
          <h2 className="text-xl font-bold">Prompt Laboratory</h2>
        </div>
        <div className="flex items-center gap-2">
          <motion.button
            className="rounded-full p-1.5 border border-studio-border hover:bg-studio-background-accent"
            whileHover={{ scale: 1.1 }}
            whileTap={{ scale: 0.95 }}
          >
            <X className="size-4" />
          </motion.button>
        </div>
      </div>
      
      {/* Panel Body */}
      <div className="flex-1 p-4 overflow-auto">
        <ResizablePanelGroup 
          direction="horizontal" 
          className="h-full rounded-lg border border-studio-border bg-studio-background-accent"
        >
          {/* Input Panel */}
          <ResizablePanel defaultSize={50} minSize={30}>
            <div className="flex flex-col h-full">
              <div className="p-4 border-b border-studio-border">
                <h3 className="text-lg font-medium mb-2">Input</h3>
                <p className="text-sm text-muted-foreground">Enter your prompt below</p>
              </div>
              <ScrollArea className="flex-1">
                <div className="p-4">
                  <Textarea 
                    className="min-h-[200px] h-full glass"
                    placeholder="Type your prompt here..."
                    value={input}
                    onChange={handleInputChange}
                  />
                </div>
              </ScrollArea>
              <div className="flex justify-end gap-2 p-4 border-t border-studio-border">
                <Button variant="outline" onClick={handleClear}>
                  Clear
                </Button>
                <Button onClick={handleSubmit}>
                  Submit
                </Button>
              </div>
            </div>
          </ResizablePanel>
          
          {/* Resize Handle */}
          <ResizableHandle withHandle />
          
          {/* Output Panel */}
          <ResizablePanel defaultSize={50} minSize={30}>
            <div className="flex flex-col h-full">
              <div className="flex items-center justify-between p-4 border-b border-studio-border">
                <div>
                  <h3 className="text-lg font-medium mb-2">Output</h3>
                  <p className="text-sm text-muted-foreground">Response will appear here</p>
                </div>
                <motion.button
                  className="rounded-full p-2 hover:bg-studio-background-accent"
                  whileHover={{ scale: 1.1 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={handleCopy}
                >
                  {copying ? (
                    <CheckCircle className="size-5 text-studio-success" />
                  ) : (
                    <Copy className="size-5" />
                  )}
                </motion.button>
              </div>
              <ScrollArea className="flex-1">
                <div className="p-4">
                  {output ? (
                    <Card className="h-full p-4 bg-studio-background border-studio-border glass">
                      <pre className="whitespace-pre-wrap font-mono text-sm">{output}</pre>
                    </Card>
                  ) : (
                    <div className="flex flex-col items-center justify-center h-full">
                      <div className="w-3/4 h-40 rounded-md border border-dashed border-studio-border bg-studio-background/40 flex flex-col items-center justify-center p-6 glass">
                        <p className="text-muted-foreground mb-2">No output yet</p>
                        <p className="text-sm text-muted-foreground text-center">Submit a prompt to see results here</p>
                      </div>
                    </div>
                  )}
                </div>
              </ScrollArea>
            </div>
          </ResizablePanel>
        </ResizablePanelGroup>
      </div>
    </motion.div>
  );
}
