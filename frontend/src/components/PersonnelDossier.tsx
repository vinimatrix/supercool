import React, { useState } from 'react';
import { Users, Image, Trash2, Plus, CheckCircle, Loader2, X } from 'lucide-react';
import { Character, AnchorFace } from '../api/client';

interface PersonnelDossierProps {
  characters: Character[];
  anchorFaces: Record<string, AnchorFace[]>;
  selectedCharId: string | null;
  setSelectedCharId: (id: string | null) => void;
  editingCharData: { name: string; biography: string; locked_traits: string[] } | null;
  setEditingCharData: (data: { name: string; biography: string; locked_traits: string[] } | null | ((prev: { name: string; biography: string; locked_traits: string[] } | null) => { name: string; biography: string; locked_traits: string[] } | null)) => void;
  traitInput: string;
  setTraitInput: (val: string) => void;
  updateCharacter: () => Promise<void>;
  uploadAnchorFace: (characterId: string, file: File) => Promise<void>;
  deleteAnchorFace: (characterId: string, faceId: string) => Promise<void>;
  faceAngle: string;
  setFaceAngle: (angle: string) => void;
  isPrimaryFace: boolean;
  setIsPrimaryFace: (primary: boolean) => void;
  loadingStates: Record<string, boolean>;
  fileInputRef: React.RefObject<HTMLInputElement>;
}

