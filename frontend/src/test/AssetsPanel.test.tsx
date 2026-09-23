import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, waitFor, fireEvent } from '@testing-library/react';
import { AssetsPanel } from '../components/story/AssetsPanel';

const setCharacters = vi.fn();
const setScenes = vi.fn();
const setSelectedSceneId = vi.fn();
const setSelectedCharId = vi.fn();
const setAnchorFaces = vi.fn();

const uploadReferenceSheet = vi.fn();
const deleteReferenceSheet = vi.fn();

let mockCharacters: any[] = [];

vi.mock('../context/StudioContext', () => ({
  useStudioContext: () => ({
    characters: mockCharacters,
    setCharacters,
    scenes: [],
    setScenes,
    selectedProject: { id: 'p1' },
    selectedSceneId: null,
    setSelectedSceneId,
    selectedCharId: 'c1',
    setSelectedCharId,
    anchorFaces: {},
    setAnchorFaces,
  }),
}));

vi.mock('../hooks/useStudioApi', () => ({
  useStudioApi: () => ({
    uploadReferenceSheet,
    deleteReferenceSheet,
    loadingStates: {},
    createCharacter: vi.fn(),
    createScene: vi.fn(),
    updateCharacter: vi.fn(),
    updateScene: vi.fn(),
    uploadAnchorFace: vi.fn(),
    deleteAnchorFace: vi.fn(),
    loadAnchorFaces: vi.fn(),
  }),
}));

describe('AssetsPanel reference sheet handlers', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockCharacters = [{ id: 'c1', name: 'Hero', locked_traits: [], reference_sheet_url: null }];
  });

  it('updates characters state after reference sheet upload', async () => {
    const updated = { id: 'c1', name: 'Hero', locked_traits: [], reference_sheet_url: '/uploads/reference_sheets/a.png' };
    uploadReferenceSheet.mockResolvedValue(updated);

    const { container } = render(<AssetsPanel />);
    const fileInput = container.querySelector('input[type="file"][accept="image/*"]');
    expect(fileInput).toBeTruthy();

    const file = new File(['x'], 'ref.png', { type: 'image/png' });
    fireEvent.change(fileInput!, { target: { files: [file] } });

    await waitFor(() => expect(uploadReferenceSheet).toHaveBeenCalledWith('c1', file));
    await waitFor(() => expect(setCharacters).toHaveBeenCalled());

    const updater = setCharacters.mock.calls[0][0];
    expect(updater(mockCharacters)).toEqual([updated]);
  });

  it('updates characters state after reference sheet delete', async () => {
    mockCharacters = [{ id: 'c1', name: 'Hero', locked_traits: [], reference_sheet_url: '/uploads/reference_sheets/a.png' }];
    const updated = { id: 'c1', name: 'Hero', locked_traits: [], reference_sheet_url: null };
    deleteReferenceSheet.mockResolvedValue(updated);

    const { getByText } = render(<AssetsPanel />);
    fireEvent.click(getByText('Delete'));

    await waitFor(() => expect(deleteReferenceSheet).toHaveBeenCalledWith('c1'));
    await waitFor(() => expect(setCharacters).toHaveBeenCalled());

    const updater = setCharacters.mock.calls[0][0];
    expect(updater(mockCharacters)).toEqual([updated]);
  });

  it('does not update state when upload fails', async () => {
    uploadReferenceSheet.mockRejectedValue(new Error('upload failed'));

    const { container } = render(<AssetsPanel />);
    const fileInput = container.querySelector('input[type="file"][accept="image/*"]');
    const file = new File(['x'], 'ref.png', { type: 'image/png' });
    fireEvent.change(fileInput!, { target: { files: [file] } });

    await waitFor(() => expect(uploadReferenceSheet).toHaveBeenCalled());
    // give the rejected promise a tick to be swallowed
    await new Promise(r => setTimeout(r, 0));
    expect(setCharacters).not.toHaveBeenCalled();
  });
});
