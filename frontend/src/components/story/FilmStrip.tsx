import React from 'react';
import { Film } from 'lucide-react';
import { ShotCard } from './ShotCard';
import { TimelineHeader } from './TimelineHeader';
import { Shot } from '../../api/client';

interface FilmStripProps {
  shots: Shot[];
  selectedSceneId: string | null;
  newShotPrompt: string;
  setNewShotPrompt: (val: string) => void;
  onCreateShot: () => Promise<void>;
  onUpdateShot: (id: string, data: any) => Promise<void>;
  loading: boolean;
}

export const FilmStrip: React.FC<FilmStripProps> = ({
  shots,
  selectedSceneId,
  newShotPrompt,
  setNewShotPrompt,
  onCreateShot,
  onUpdateShot,
  loading
}) => {
  return (
    <div className="h-48 border-t surface-panel" style={{ borderColor: 'var(--color-border)' }}>
      <TimelineHeader
        newShotPrompt={newShotPrompt}
        setNewShotPrompt={setNewShotPrompt}
        onCreateShot={onCreateShot}
        loading={loading}
      />
      <div className="flex-1 overflow-x-auto p-3 flex gap-3 film-strip-container">
        {shots.length === 0 ? (
          <div className="flex-1 flex items-center justify-center text-gray-600 text-xs mono italic">
            Select scene to populate film strip...
          </div>
        ) : (
          shots.map(shot => (
            <ShotCard
              key={shot.id}
              shot={shot}
              onUpdate={onUpdateShot}
            />
          ))
        )}
      </div>
    </div>
  );
};