import { describe, it, expect, vi, beforeEach } from 'vitest';
import axios from 'axios';
import { api, charactersApi } from '../api/client';

vi.mock('axios', () => {
  const mockAxios = {
    create: vi.fn(() => mockAxios),
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
    defaults: { headers: { common: {} } },
    interceptors: {
      request: { use: vi.fn() },
      response: { use: vi.fn() },
    },
  };
  return { default: mockAxios };
});

const mockedAxios = vi.mocked(axios, true);

describe('API Client', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('projectsApi', () => {
    it('list calls GET /projects', async () => {
      const mockData = [{ id: '1', title: 'Test Project' }];
      mockedAxios.get.mockResolvedValue({ data: mockData });

      const { projectsApi } = await import('../api/client');
      const result = await projectsApi.list();

      expect(mockedAxios.get).toHaveBeenCalledWith('/projects');
      expect(result.data).toEqual(mockData);
    });

    it('create calls POST /projects', async () => {
      const mockData = { id: '1', title: 'New Project' };
      mockedAxios.post.mockResolvedValue({ data: mockData });

      const { projectsApi } = await import('../api/client');
      const result = await projectsApi.create({ title: 'New Project' });

      expect(mockedAxios.post).toHaveBeenCalledWith('/projects', { title: 'New Project' });
      expect(result.data).toEqual(mockData);
    });
  });

  describe('charactersApi', () => {
    it('list calls GET /projects/:id/characters', async () => {
      const mockData = [{ id: '1', name: 'Boruto' }];
      mockedAxios.get.mockResolvedValue({ data: mockData });

      const { charactersApi } = await import('../api/client');
      const result = await charactersApi.list('project-1');

      expect(mockedAxios.get).toHaveBeenCalledWith('/projects/project-1/characters');
      expect(result.data).toEqual(mockData);
    });
  });

  describe('shotsApi', () => {
    it('list calls GET /scenes/:id/shots', async () => {
      const mockData = [{ id: '1', shot_number: 1 }];
      mockedAxios.get.mockResolvedValue({ data: mockData });

      const { shotsApi } = await import('../api/client');
      const result = await shotsApi.list('scene-1');

      expect(mockedAxios.get).toHaveBeenCalledWith('/scenes/scene-1/shots');
      expect(result.data).toEqual(mockData);
    });
  });

  describe('renderApi', () => {
    it('start calls POST /shots/:id/render', async () => {
      const mockData = { id: 'job-1', status: 'QUEUED' };
      mockedAxios.post.mockResolvedValue({ data: mockData });

      const { renderApi } = await import('../api/client');
      const result = await renderApi.start('shot-1');

      expect(mockedAxios.post).toHaveBeenCalledWith('/shots/shot-1/render');
      expect(result.data).toEqual(mockData);
    });
  });

  describe('creativeApi', () => {
    it('render calls POST /creative/render', async () => {
      const mockData = { final_output: '/output.mp4', mood: 'dramatic' };
      mockedAxios.post.mockResolvedValue({ data: mockData });

      const { creativeApi } = await import('../api/client');
      const result = await creativeApi.render({ clip_paths: ['/clip.mp4'] });

      expect(mockedAxios.post).toHaveBeenCalledWith('/creative/render', {
        clip_paths: ['/clip.mp4'],
      });
      expect(result.data).toEqual(mockData);
    });
  });
});

describe('charactersApi reference sheet', () => {
  beforeEach(() => vi.restoreAllMocks());

  it('uploadReferenceSheet posts multipart form data', async () => {
    const spy = vi.spyOn(api, 'post').mockResolvedValue({ data: {} } as any);
    const file = new File(['x'], 's.png', { type: 'image/png' });
    await charactersApi.uploadReferenceSheet('c1', file);
    expect(spy).toHaveBeenCalledWith(
      '/characters/c1/reference-sheet',
      expect.any(FormData),
      expect.objectContaining({ headers: { 'Content-Type': 'multipart/form-data' } })
    );
  });

  it('deleteReferenceSheet calls delete', async () => {
    const spy = vi.spyOn(api, 'delete').mockResolvedValue({ data: {} } as any);
    await charactersApi.deleteReferenceSheet('c1');
    expect(spy).toHaveBeenCalledWith('/characters/c1/reference-sheet');
  });
});

