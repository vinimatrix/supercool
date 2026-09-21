import React from 'react';
import { Activity, AlertCircle, CheckCircle2, Clock } from 'lucide-react';
import { useStudioContext } from '../../context/StudioContext';

export const QAMonitor: React.FC = () => {
  const { shots } = useStudioContext();

  return (
    <div className="flex flex-col h-full space-y-4">
      <div className="flex items-center gap-2 px-2">
        <Activity className="w-3 h-3 text-[var(--color-accent)]" />
        <span className="text-[10px] font-bold text-gray-500 uppercase tracking-widest">QA Status Stream</span>
      </div>

      <div className="flex-1 overflow-y-auto space-y-1 px-2 scrollbar-thin">
        {shots.length === 0 ? (
          <div className="text-center py-8 opacity-30">
            <p className="text-[10px] mono text-gray-500">NO SHOTS IN SEQUENCE</p>
          </div>
        ) : (
          shots.map((shot) => (
            <div
              key={shot.id}
              className="flex items-center justify-between p-2 rounded-sm border border-[var(--color-border)] bg-black/20 group hover:bg-black/40 transition-colors"
            >
              <div className="flex items-center gap-3">
                <span className="text-[9px] mono text-gray-600">S_{shot.shot_number}</span>
                <span className="text-[10px] mono text-gray-400 truncate max-w-[120px]">
                  {shot.prompt_text}
                </span>
              </div>

              <div className="flex items-center gap-2">
                {shot.video_path ? (
                  <CheckCircle2 className="w-3 h-3 text-emerald-500" />
                ) : (
                  <div className="flex items-center gap-1">
                    <span className="text-[8px] mono text-gray-500">{shot.status || 'PENDING'}</span>
                    <Clock className="w-2 h-2 text-gray-600" />
                  </div>
                )}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};
