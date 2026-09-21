import React from 'react';
import { Film, Info } from 'lucide-react';
import { CreativeRenderResult } from '../../api/client';
import { useStudioContext } from '../../context/StudioContext';

interface MainPreviewProps {
  creativeResult: CreativeRenderResult | null;
}

export const MainPreview: React.FC<MainPreviewProps> = ({ creativeResult }) => {
  const { selectedProject, scenes, selectedSceneId } = useStudioContext();
  const currentScene = scenes.find(s => s.id === selectedSceneId);

  return (
    <div className="flex-1 flex items-center justify-center p-8 relative">
      {/* Contextual Breadcrumbs */}
      <div className="absolute top-4 left-4 z-10 flex items-center gap-2 px-3 py-1.5 bg-black/60 backdrop-blur-md rounded-full border border-white/10 text-[9px] mono text-gray-400">
        <Info className="w-3 h-3 text-[var(--color-accent)]" />
        <span>
          <span className="text-gray-600 uppercase">PROJ:</span> {selectedProject?.title || 'NONE'}
        </span>
        <span className="opacity-30">/</span>
        <span>
          <span className="text-gray-600 uppercase">SCENE:</span> {currentScene?.title || 'NONE'}
        </span>
      </div>

      {creativeResult ? (
        <div className="w-full h-full max-w-5xl max-h-[70vh] relative group">
          <video
            key={creativeResult.video_only}
            controls
            className="w-full h-full object-contain rounded-lg shadow-2xl border border-[var(--color-border)]"
            src={`http://localhost:8000/workspace/pipeline_output/${creativeResult.final_output.split(/[/\\]/).pop()}`}
          />
          <div className="absolute top-4 right-4 flex gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
            <span className="px-2 py-1 bg-black/60 backdrop-blur-md rounded text-[10px] mono text-white border border-white/10">4K UHD</span>
            <span className="px-2 py-1 bg-black/60 backdrop-blur-md rounded text-[10px] mono text-white border border-white/10">23.976 fps</span>
          </div>
        </div>
      ) : (
        <div className="text-center space-y-4 opacity-30">
          <div className="relative">
            <Film className="w-20 h-20 mx-auto text-gray-700" />
            <div className="absolute inset-0 animate-pulse bg-accent-muted blur-3xl rounded-full" />
          </div>
          <div>
            <p className="text-sm mono text-gray-500">NO SIGNAL</p>
            <p className="text-[10px] mono text-gray-600 mt-1">Ready for cinematic render</p>
          </div>
        </div>
      )}
    </div>
  );
};