export const PersonnelDossier: React.FC<PersonnelDossierProps> = ({
  characters,
  anchorFaces,
  selectedCharId,
  setSelectedCharId,
  editingCharData,
  setEditingCharData,
  traitInput,
  setTraitInput,
  updateCharacter,
  uploadAnchorFace,
  deleteAnchorFace,
  faceAngle,
  setFaceAngle,
  isPrimaryFace,
  setIsPrimaryFace,
  loadingStates,
  fileInputRef,
}) => {
  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <Users className="w-3 h-3 text-[var(--color-accent)]" />
          <span className="text-[10px] font-bold text-gray-500 uppercase tracking-tight">Personnel Dossiers</span>
        </div>
      </div>
      <div className="space-y-3">
        {characters.map(c => (
          <div
            key={c.id}
            onClick={() => setSelectedCharId(selectedCharId === c.id ? null : c.id)}
            className={`p-3 rounded border transition-all cursor-pointer ${
              selectedCharId === c.id ? 'active-context-glow bg-[var(--color-accent-muted)]' : 'border-transparent bg-black/20 hover:bg-black/40'
            }`}
          >
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-bold text-white">{c.name}</span>
              <span className="text-[9px] mono text-gray-500">ID: {c.id.slice(0,5)}</span>
            </div>
            <div className="flex flex-wrap gap-1">
              {c.locked_traits.map((t, i) => (
                <span key={i} className="trait-chip">{t}</span>
              ))}
            </div>
            {selectedCharId === c.id && (
              <div className="mt-3 pt-3 border-t border-[var(--color-border)] space-y-3">
                <div className="space-y-2">
                  <input
                    value={editingCharData?.name || ''}
                    onChange={e => setEditingCharData(prev => prev ? { ...prev, name: e.target.value } : null)}
                    className="w-full bg-black/40 text-xs px-2 py-1 rounded border mono text-white focus:outline-none focus:border-[var(--color-accent)]"
                    style={{ borderColor: 'var(--color-border)' }}
                    placeholder="Name"
                  />
                  <textarea
                    value={editingCharData?.biography || ''}
                    onChange={e => setEditingCharData(prev => prev ? { ...prev, biography: e.target.value } : null)}
                    className="w-full bg-black/40 text-xs px-2 py-1 rounded border mono text-white focus:outline-none focus:border-[var(--color-accent)] h-20 resize-none"
                    style={{ borderColor: 'var(--color-border)' }}
                    placeholder="Character Biography..."
                  />
                  <div className="flex flex-wrap gap-1">
                    {editingCharData?.locked_traits.map((t, i) => (
                      <span key={i} className="trait-chip flex items-center gap-1">
                        {t}
                        <X className="w-2 h-2 cursor-pointer hover:text-red-500" onClick={(e) => {
                          e.stopPropagation();
                          setEditingCharData(prev => prev ? { ...prev, locked_traits: prev.locked_traits.filter((_, idx) => idx !== i) } : null);
                        }} />
                      </span>
                    ))}
                    <div className="flex gap-1">
                      <input
                        value={traitInput}
                        onChange={e => setTraitInput(e.target.value)}
                        onKeyDown={e => {
                          if (e.key === 'Enter') {
                            e.preventDefault();
                            const val = traitInput.trim();
                            if (val && !editingCharData?.locked_traits.includes(val)) {
                              setEditingCharData(prev => prev ? { ...prev, locked_traits: [...prev.locked_traits, val] } : null);
                              setTraitInput('');
                            }
                          }
                        }}
                        placeholder="Add trait..."
                        className="bg-black/40 text-[10px] px-2 py-0.5 rounded border mono text-white focus:outline-none"
                        style={{ borderColor: 'var(--color-border)' }}
                      />
                    </div>
                  </div>
                  <button
                    onClick={(e) => { e.stopPropagation(); updateCharacter(); }}
                    disabled={loadingStates['character-update']}
                    className="w-full py-1 bg-[var(--color-accent)] text-black rounded text-[10px] font-bold hover:opacity-90 flex items-center justify-center gap-1"
                  >
                    {loadingStates['character-update'] ? <Loader2 className="w-3 h-3 animate-spin" /> : <CheckCircle className="w-3 h-3" />}
                    SAVE DOSSIER
                  </button>
                </div>
                <div className="pt-3 border-t border-[var(--color-border)]">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <Image className="w-3 h-3 text-gray-500" />
                      <span className="text-[9px] mono text-gray-500 uppercase">Anchor Faces</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <select
                        value={faceAngle}
                        onChange={e => setFaceAngle(e.target.value)}
                        className="bg-black/40 text-[9px] mono text-gray-400 border rounded px-1 py-0.5 outline-none"
                        style={{ borderColor: 'var(--color-border)' }}
                      >
                        <option value="Front">Front</option>
                        <option value="Profile">Profile</option>
                        <option value="3/4">3/4 View</option>
                        <option value="Top">Top</option>
                        <option value="Bottom">Bottom</option>
                      </select>
                      <label className="flex items-center gap-1 text-[9px] mono text-gray-400 cursor-pointer">
                        <input
                          type="checkbox"
                          checked={isPrimaryFace}
                          onChange={e => setIsPrimaryFace(e.target.checked)}
                          className="accent-[var(--color-accent)]"
                        />
                        PRIMARY
                      </label>
                    </div>
                  </div>
                  <div className="grid grid-cols-3 gap-1 mb-2">
                    {(anchorFaces[c.id] || []).map(face => (
                      <div key={face.id} className="relative group aspect-square">
                        <img
                          src={face.image_url}
                          alt={face.view_angle || 'face'}
                          className="w-full h-full object-cover rounded border border-[var(--color-border)]"
                        />
                        <button
                          onClick={(e) => { e.stopPropagation(); deleteAnchorFace(c.id, face.id); }}
                          className="absolute top-0 right-0 p-0.5 bg-red-600 rounded opacity-0 group-hover:opacity-100 transition-opacity"
                        >
                          <Trash2 className="w-2 h-2 text-white" />
                        </button>
                        {face.is_primary && (
                          <div className="absolute bottom-0 left-0 right-0 px-1 bg-[var(--color-accent)] text-black text-[7px] font-bold text-center rounded-b">PRIMARY</div>
                        )}
                      </div>
                    ))}
                  </div>
                  <button
                    onClick={(e) => { e.stopPropagation(); fileInputRef.current?.click(); }}
                    className="w-full py-1 border border-dashed rounded text-[9px] mono text-gray-500 hover:text-[var(--color-accent)] hover:border-[var(--color-accent)] transition-colors"
                    style={{ borderColor: 'var(--color-border)' }}
                  >
                    + UPLOAD REFERENCE
                  </button>
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};
