import React from 'react';
import { Zap, Sparkles } from 'lucide-react';
import { Button } from '../ui/Button';
import { useStudioContext } from '../../context/StudioContext';

interface RenderModuleProps {
  isRendering: boolean;
  onRender: () => Promise<void>;
  renderCount: number;
  creativeResult?: any;
}

export const RenderModule: React.FC<RenderModuleProps> = ({
  isRendering,
  onRender,
  renderCount,
  creativeResult
}) => {
  return (
    <div className="p-4 border-t surface-panel" style={{ borderColor: 'var(--color-border)' }}>
      <div className="text-[10px] mono text-gray-500 uppercase mb-4 tracking-widest flex items-center gap-2">
        <Zap className="w-3 h-3" /> Render Module
      </div>

      <div className="grid grid-cols-2 gap-2 text-[10px] mono mb-4">
        {[
          { label: 'Engine', val: 'Auto-Route' },
          { label: 'Resolution', val: '4K' },
          { label: 'FPS', val: '24' },
          { label: 'IP-Adapter', val: '0.85' },
        ].map((item, i) => (
          <div key={i} className="p-2 rounded bg-black/40 border border-[var(--color-border)] flex flex-col">
            <span className="text-gray-600 mb-1">{item.label}</span>
            <span className="text-white font-bold">{item.val}</span>
          </div>
        ))}
      </div>

      <Button
        onClick={onRender}
        disabled={isRendering || renderCount === 0}
        className={`w-full py-2 rounded text-xs font-bold flex items-center justify-center gap-2 transition-all ${
          isRendering ? 'bg-gray-800 text-gray-400' : 'bg-[var(--color-accent)] text-black hover:opacity-90'
        } ${isRendering ? 'rendering-active' : ''}`}
        loading={isRendering}
        icon={!isRendering && <Sparkles className="w-3 h-3" />}
      >
        {isRendering ? 'PROCESSING...' : `RENDER FINAL (${renderCount} CLIPS)`}
      </Button>

      {creativeResult && (
        <div className="mt-4 p-3 rounded border border-[var(--color-border)] bg-black/40 space-y-2">
          <div className="flex justify-between text-[10px] mono">
            <span className="text-gray-500">MOOD:</span>
            <span className="text-purple-400 font-bold uppercase">{creativeResult.mood}</span>
          </div>
          <div className="flex justify-between text-[10px] mono">
            <span className="text-gray-500">DURATION:</span>
            <span className="text-white font-bold">{creativeResult.duration.toFixed(1)}s</span>
          </div>
          <div className="flex justify-between text-[10px] mono">
            <span className="text-gray-500">CLIPS:</span>
            <span className="text-white font-bold">{creativeResult.shots}</span>
          </div>
          <a
            href={`http://localhost:8000/api/v1/creative/workspace`}
            target="_blank"
            className="mt-2 flex items-center justify-center gap-2 py-1 bg-emerald-600/20 text-emerald-400 rounded text-[9px] mono hover:bg-emerald-600/40 transition-colors"
          >
            DOWNLOAD OUTPUT
          </a>
        </div>
      )}
    </div>
  );
};