import React from 'react';

export const RenderOverlay: React.FC<{ isRendering: boolean }> = ({ isRendering }) => {
  if (!isRendering) return null;

  return (
    <div className="fixed inset-0 z-[100] bg-black/80 backdrop-blur-md flex flex-col items-center justify-center animate-in fade-in duration-300">
      <div className="flex flex-col items-center gap-4">
        <div className="w-16 h-16 border-4 border-[var(--color-accent)] border-t-transparent rounded-full animate-spin" />
        <div className="text-center">
          <h2 className="text-xl font-bold mono tracking-widest uppercase text-[var(--color-accent)]">Processing Cinematic Render</h2>
          <p className="text-xs mono text-gray-500 mt-2">Splicing clips and applying AI mood... Please wait.</p>
        </div>
      </div>
    </div>
  );
};