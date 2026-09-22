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

    expect(screen.getByText('SUPERCOOL')).toBeInTheDocument();
    expect(screen.getByText('AI CINEMATIC STUDIO')).toBeInTheDocument();
  });

  it('renders the project selector', async () => {
    render(<App />);

    expect(screen.getByText('Select project...')).toBeInTheDocument();
  });

  it('renders the Story Bible tab', async () => {
    render(<App />);

    expect(screen.getByText('Story Bible')).toBeInTheDocument();
  });

  it('renders the QA Monitor tab', async () => {
    render(<App />);

    expect(screen.getByText('QA Monitor')).toBeInTheDocument();
  });

  it('renders the Analytics tab', async () => {
    render(<App />);

    expect(screen.getByText('Analytics')).toBeInTheDocument();
  });

  it('renders the Direction Chat panel', async () => {
    render(<App />);

    expect(screen.getByText('Direction Chat')).toBeInTheDocument();
  });

  it('renders the 4K Preview panel', async () => {
    render(<App />);

    expect(screen.getByText('4K Preview')).toBeInTheDocument();
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
      expect(screen.getByText('Start directing your film')).toBeInTheDocument();
    });
  });
});
