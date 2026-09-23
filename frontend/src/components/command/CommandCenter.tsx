import React from 'react';
import { Settings } from 'lucide-react';
import { ChatInterface } from './ChatInterface';
import { RenderModule } from './RenderModule';
import { useResizablePanel } from '../../hooks/useResizablePanel';
import { PanelDivider } from '../layout/PanelDivider';

interface CommandCenterProps {
  chatMessages: { role: string; text: string }[];
  onSendMessage: (text: string) => void;
  isRendering: boolean;
  onRender: () => Promise<void>;
  renderCount: number;
  creativeResult?: any;
}

export const CommandCenter: React.FC<CommandCenterProps> = ({
  chatMessages,
  onSendMessage,
  isRendering,
  onRender,
  renderCount,
  creativeResult
}) => {
  const { width, dividerProps } = useResizablePanel('command', 384, 300, 640, -1);

  return (
    <aside className="relative flex flex-col border-l shrink-0 overflow-hidden surface-panel" style={{ width, borderColor: 'var(--color-border)' }}>
      <PanelDivider
        {...dividerProps}
        style={{ backgroundColor: 'var(--color-border)', position: 'absolute', top: 0, bottom: 0, left: 0, zIndex: 10 }}
      />
      <div className="h-10 flex items-center px-4 border-b" style={{ borderColor: 'var(--color-border)' }}>
        <div className="flex items-center gap-2">
          <Settings className="w-3 h-3 text-[var(--color-accent)]" />
          <span className="text-[10px] font-bold text-gray-500 uppercase tracking-widest">Command Center</span>
        </div>
      </div>

      <div className="flex-1 flex flex-col overflow-hidden">
        <div className="flex-1 flex flex-col overflow-hidden">
          <ChatInterface messages={chatMessages} onSend={onSendMessage} />
        </div>
        <RenderModule
          isRendering={isRendering}
          onRender={onRender}
          renderCount={renderCount}
          creativeResult={creativeResult}
        />
      </div >
    </aside>
  );
};