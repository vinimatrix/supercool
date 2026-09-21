import React from 'react';
import { Header } from './Header';
import { Sidebar } from './Sidebar';
import { MainPreview } from '../story/MainPreview';
import { FilmStrip } from '../story/FilmStrip';
import { CommandCenter } from '../command/CommandCenter';
import { RenderOverlay } from '../shared/RenderOverlay';
import { useStudioContext } from '../../context/StudioContext';

interface MainLayoutProps {
  creativeResult: any;
  isRendering: boolean;
  onRender: () => Promise<void>;
  renderCount: number;
  shots: any[];
  selectedSceneId: string | null;
  newShotPrompt: string;
  setNewShotPrompt: (val: string) => void;
  onCreateShot: () => Promise<void>;
  onUpdateShot: (id: string, data: any) => Promise<void>;
  chatMessages: any[];
  onSendMessage: (text: string) => void;
}

export const MainLayout: React.FC<MainLayoutProps> = ({
  creativeResult,
  isRendering,
  onRender,
  renderCount,
  shots,
  selectedSceneId,
  newShotPrompt,
  setNewShotPrompt,
  onCreateShot,
  onUpdateShot,
  chatMessages,
  onSendMessage
}) => {
  return (
    <div className="h-screen flex flex-col overflow-hidden relative" style={{ backgroundColor: 'var(--color-base)', color: 'var(--color-text-main)' }}>
      <RenderOverlay isRendering={isRendering} />

      <Header />

      <div className="flex-1 flex overflow-hidden">
        <Sidebar />

        <main className="flex-1 flex flex-col relative overflow-hidden" style={{ backgroundColor: 'var(--color-base)' }}>
          <MainPreview creativeResult={creativeResult} />
          <FilmStrip
            shots={shots}
            selectedSceneId={selectedSceneId}
            newShotPrompt={newShotPrompt}
            setNewShotPrompt={setNewShotPrompt}
            onCreateShot={onCreateShot}
            onUpdateShot={onUpdateShot}
            loading={false} // Simplified for now, can be linked to useStudioApi
          />
        </main>

        <CommandCenter
          chatMessages={chatMessages}
          onSendMessage={onSendMessage}
          isRendering={isRendering}
          onRender={onRender}
          renderCount={renderCount}
          creativeResult={creativeResult}
        />
      </div >
    </div >
  );
};