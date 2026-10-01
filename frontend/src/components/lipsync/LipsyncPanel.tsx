import React, { useEffect, useState } from 'react';
import { lipsyncApi, scenesApi, shotsApi } from '../../api/client';
import type { MediaItem, LipsyncJob, Shot } from '../../api/client';
import { useStudioContext } from '../../context/StudioContext';
import { useStudioApi } from '../../hooks/useStudioApi';

const TERMINAL_STATUSES = new Set(['DONE', 'FAILED']);
const MAX_VIDEO_BYTES = 500 * 1024 * 1024;
const MAX_AUDIO_BYTES = 50 * 1024 * 1024;
const MEDIA_BASE = 'http://localhost:8000';

export const LipsyncPanel: React.FC = () => {
  const { selectedProject, setShots } = useStudioContext();
  const { createLipsyncJob, assignLipsyncJob } = useStudioApi((msg, type) =>
    console.log(`[Toast ${type}] ${msg}`)
  );

  const projectId = selectedProject?.id ?? null;

  const [videos, setVideos] = useState<MediaItem[]>([]);
  const [audios, setAudios] = useState<MediaItem[]>([]);
  const [history, setHistory] = useState<LipsyncJob[]>([]);
  const [shotOptions, setShotOptions] = useState<Shot[]>([]);
  const [videoMode, setVideoMode] = useState<'workspace' | 'upload'>('workspace');
  const [audioMode, setAudioMode] = useState<'workspace' | 'upload'>('workspace');
  const [videoPath, setVideoPath] = useState('');
  const [audioPath, setAudioPath] = useState('');
  const [videoFile, setVideoFile] = useState<File | null>(null);
  const [audioFile, setAudioFile] = useState<File | null>(null);
  const [trimStart, setTrimStart] = useState('0');
  const [trimEnd, setTrimEnd] = useState('');
  const [job, setJob] = useState<LipsyncJob | null>(null);
  const [assignShotId, setAssignShotId] = useState('');
  const [panelError, setPanelError] = useState<string | null>(null);

  useEffect(() => {
    if (!projectId) return;
    let cancelled = false;
    const load = async () => {
      try {
        const [videoRes, audioRes, jobRes, sceneRes] = await Promise.all([
          lipsyncApi.listVideos(projectId),
          lipsyncApi.listAudios(projectId),
          lipsyncApi.listJobs(projectId),
          scenesApi.list(projectId),
        ]);
        if (cancelled) return;
        setVideos(videoRes.data);
        setAudios(audioRes.data);
        setHistory(jobRes.data);
        const shotLists = await Promise.all(sceneRes.data.map(sc => shotsApi.list(sc.id)));
        if (cancelled) return;
        setShotOptions(shotLists.flatMap(res => res.data));
      } catch {
        if (!cancelled) setPanelError('Failed to load lipsync workspace');
      }
    };
    void load();
    return () => {
      cancelled = true;
    };
  }, [projectId]);

  const activeJobId = job?.id ?? null;
  const activeJobStatus = job?.status ?? null;

  useEffect(() => {
    if (!activeJobId || !activeJobStatus || TERMINAL_STATUSES.has(activeJobStatus)) return;
    const jobId = activeJobId;
    let cancelled = false;
    let failures = 0;
    let handle: ReturnType<typeof setInterval> | undefined;
    const stop = () => {
      if (handle !== undefined) clearInterval(handle);
    };
    const poll = async () => {
      try {
        const res = await lipsyncApi.getJob(jobId);
        if (cancelled) return;
        failures = 0;
        setJob(res.data);
        setHistory(prev => prev.map(h => (h.id === jobId ? res.data : h)));
      } catch {
        if (cancelled) return;
        failures += 1;
        if (failures >= 3) {
          setPanelError('Lost connection while polling job status');
          stop();
        }
      }
    };
    void poll();
    handle = setInterval(() => void poll(), 2000);
    return () => {
      cancelled = true;
      stop();
    };
  }, [activeJobId, activeJobStatus]);

  const selectedVideo = videos.find(v => v.path === videoPath);

  const trimValid = (() => {
    const start = Number(trimStart);
    const end = Number(trimEnd);
    if (!Number.isFinite(start) || !Number.isFinite(end)) return false;
    if (start < 0 || end <= start) return false;
    if (videoMode === 'workspace' && selectedVideo?.duration != null && end > selectedVideo.duration) {
      return false;
    }
    return true;
  })();

  const canRun =
    !!projectId &&
    trimValid &&
    (videoMode === 'workspace' ? !!videoPath : !!videoFile) &&
    (audioMode === 'workspace' ? !!audioPath : !!audioFile);

  const handleRun = async () => {
    if (!projectId) return;
    setPanelError(null);
    try {
      let resolvedVideoPath = videoPath;
      let resolvedAudioPath = audioPath;
      if (videoMode === 'upload' && videoFile) {
        if (videoFile.size > MAX_VIDEO_BYTES) {
          setPanelError('Video exceeds the 500 MB limit');
          return;
        }
        const res = await lipsyncApi.uploadVideo(projectId, videoFile);
        resolvedVideoPath = res.data.path;
      }
      if (audioMode === 'upload' && audioFile) {
        if (audioFile.size > MAX_AUDIO_BYTES) {
          setPanelError('Audio exceeds the 50 MB limit');
          return;
        }
        const res = await lipsyncApi.uploadAudio(projectId, audioFile);
        resolvedAudioPath = res.data.path;
      }
      const created = await createLipsyncJob({
        project_id: projectId,
        video_path: resolvedVideoPath,
        trim_start: Number(trimStart),
        trim_end: Number(trimEnd),
        audio_path: resolvedAudioPath,
      });
      if (created) {
        setJob(created);
        setHistory(prev => [created, ...prev.filter(h => h.id !== created.id)]);
      }
    } catch {
      setPanelError('Failed to start lipsync job');
    }
  };

  const handleAssign = async () => {
    if (!job || !assignShotId) return;
    setPanelError(null);
    const updated = await assignLipsyncJob(job.id, assignShotId);
    if (updated) {
      setJob(updated);
      setHistory(prev => prev.map(h => (h.id === updated.id ? updated : h)));
      setShots(prev =>
        prev.map(s =>
          s.id === assignShotId ? { ...s, video_path: updated.output_path, status: 'CLIP_ASSIGNED' } : s
        )
      );
    }
  };

  if (!projectId) {
    return <p className="text-xs text-gray-500">Select a project to use Lipsync.</p>;
  }

  const statusColor =
    job?.status === 'FAILED'
      ? 'text-red-400'
      : job?.status === 'DONE'
        ? 'text-green-400'
        : 'text-[var(--color-accent)]';

  return (
    <div className="space-y-4" data-testid="lipsync-panel">
      <div className="flex items-center justify-between">
        <span className="text-xs font-bold uppercase tracking-widest">Lip Sync</span>
        {job && (
          <span className="flex items-center gap-1 text-[10px] font-bold uppercase px-2 py-0.5 rounded border" style={{ borderColor: 'var(--color-border)' }}>
            <span className={statusColor}>{job.status}</span>
            {job.stage && <span className="text-gray-400">— {job.stage}</span>}
          </span>
        )}
      </div>

      {panelError && (
        <p role="alert" className="text-xs text-red-400">
          {panelError}
        </p>
      )}

      <fieldset className="space-y-2">
        <legend className="text-[10px] font-bold uppercase tracking-wider text-gray-400">Video</legend>
        <div className="flex gap-3 text-xs">
          <label className="flex items-center gap-1">
            <input
              type="radio"
              name="lipsync-video-mode"
              checked={videoMode === 'workspace'}
              onChange={() => setVideoMode('workspace')}
            />
            Workspace video
          </label>
          <label className="flex items-center gap-1">
            <input
              type="radio"
              name="lipsync-video-mode"
              checked={videoMode === 'upload'}
              onChange={() => setVideoMode('upload')}
            />
            Upload video
          </label>
        </div>
        {videoMode === 'workspace' ? (
          <select
            aria-label="Video"
            value={videoPath}
            onChange={e => setVideoPath(e.target.value)}
            className="w-full bg-black border text-xs p-1.5"
            style={{ borderColor: 'var(--color-border)' }}
          >
            <option value="">Select a video…</option>
            {videos.map(v => (
              <option key={v.path} value={v.path}>
                {v.name}
              </option>
            ))}
          </select>
        ) : (
          <input
            type="file"
            aria-label="Upload video"
            accept="video/*"
            onChange={e => setVideoFile(e.target.files?.[0] ?? null)}
            className="w-full text-xs"
          />
        )}
        {videoMode === 'workspace' && selectedVideo?.duration != null && (
          <p className="text-[10px] text-gray-500">Duration: {selectedVideo.duration}s</p>
        )}
      </fieldset>

      <fieldset className="space-y-2">
        <legend className="text-[10px] font-bold uppercase tracking-wider text-gray-400">Audio</legend>
        <div className="flex gap-3 text-xs">
          <label className="flex items-center gap-1">
            <input
              type="radio"
              name="lipsync-audio-mode"
              checked={audioMode === 'workspace'}
              onChange={() => setAudioMode('workspace')}
            />
            Workspace audio
          </label>
          <label className="flex items-center gap-1">
            <input
              type="radio"
              name="lipsync-audio-mode"
              checked={audioMode === 'upload'}
              onChange={() => setAudioMode('upload')}
            />
            Upload audio
          </label>
        </div>
        {audioMode === 'workspace' ? (
          <select
            aria-label="Audio"
            value={audioPath}
            onChange={e => setAudioPath(e.target.value)}
            className="w-full bg-black border text-xs p-1.5"
            style={{ borderColor: 'var(--color-border)' }}
          >
            <option value="">Select audio…</option>
            {audios.map(a => (
              <option key={a.path} value={a.path}>
                {a.name}
              </option>
            ))}
          </select>
        ) : (
          <input
            type="file"
            aria-label="Upload audio"
            accept="audio/*"
            onChange={e => setAudioFile(e.target.files?.[0] ?? null)}
            className="w-full text-xs"
          />
        )}
      </fieldset>

      <fieldset className="space-y-2">
        <legend className="text-[10px] font-bold uppercase tracking-wider text-gray-400">Trim</legend>
        <div className="flex gap-3">
          <label className="text-xs text-gray-400">
            Trim start
            <input
              type="number"
              min={0}
              step={0.1}
              aria-label="Trim start"
              value={trimStart}
              onChange={e => setTrimStart(e.target.value)}
              className="ml-2 w-20 bg-black border text-xs p-1"
              style={{ borderColor: 'var(--color-border)' }}
            />
          </label>
          <label className="text-xs text-gray-400">
            Trim end
            <input
              type="number"
              min={0}
              step={0.1}
              aria-label="Trim end"
              value={trimEnd}
              onChange={e => setTrimEnd(e.target.value)}
              className="ml-2 w-20 bg-black border text-xs p-1"
              style={{ borderColor: 'var(--color-border)' }}
            />
          </label>
        </div>
      </fieldset>

      <button
        onClick={() => void handleRun()}
        disabled={!canRun}
        className="w-full py-2 text-xs font-bold uppercase tracking-wider border transition-colors disabled:opacity-40"
        style={{ borderColor: 'var(--color-border)' }}
      >
        Run Lipsync
      </button>

      {job && (
        <div className="space-y-3 border-t pt-3" style={{ borderColor: 'var(--color-border)' }}>
          {job.error && (
            <p role="alert" className="text-xs text-red-400">
              {job.error}
            </p>
          )}
          {job.status === 'DONE' && job.output_path && (
            <div className="space-y-2">
              <video
                src={`${MEDIA_BASE}/${job.output_path}`}
                controls
                className="w-full"
                data-testid="lipsync-preview"
              />
              <a
                href={`${MEDIA_BASE}/${job.output_path}`}
                download
                className="text-xs text-[var(--color-accent)]"
              >
                Download
              </a>
            </div>
          )}
          {job.status === 'DONE' && (
            <div className="flex items-end gap-2">
              <label className="text-xs text-gray-400">
                Shot
                <select
                  aria-label="Shot"
                  value={assignShotId}
                  onChange={e => setAssignShotId(e.target.value)}
                  className="ml-2 bg-black border text-xs p-1"
                  style={{ borderColor: 'var(--color-border)' }}
                >
                  <option value="">Select shot…</option>
                  {shotOptions.map(s => (
                    <option key={s.id} value={s.id}>
                      Shot #{s.shot_number} — {s.prompt_text}
                    </option>
                  ))}
                </select>
              </label>
              <button
                onClick={() => void handleAssign()}
                disabled={!assignShotId}
                className="py-1.5 px-3 text-xs font-bold uppercase tracking-wider border disabled:opacity-40"
                style={{ borderColor: 'var(--color-border)' }}
              >
                Assign to Shot
              </button>
            </div>
          )}
        </div>
      )}

      <div className="border-t pt-3 space-y-2" style={{ borderColor: 'var(--color-border)' }}>
        <span className="text-[10px] font-bold uppercase tracking-wider text-gray-400">History</span>
        {history.length === 0 && <p className="text-xs text-gray-500">No lipsync jobs yet.</p>}
        <ul className="space-y-1">
          {history.map(h => (
            <li key={h.id} className="flex items-center justify-between text-xs">
              <button
                onClick={() => setJob(h)}
                className={`text-left hover:text-[var(--color-accent)] ${job?.id === h.id ? 'text-[var(--color-accent)]' : 'text-gray-300'}`}
              >
                {h.id}
              </button>
              <span className="text-gray-500">[{h.status}]</span>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
};
