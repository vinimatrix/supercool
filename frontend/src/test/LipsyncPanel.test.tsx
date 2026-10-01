import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import { LipsyncPanel } from '../components/lipsync/LipsyncPanel';
import { lipsyncApi, scenesApi, shotsApi } from '../api/client';
import { useStudioContext } from '../context/StudioContext';

vi.mock('../api/client', () => ({
  lipsyncApi: {
    listVideos: vi.fn(),
    listAudios: vi.fn(),
    uploadVideo: vi.fn(),
    uploadAudio: vi.fn(),
    createJob: vi.fn(),
    listJobs: vi.fn(),
    getJob: vi.fn(),
    assignJob: vi.fn(),
  },
  scenesApi: { list: vi.fn() },
  shotsApi: { list: vi.fn() },
}));

vi.mock('../context/StudioContext', () => ({
  useStudioContext: vi.fn(),
}));

const mockedLipsyncApi = vi.mocked(lipsyncApi, true);
const mockedScenesApi = vi.mocked(scenesApi, true);
const mockedShotsApi = vi.mocked(shotsApi, true);
const mockedUseStudioContext = vi.mocked(useStudioContext, true);

const videos = [
  { path: 'workspace/shots/take1.mp4', name: 'take1.mp4', size: 1024, duration: 12 },
];
const audios = [
  { path: 'workspace/audio/line1.wav', name: 'line1.wav', size: 2048, duration: null },
];
const shot = {
  id: 'shot-1',
  scene_id: 's1',
  shot_number: 1,
  shot_type: null,
  motion_type: null,
  assigned_engine: null,
  prompt_text: 'Take 1',
  injected_prompt: null,
  dialogue_text: null,
  video_path: null,
  status: 'SCRIPTED',
};
const doneJob = {
  id: 'job-2',
  project_id: 'p1',
  status: 'DONE',
  stage: null,
  video_source: 'workspace/shots/take1.mp4',
  trim_start: 0,
  trim_end: 3,
  audio_path: 'workspace/audio/line1.wav',
  output_path: 'workspace/lipsync/lipsync_job-2.mp4',
  shot_id: null,
  error: null,
  created_at: '2026-09-30T00:00:00',
  completed_at: '2026-09-30T00:01:00',
};

const flush = async () => {
  await act(async () => {
    await vi.advanceTimersByTimeAsync(0);
  });
};

const waitForCondition = async (fn: () => boolean, message: string) => {
  for (let i = 0; i < 100; i++) {
    if (fn()) return;
    await act(async () => {
      await vi.advanceTimersByTimeAsync(100);
    });
  }
  throw new Error(message);
};

const selectVideoAndAudio = () => {
  fireEvent.change(screen.getByLabelText('Video'), {
    target: { value: 'workspace/shots/take1.mp4' },
  });
  fireEvent.change(screen.getByLabelText('Audio'), {
    target: { value: 'workspace/audio/line1.wav' },
  });
  fireEvent.change(screen.getByLabelText('Trim end'), { target: { value: '3' } });
};

