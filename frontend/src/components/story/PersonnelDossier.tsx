import React from 'react';
import { User, Upload, Trash2, Camera, Lock, Unlock, Image as ImageIcon } from 'lucide-react';
import { Button } from '../ui/Button';
import { Input } from '../ui/Input';

interface PersonnelDossierProps {
  characters: any[];
  anchorFaces: Record<string, any[]>;
  selectedCharId: string | null;
  setSelectedCharId: (id: string | null) => void;
  editingCharData: any;
  setEditingCharData: (data: any) => void;
  traitInput: string;
  setTraitInput: (val: string) => void;
  updateCharacter: () => Promise<void>;
  uploadAnchorFace: (charId: string, file: File) => Promise<void>;
  deleteAnchorFace: (faceId: string) => Promise<void>;
  faceAngle: string;
  setFaceAngle: (val: string) => void;
  isPrimaryFace: boolean;
  setIsPrimaryFace: (val: boolean) => void;
  loadingStates: Record<string, boolean>;
  fileInputRef: React.RefObject<HTMLInputElement>;
  uploadReferenceSheet?: (charId: string, file: File) => Promise<any>;
  deleteReferenceSheet?: (charId: string) => Promise<any>;
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
  uploadReferenceSheet,
  deleteReferenceSheet
}) => {
  const activeChar = characters.find(c => c.id === selectedCharId);
  const faces = selectedCharId ? anchorFaces[selectedCharId] || [] : [];

  return (
    <div className="flex flex-col gap-4">
      {/* Character List */}
      <div className="flex flex-wrap gap-2">
        {characters.map(char => (
          <button
            key={char.id}
            onClick={() => setSelectedCharId(char.id)}
            className={`px-2 py-1 rounded text-[10px] mono transition-all border ${
              selectedCharId === char.id
                ? 'bg-[var(--color-accent)] text-black border-[var(--color-accent)] font-bold'
                : 'bg-black/40 text-gray-400 border-[var(--color-border)] hover:border-gray-600'
            }`}
          >
            {char.name}
          </button>
        ))}
      </div>

      {activeChar && editingCharData && (
        <div className="p-3 rounded-sm border border-[var(--color-border)] bg-black/60 space-y-4 animate-in fade-in slide-in-from-left-2 duration-200">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <User className="w-3 h-3 text-[var(--color-accent)]" />
              <span className="text-[10px] font-bold text-gray-500 uppercase tracking-widest">Personnel Dossier: {activeChar.name}</span>
            </div>
            <Button onClick={updateCharacter} loading={loadingStates['character-update']} className="px-2 py-0.5 text-[9px]">
              SAVE CHANGES
            </Button>
          </div>

          <div className="space-y-3">
            <div className="space-y-1">
              <label className="text-[8px] mono text-gray-600 uppercase">Full Name</label>
              <Input
                value={editingCharData.name}
                onChange={e => setEditingCharData({...editingCharData, name: e.target.value})}
                className="h-7 text-xs"
              />
            </div>
            <div className="space-y-1">
              <label className="text-[8px] mono text-gray-600 uppercase">Biography / Notes</label>
              <textarea
                value={editingCharData.biography}
                onChange={e => setEditingCharData({...editingCharData, biography: e.target.value})}
                className="w-full bg-black/40 text-xs p-2 rounded border border-[var(--color-border)] mono text-white h-20 resize-none focus:border-[var(--color-accent)] outline-none"
              />
            </div>
            <div className="space-y-1">
              <label className="text-[8px] mono text-gray-600 uppercase">
                Visual Reference (for AI)
              </label>
              <textarea
                aria-label="Visual Reference"
                value={editingCharData.visual_prompt ?? ''}
                onChange={(e) => setEditingCharData({ ...editingCharData, visual_prompt: e.target.value })}
                placeholder="Appearance, wardrobe, personality for renders..."
                className="w-full bg-black/40 text-xs p-2 rounded border border-[var(--color-border)] mono text-white h-24 resize-none focus:border-[var(--color-accent)] outline-none"
              />
            </div>
          </div>

          <div className="pt-3 border-t border-[var(--color-border)] space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Camera className="w-3 h-3 text-gray-500" />
                <span className="text-[9px] mono text-gray-500 uppercase">Anchor Faces</span>
              </div>
              <div className="flex items-center gap-2">
                <select
                  value={faceAngle}
                  onChange={e => setFaceAngle(e.target.value)}
                  className="bg-black/40 text-[8px] mono p-1 rounded border border-[var(--color-border)] text-gray-400 outline-none"
                >
                  <option value="Front">Front</option>
                  <option value="Profile">Profile</option>
                  <option value="Three-Quarter">3/4 View</option>
                </select>
                <label className="flex items-center gap-1 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={isPrimaryFace}
                    onChange={e => setIsPrimaryFace(e.target.checked)}
                    className="w-2 h-2 accent-[var(--color-accent)]"
                  />
                  <span className="text-[8px] mono text-gray-500 uppercase">Primary</span>
                </label>
              </div>
            </div>

            <div className="grid grid-cols-3 gap-2">
              {faces.map(face => (
                <div key={face.id} className="relative aspect-square rounded-sm border border-[var(--color-border)] bg-black/40 group overflow-hidden">
                  <img
                    src={`http://localhost:8000/workspace/faces/${face.file_path.split('/').pop()}`}
                    className="w-full h-full object-cover opacity-60 group-hover:opacity-100 transition-opacity"
                  />
                  <div className="absolute bottom-0 left-0 right-0 p-1 bg-black/80 text-[7px] mono text-white truncate">
                    {face.angle}
                  </div>
                  <button
                    onClick={() => deleteAnchorFace(face.id)}
                    className="absolute top-1 right-1 p-1 bg-red-500/20 text-red-400 rounded-full opacity-0 group-hover:opacity-100 transition-opacity"
                  >
                    <Trash2 className="w-2 h-2" />
                  </button>
                </div>
              ))}
              <label className="aspect-square rounded-sm border border-dashed border-[var(--color-border)] flex flex-col items-center justify-center cursor-pointer hover:border-[var(--color-accent)] hover:text-[var(--color-accent)] transition-all group">
                <Upload className="w-3 h-3 mb-1 opacity-50 group-hover:opacity-100" />
                <span className="text-[7px] mono text-gray-500 group-hover:text-[var(--color-accent)] uppercase">Add Face</span>
                <input
                  type="file"
                  className="hidden"
                  onChange={e => {
                    const file = e.target.files?.[0];
                    if (file) uploadAnchorFace(activeChar.id, file);
                  }}
                />
              </label>
            </div>
          </div>

          <div className="pt-3 border-t border-[var(--color-border)] space-y-2">
            <div className="flex items-center gap-2">
              <ImageIcon className="w-3 h-3 text-gray-500" />
              <span className="text-[9px] mono text-gray-500 uppercase">Reference Sheet</span>
            </div>
            {activeChar.reference_sheet_url ? (
              <div className="relative aspect-[3/4] max-w-[120px] rounded border border-[var(--color-border)] bg-black group">
                <img
                  src={`http://localhost:8000${activeChar.reference_sheet_url}`}
                  alt="Character reference sheet"
                  className="w-full h-full object-contain"
                />
                <div className="absolute top-1 right-1 flex gap-1 opacity-0 group-hover:opacity-100">
                  <label className="cursor-pointer px-1 py-0.5 bg-black/80 text-[8px] mono rounded border border-white/20">
                    Replace
                    <input type="file" accept="image/*" className="hidden"
                      onChange={(e) => {
                        const f = e.target.files?.[0];
                        if (f) uploadReferenceSheet?.(activeChar.id, f);
                      }} />
                  </label>
                  <button
                    onClick={() => deleteReferenceSheet?.(activeChar.id)}
                    className="px-1 py-0.5 bg-red-500/40 text-[8px] mono rounded"
                  >Delete</button>
                </div>
              </div>
            ) : (
              <label className="flex flex-col items-center justify-center aspect-[3/4] max-w-[120px] rounded border border-dashed border-[var(--color-border)] cursor-pointer hover:border-[var(--color-accent)]">
                <Upload className="w-4 h-4 mb-1 opacity-50" />
                <span className="text-[8px] mono text-gray-500 uppercase">REFERENCE SHEET</span>
                <input type="file" accept="image/*" className="hidden"
                  onChange={(e) => {
                    const f = e.target.files?.[0];
                    if (f) uploadReferenceSheet?.(activeChar.id, f);
                  }} />
              </label>
            )}
          </div>

          <div className="pt-3 border-t border-[var(--color-border)]">
            <div className="flex items-center gap-2 mb-2">
              <Lock className="w-3 h-3 text-gray-500" />
              <span className="text-[9px] mono text-gray-500 uppercase">Locked Traits</span>
            </div>
            <div className="flex flex-wrap gap-1">
              {editingCharData.locked_traits.map((trait: string, i: number) => (
                <span key={i} className="px-1.5 py-0.5 rounded-sm bg-black/60 border border-[var(--color-border)] text-[9px] mono text-gray-400 flex items-center gap-1">
                  {trait}
                  <Unlock className="w-2 h-2 cursor-pointer hover:text-red-400" />
                </span>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
