import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { DriftPanel } from '../components/DriftPanel';
import { driftApi } from '../api/drift';

vi.mock('../api/drift', () => ({
  driftApi: {
    status: vi.fn(),
    connect: vi.fn(),
    disconnect: vi.fn(),
    executePlan: vi.fn(),
    saveProject: vi.fn(),
    exportVideo: vi.fn(),
  },
}));

const mockedDriftApi = vi.mocked(driftApi, true);

describe('DriftPanel', () => {
  const mockOnPlanExecuted = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    mockedDriftApi.status.mockResolvedValue({ connected: false });
  });

  it('renders connect button when disconnected', async () => {
    render(<DriftPanel editPlan={null} onPlanExecuted={mockOnPlanExecuted} />);

    await waitFor(() => {
      expect(screen.getByText('Connect')).toBeInTheDocument();
    });
  });

  it('shows connected status when connected', async () => {
    mockedDriftApi.status.mockResolvedValue({
      connected: true,
      port: 4731,
      project_loaded: true,
    });

    render(<DriftPanel editPlan={null} onPlanExecuted={mockOnPlanExecuted} />);

    await waitFor(() => {
      expect(screen.getByText('Connected')).toBeInTheDocument();
    });
  });

  it('calls connect when connect button clicked', async () => {
    mockedDriftApi.connect.mockResolvedValue({ status: 'ok', port: 4731 });

    render(<DriftPanel editPlan={null} onPlanExecuted={mockOnPlanExecuted} />);

    await waitFor(() => {
      expect(screen.getByText('Connect')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText('Connect'));

    await waitFor(() => {
      expect(mockedDriftApi.connect).toHaveBeenCalledWith(4731);
    });
  });

  it('shows execute plan button when connected and plan exists', async () => {
    mockedDriftApi.status.mockResolvedValue({
      connected: true,
      port: 4731,
      project_loaded: true,
    });

    const editPlan = {
      clips: [{ path: '/clip.mp4', duration: 5 }],
      transitions: [],
    };

    render(<DriftPanel editPlan={editPlan} onPlanExecuted={mockOnPlanExecuted} />);

    await waitFor(() => {
      expect(screen.getByText('Execute Plan')).toBeInTheDocument();
    });
  });

  it('does not show execute plan button when no plan', async () => {
    mockedDriftApi.status.mockResolvedValue({
      connected: true,
      port: 4731,
      project_loaded: true,
    });

    render(<DriftPanel editPlan={null} onPlanExecuted={mockOnPlanExecuted} />);

    await waitFor(() => {
      expect(screen.getByText('Connected')).toBeInTheDocument();
    });

    expect(screen.queryByText('Execute Plan')).not.toBeInTheDocument();
  });

  it('shows error on connection failure', async () => {
    mockedDriftApi.status.mockRejectedValue(new Error('Connection refused'));

    render(<DriftPanel editPlan={null} onPlanExecuted={mockOnPlanExecuted} />);

    await waitFor(() => {
      expect(screen.getByText('Disconnected')).toBeInTheDocument();
    });
  });
});
