import { useState, useEffect } from 'react';
import { StudioProvider, useStudioContext } from './context/StudioContext';
import { MainLayout } from './components/layout/MainLayout';
import { useStudioApi } from './hooks/useStudioApi';
import { type EditPlan } from './api/drift';
import { Toast } from './components/ui/Toast';

function StudioApp() {
  const {
    setProjects,
    selectedProject,
    setCharacters,
    setScenes,
    selectedSceneId,
    shots,
    setShots,
    setIsRendering,
    setEditPlan,
    setCreativeResult,
    newShotPrompt,
    setNewShotPrompt,
    setChatMessages
  } = useStudioContext();

  const [toasts, setToasts] = useState<{ id: string; message: string; type: 'success' | 'error' | 'info' }[]>([]);

  const showToast = (message: string, type: 'success' | 'error' | 'info' = 'info') => {
    const id = Math.random().toString(36).substring(7);
    setToasts(prev => [...prev, { id, message, type }]);
    setTimeout(() => setToasts(prev => prev.filter(t => t.id !== id)), 3000);
  };

  const api = useStudioApi(showToast);

  useEffect(() => {
    const init = async () => {
      try {
        const projs = await api.loadProjects();
        setProjects(projs);
      } catch (e) { console.error(e); }
    };
    init();
  }, []);

  useEffect(() => {
    if (selectedProject) {
      const loadData = async () => {
        try {
          const [chars, scs] = await Promise.all([
            api.loadCharacters(selectedProject.id),
            api.loadScenes(selectedProject.id)
          ]);
          setCharacters(chars);
          setScenes(scs);
        } catch (e) { console.error(e); }
      };
      loadData();
    }
  }, [selectedProject]);

  useEffect(() => {
    if (selectedSceneId) {
      api.loadShots(selectedSceneId).then(setShots).catch(console.error);
    }
  }, [selectedSceneId]);

  const handleCreateShot = async () => {
    if (!selectedSceneId || !newShotPrompt.trim()) return;
    try {
      const shot = await api.createShot(selectedSceneId, newShotPrompt, shots.length + 1);
      setShots([...shots, shot]);
      setNewShotPrompt('');
    } catch (e) { console.error(e); }
  };

  const handleUpdateShot = async (id: string, data: any) => {
    try {
      const shot = await api.updateShot(id, data);
      setShots(shots.map(s => s.id === id ? shot : s));
    } catch (e) { console.error(e); }
  };

  const handleSendMessage = (text: string) => {
    setChatMessages(prev => [...prev, { role: 'user', text }]);
    setChatMessages(prev => [...prev, { role: 'system', text: 'Processing your request...' }]);
  };

  const handleRender = async () => {
    const shotsWithClips = shots.filter(s => s.video_path);
    if (shotsWithClips.length === 0) {
      showToast('Attach video clips to shots first', 'error');
      return;
    }
    setIsRendering(true);
    setChatMessages(prev => [...prev, { role: 'system', text: `Rendering ${shotsWithClips.length} shots...` }]);
    try {
      const context = shotsWithClips.map(s => `Shot ${s.shot_number}: ${s.prompt_text}`).join('. ');
      const clipPaths = shotsWithClips.map(s => s.video_path!);
      const result = await api.startCreativeRender(clipPaths, context);
      setCreativeResult(result);
      setChatMessages(prev => [
        ...prev,
        { role: 'system', text: `Done! Mood: ${result.mood} | ${result.duration.toFixed(1)}s | ${shotsWithClips.length} clips merged` }
      ]);

      const clips = shotsWithClips.map((s, i) => {
        const dur = (s as any).duration || 5;
        const seg = result.timeline_segments?.[i];
        return {
          path: s.video_path!,
          duration: dur,
          in_point: seg?.clip_start || 0,
          out_point: seg?.clip_start !== undefined ? seg.clip_start + dur : undefined,
          speed: result.speed_adjustments?.[i] || 1,
          color_grade: result.color_grades?.[i] ?? undefined,
          volume: 1.0,
        };
      });
      const transitions: EditPlan['transitions'] = [];
      if (result.transition_points) {
        for (const tp of result.transition_points) {
          if (tp.type !== 'cut') {
            transitions.push({
              from_clip: `shot-${tp.from_shot}`,
              to_clip: `shot-${tp.to_shot}`,
              type: tp.type,
              duration: tp.duration,
            });
          }
        }
      }
      setEditPlan({ clips, transitions });
    } catch {
      setChatMessages(prev => [...prev, { role: 'system', text: 'Render failed. Check API.' }]);
    } finally {
      setIsRendering(false);
    }
  };

  return (
    <div className="relative h-screen w-screen overflow-hidden">
      <MainLayout
        onRender={handleRender}
        onCreateShot={handleCreateShot}
        onUpdateShot={handleUpdateShot}
        onSendMessage={handleSendMessage}
      />

      <div className="fixed top-4 right-4 z-[100] flex flex-col gap-2">
        {toasts.map(t => (
          <Toast key={t.id} {...t} />
        ))}
      </div>
    </div>
  );
}

export default function App() {
  return (
    <StudioProvider>
      <StudioApp />
    </StudioProvider>
  );
}
