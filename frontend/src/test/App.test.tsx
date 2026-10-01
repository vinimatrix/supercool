import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import App from '../App';
import { projectsApi, charactersApi, scenesApi, shotsApi } from '../api/client';

vi.mock('../api/client', () => ({
  projectsApi: { list: vi.fn(), get: vi.fn(), create: vi.fn() },
  charactersApi: { list: vi.fn(), create: vi.fn() },
  scenesApi: { list: vi.fn(), create: vi.fn() },
  shotsApi: { list: vi.fn(), create: vi.fn(), uploadVideo: vi.fn(), assignVideo: vi.fn() },
  renderApi: { start: vi.fn(), getJob: vi.fn() },
  anchorFacesApi: { list: vi.fn(), upload: vi.fn(), delete: vi.fn() },
  creativeApi: { render: vi.fn(), workspace: vi.fn() },
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
}));

vi.mock('../api/drift', () => ({
  driftApi: {
    status: vi.fn().mockResolvedValue({ connected: false }),
    connect: vi.fn(),
    disconnect: vi.fn(),
    executePlan: vi.fn(),
  },
}));

const mockedProjectsApi = vi.mocked(projectsApi, true);
const mockedScenesApi = vi.mocked(scenesApi, true);
const mockedShotsApi = vi.mocked(shotsApi, true);
const mockedCharactersApi = vi.mocked(charactersApi, true);

describe('App', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockedProjectsApi.list.mockResolvedValue({ data: [], status: 200, statusText: 'OK', headers: {}, config: {} as any });
    mockedScenesApi.list.mockResolvedValue({ data: [], status: 200, statusText: 'OK', headers: {}, config: {} as any });
    mockedShotsApi.list.mockResolvedValue({ data: [], status: 200, statusText: 'OK', headers: {}, config: {} as any });
    mockedCharactersApi.list.mockResolvedValue({ data: [], status: 200, statusText: 'OK', headers: {}, config: {} as any });
  });

  it('renders the SUPERCOOL header', async () => {
    render(<App />);

    expect(screen.getByText('Supercool Studio')).toBeInTheDocument();
  });

  it('renders the project selector', async () => {
    render(<App />);

    expect(screen.getByText('Select Active Project...')).toBeInTheDocument();
  });

  it('renders the Story Bible tab', async () => {
    render(<App />);

    expect(screen.getByText('Story Bible')).toBeInTheDocument();
  });

  it('renders the QA tab', async () => {
    render(<App />);

    expect(screen.getByText('QA')).toBeInTheDocument();
  });

  it('renders the Data tab', async () => {
    render(<App />);

    expect(screen.getByText('Data')).toBeInTheDocument();
  });

  it('renders the YouTube tab', async () => {
    render(<App />);

    expect(screen.getByText('YT')).toBeInTheDocument();
  });

  it('renders the Drift tab', async () => {
    render(<App />);

    expect(screen.getByText('Drift')).toBeInTheDocument();
  });

  it('renders the Command Center', async () => {
    render(<App />);

    expect(screen.getByText('Command Center')).toBeInTheDocument();
  });

  it('renders the 4K Preview placeholder', async () => {
    render(<App />);

    expect(screen.getByText('NO SIGNAL')).toBeInTheDocument();
  });

  it('renders the Shot Timeline panel', async () => {
    render(<App />);

    expect(screen.getByText('Shot Timeline')).toBeInTheDocument();
  });

  it('loads projects on mount', async () => {
    const mockProjects = [
      { id: '1', title: 'Boruto Film', description: null, target_resolution: '4K', fps: 24, aspect_ratio: '16:9', created_at: '2024-01-01' },
    ];
    mockedProjectsApi.list.mockResolvedValue({ data: mockProjects, status: 200, statusText: 'OK', headers: {}, config: {} as any });

    render(<App />);

    await waitFor(() => {
      expect(mockedProjectsApi.list).toHaveBeenCalled();
    });
  });

  it('shows empty state when no projects', async () => {
    render(<App />);

    await waitFor(() => {
      expect(screen.getByText('WAITING FOR INPUT')).toBeInTheDocument();
    });
  });
});
