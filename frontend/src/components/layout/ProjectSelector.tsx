import React from 'react';
import { useStudioContext } from '../../context/StudioContext';

export const ProjectSelector: React.FC<{
  projects: any[];
  selectedProject: any | null;
  setSelectedProject: (p: any | null) => void;
}> = ({ projects, selectedProject, setSelectedProject }) => {
  return (
    <div className="space-y-3">
      <div className="flex gap-2">
        <input
          placeholder="Project Name..."
          className="flex-1 bg-black/40 text-xs px-2 py-1.5 rounded border mono text-white focus:outline-none focus:border-[var(--color-accent)]"
          style={{ borderColor: 'var(--color-border)' }}
          onChange={(e) => {
            // This would call the createProject action from useStudioApi
          }}
        />
        <button className="px-2 py-1 bg-[var(--color-accent)] text-black rounded text-xs font-bold hover:opacity-90 flex items-center justify-center">
          +
        </button>
      </div>
      <select
        value={selectedProject?.id || ''}
        onChange={e => {
          const p = projects.find(p => p.id === e.target.value);
          setSelectedProject(p || null);
        }}
        className="w-full bg-black/40 text-xs px-2 py-1.5 rounded border mono text-white focus:outline-none"
        style={{ borderColor: 'var(--color-border)' }}
      >
        <option value="">Select Active Project...</option>
        {projects.map(p => (
          <option key={p.id} value={p.id}>{p.title}</option>
        ))}
      </select>
    </div>
  );
};