import React, { useState, useRef } from 'react';
import { Users, Clapperboard, Plus, MapPin, Clock, FileText, Settings } from 'lucide-react';
import { PersonnelDossier } from './PersonnelDossier';
import { useStudioContext } from '../../context/StudioContext';
import { useStudioApi } from '../../hooks/useStudioApi';
import { Button } from '../ui/Button';
import { Input } from '../ui/Input';

export const AssetsPanel: React.FC = () => {
  const {
    characters, setCharacters,
    scenes, setScenes,
    selectedProject,
    selectedSceneId, setSelectedSceneId,
    selectedCharId, setSelectedCharId,
    anchorFaces, setAnchorFaces
  } = useStudioContext();

  const api = useStudioApi((msg, type) => {
    console.log(`[Toast ${type}] ${msg}`);
  });

  // Local state for creators
  const [newCharName, setNewCharName] = useState('');
  const [newSceneTitle, setNewSceneTitle] = useState('');
  const [traitInput, setTraitInput] = useState('');
  const [newCharTraits, setNewCharTraits] = useState<string[]>([]);

  // Edit state for the active character
  const [editingCharData, setEditingCharData] = useState<{
    name: string; biography: string; locked_traits: string[]; visual_prompt: string;
  } | null>(null);
  const [faceAngle, setFaceAngle] = useState('Front');
  const [isPrimaryFace, setIsPrimaryFace] = useState(false);

  // Edit state for the active scene
  const [editingSceneData, setEditingSceneData] = useState<{ title: string; location: string; time_of_day: string; summary: string } | null>(null);

  // Sync editing data when character is selected
  React.useEffect(() => {
    if (selectedCharId) {
      const char = characters.find(c => c.id === selectedCharId);
      if (char) {
        setEditingCharData({
          name: char.name,
          biography: char.biography || '',
          locked_traits: [...char.locked_traits],
          visual_prompt: char.visual_prompt || ''
        });
      }
    } else {
      setEditingCharData(null);
    }
  }, [selectedCharId, characters]);

  // Sync editing data when scene is selected
  React.useEffect(() => {
    if (selectedSceneId) {
      const scene = scenes.find(s => s.id === selectedSceneId);
      if (scene) {
        setEditingSceneData({
          title: scene.title || '',
          location: scene.location || '',
          time_of_day: scene.time_of_day || '',
          summary: scene.summary || ''
        });
      }
    } else {
      setEditingSceneData(null);
    }
  }, [selectedSceneId, scenes]);

  const handleCreateCharacter = async () => {
    if (!selectedProject || !newCharName.trim()) return;
    try {
      const char = await api.createCharacter(selectedProject.id, newCharName, newCharTraits);
      setCharacters([...characters, char]);
      setNewCharName('');
      setNewCharTraits([]);
    } catch (e) { console.error(e); }
  };

  const handleCreateScene = async () => {
    if (!selectedProject || !newSceneTitle.trim()) return;
    try {
      const scene = await api.createScene(selectedProject.id, newSceneTitle, scenes.length + 1);
      setScenes([...scenes, scene]);
      setNewSceneTitle('');
      setSelectedSceneId(scene.id);
    } catch (e) { console.error(e); }
  };

  const handleUpdateCharacter = async () => {
    if (!selectedCharId || !editingCharData) return;
    try {
      const updated = await api.updateCharacter(selectedCharId, editingCharData);
      setCharacters(characters.map(c => c.id === selectedCharId ? updated : c));
    } catch (e) { console.error(e); }
  };

  const handleUpdateScene = async () => {
    if (!selectedSceneId || !editingSceneData) return;
    try {
      const updated = await api.updateScene(selectedSceneId, editingSceneData);
      setScenes(scenes.map(s => s.id === selectedSceneId ? updated : s));
    } catch (e) { console.error(e); }
  };

  const handleUploadFace = async (characterId: string, file: File) => {
    try {
      await api.uploadAnchorFace(characterId, file, faceAngle, isPrimaryFace);
      const faces = await api.loadAnchorFaces(characterId);
      setAnchorFaces(prev => ({ ...prev, [characterId]: faces }));
    } catch (e) { console.error(e); }
  };

  const handleDeleteFace = async (faceId: string) => {
    try {
      await api.deleteAnchorFace(faceId);
      if (selectedCharId) {
        const faces = await api.loadAnchorFaces(selectedCharId);
        setAnchorFaces(prev => ({ ...prev, [selectedCharId]: faces }));
      }
    } catch (e) { console.error(e); }
  };

  return (
    <div className="space-y-6">
      {/* Personnel Section */}
      <div className="space-y-3">
        <div className="flex items-center gap-2 mb-2">
          <Users className="w-3 h-3 text-[var(--color-accent)]" />
          <span className="text-[10px] font-bold text-gray-500 uppercase tracking-tight">Personnel Dossiers</span>
        </div>

        <PersonnelDossier
          characters={characters}
          anchorFaces={anchorFaces}
          selectedCharId={selectedCharId}
          setSelectedCharId={setSelectedCharId}
          editingCharData={editingCharData}
          setEditingCharData={setEditingCharData}
          traitInput={traitInput}
          setTraitInput={setTraitInput}
          updateCharacter={handleUpdateCharacter}
          uploadAnchorFace={handleUploadFace}
          deleteAnchorFace={handleDeleteFace}
          faceAngle={faceAngle}
          setFaceAngle={setFaceAngle}
          isPrimaryFace={isPrimaryFace}
          setIsPrimaryFace={setIsPrimaryFace}
          loadingStates={api.loadingStates}
          fileInputRef={useRef<HTMLInputElement>(null) as React.RefObject<HTMLInputElement>}
          uploadReferenceSheet={api.uploadReferenceSheet}
          deleteReferenceSheet={api.deleteReferenceSheet}
        />

        <div className="flex flex-col gap-2 mt-4">
          <div className="flex gap-1">
            <Input
              value={newCharName}
              onChange={e => setNewCharName(e.target.value)}
              placeholder="Name"
              className="flex-1"
              onKeyDown={e => e.key === 'Enter' && handleCreateCharacter()}
            />
            <Button onClick={handleCreateCharacter} loading={api.loadingStates['character']}>
              <Plus className="w-3 h-3" />
            </Button>
          </div>
          <div className="flex gap-1">
            <Input
              value={traitInput}
              onChange={e => setTraitInput(e.target.value)}
              placeholder="Add trait..."
              className="flex-1"
              onKeyDown={e => {
                if (e.key === 'Enter') {
                  const val = traitInput.trim();
                  if (val && !newCharTraits.includes(val)) {
                    setNewCharTraits([...newCharTraits, val]);
                    setTraitInput('');
                  }
                }
              }}
            />
            <Button onClick={() => {
              const val = traitInput.trim();
              if (val && !newCharTraits.includes(val)) {
                setNewCharTraits([...newCharTraits, val]);
                setTraitInput('');
              }
            }}>
              <Plus className="w-3 h-3" />
            </Button>
          </div>
          <div className="flex flex-wrap gap-1">
            {newCharTraits.map((t, i) => (
              <span key={i} className="trait-chip flex items-center gap-1">
                {t}
                <span className="cursor-pointer hover:text-red-500" onClick={() => setNewCharTraits(prev => prev.filter((_, idx) => idx !== i))}>×</span>
              </span>
            ))}
          </div>
        </div>
      </div>

      {/* Scenes Section */}
      <div className="space-y-3 pt-4 border-t border-[var(--color-border)]">
        <div className="flex items-center gap-2 mb-2">
          <Clapperboard className="w-3 h-3 text-[var(--color-accent)]" />
          <span className="text-[10px] font-bold text-gray-500 uppercase tracking-tight">Scene Sequence</span>
        </div>
        <div className="space-y-1">
          {scenes.map(s => (
            <div
              key={s.id}
              onClick={() => setSelectedSceneId(s.id)}
              className={`p-2 rounded text-xs transition-all cursor-pointer ${
                selectedSceneId === s.id ? 'active-context-glow bg-[var(--color-accent-muted)] text-white' : 'hover:bg-black/40 text-gray-400'
              }`}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center">
                  <span className="mono text-[10px] opacity-50 mr-2">#{s.scene_number}</span>
                  <span className="font-medium">{s.title || 'Untitled'}</span>
                </div>
              </div>
            </div>
          ))}
        </div>

        {selectedSceneId && editingSceneData && (
          <div className="p-3 rounded border border-[var(--color-border)] bg-black/40 space-y-3 animate-in slide-in-from-top-2 duration-200">
            <div className="flex items-center gap-2 mb-2">
              <Settings className="w-3 h-3 text-gray-500" />
              <span className="text-[9px] mono text-gray-500 uppercase">Scene Details</span>
            </div>
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <MapPin className="w-3 h-3 text-gray-600" />
                <Input
                  value={editingSceneData.location}
                  onChange={e => setEditingSceneData(prev => prev ? { ...prev, location: e.target.value } : null)}
                  placeholder="Location"
                  className="flex-1 h-7 text-[10px]"
                />
              </div>
              <div className="flex items-center gap-2">
                <Clock className="w-3 h-3 text-gray-600" />
                <Input
                  value={editingSceneData.time_of_day}
                  onChange={e => setEditingSceneData(prev => prev ? { ...prev, time_of_day: e.target.value } : null)}
                  placeholder="Time of Day"
                  className="flex-1 h-7 text-[10px]"
                />
              </div>
              <div className="flex items-center gap-2">
                <FileText className="w-3 h-3 text-gray-600" />
                <textarea
                  value={editingSceneData.summary}
                  onChange={e => setEditingSceneData(prev => prev ? { ...prev, summary: e.target.value } : null)}
                  placeholder="Scene Summary..."
                  className="flex-1 bg-black/40 text-[10px] px-2 py-1 rounded border border-[var(--color-border)] mono text-white focus:outline-none focus:border-[var(--color-accent)] h-16 resize-none"
                />
              </div>
              <Button
                onClick={handleUpdateScene}
                loading={api.loadingStates['scene-update']}
                className="w-full text-[10px] py-1"
              >
                SAVE SCENE
              </Button>
            </div>
          </div>
        )}

        <div className="flex gap-1 mt-3">
          <Input
            value={newSceneTitle}
            onChange={e => setNewSceneTitle(e.target.value)}
            placeholder="Scene Title..."
            className="flex-1"
            onKeyDown={e => e.key === 'Enter' && handleCreateScene()}
          />
          <Button onClick={handleCreateScene} loading={api.loadingStates['scene']}>
            <Plus className="w-3 h-3" />
          </Button>
        </div>
      </div>
    </div>
  );
};
