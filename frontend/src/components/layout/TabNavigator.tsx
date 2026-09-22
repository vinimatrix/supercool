import React from 'react';
import { useStudioContext } from '../../context/StudioContext';

export const TabNavigator: React.FC = () => {
  const { activeTab, setActiveTab } = useStudioContext();

  const tabs: { id: 'story' | 'qa' | 'analytics' | 'youtube' | 'drift'; label: string }[] = [
    { id: 'story', label: 'Assets' },
    { id: 'qa', label: 'QA' },
    { id: 'analytics', label: 'Data' },
    { id: 'youtube', label: 'YT' },
    { id: 'drift', label: 'Drift' },
  ];

  return (
    <div className="flex w-full">
      {tabs.map(tab => (
        <button
          key={tab.id}
          onClick={() => setActiveTab(tab.id)}
          className={`flex-1 py-2 text-[10px] font-bold uppercase tracking-wider transition-colors ${
            activeTab === tab.id ? 'text-[var(--color-accent)] bg-[var(--color-accent-muted)]' : 'text-gray-500 hover:text-gray-300'
          }`}
        >
          {tab.label}
        </button>
      ))}
    </div>
  );
};