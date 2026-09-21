import React, { useState } from 'react';
import { Film, Plus, CheckCircle, Loader2, Upload } from 'lucide-react';
import { Button } from '../ui/Button';
import { Input } from '../ui/Input';
import { useStudioApi } from '../../hooks/useStudioApi';
import { useStudioContext } from '../../context/StudioContext';

interface ShotCardProps {
  shot: any;
  onUpdate: (id: string, data: any) => Promise<void>;
}

export const ShotCard: React.FC<ShotCardProps> = ({ shot, onUpdate }) => {
  const [isEditing, setIsEditing] = useState(false);
  const [prompt, setPrompt] = useState(shot.prompt_text);
  const api = useStudioApi((msg, type) => console.log(`[Toast ${type}] ${msg}`));

  const handleBlur = () => {
    setIsEditing(false);
    if (prompt !== shot.prompt_text) {
      onUpdate(shot.id, { prompt_text: prompt });
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleBlur();
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    try {
      await api.uploadShotClip(shot.id, file);
      // The parent should handle the refresh of shots list
      // but we can trigger a re-fetch if needed or rely on global state
    } catch (e) {
      console.error('Upload failed:', e);
    }
  };

  return (
    <div
      className={`flex-shrink-0 w-56 group rounded-sm overflow-hidden transition-all border border-[var(--color-border)]`}
      style={{ backgroundColor: 'var(--color-surface)' }}
    >
      <div className="relative aspect-video bg-black flex items-center justify-center overflow-hidden">
        {shot.video_path ? (
          <video
            src={`http://localhost:8000/workspace/${shot.video_path.split('/').pop()}`}
            className="w-full h-full object-cover opacity-60 group-hover:opacity-100 transition-opacity"
          />
        ) : (
          <div className="flex flex-col items-center gap-2 opacity-20">
            <Film className="w-6 h-6" />
            <span className="text-[8px] mono">NO CLIP</span>
          </div>
        )}
        <div className="absolute top-1 left-1 px-1 bg-black/80 text-[8px] mono text-white rounded">
          S_{shot.shot_number}
        </div>
        <div className="absolute top-1 right-1">
          {shot.video_path ? (
            <div className="p-0.5 bg-emerald-500/20 text-emerald-400 rounded text-[8px] mono flex items-center gap-1">
              <CheckCircle className="w-2 h-2" /> CLIP
            </div>
          ) : (
            <div className="text-[8px] mono text-gray-500">{shot.status}</div>
          )}
        </div>
      </div>
      <div className="p-2 space-y-2">
        {isEditing ? (
          <div className="space-y-2">
            <Input
              autoFocus
              value={prompt}
              onChange={e => setPrompt(e.target.value)}
              onBlur={handleBlur}
              onKeyDown={handleKeyDown}
              className="w-full bg-black/60 text-[10px] px-1 py-0.5 rounded border border-[var(--color-accent)] outline-none text-white mono"
            />
            <div className="flex gap-1">
              <select
                value={shot.shot_type || 'Wide'}
                onChange={e => onUpdate(shot.id, { shot_type: e.target.value })}
                className="flex-1 bg-black/40 text-[8px] px-1 py-0.5 rounded border border-[var(--color-border)] text-gray-400 outline-none"
              >
                <option value="Wide">Wide</option>
                <option value="Medium">Medium</option>
                <option value="Close-up">Close-up</option>
                <option value="ECU">ECU</option>
              </select>
              <select
                value={shot.motion_type || 'Static'}
                onChange={e => onUpdate(shot.id, { motion_type: e.target.value })}
                className="flex-1 bg-black/40 text-[8px] px-1 py-0.5 rounded border border-[var(--color-border)] text-gray-400 outline-none"
              >
                <option value="Static">Static</option>
                <option value="Pan">Pan</option>
                <option value="Tilt">Tilt</option>
                <option value="Zoom">Zoom</option>
              </select>
            </div>
          </div>
        ) : (
          <>
            <p
              onClick={() => setIsEditing(true)}
              className="text-[10px] text-gray-400 line-clamp-1 mono italic cursor-pointer hover:text-white transition-colors"
            >
              "{shot.prompt_text}"
            </p>
            <div className="flex gap-1 opacity-50 group-hover:opacity-100 transition-opacity">
              <span className="text-[7px] mono text-gray-600 bg-black/40 px-1 rounded">{shot.shot_type || 'Wide'}</span>
              <span className="text-[7px] mono text-gray-600 bg-black/40 px-1 rounded">{shot.motion_type || 'Static'}</span>
            </div>
          </>
        )}
        {!shot.video_path && (
          <label className="w-full py-1 bg-black/40 border border-dashed border-[var(--color-border)] rounded text-[9px] mono text-gray-500 hover:text-[var(--color-accent)] hover:border-[var(--color-accent)] flex items-center justify-center cursor-pointer transition-all">
            <Upload className="w-2 h-2 mr-1" /> ATTACH CLIP
            <input
              type="file"
              accept="video/*"
              className="hidden"
              onChange={handleFileUpload}
            />
          </label>
        )}
        {shot.video_path && (
          <div className="text-[8px] mono text-emerald-400 truncate opacity-70">
            {shot.video_path.split(/[/\\]/).pop()}
          </div>
        )}
      </div>
    </div>
  );
};
