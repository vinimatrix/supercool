import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { PersonnelDossier } from '../components/story/PersonnelDossier';

const baseProps = {
  characters: [{ id: 'c1', name: 'Hero', locked_traits: [] }],
  anchorFaces: { c1: [] },
  selectedCharId: 'c1',
  setSelectedCharId: vi.fn(),
  editingCharData: { name: 'Hero', biography: '', locked_traits: [], visual_prompt: '' },
  setEditingCharData: vi.fn(),
  traitInput: '',
  setTraitInput: vi.fn(),
  updateCharacter: vi.fn(),
  uploadAnchorFace: vi.fn(),
  deleteAnchorFace: vi.fn(),
  faceAngle: 'Front',
  setFaceAngle: vi.fn(),
  isPrimaryFace: false,
  setIsPrimaryFace: vi.fn(),
  loadingStates: {},
  fileInputRef: { current: null } as any,
  uploadReferenceSheet: vi.fn(),
  deleteReferenceSheet: vi.fn(),
};

describe('PersonnelDossier', () => {
  it('shows reference sheet dropzone when no image', () => {
    render(<PersonnelDossier {...baseProps} />);
    expect(screen.getByText('REFERENCE SHEET')).toBeInTheDocument();
  });

  it('shows visual reference textarea', () => {
    render(<PersonnelDossier {...baseProps} />);
    expect(screen.getByLabelText(/visual reference/i)).toBeInTheDocument();
  });

  it('shows preview when reference_sheet_url present', () => {
    const char = { ...baseProps.characters[0], reference_sheet_url: '/uploads/reference_sheets/a.png' };
    render(<PersonnelDossier {...baseProps} characters={[char]} />);
    expect(screen.getByRole('img', { name: /reference/i })).toBeInTheDocument();
  });
});
