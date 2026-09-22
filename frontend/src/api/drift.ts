/** Drift MCP API Client - Comunica frontend con Drift via SuperCool API */

const API_BASE = '/api/v1/drift';

export interface DriftStatus {
  connected: boolean;
  port?: number;
  project_loaded?: boolean;
  project_info?: any;
}

export interface EditPlanClip {
  path: string;
  duration: number;
  in_point?: number;
  out_point?: number;
  speed?: number;
  color_grade?: string;
  volume?: number;
}

export interface EditPlanTransition {
  from_clip: string;
  to_clip: string;
  type: string;
  duration: number;
}

export interface EditPlan {
  clips: EditPlanClip[];
  transitions: EditPlanTransition[];
}

export interface DriftProject {
  name?: string;
  fps?: number;
  width?: number;
  height?: number;
  tracks?: any[];
  assets?: any;
  duration?: number;
}

export interface DriftAsset {
  id: string;
  name: string;
  path: string;
  duration?: number;
}

export interface DriftClip {
  id: string;
  track: number;
  index: number;
  start?: number;
  duration?: number;
  in?: number;
  out?: number;
  x?: number;
  y?: number;
  w?: number;
  h?: number;
  volume?: number;
  speed?: number;
}

async function apiCall<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(error.detail || 'API request failed');
  }
  return res.json();
}

export const driftApi = {
  // Connection
  async connect(port: number = 4731, token?: string): Promise<{ status: string; port: number }> {
    return apiCall('/connect', {
      method: 'POST',
      body: JSON.stringify({ port, token }),
    });
  },

  async status(): Promise<DriftStatus> {
    return apiCall('/status');
  },

  async disconnect(): Promise<{ status: string }> {
    return apiCall('/disconnect', { method: 'POST' });
  },

  // Project inspection
  async inspect(clips: boolean = true, detail: boolean = true): Promise<DriftProject> {
    return apiCall(`/inspect?clips=${clips}&detail=${detail}`);
  },

  async activity(start: number = 0, end: number = -1): Promise<any> {
    return apiCall(`/activity?start=${start}&end=${end}`);
  },

  async capture(at: number = 0): Promise<any> {
    return apiCall(`/capture?at=${at}`);
  },

  async frames(at?: number[], n: number = 12): Promise<any> {
    const params = new URLSearchParams({ n: n.toString() });
    if (at) {
      at.forEach((t) => params.append('at', t.toString()));
    }
    return apiCall(`/frames?${params.toString()}`);
  },

  // Media
  async importMedia(paths: string[]): Promise<any> {
    return apiCall('/import', {
      method: 'POST',
      body: JSON.stringify({ paths }),
    });
  },

  async listAssets(): Promise<{ assets: DriftAsset[] }> {
    return apiCall('/assets');
  },

  // Timeline
  async addTrack(type: string = 'video'): Promise<any> {
    return apiCall(`/track?type=${type}`, { method: 'POST' });
  },

  async placeClip(asset: string, at: number = 0, track: number = 0): Promise<DriftClip> {
    return apiCall('/place', {
      method: 'POST',
      body: JSON.stringify({ asset, at, track }),
    });
  },

  async moveClip(clip: string, to: number, track?: number): Promise<any> {
    const body: any = { clip, to };
    if (track !== undefined) body.track = track;
    return apiCall('/move', {
      method: 'POST',
      body: JSON.stringify(body),
    });
  },

  async splitClip(clip: string, at: number): Promise<any> {
    return apiCall('/split', {
      method: 'POST',
      body: JSON.stringify({ clip, at }),
    });
  },

  async deleteClip(clipId: string): Promise<any> {
    return apiCall(`/clip/${clipId}`, { method: 'DELETE' });
  },

  // Effects
  async listTransitions(): Promise<any> {
    return apiCall('/transitions');
  },

  async addTransition(
    from: string,
    to: string,
    kind: string = 'crossfade',
    duration: number = 0.5,
  ): Promise<any> {
    return apiCall('/transition', {
      method: 'POST',
      body: JSON.stringify({ from_clip: from, to_clip: to, kind, duration }),
    });
  },

  async listEffects(): Promise<any> {
    return apiCall('/effects');
  },

  async addEffect(clip: string, effectId: string): Promise<any> {
    return apiCall('/effect', {
      method: 'POST',
      body: JSON.stringify({ clip, effect_id: effectId }),
    });
  },

  async listAudioEffects(): Promise<any> {
    return apiCall('/audio-effects');
  },

  // Canvas
  async setVolume(clip: string, volume: number): Promise<any> {
    return apiCall('/volume', {
      method: 'POST',
      body: JSON.stringify({ clip, volume }),
    });
  },

  async setFade(clip: string, fadeIn: number = 0, fadeOut: number = 0): Promise<any> {
    return apiCall('/fade', {
      method: 'POST',
      body: JSON.stringify({ clip, fade_in: fadeIn, fade_out: fadeOut }),
    });
  },

  async setSpeed(clip: string, speed: number): Promise<any> {
    return apiCall('/speed', {
      method: 'POST',
      body: JSON.stringify({ clip, speed }),
    });
  },

  // Text
  async addText(
    text: string,
    preset: string = 'title',
    at: number = 0,
    track: number = -1,
    duration: number = 5,
  ): Promise<any> {
    return apiCall('/text', {
      method: 'POST',
      body: JSON.stringify({ text, preset, at, track, duration }),
    });
  },

  // Audio
  async detectBeats(start: number = 0, duration: number = 30): Promise<any> {
    return apiCall('/detect-beats', {
      method: 'POST',
      body: JSON.stringify({ start, duration }),
    });
  },

  async detectScenes(clip: string): Promise<any> {
    return apiCall('/detect-scenes', {
      method: 'POST',
      body: JSON.stringify({ clip }),
    });
  },

  // Project
  async saveProject(path?: string): Promise<any> {
    return apiCall('/save', {
      method: 'POST',
      body: JSON.stringify({ path }),
    });
  },

  async exportVideo(path: string, fps: number = 24, resolution: string = '4K'): Promise<any> {
    return apiCall('/export', {
      method: 'POST',
      body: JSON.stringify({ path, fps, resolution }),
    });
  },

  async exportStatus(): Promise<any> {
    return apiCall('/export-status');
  },

  // Undo/Redo
  async undo(): Promise<any> {
    return apiCall('/undo', { method: 'POST' });
  },

  async redo(): Promise<any> {
    return apiCall('/redo', { method: 'POST' });
  },

  async listHistory(limit: number = 20): Promise<any> {
    return apiCall(`/history?limit=${limit}`);
  },

  // Playback
  async seek(time: number): Promise<any> {
    return apiCall('/seek', {
      method: 'POST',
      body: JSON.stringify({ time }),
    });
  },

  async play(): Promise<any> {
    return apiCall('/play', { method: 'POST' });
  },

  async pause(): Promise<any> {
    return apiCall('/pause', { method: 'POST' });
  },

  // Edit Plan execution
  async executePlan(plan: EditPlan): Promise<{
    status: string;
    clips_placed: number;
    transitions_added: number;
    clip_ids: string[];
  }> {
    return apiCall('/execute-plan', {
      method: 'POST',
      body: JSON.stringify(plan),
    });
  },
};
