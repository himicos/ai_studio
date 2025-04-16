import React from 'react';
import type { MemoryNode } from '../../lib/types'; // Adjust path if needed

interface ContextMenuProps {
  node: MemoryNode | null;
  position: { x: number; y: number } | null;
  isVisible: boolean;
  onClose: () => void;
  onAction: (actionName: string, node: MemoryNode) => void;
}

const ContextMenu: React.FC<ContextMenuProps> = ({ 
  node,
  position,
  isVisible,
  onClose,
  onAction 
}) => {
  if (!isVisible || !position || !node) {
    return null;
  }

  // Define actions based on node type
  const standardActions = [
    { name: 'Summarize', icon: '🔍', actionKey: 'summarize' },
    { name: 'Find Similar', icon: '🔁', actionKey: 'findSimilar' },
    { name: 'Copy Content', icon: '📋', actionKey: 'copyContent' },
    { name: 'Copy Node ID', icon: '🆔', actionKey: 'copyNodeId' },
    { name: 'Delete', icon: '🗑️', actionKey: 'delete', isDestructive: true },
  ];

  const tweetActions = node.type === 'tweet' ? [
    { name: 'View on X', icon: '🔗', actionKey: 'viewOnX' },
    { name: 'Generate Reply', icon: '💬', actionKey: 'generateReply' },
  ] : [];

  const redditActions = node.type === 'reddit_post' ? [
    { name: 'View on Reddit', icon: '🔗', actionKey: 'viewOnReddit' },
    { name: 'Summarize Comments', icon: '💬', actionKey: 'summarizeComments' },
  ] : [];

  const typeSpecificActions = [
    ...tweetActions,
    ...redditActions,
    // ... add other types later
  ];

  const handleItemClick = (actionKey: string) => {
    if (node) {
      onAction(actionKey, node);
    }
    onClose(); // Close after action
  };

  // Simple click outside handling (can be improved with event listener on document)
  // For now, assume parent component handles closing on background click.

  return (
    <div
      className="context-menu absolute z-[1000] bg-[#2a2a2e] text-[#e0e0e0] border border-[#444] rounded-md min-w-[180px] shadow-lg py-1.5 font-sans text-sm"
      style={{ left: `${position.x}px`, top: `${position.y}px` }}
      role="menu"
    >
      {/* Standard Actions */}
      <ul className="menu-group list-none p-0 m-0">
        {standardActions.map((action) => (
          <li
            key={action.actionKey}
            className={`flex items-center px-3 py-2 cursor-pointer whitespace-nowrap hover:bg-[#3a3a40] ${action.isDestructive ? 'text-[#ff9999] hover:bg-[#5a2a2a] hover:text-[#ffdddd]' : ''}`}
            role="menuitem"
            tabIndex={-1}
            onClick={() => handleItemClick(action.actionKey)}
            onKeyDown={(e) => e.key === 'Enter' && handleItemClick(action.actionKey)}
          >
            <span className="icon mr-2 inline-block w-4 text-center">{action.icon}</span>
            <span>{action.name}</span>
          </li>
        ))}
      </ul>

      {/* Type-Specific Actions */}
      {typeSpecificActions.length > 0 && (
        <>
          <hr className="divider border-none h-[1px] bg-[#444] my-1.5" />
          <ul className="menu-group list-none p-0 m-0">
            {typeSpecificActions.map((action) => (
              <li
                key={action.actionKey}
                className="flex items-center px-3 py-2 cursor-pointer whitespace-nowrap hover:bg-[#3a3a40]"
                role="menuitem"
                tabIndex={-1}
                onClick={() => handleItemClick(action.actionKey)}
                onKeyDown={(e) => e.key === 'Enter' && handleItemClick(action.actionKey)}
              >
                <span className="icon mr-2 inline-block w-4 text-center">{action.icon}</span>
                <span>{action.name}</span>
              </li>
            ))}
          </ul>
        </>
      )}
    </div>
  );
};

export default ContextMenu; 