describe('lipsyncApi', () => {
  beforeEach(() => vi.restoreAllMocks());

  it('listVideos calls GET /lipsync/videos with project filter', async () => {
    const spy = vi.spyOn(api, 'get').mockResolvedValue({ data: [] } as any);
    const { lipsyncApi } = await import('../api/client');
    await lipsyncApi.listVideos('p1');
    expect(spy).toHaveBeenCalledWith('/lipsync/videos', { params: { project_id: 'p1' } });
  });

  it('listAudios calls GET /lipsync/audios without params when no project', async () => {
    const spy = vi.spyOn(api, 'get').mockResolvedValue({ data: [] } as any);
    const { lipsyncApi } = await import('../api/client');
    await lipsyncApi.listAudios();
    expect(spy).toHaveBeenCalledWith('/lipsync/audios', { params: undefined });
  });

  it('uploadVideo posts multipart form data with project param', async () => {
    const spy = vi.spyOn(api, 'post').mockResolvedValue({ data: {} } as any);
    const file = new File(['x'], 'v.mp4', { type: 'video/mp4' });
    const { lipsyncApi } = await import('../api/client');
    await lipsyncApi.uploadVideo('p1', file);
    expect(spy).toHaveBeenCalledWith(
      '/lipsync/videos',
      expect.any(FormData),
      expect.objectContaining({
        headers: { 'Content-Type': 'multipart/form-data' },
        params: { project_id: 'p1' },
      })
    );
  });

  it('uploadAudio posts multipart form data', async () => {
    const spy = vi.spyOn(api, 'post').mockResolvedValue({ data: {} } as any);
    const file = new File(['x'], 'a.wav', { type: 'audio/wav' });
    const { lipsyncApi } = await import('../api/client');
    await lipsyncApi.uploadAudio(undefined, file);
    expect(spy).toHaveBeenCalledWith(
      '/lipsync/audios',
      expect.any(FormData),
      expect.objectContaining({ headers: { 'Content-Type': 'multipart/form-data' } })
    );
  });

  it('createJob calls POST /lipsync/jobs with the payload', async () => {
    const body = {
      project_id: 'p1',
      video_path: 'workspace/shots/v.mp4',
      trim_start: 0,
      trim_end: 3,
      audio_path: 'workspace/audio/a.wav',
    };
    const spy = vi.spyOn(api, 'post').mockResolvedValue({ data: { id: 'j1' } } as any);
    const { lipsyncApi } = await import('../api/client');
    const result = await lipsyncApi.createJob(body);
    expect(spy).toHaveBeenCalledWith('/lipsync/jobs', body);
    expect(result.data).toEqual({ id: 'j1' });
  });

  it('listJobs calls GET /lipsync/jobs with project_id', async () => {
    const spy = vi.spyOn(api, 'get').mockResolvedValue({ data: [] } as any);
    const { lipsyncApi } = await import('../api/client');
    await lipsyncApi.listJobs('p1');
    expect(spy).toHaveBeenCalledWith('/lipsync/jobs', { params: { project_id: 'p1' } });
  });

  it('getJob calls GET /lipsync/jobs/:id', async () => {
    const spy = vi.spyOn(api, 'get').mockResolvedValue({ data: { id: 'j1' } } as any);
    const { lipsyncApi } = await import('../api/client');
    await lipsyncApi.getJob('j1');
    expect(spy).toHaveBeenCalledWith('/lipsync/jobs/j1');
  });

  it('assignJob calls POST /lipsync/jobs/:id/assign with shot_id', async () => {
    const spy = vi.spyOn(api, 'post').mockResolvedValue({ data: { id: 'j1' } } as any);
    const { lipsyncApi } = await import('../api/client');
    await lipsyncApi.assignJob('j1', 'shot-1');
    expect(spy).toHaveBeenCalledWith('/lipsync/jobs/j1/assign', { shot_id: 'shot-1' });
  });
});
