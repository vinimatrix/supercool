import { describe, it, expect, vi, beforeEach } from 'vitest';
import axios from 'axios';

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
