import React from 'react';
import { ProjectSelector } from './ProjectSelector';
import { TabNavigator } from './TabNavigator';
import { AssetsPanel } from '../story/AssetsPanel';
import { QAMonitor } from '../analytics/QAMonitor';
import { AnalyticsPanel } from '../analytics/AnalyticsPanel';
import { useStudioContext } from '../../context/StudioContext';

export const Sidebar: React.FC = () => {
  const {
    activeTab,
    setActiveTab,
    selectedProject,
    setSelectedProject,
    projects
  } = useStudioContext();

  return (
    <aside className="w-80 flex flex-col border-r shrink-0 overflow-hidden surface-panel" style={{ borderColor: 'var(--color-border)' }}>
      <div className="p-4 border-b" style={{ borderColor: 'var(--color-border)' }}>
        <div className="flex items-center gap-2 mb-4">
          <span className="text-xs font-bold uppercase tracking-widest">Story Bible</span>
        </div>
        <ProjectSelector
          projects={projects}
          selectedProject={selectedProject}
          setSelectedProject={setSelectedProject}
        />
      </div>

      <div className="flex border-b" style={{ borderColor: 'var(--color-border)' }}>
        <TabNavigator />
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-6 scrollbar-thin">
        {activeTab === 'story' && <AssetsPanel />}
        {activeTab === 'qa' && <QAMonitor />}
        {activeTab === 'analytics' && <AnalyticsPanel />}
      </div>
    </aside>
  );
};