describe('LipsyncPanel', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockedUseStudioContext.mockReturnValue({
      selectedProject: { id: 'p1', title: 'Project One' },
      setShots: vi.fn(),
    } as any);
    mockedLipsyncApi.listVideos.mockResolvedValue({ data: videos } as any);
    mockedLipsyncApi.listAudios.mockResolvedValue({ data: audios } as any);
    mockedLipsyncApi.listJobs.mockResolvedValue({ data: [] } as any);
    mockedScenesApi.list.mockResolvedValue({
      data: [{ id: 's1', project_id: 'p1', scene_number: 1, title: 'Scene 1', location: null, time_of_day: null, summary: null }],
    } as any);
    mockedShotsApi.list.mockResolvedValue({ data: [shot] } as any);
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('loads workspace videos, audios, and shots on mount', async () => {
    render(<LipsyncPanel />);

    await waitFor(() => {
      expect(mockedLipsyncApi.listVideos).toHaveBeenCalledWith('p1');
      expect(mockedLipsyncApi.listAudios).toHaveBeenCalledWith('p1');
      expect(mockedLipsyncApi.listJobs).toHaveBeenCalledWith('p1');
      expect(mockedShotsApi.list).toHaveBeenCalledWith('s1');
    });

    expect(screen.getByLabelText('Video')).toBeInTheDocument();
    expect(screen.getByLabelText('Audio')).toBeInTheDocument();
    expect(screen.getByText('take1.mp4')).toBeInTheDocument();
    expect(screen.getByText('line1.wav')).toBeInTheDocument();
  });

  it('keeps Run disabled until video, audio, and a valid trim are selected', async () => {
    render(<LipsyncPanel />);

    await waitFor(() => {
      expect(screen.getByLabelText('Video')).toBeInTheDocument();
    });

    const runButton = screen.getByRole('button', { name: 'Run Lipsync' });
    expect(runButton).toBeDisabled();

    fireEvent.change(screen.getByLabelText('Video'), {
      target: { value: 'workspace/shots/take1.mp4' },
    });
    expect(screen.getByRole('button', { name: 'Run Lipsync' })).toBeDisabled();

    fireEvent.change(screen.getByLabelText('Audio'), {
      target: { value: 'workspace/audio/line1.wav' },
    });
    expect(screen.getByRole('button', { name: 'Run Lipsync' })).toBeDisabled();

    fireEvent.change(screen.getByLabelText('Trim end'), { target: { value: '3' } });
    expect(screen.getByRole('button', { name: 'Run Lipsync' })).toBeEnabled();
  });

  it('starts a job with the snake_case numeric payload', async () => {
    const createdJob = { ...doneJob, id: 'job-1', status: 'PENDING', output_path: null };
    mockedLipsyncApi.createJob.mockResolvedValue({ data: createdJob } as any);
    mockedLipsyncApi.getJob.mockResolvedValue({ data: { ...createdJob, status: 'RUNNING' } } as any);

    render(<LipsyncPanel />);
    await waitFor(() => {
      expect(screen.getByLabelText('Video')).toBeInTheDocument();
    });

    selectVideoAndAudio();
    fireEvent.click(screen.getByRole('button', { name: 'Run Lipsync' }));

    await waitFor(() => {
      expect(mockedLipsyncApi.createJob).toHaveBeenCalledWith({
        project_id: 'p1',
        video_path: 'workspace/shots/take1.mp4',
        trim_start: 0,
        trim_end: 3,
        audio_path: 'workspace/audio/line1.wav',
      });
    });

    await waitFor(() => {
      expect(screen.getByText('RUNNING')).toBeInTheDocument();
    });
  });

  it('polls every 2 seconds while the job is active and stops once DONE', async () => {
    vi.useFakeTimers();
    const createdJob = { ...doneJob, id: 'job-1', status: 'PENDING', output_path: null };
    mockedLipsyncApi.createJob.mockResolvedValue({ data: createdJob } as any);
    mockedLipsyncApi.getJob.mockResolvedValue({ data: { ...createdJob, status: 'RUNNING' } } as any);

    render(<LipsyncPanel />);
    await flush();
    await waitForCondition(
      () => screen.queryByText('take1.mp4') !== null,
      'workspace lists never loaded'
    );
    selectVideoAndAudio();
    fireEvent.click(screen.getByRole('button', { name: 'Run Lipsync' }));

    await waitForCondition(
      () => screen.queryByText('RUNNING') !== null,
      'job never reached RUNNING'
    );
    const before = mockedLipsyncApi.getJob.mock.calls.length;
    expect(before).toBeGreaterThan(0);

    await act(async () => {
      await vi.advanceTimersByTimeAsync(2000);
    });
    expect(mockedLipsyncApi.getJob.mock.calls.length).toBeGreaterThan(before);

    mockedLipsyncApi.getJob.mockResolvedValue({ data: doneJob } as any);
    await waitForCondition(
      () => screen.queryByText('DONE') !== null,
      'job never reached DONE'
    );
    expect(screen.getByText('Download')).toBeInTheDocument();
    const afterDone = mockedLipsyncApi.getJob.mock.calls.length;
    await act(async () => {
      await vi.advanceTimersByTimeAsync(6000);
    });
    expect(mockedLipsyncApi.getJob.mock.calls.length).toBe(afterDone);
  });

  it('stops polling after 3 consecutive failures and surfaces an error', async () => {
    vi.useFakeTimers();
    const createdJob = { ...doneJob, id: 'job-1', status: 'PENDING', output_path: null };
    mockedLipsyncApi.createJob.mockResolvedValue({ data: createdJob } as any);
    mockedLipsyncApi.getJob.mockRejectedValue(new Error('network down'));

    render(<LipsyncPanel />);
    await flush();
    await waitForCondition(
      () => screen.queryByText('take1.mp4') !== null,
      'workspace lists never loaded'
    );
    selectVideoAndAudio();
    fireEvent.click(screen.getByRole('button', { name: 'Run Lipsync' }));

    await waitForCondition(
      () => screen.queryByText('Lost connection while polling job status') !== null,
      'polling failure error never surfaced'
    );
    const afterStop = mockedLipsyncApi.getJob.mock.calls.length;
    await act(async () => {
      await vi.advanceTimersByTimeAsync(10000);
    });
    expect(mockedLipsyncApi.getJob.mock.calls.length).toBe(afterStop);
  });

  it('stops polling when unmounted', async () => {
    vi.useFakeTimers();
    const createdJob = { ...doneJob, id: 'job-1', status: 'PENDING', output_path: null };
    mockedLipsyncApi.createJob.mockResolvedValue({ data: createdJob } as any);
    mockedLipsyncApi.getJob.mockResolvedValue({ data: { ...createdJob, status: 'RUNNING' } } as any);

    const { unmount } = render(<LipsyncPanel />);
    await flush();
    await waitForCondition(
      () => screen.queryByText('take1.mp4') !== null,
      'workspace lists never loaded'
    );
    selectVideoAndAudio();
    fireEvent.click(screen.getByRole('button', { name: 'Run Lipsync' }));

    await waitForCondition(
      () => mockedLipsyncApi.getJob.mock.calls.length > 0,
      'polling never started'
    );
    const before = mockedLipsyncApi.getJob.mock.calls.length;
    unmount();
    await act(async () => {
      await vi.advanceTimersByTimeAsync(6000);
    });
    expect(mockedLipsyncApi.getJob.mock.calls.length).toBe(before);
  });

  it('assigns a selected DONE job to a shot', async () => {
    mockedLipsyncApi.listJobs.mockResolvedValue({ data: [doneJob] } as any);
    mockedLipsyncApi.assignJob.mockResolvedValue({ data: { ...doneJob, shot_id: 'shot-1' } } as any);

    render(<LipsyncPanel />);
    await waitFor(() => {
      expect(screen.getByText('job-2')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText('job-2'));
    fireEvent.change(screen.getByLabelText('Shot'), { target: { value: 'shot-1' } });
    fireEvent.click(screen.getByRole('button', { name: 'Assign to Shot' }));

    await waitFor(() => {
      expect(mockedLipsyncApi.assignJob).toHaveBeenCalledWith('job-2', 'shot-1');
    });
  });

  it('shows job.error for a FAILED job', async () => {
    const failedJob = {
      ...doneJob,
      id: 'job-3',
      status: 'FAILED',
      output_path: null,
      error: 'MuseTalk failed: model not found',
    };
    mockedLipsyncApi.listJobs.mockResolvedValue({ data: [failedJob] } as any);

    render(<LipsyncPanel />);
    await waitFor(() => {
      expect(screen.getByText('job-3')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText('job-3'));

    expect(screen.getByText('FAILED')).toBeInTheDocument();
    expect(screen.getByText('MuseTalk failed: model not found')).toBeInTheDocument();
  });
});
