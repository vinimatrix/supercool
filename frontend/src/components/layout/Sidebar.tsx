import React from 'react';
import { ProjectSelector } from './ProjectSelector';
import { TabNavigator } from './TabNavigator';
import { AssetsPanel } from '../story/AssetsPanel';
import { QAMonitor } from '../analytics/QAMonitor';
import { AnalyticsPanel } from '../analytics/AnalyticsPanel';
import { YouTubeConnect, YouTubeDashboard, YouTubeAIReport } from '../youtube';
import { DriftPanel } from '../DriftPanel';
import { LipsyncPanel } from '../lipsync/LipsyncPanel';
import { useStudioContext } from '../../context/StudioContext';
import { youtubeApi } from '../../api/youtube';
import type { ChannelStats, VideoMetrics, AnalysisReport } from '../../api/youtube';
import { useResizablePanel } from '../../hooks/useResizablePanel';
import { PanelDivider } from './PanelDivider';

export const Sidebar: React.FC = () => {
  const {
    activeTab,
    selectedProject,
    setSelectedProject,
    projects,
    editPlan,
    setEditPlan,
    setChatMessages
  } = useStudioContext();

  const [youtubeConnected, setYoutubeConnected] = React.useState(false);
  const [youtubeToken, setYoutubeToken] = React.useState<string | null>(null);
  const [channelStats, setChannelStats] = React.useState<ChannelStats | null>(null);
  const [videos, setVideos] = React.useState<VideoMetrics[]>([]);
  const [aiReport, setAiReport] = React.useState<AnalysisReport | null>(null);
  const [aiProvider, setAiProvider] = React.useState('gemini');
  const [analyzeLoading, setAnalyzeLoading] = React.useState(false);

  const { width, dividerProps } = useResizablePanel('sidebar', 320, 220, 560, 1);

  const handleYouTubeConnect = async (token: string | null) => {
    setYoutubeToken(token);
    setYoutubeConnected(true);
    try {
      const [stats, videoList] = await Promise.all([
        youtubeApi.getChannelStats(token),
        youtubeApi.getVideoMetrics(token)
      ]);
      setChannelStats(stats);
      setVideos(Array.isArray(videoList) ? videoList : []);
    } catch (e) {
      console.error('Failed to connect YouTube:', e);
    }
  };

  const handleAnalyze = async () => {
    setAnalyzeLoading(true);
    try {
      const report = await youtubeApi.analyze(youtubeToken, aiProvider);
      setAiReport(report);
    } catch (e) {
      console.error('YouTube AI analyze failed:', e);
    } finally {
      setAnalyzeLoading(false);
    }
  };

  const handlePlanExecuted = () => {
    setEditPlan(null);
    setChatMessages(prev => [
      ...prev,
      { role: 'system', text: 'Edit Plan executed in Drift. Open Drift Editor to see the timeline.' }
    ]);
  };

  return (
    <aside className="relative flex flex-col border-r shrink-0 overflow-hidden surface-panel" style={{ width, borderColor: 'var(--color-border)' }}>
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
        {activeTab === 'youtube' && (
          <div className="space-y-4">
            <YouTubeConnect onConnect={handleYouTubeConnect} connected={youtubeConnected} />
            {youtubeConnected && channelStats && (
              <>
                <YouTubeDashboard stats={channelStats} videos={videos} />
                <YouTubeAIReport
                  report={aiReport}
                  onAnalyze={handleAnalyze}
                  loading={analyzeLoading}
                  provider={aiProvider}
                  onProviderChange={setAiProvider}
                />
              </>
            )}
          </div>
        )}
        {activeTab === 'drift' && (
          <DriftPanel editPlan={editPlan} onPlanExecuted={handlePlanExecuted} />
        )}
        {activeTab === 'lipsync' && <LipsyncPanel />}
      </div>
      <PanelDivider
        {...dividerProps}
        style={{ backgroundColor: 'var(--color-border)', position: 'absolute', top: 0, bottom: 0, right: 0, zIndex: 10 }}
      />
    </aside>
  );
};