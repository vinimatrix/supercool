import axios from 'axios';

const api = axios.create({ baseURL: '/api/v1' });

export interface Project {
  id: string;
  title: string;
  description: string | null;
  target_resolution: string;
  fps: number;
  aspect_ratio: string;
  created_at: string;
}

export interface Character {
  id: string;
  project_id: string;
  name: string;
  biography: string | null;
  locked_traits: string[];
  voice_profile_id: string | null;
}

export interface AnchorFace {
  id: string;
  character_id: string;
  image_url: string;
  view_angle: string | null;
  is_primary: boolean;
  created_at: string;
}

export interface Scene {
  id: string;
  project_id: string;
  scene_number: number;
  title: string | null;
  location: string | null;
  time_of_day: string | null;
  summary: string | null;
}

export interface Shot {
  id: string;
  scene_id: string;
  shot_number: number;
  shot_type: string | null;
  motion_type: string | null;
  assigned_engine: string | null;
  prompt_text: string;
  injected_prompt: string | null;
  dialogue_text: string | null;
  video_path: string | null;
  status: string;
}

export interface RenderJob {
  id: string;
  shot_id: string;
  engine_name: string;
  status: string;
  output_url: string | null;
  qa_score: number | null;
  qa_feedback: string | null;
  retry_count: number;
}

export const projectsApi = {
  list: () => api.get<Project[]>('/projects'),
  get: (id: string) => api.get<Project>(`/projects/${id}`),
  create: (data: { title: string; description?: string }) => api.post<Project>('/projects', data),
};

export const charactersApi = {
  list: (projectId: string) => api.get<Character[]>(`/projects/${projectId}/characters`),
  create: (projectId: string, data: { name: string; locked_traits?: string[] }) =>
    api.post<Character>(`/projects/${projectId}/characters`, data),
  update: (id: string, data: Partial<Character>) => api.put<Character>(`/characters/${id}`, data),
};

export const scenesApi = {
  list: (projectId: string) => api.get<Scene[]>(`/projects/${projectId}/scenes`),
  create: (projectId: string, data: { scene_number: number; title?: string; location?: string }) =>
    api.post<Scene>(`/projects/${projectId}/scenes`, data),
  update: (id: string, data: Partial<Scene>) => api.put<Scene>(`/scenes/${id}`, data),
};

export const shotsApi = {
  list: (sceneId: string) => api.get<Shot[]>(`/scenes/${sceneId}/shots`),
  create: (sceneId: string, data: { shot_number: number; prompt_text: string; speaker_character_id?: string }) =>
    api.post<Shot>(`/scenes/${sceneId}/shots`, data),
  update: (id: string, data: Partial<Shot>) => api.put<Shot>(`/shots/${id}`, data),
  uploadVideo: (shotId: string, file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post<Shot>(`/shots/${shotId}/upload-video`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
  assignVideo: (shotId: string, videoPath: string) =>
    api.put<Shot>(`/shots/${shotId}/assign-video`, { video_path: videoPath }),
};

export const renderApi = {
  start: (shotId: string) => api.post<RenderJob>(`/shots/${shotId}/render`),
  getJob: (jobId: string) => api.get<RenderJob>(`/jobs/${jobId}`),
};

export const anchorFacesApi = {
  list: (characterId: string) => api.get<AnchorFace[]>(`/characters/${characterId}/anchor-faces`),
  upload: (characterId: string, file: File, viewAngle?: string, isPrimary?: boolean) => {
    const formData = new FormData();
    formData.append('file', file);
    if (viewAngle) formData.append('view_angle', viewAngle);
    if (isPrimary !== undefined) formData.append('is_primary', String(isPrimary));
    return api.post<AnchorFace>(`/characters/${characterId}/anchor-faces`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
  delete: (faceId: string) => api.delete(`/anchor-faces/${faceId}`),
};

export interface CreativeRenderResult {
  final_output: string;
  video_only: string;
  duration: number;
  shots: number;
  mood: string;
  music_crescendo: boolean;
}

export interface WorkspaceFile {
  path: string;
  size: number;
  type: string;
}

export const creativeApi = {
  render: (data: {
    clip_paths: string[];
    scene_context?: string;
    output_name?: string;
    master_volume?: number;
    enable_audio?: boolean;
  }) => api.post<CreativeRenderResult>('/creative/render', data),
  workspace: () => api.get<WorkspaceFile[]>('/creative/workspace'),
};
