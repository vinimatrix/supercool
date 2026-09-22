import { useState, useEffect } from 'react';
import { driftApi } from '../api/drift';
import type { DriftStatus, EditPlan, DriftProject } from '../api/drift';
import { Monitor, Plug, Unplug, ExternalLink, Save, Download, Loader2, AlertCircle } from 'lucide-react';

interface DriftPanelProps {
  editPlan: EditPlan | null;
  onPlanExecuted: () => void;
}

export function DriftPanel({ editPlan, onPlanExecuted }: DriftPanelProps) {
  const [status, setStatus] = useState<DriftStatus>({ connected: false });
  const [loading, setLoading] = useState(false);
  const [projectInfo, setProjectInfo] = useState<DriftProject | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [port, setPort] = useState(4731);

  useEffect(() => {
    checkStatus();
  }, []);

  const checkStatus = async () => {
    try {
      const s = await driftApi.status();
      setStatus(s);
      if (s.connected && s.project_loaded && s.project_info) {
        setProjectInfo(s.project_info);
      }
    } catch {
      setStatus({ connected: false });
    }
  };

  const connect = async () => {
    setLoading(true);
    setError(null);
    try {
      await driftApi.connect(port);
      await checkStatus();
    } catch (e: any) {
      setError(e.message || 'Connection failed');
    }
    setLoading(false);
  };

  const disconnect = async () => {
    setLoading(true);
    try {
      await driftApi.disconnect();
      setStatus({ connected: false });
      setProjectInfo(null);
    } catch (e: any) {
      setError(e.message || 'Disconnect failed');
    }
    setLoading(false);
  };

  const executePlan = async () => {
    if (!editPlan) return;
    setLoading(true);
    setError(null);
    try {
      await driftApi.executePlan(editPlan);
      await checkStatus();
      onPlanExecuted();
    } catch (e: any) {
      setError(e.message || 'Execute plan failed');
    }
    setLoading(false);
  };

  const saveProject = async () => {
    setLoading(true);
    setError(null);
    try {
      await driftApi.saveProject();
    } catch (e: any) {
      setError(e.message || 'Save failed');
    }
    setLoading(false);
  };

  const exportVideo = async () => {
    setLoading(true);
    setError(null);
    try {
      const timestamp = Date.now();
      await driftApi.exportVideo(
        `workspace/pipeline_output/drift_export_${timestamp}.mp4`,
        24,
        '4K',
      );
    } catch (e: any) {
      setError(e.message || 'Export failed');
    }
    setLoading(false);
  };

  const openInDrift = () => {
    window.open('drift://', '_blank');
  };

  const refreshProject = async () => {
    setLoading(true);
    try {
      const info = await driftApi.inspect();
      setProjectInfo(info);
    } catch (e: any) {
      setError(e.message || 'Refresh failed');
    }
    setLoading(false);
  };

  return (
    <div className="p-4 rounded-lg" style={{ backgroundColor: '#1A1D24' }}>
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Monitor className="w-4 h-4 text-purple-400" />
          <span className="text-sm font-medium text-white">Drift Editor</span>
        </div>
        <div className="flex items-center gap-2">
          {status.connected ? (
            <div className="flex items-center gap-1">
              <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              <span className="text-xs text-emerald-400">Connected</span>
            </div>
          ) : (
            <div className="flex items-center gap-1">
              <div className="w-2 h-2 rounded-full bg-gray-500" />
              <span className="text-xs text-gray-500">Disconnected</span>
            </div>
          )}
        </div>
      </div>

      {error && (
        <div className="mb-3 p-2 rounded text-xs flex items-center gap-2" style={{ backgroundColor: '#7F1D1D20', color: '#FCA5A5' }}>
          <AlertCircle className="w-3 h-3 flex-shrink-0" />
          <span>{error}</span>
          <button onClick={() => setError(null)} className="ml-auto text-red-400 hover:text-red-300">
            ×
          </button>
        </div>
      )}

      {!status.connected ? (
        <div className="space-y-3">
          <p className="text-xs text-gray-400">
            Connect to Drift Editor to edit your project with full timeline capabilities.
          </p>
          <div className="flex gap-2">
            <input
              type="number"
              value={port}
              onChange={(e) => setPort(parseInt(e.target.value) || 4731)}
              className="w-20 bg-gray-800 text-xs px-2 py-1.5 rounded border text-white"
              style={{ borderColor: '#2A2F3D' }}
            />
            <button
              onClick={connect}
              disabled={loading}
              className="flex-1 px-3 py-1.5 bg-purple-600 rounded text-xs text-white hover:bg-purple-500 disabled:opacity-50 flex items-center justify-center gap-1"
            >
              {loading ? (
                <Loader2 className="w-3 h-3 animate-spin" />
              ) : (
                <Plug className="w-3 h-3" />
              )}
              Connect
            </button>
          </div>
          <p className="text-[10px] text-gray-500">
            Enable "Agent access" in Drift Settings first.
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {projectInfo && (
            <div className="p-2 rounded text-xs space-y-1" style={{ backgroundColor: '#0D0F12' }}>
              <div className="flex justify-between">
                <span className="text-gray-500">Tracks</span>
                <span className="text-white">{projectInfo.tracks?.length || 0}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">Resolution</span>
                <span className="text-white">{projectInfo.width}×{projectInfo.height}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">FPS</span>
                <span className="text-white">{projectInfo.fps}</span>
              </div>
            </div>
          )}

          <div className="grid grid-cols-2 gap-2">
            {editPlan && (
              <button
                onClick={executePlan}
                disabled={loading}
                className="py-2 bg-emerald-600 rounded text-xs text-white hover:bg-emerald-500 disabled:opacity-50 flex items-center justify-center gap-1"
              >
                {loading ? (
                  <Loader2 className="w-3 h-3 animate-spin" />
                ) : (
                  <span>Execute Plan</span>
                )}
              </button>
            )}
            <button
              onClick={openInDrift}
              className="py-2 bg-blue-600 rounded text-xs text-white hover:bg-blue-500 flex items-center justify-center gap-1"
            >
              <ExternalLink className="w-3 h-3" />
              Open Drift
            </button>
            <button
              onClick={saveProject}
              disabled={loading}
              className="py-2 bg-gray-700 rounded text-xs text-white hover:bg-gray-600 disabled:opacity-50 flex items-center justify-center gap-1"
            >
              <Save className="w-3 h-3" />
              Save
            </button>
            <button
              onClick={exportVideo}
              disabled={loading}
              className="py-2 bg-gray-700 rounded text-xs text-white hover:bg-gray-600 disabled:opacity-50 flex items-center justify-center gap-1"
            >
              <Download className="w-3 h-3" />
              Export
            </button>
          </div>

          <div className="flex gap-2">
            <button
              onClick={refreshProject}
              disabled={loading}
              className="flex-1 py-1.5 bg-gray-800 rounded text-xs text-gray-400 hover:text-white disabled:opacity-50"
            >
              Refresh
            </button>
            <button
              onClick={disconnect}
              disabled={loading}
              className="flex-1 py-1.5 bg-red-600/20 text-red-400 rounded text-xs hover:bg-red-600/30 disabled:opacity-50 flex items-center justify-center gap-1"
            >
              <Unplug className="w-3 h-3" />
              Disconnect
            </button>
          </div>

          {editPlan && (
            <div className="p-2 rounded text-xs" style={{ backgroundColor: '#0D0F12' }}>
              <div className="text-gray-500 uppercase mb-1">Pending Edit Plan</div>
              <div className="flex justify-between">
                <span className="text-gray-400">Clips</span>
                <span className="text-white">{editPlan.clips.length}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Transitions</span>
                <span className="text-white">{editPlan.transitions.length}</span>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
