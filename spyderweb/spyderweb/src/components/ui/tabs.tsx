
import * as React from "react"
import * as TabsPrimitive from "@radix-ui/react-tabs"

import { cn } from "@/lib/utils"

const Tabs = TabsPrimitive.Root

const TabsList = React.forwardRef<
  React.ElementRef<typeof TabsPrimitive.List>,
  React.ComponentPropsWithoutRef<typeof TabsPrimitive.List>
>(({ className, ...props }, ref) => (
  <TabsPrimitive.List
    ref={ref}
    className={cn(
      "inline-flex h-10 items-center justify-center rounded-md bg-muted p-1 text-muted-foreground",
      className
    )}
    {...props}
  />
))
TabsList.displayName = TabsPrimitive.List.displayName

const TabsTrigger = React.forwardRef<
  React.ElementRef<typeof TabsPrimitive.Trigger>,
  React.ComponentPropsWithoutRef<typeof TabsPrimitive.Trigger> & {
    showCloseButton?: boolean;
    showPinButton?: boolean;
    isPinned?: boolean;
    onClose?: (e: React.MouseEvent) => void;
    onTogglePin?: (e: React.MouseEvent) => void;
  }
>(({ className, children, showCloseButton, showPinButton, isPinned, onClose, onTogglePin, ...props }, ref) => (
  <TabsPrimitive.Trigger
    ref={ref}
    className={cn(
      "inline-flex items-center justify-center whitespace-nowrap rounded-sm px-3 py-1.5 text-sm font-medium ring-offset-background transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 data-[state=active]:bg-background data-[state=active]:text-foreground data-[state=active]:shadow-sm",
      isPinned && "order-first",
      className
    )}
    {...props}
  >
    <div className="flex items-center gap-2">
      {children}
      
      {(showCloseButton || showPinButton) && (
        <div className="flex items-center ml-2 space-x-1">
          {showPinButton && (
            <button
              className="p-1 rounded-full hover:bg-background/20 transition-colors"
              onClick={(e) => {
                e.preventDefault();
                e.stopPropagation();
                onTogglePin?.(e);
              }}
            >
              {isPinned ? (
                <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-primary">
                  <line x1="2" y1="2" x2="22" y2="22"></line>
                  <path d="M12 17v5"></path>
                  <path d="M9 9v1.76a2 2 0 0 1-1.11 1.79l-1.78.9A2 2 0 0 0 5 15.24V17h12"></path>
                  <path d="M15 7h5a2 2 0 0 0 0-4h-2.09a5.58 5.58 0 0 0-1.64-1.36A5.52 5.52 0 0 0 12 1a5.52 5.52 0 0 0-4.27.64A5.59 5.59 0 0 0 6.09 3H4a2 2 0 0 0 0 4h5"></path>
                </svg>
              ) : (
                <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M12 17v5"></path>
                  <path d="M5 17h14"></path>
                  <path d="M15 7h5a2 2 0 0 0 0-4h-2.09a5.58 5.58 0 0 0-1.64-1.36A5.52 5.52 0 0 0 12 1a5.52 5.52 0 0 0-4.27.64A5.59 5.59 0 0 0 6.09 3H4a2 2 0 0 0 0 4h5"></path>
                </svg>
              )}
            </button>
          )}
          
          {showCloseButton && !isPinned && (
            <button
              className="p-1 rounded-full hover:bg-background/20 transition-colors"
              onClick={(e) => {
                e.preventDefault();
                e.stopPropagation();
                onClose?.(e);
              }}
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <line x1="18" y1="6" x2="6" y2="18"></line>
                <line x1="6" y1="6" x2="18" y2="18"></line>
              </svg>
            </button>
          )}
        </div>
      )}
    </div>
  </TabsPrimitive.Trigger>
))
TabsTrigger.displayName = TabsPrimitive.Trigger.displayName

const TabsContent = React.forwardRef<
  React.ElementRef<typeof TabsPrimitive.Content>,
  React.ComponentPropsWithoutRef<typeof TabsPrimitive.Content>
>(({ className, ...props }, ref) => (
  <TabsPrimitive.Content
    ref={ref}
    className={cn(
      "mt-2 ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
      className
    )}
    {...props}
  />
))
TabsContent.displayName = TabsPrimitive.Content.displayName

export { Tabs, TabsList, TabsTrigger, TabsContent }
