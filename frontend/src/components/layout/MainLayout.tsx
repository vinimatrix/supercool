import React from 'react';
import { Header } from './Header';
import { Sidebar } from './Sidebar';
import { MainPreview } from '../story/MainPreview';
import { FilmStrip } from '../story/FilmStrip';
import { CommandCenter } from '../command/CommandCenter';
import { RenderOverlay } from '../shared/RenderOverlay';
import { useStudioContext } from '../../context/StudioContext';

interface MainLayoutProps {
  onCreateShot: () => Promise<void>;
  onUpdateShot: (id: string, data: any) => Promise<void>;
  onSendMessage: (text: string) => void;
  onRender: () => Promise<void>;
}

export const MainLayout: React.FC<MainLayoutProps> = ({
  onCreateShot,
  onUpdateShot,
  onSendMessage,
  onRender
}) => {
  const {
    creativeResult,
    isRendering,
    shots,
    selectedSceneId,
    newShotPrompt,
    setNewShotPrompt,
    chatMessages
  } = useStudioContext();

  const renderCount = shots.filter(s => s.video_path).length;

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
            loading={false}
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