import React from 'react';
import { Zap } from 'lucide-react';
import { useStudioContext } from '../../context/StudioContext';

export const Header: React.FC = () => {
  const { selectedProject, scenes, selectedSceneId } = useStudioContext();
  const currentScene = scenes.find(s => s.id === selectedSceneId);

  return (
    <header className="h-8 flex items-center justify-between px-4 border-b shrink-0" style={{ backgroundColor: 'var(--color-surface)', borderColor: 'var(--color-border)' }}>
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2">
          <Zap className="w-3 h-3 text-[var(--color-accent)]" />
          <span className="font-bold text-[10px] tracking-tighter uppercase">Supercool Studio</span>
        </div>
        <div className="flex items-center gap-2 text-[9px] mono text-gray-500 border-l pl-4 border-[var(--color-border)]">
          <span className="text-gray-600 uppercase">Project:</span>
          <span className="text-white font-bold">{selectedProject?.title || 'None'}</span>
          <span className="mx-1 opacity-30">{'>'}</span>
          <span className="text-gray-600 uppercase">Scene:</span>
          <span className="text-white font-bold">{currentScene?.title || 'None'}</span>
        </div>
        <div className="flex items-center gap-3 text-[9px] mono text-gray-500 border-l pl-4 border-[var(--color-border)]">
          <span className="flex items-center gap-1">4K</span>
          <span className="flex items-center gap-1">24fps</span>
          <span className="flex items-center gap-1">Auto-Route</span>
        </div>
      </div>
      <div className="flex items-center gap-2">
        <div className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
        <span className="text-[9px] mono text-gray-500 uppercase">Live System</span>
      </div>
    </header>
  );
};