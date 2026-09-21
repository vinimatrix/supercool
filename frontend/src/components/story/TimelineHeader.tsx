import React from 'react';
import { Film, Plus, Loader2 } from 'lucide-react';
import { Button } from '../ui/Button';
import { Input } from '../ui/Input';
import { Shot } from '../../api/client';

interface TimelineHeaderProps {
  newShotPrompt: string;
  setNewShotPrompt: (val: string) => void;
  onCreateShot: () => Promise<void>;
  loading: boolean;
}

export const TimelineHeader: React.FC<TimelineHeaderProps> = ({
  newShotPrompt,
  setNewShotPrompt,
  onCreateShot,
  loading
}) => {
  return (
    <div className="h-8 flex items-center justify-between px-3 border-b" style={{ borderColor: 'var(--color-border)' }}>
      <div className="flex items-center gap-2">
        <Film className="w-3 h-3 text-[var(--color-accent)]" />
        <span className="text-[10px] font-bold text-gray-500 uppercase tracking-widest">Shot Timeline</span>
      </div>
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-1">
          <Button
            variant="secondary"
            className="px-2 py-0.5 text-[10px] mono text-gray-400 flex items-center gap-1"
            onClick={() => document.getElementById('video-upload-input')?.click()}
          >
            <Plus className="w-2 h-2" /> IMPORT CLIPS
          </Button>
          <input
            id="video-upload-input"
            type="file"
            accept="video/*"
            multiple
            className="hidden"
          />
        </div>
        <div className="flex gap-1">
          <Input
            value={newShotPrompt}
            onChange={e => setNewShotPrompt(e.target.value)}
            placeholder="Define shot..."
            className="w-40 text-xs px-2 py-0.5 rounded border mono text-white focus:outline-none"
            onKeyDown={e => e.key === 'Enter' && onCreateShot()}
          />
          <Button
            onClick={onCreateShot}
            disabled={loading}
            className="px-2 py-0.5"
            loading={loading}
          >
            <Plus className="w-3 h-3" />
          </Button>
        </div>
      </div>
    </div>
  );
};