import { useState, useCallback } from 'react';
import {
  projectsApi,
  charactersApi,
  scenesApi,
  shotsApi,
  renderApi,
  anchorFacesApi,
  creativeApi
} from '../api/client';
import type { Character, Scene, Shot } from '../api/client';

export const useStudioApi = (showToast: (msg: string, type?: 'success' | 'error' | 'info') => void) => {
  const [loadingStates, setLoadingStates] = useState<Record<string, boolean>>({});

  const setLoading = useCallback((key: string, state: boolean) => {
    setLoadingStates(prev => ({ ...prev, [key]: state }));
  }, []);

  const loadProjects = async () => {
    try {
      const res = await projectsApi.list();
      return res.data;
    } catch {
      showToast('Failed to load projects', 'error');
      throw new Error('Projects load failed');
    }
  };

  const loadCharacters = async (projectId: string) => {
    try {
      const res = await charactersApi.list(projectId);
      return res.data;
    } catch {
      showToast('Failed to load characters', 'error');
      throw new Error('Characters load failed');
    }
  };

  const loadScenes = async (projectId: string) => {
    try {
      const res = await scenesApi.list(projectId);
      return res.data;
    } catch {
      showToast('Failed to load scenes', 'error');
      throw new Error('Scenes load failed');
    }
  };

  const loadShots = async (sceneId: string) => {
    try {
      const res = await shotsApi.list(sceneId);
      return res.data;
    } catch {
      showToast('Failed to load shots', 'error');
      throw new Error('Shots load failed');
    }
  };

  const loadAnchorFaces = async (characterId: string) => {
    try {
      const res = await anchorFacesApi.list(characterId);
      return res.data;
    } catch {
      showToast('Failed to load reference faces', 'error');
      throw new Error('Anchor faces load failed');
    }
  };

  const createProject = async (name: string) => {
    setLoading('project', true);
    try {
      const res = await projectsApi.create({ title: name });
      const project = res.data;
      const sceneRes = await scenesApi.create(project.id, {
        scene_number: 1,
        title: 'Scene 1',
      });
      showToast('Project & Scene 1 created', 'success');
      return { project, firstScene: sceneRes.data };
    } catch {
      showToast('Failed to create project', 'error');
      throw new Error('Project creation failed');
    } finally {
      setLoading('project', false);
    }
  };

  const createCharacter = async (projectId: string, name: string, traits: string[]) => {
    setLoading('character', true);
    try {
      const res = await charactersApi.create(projectId, {
        name,
        locked_traits: traits
      });
      showToast('Character added to dossier', 'success');
      return res.data;
    } catch {
      showToast('Failed to create character', 'error');
      throw new Error('Character creation failed');
    } finally {
      setLoading('character', false);
    }
  };

  const createScene = async (projectId: string, title: string, sceneNumber: number) => {
    setLoading('scene', true);
    try {
      const res = await scenesApi.create(projectId, {
        scene_number: sceneNumber,
        title,
      });
      showToast('Scene added to sequence', 'success');
      return res.data;
    } catch {
      showToast('Failed to create scene', 'error');
      throw new Error('Scene creation failed');
    } finally {
      setLoading('scene', false);
    }
  };

  const createShot = async (sceneId: string, prompt: string, shotNumber: number) => {
    setLoading('shot', true);
    try {
      const res = await shotsApi.create(sceneId, {
        shot_number: shotNumber,
        prompt_text: prompt,
      });
      showToast('Shot defined in sequence', 'success');
      return res.data;
    } catch {
      showToast('Failed to create shot', 'error');
      throw new Error('Shot creation failed');
    } finally {
      setLoading('shot', false);
    }
  };

  const updateCharacter = async (id: string, data: Partial<Character>) => {
    setLoading('character-update', true);
    try {
      const res = await charactersApi.update(id, data);
      showToast('Character dossier updated', 'success');
      return res.data;
    } catch {
      showToast('Failed to update character', 'error');
      throw new Error('Character update failed');
    } finally {
      setLoading('character-update', false);
    }
  };

  const updateScene = async (id: string, data: Partial<Scene>) => {
    setLoading('scene-update', true);
    try {
      const res = await scenesApi.update(id, data);
      showToast('Scene updated', 'success');
      return res.data;
    } catch {
      showToast('Failed to update scene', 'error');
      throw new Error('Scene update failed');
    } finally {
      setLoading('scene-update', false);
    }
  };

  const updateShot = async (id: string, data: Partial<Shot>) => {
    setLoading(`shot-${id}`, true);
    try {
      const res = await shotsApi.update(id, data);
      showToast('Shot updated', 'success');
      return res.data;
    } catch {
      showToast('Failed to update shot', 'error');
      throw new Error('Shot update failed');
    } finally {
      setLoading(`shot-${id}`, false);
    }
  };

  const uploadAnchorFace = async (characterId: string, file: File, angle: string, isPrimary: boolean) => {
    try {
      await anchorFacesApi.upload(characterId, file, angle, isPrimary);
      showToast('Reference face uploaded', 'success');
    } catch {
      showToast('Upload failed', 'error');
      throw new Error('Face upload failed');
    }
  };

  const deleteAnchorFace = async (faceId: string) => {
    try {
      await anchorFacesApi.delete(faceId);
      showToast('Face removed from dossier', 'info');
    } catch {
      showToast('Deletion failed', 'error');
      throw new Error('Face deletion failed');
    }
  };

  const uploadReferenceSheet = async (characterId: string, file: File) => {
    setLoading('reference-sheet', true);
    try {
      const res = await charactersApi.uploadReferenceSheet(characterId, file);
      showToast('Reference sheet uploaded', 'success');
      return res.data;
    } catch {
      showToast('Reference sheet upload failed', 'error');
      throw new Error('Reference sheet upload failed');
    } finally {
      setLoading('reference-sheet', false);
    }
  };

  const deleteReferenceSheet = async (characterId: string) => {
    try {
      const res = await charactersApi.deleteReferenceSheet(characterId);
      showToast('Reference sheet removed', 'info');
      return res.data;
    } catch {
      showToast('Reference sheet deletion failed', 'error');
      throw new Error('Reference sheet deletion failed');
    }
  };

  const startRender = async (shotId: string) => {
    try {
      await renderApi.start(shotId);
      showToast('Shot render queued', 'info');
    } catch {
      showToast('Render failed to start', 'error');
      throw new Error('Render start failed');
    }
  };

  const uploadShotClip = async (shotId: string, file: File) => {
    try {
      const res = await shotsApi.uploadVideo(shotId, file);
      showToast('Clip uploaded to shot', 'success');
      return res.data;
    } catch {
      showToast('Clip upload failed', 'error');
      throw new Error('Clip upload failed');
    }
  };

  const startCreativeRender = async (clipPaths: string[], context: string) => {
    try {
      const result = await creativeApi.render({
        clip_paths: clipPaths,
        scene_context: context,
        output_name: 'final_render',
      });
      showToast('Cinematic render complete', 'success');
      return result.data;
    } catch {
      showToast('Render failed', 'error');
      throw new Error('Creative render failed');
    }
  };

  return {
    loadingStates,
    setLoading,
    loadProjects,
    loadCharacters,
    loadScenes,
    loadShots,
    loadAnchorFaces,
    createProject,
    createCharacter,
    createScene,
    createShot,
    updateCharacter,
    updateScene,
    updateShot,
    uploadAnchorFace,
    deleteAnchorFace,
    uploadReferenceSheet,
    deleteReferenceSheet,
    startRender,
    startCreativeRender,
    uploadShotClip
  };
};