import { useState, useEffect, useRef } from 'react';
import { Film, Users, Clapperboard, Play, Plus, Send, CheckCircle, Clock, XCircle, Zap, Eye, Image, Trash2, Sparkles, Download } from 'lucide-react';
import { projectsApi, charactersApi, scenesApi, shotsApi, renderApi, anchorFacesApi, creativeApi, type Project, type Character, type Scene, type Shot, type AnchorFace, type CreativeRenderResult } from './api/client';
import { DriftPanel } from './components/DriftPanel';
import { type EditPlan } from './api/drift';
import { YouTubeConnect, YouTubeDashboard, YouTubeAIReport } from './components/youtube';
import { youtubeApi } from './api/youtube';
import type { ChannelStats, VideoMetrics, AnalysisReport } from './api/youtube';

function App() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProject, setSelectedProject] = useState<Project | null>(null);
  const [characters, setCharacters] = useState<Character[]>([]);
  const [scenes, setScenes] = useState<Scene[]>([]);
  const [shots, setShots] = useState<Shot[]>([]);
  const [anchorFaces, setAnchorFaces] = useState<Record<string, AnchorFace[]>>({});
  const [newProjectName, setNewProjectName] = useState('');
  const [newCharName, setNewCharName] = useState('');
  const [newCharTraits, setNewCharTraits] = useState('');
  const [newSceneTitle, setNewSceneTitle] = useState('');
  const [newShotPrompt, setNewShotPrompt] = useState('');
  const [selectedSceneId, setSelectedSceneId] = useState<string | null>(null);
  const [selectedCharId, setSelectedCharId] = useState<string | null>(null);
  const [chatMessages, setChatMessages] = useState<{ role: string; text: string }[]>([]);
  const [chatInput, setChatInput] = useState('');
  const [activeTab, setActiveTab] = useState<'story' | 'qa' | 'analytics' | 'youtube'>('story');
  const [creativeResult, setCreativeResult] = useState<CreativeRenderResult | null>(null);
  const [isRendering, setIsRendering] = useState(false);
  const [editPlan, setEditPlan] = useState<EditPlan | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const videoUploadRef = useRef<HTMLInputElement>(null);

  // YouTube Analytics state
  const [youtubeConnected, setYoutubeConnected] = useState(false);
  const [youtubeToken, setYoutubeToken] = useState<string | null>(null);
  const [channelStats, setChannelStats] = useState<ChannelStats | null>(null);
  const [videos, setVideos] = useState<VideoMetrics[]>([]);
  const [analysisReport, setAnalysisReport] = useState<AnalysisReport | null>(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [aiProvider, setAiProvider] = useState("groq");

  useEffect(() => {
    loadProjects();
  }, []);

  useEffect(() => {
    if (selectedProject) {
      loadCharacters(selectedProject.id);
      loadScenes(selectedProject.id);
    }
  }, [selectedProject]);

  useEffect(() => {
    if (selectedSceneId) {
      loadShots(selectedSceneId);
    }
  }, [selectedSceneId]);

  useEffect(() => {
    if (selectedCharId) {
      loadAnchorFaces(selectedCharId);
    }
  }, [selectedCharId]);

  const loadProjects = async () => {
    try {
      const res = await projectsApi.list();
      setProjects(res.data);
    } catch { /* api offline */ }
  };

  const loadCharacters = async (projectId: string) => {
    try {
      const res = await charactersApi.list(projectId);
      setCharacters(res.data);
    } catch { /* api offline */ }
  };

  const loadScenes = async (projectId: string) => {
    try {
      const res = await scenesApi.list(projectId);
      setScenes(res.data);
    } catch { /* api offline */ }
  };

  const loadShots = async (sceneId: string) => {
    try {
      const res = await shotsApi.list(sceneId);
      setShots(res.data);
    } catch { /* api offline */ }
  };

  const loadAnchorFaces = async (characterId: string) => {
    try {
      const res = await anchorFacesApi.list(characterId);
      setAnchorFaces(prev => ({ ...prev, [characterId]: res.data }));
    } catch { /* api offline */ }
  };

  const createProject = async () => {
    if (!newProjectName.trim()) return;
    try {
      const res = await projectsApi.create({ title: newProjectName });
      setProjects([...projects, res.data]);
      setSelectedProject(res.data);
      setNewProjectName('');
    } catch { /* api offline */ }
  };

  const createCharacter = async () => {
    if (!selectedProject || !newCharName.trim()) return;
    try {
      const traits = newCharTraits.split(',').map(t => t.trim()).filter(Boolean);
      const res = await charactersApi.create(selectedProject.id, { name: newCharName, locked_traits: traits });
      setCharacters([...characters, res.data]);
      setNewCharName('');
      setNewCharTraits('');
    } catch { /* api offline */ }
  };

  const createScene = async () => {
    if (!selectedProject || !newSceneTitle.trim()) return;
    try {
      const res = await scenesApi.create(selectedProject.id, {
        scene_number: scenes.length + 1,
        title: newSceneTitle,
      });
      setScenes([...scenes, res.data]);
      setNewSceneTitle('');
    } catch { /* api offline */ }
  };

  const createShot = async () => {
    if (!selectedSceneId || !newShotPrompt.trim()) return;
    try {
      const res = await shotsApi.create(selectedSceneId, {
        shot_number: shots.length + 1,
        prompt_text: newShotPrompt,
      });
      setShots([...shots, res.data]);
      setNewShotPrompt('');
    } catch { /* api offline */ }
  };

  const startRender = async (shotId: string) => {
    try {
      await renderApi.start(shotId);
      setChatMessages([...chatMessages, { role: 'system', text: 'Render started for shot' }]);
    } catch { /* api offline */ }
  };

  const uploadAnchorFace = async (characterId: string, file: File) => {
    try {
      await anchorFacesApi.upload(characterId, file);
      loadAnchorFaces(characterId);
    } catch { /* api offline */ }
  };

  const deleteAnchorFace = async (characterId: string, faceId: string) => {
    try {
      await anchorFacesApi.delete(faceId);
      loadAnchorFaces(characterId);
    } catch { /* api offline */ }
  };

  const sendChat = () => {
    if (!chatInput.trim()) return;
    setChatMessages([...chatMessages, { role: 'user', text: chatInput }]);
    setChatMessages(prev => [...prev, { role: 'system', text: 'Processing your request...' }]);
    setChatInput('');
  };

  const startCreativeRender = async () => {
    const shotsWithClips = shots.filter(s => s.video_path);
    if (shotsWithClips.length === 0) {
      setChatMessages(prev => [...prev, { role: 'system', text: 'Attach video clips to shots first.' }]);
      return;
    }

    setIsRendering(true);
    setChatMessages(prev => [...prev, { role: 'system', text: `Rendering ${shotsWithClips.length} shots...` }]);

    try {
      // Build context from shot prompts (the guion)
      const context = shotsWithClips.map(s => `Shot ${s.shot_number}: ${s.prompt_text}`).join('. ');

      // Use video paths from shots
      const clipPaths = shotsWithClips.map(s => s.video_path!);

      const result = await creativeApi.render({
        clip_paths: clipPaths,
        scene_context: context,
        output_name: 'final_render',
      });

      setCreativeResult(result.data);
      setChatMessages(prev => [
        ...prev,
        { role: 'system', text: `Done! Mood: ${result.data.mood} | ${result.data.duration.toFixed(1)}s | ${shotsWithClips.length} clips merged` }
      ]);

      // Generate Edit Plan for Drift
      const clips = shotsWithClips.map((s, i) => {
        const dur = (s as any).duration || 5;
        const seg = result.data.timeline_segments[i];
        return {
          path: s.video_path!,
          duration: dur,
          in_point: seg?.clip_start || 0,
          out_point: seg?.clip_start !== undefined ? seg.clip_start + dur : undefined,
          speed: result.data.speed_adjustments?.[i] || 1,
          color_grade: result.data.color_grades?.[i],
          volume: 1.0,
        };
      });
      const transitions: EditPlan['transitions'] = [];
      if (result.data.transition_points) {
        for (const tp of result.data.transition_points) {
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

    } catch (e) {
      setChatMessages(prev => [...prev, { role: 'system', text: 'Render failed. Check API.' }]);
    }
    setIsRendering(false);
  };

  const handleYouTubeConnect = async (token: string | null) => {
    setYoutubeToken(token);
    setYoutubeConnected(true);
    try {
      const stats = await youtubeApi.getChannelStats(token);
      setChannelStats(stats);
      const videoMetrics = await youtubeApi.getVideoMetrics(token);
      setVideos(videoMetrics);
    } catch (error) {
      console.error("Failed to connect YouTube:", error);
    }
  };

  const handleAnalyze = async () => {
    setAnalyzing(true);
    try {
      const report = await youtubeApi.analyze(youtubeToken, aiProvider);
      setAnalysisReport(report);
    } catch (error) {
      console.error("Analysis failed:", error);
    } finally {
      setAnalyzing(false);
    }
  };

  const statusIcon = (status: string) => {
    switch (status) {
      case 'APPROVED': return <CheckCircle className="w-4 h-4 text-emerald-400" />;
      case 'PENDING': return <Clock className="w-4 h-4 text-amber-400" />;
      case 'REJECTED': return <XCircle className="w-4 h-4 text-red-400" />;
      default: return <Clock className="w-4 h-4 text-gray-400" />;
    }
  };

  return (
    <div className="h-screen flex flex-col" style={{ backgroundColor: '#0D0F12' }}>
      <input
        type="file"
        ref={fileInputRef}
        className="hidden"
        accept="image/*"
        onChange={e => {
          const file = e.target.files?.[0];
          if (file && selectedCharId) {
            uploadAnchorFace(selectedCharId, file);
          }
          e.target.value = '';
        }}
      />

      <header className="h-12 flex items-center justify-between px-4 border-b" style={{ backgroundColor: '#1A1D24', borderColor: '#2A2F3D' }}>
        <div className="flex items-center gap-2">
          <Zap className="w-5 h-5 text-blue-400" />
          <span className="font-bold text-sm tracking-wider">SUPERCOOL</span>
          <span className="text-xs text-gray-500 ml-2">AI CINEMATIC STUDIO</span>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-xs text-gray-500">4K | 24fps</span>
          <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
        </div>
      </header>

      <div className="flex-1 flex overflow-hidden">
        <aside className="w-72 flex flex-col border-r overflow-hidden" style={{ borderColor: '#2A2F3D' }}>
          <div className="p-3 border-b" style={{ borderColor: '#2A2F3D' }}>
            <div className="flex gap-1 mb-2">
              <input
                value={newProjectName}
                onChange={e => setNewProjectName(e.target.value)}
                placeholder="New project..."
                className="flex-1 bg-gray-800 text-xs px-2 py-1.5 rounded border text-white"
                style={{ borderColor: '#2A2F3D' }}
                onKeyDown={e => e.key === 'Enter' && createProject()}
              />
              <button onClick={createProject} className="px-2 py-1 bg-blue-600 rounded text-xs hover:bg-blue-500">
                <Plus className="w-3 h-3" />
              </button>
            </div>
            <select
              value={selectedProject?.id || ''}
              onChange={e => {
                const p = projects.find(p => p.id === e.target.value);
                setSelectedProject(p || null);
              }}
              className="w-full bg-gray-800 text-xs px-2 py-1.5 rounded border text-white"
              style={{ borderColor: '#2A2F3D' }}
            >
              <option value="">Select project...</option>
              {projects.map(p => (
                <option key={p.id} value={p.id}>{p.title}</option>
              ))}
            </select>
          </div>

          <div className="flex border-b" style={{ borderColor: '#2A2F3D' }}>
            {(['story', 'qa', 'analytics', 'youtube'] as const).map(tab => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`flex-1 py-2 text-xs font-medium uppercase tracking-wider ${
                  activeTab === tab ? 'text-blue-400 border-b-2 border-blue-400' : 'text-gray-500 hover:text-gray-300'
                }`}
              >
                {tab === 'story' ? 'Story Bible' : tab === 'qa' ? 'QA Monitor' : tab === 'analytics' ? 'Analytics' : 'YT Analytics'}
              </button>
            ))}
          </div>

          <div className="flex-1 overflow-y-auto scrollbar-thin p-3">
            {activeTab === 'story' && (
              <div className="space-y-4">
                <div>
                  <div className="flex items-center gap-1 mb-2">
                    <Users className="w-3 h-3 text-blue-400" />
                    <span className="text-xs font-medium text-gray-400 uppercase">Characters</span>
                  </div>
                  <div className="space-y-2 mb-2">
                    {characters.map(c => (
                      <div key={c.id} className="p-2 rounded text-xs" style={{ backgroundColor: '#0D0F12' }}>
                        <div
                          className="font-medium text-white cursor-pointer hover:text-blue-400"
                          onClick={() => setSelectedCharId(selectedCharId === c.id ? null : c.id)}
                        >
                          {c.name}
                        </div>
                        <div className="flex flex-wrap gap-1 mt-1">
                          {c.locked_traits.map((t, i) => (
                            <span key={i} className="px-1.5 py-0.5 bg-gray-800 rounded text-[10px] text-gray-400">{t}</span>
                          ))}
                        </div>
                        {selectedCharId === c.id && (
                          <div className="mt-2 pt-2 border-t" style={{ borderColor: '#2A2F3D' }}>
                            <div className="flex items-center gap-1 mb-2">
                              <Image className="w-3 h-3 text-emerald-400" />
                              <span className="text-[10px] text-gray-500 uppercase">Anchor Faces</span>
                            </div>
                            <div className="grid grid-cols-3 gap-1 mb-2">
                              {(anchorFaces[c.id] || []).map(face => (
                                <div key={face.id} className="relative group">
                                  <img
                                    src={face.image_url}
                                    alt={face.view_angle || 'face'}
                                    className="w-full h-16 object-cover rounded"
                                  />
                                  <button
                                    onClick={() => deleteAnchorFace(c.id, face.id)}
                                    className="absolute top-0 right-0 p-0.5 bg-red-600 rounded opacity-0 group-hover:opacity-100"
                                  >
                                    <Trash2 className="w-2 h-2" />
                                  </button>
                                  {face.is_primary && (
                                    <span className="absolute bottom-0 left-0 px-1 bg-blue-600 rounded text-[8px]">Primary</span>
                                  )}
                                </div>
                              ))}
                            </div>
                            <button
                              onClick={() => fileInputRef.current?.click()}
                              className="w-full py-1 border border-dashed rounded text-[10px] text-gray-500 hover:text-emerald-400 hover:border-emerald-400"
                              style={{ borderColor: '#2A2F3D' }}
                            >
                              + Upload Reference
                            </button>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                  <div className="flex gap-1">
                    <input
                      value={newCharName}
                      onChange={e => setNewCharName(e.target.value)}
                      placeholder="Name"
                      className="flex-1 bg-gray-800 text-xs px-2 py-1 rounded border text-white"
                      style={{ borderColor: '#2A2F3D' }}
                    />
                    <button onClick={createCharacter} className="px-2 py-1 bg-blue-600 rounded text-xs"><Plus className="w-3 h-3" /></button>
                  </div>
                  <input
                    value={newCharTraits}
                    onChange={e => setNewCharTraits(e.target.value)}
                    placeholder="Traits (comma separated)"
                    className="w-full mt-1 bg-gray-800 text-xs px-2 py-1 rounded border text-white"
                    style={{ borderColor: '#2A2F3D' }}
                  />
                </div>

                <div>
                  <div className="flex items-center gap-1 mb-2">
                    <Clapperboard className="w-3 h-3 text-amber-400" />
                    <span className="text-xs font-medium text-gray-400 uppercase">Scenes</span>
                  </div>
                  <div className="space-y-1 mb-2">
                    {scenes.map(s => (
                      <button
                        key={s.id}
                        onClick={() => setSelectedSceneId(s.id)}
                        className={`w-full text-left p-2 rounded text-xs ${
                          selectedSceneId === s.id ? 'bg-blue-900/50 border border-blue-500/50' : 'hover:bg-gray-800'
                        }`}
                      >
                        <span className="text-gray-500">#{s.scene_number}</span>{' '}
                        <span className="text-white">{s.title || 'Untitled'}</span>
                        {s.location && <span className="text-gray-500 ml-1">— {s.location}</span>}
                      </button>
                    ))}
                  </div>
                  <div className="flex gap-1">
                    <input
                      value={newSceneTitle}
                      onChange={e => setNewSceneTitle(e.target.value)}
                      placeholder="Scene title"
                      className="flex-1 bg-gray-800 text-xs px-2 py-1 rounded border text-white"
                      style={{ borderColor: '#2A2F3D' }}
                      onKeyDown={e => e.key === 'Enter' && createScene()}
                    />
                    <button onClick={createScene} className="px-2 py-1 bg-amber-600 rounded text-xs"><Plus className="w-3 h-3" /></button>
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'qa' && (
              <div className="space-y-3">
                <div className="text-xs text-gray-500 uppercase mb-2">QA Monitor</div>
                {shots.filter(s => s.status !== 'PENDING').length === 0 ? (
                  <div className="text-xs text-gray-600 text-center py-8">No QA data yet</div>
                ) : (
                  shots.map(s => (
                    <div key={s.id} className="p-2 rounded text-xs" style={{ backgroundColor: '#0D0F12' }}>
                      <div className="flex items-center justify-between">
                        <span className="text-white">Shot #{s.shot_number}</span>
                        {statusIcon(s.status)}
                      </div>
                      <div className="text-gray-500 mt-1 truncate">{s.prompt_text}</div>
                    </div>
                  ))
                )}
              </div>
            )}

            {activeTab === 'analytics' && (
              <div className="space-y-4">
                <div className="text-xs text-gray-500 uppercase mb-2">Project Analytics</div>
                <div className="grid grid-cols-2 gap-2">
                  <div className="p-3 rounded text-center" style={{ backgroundColor: '#0D0F12' }}>
                    <div className="text-lg font-bold text-white">{scenes.length}</div>
                    <div className="text-[10px] text-gray-500">Scenes</div>
                  </div>
                  <div className="p-3 rounded text-center" style={{ backgroundColor: '#0D0F12' }}>
                    <div className="text-lg font-bold text-white">{shots.length}</div>
                    <div className="text-[10px] text-gray-500">Shots</div>
                  </div>
                  <div className="p-3 rounded text-center" style={{ backgroundColor: '#0D0F12' }}>
                    <div className="text-lg font-bold text-white">{characters.length}</div>
                    <div className="text-[10px] text-gray-500">Characters</div>
                  </div>
                  <div className="p-3 rounded text-center" style={{ backgroundColor: '#0D0F12' }}>
                    <div className="text-lg font-bold text-emerald-400">0</div>
                    <div className="text-[10px] text-gray-500">Rendered</div>
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'youtube' && (
              <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
                <YouTubeConnect onConnect={handleYouTubeConnect} connected={youtubeConnected} />
                {youtubeConnected && (
                  <>
                    <YouTubeDashboard stats={channelStats} videos={videos} />
                    <YouTubeAIReport
                      report={analysisReport}
                      onAnalyze={handleAnalyze}
                      loading={analyzing}
                      provider={aiProvider}
                      onProviderChange={setAiProvider}
                    />
                  </>
                )}
              </div>
            )}
          </div>
        </aside>

        <div className="flex-1 flex flex-col overflow-hidden">
          <div className="flex-1 flex overflow-hidden">
            <div className="flex-1 flex flex-col border-r" style={{ borderColor: '#2A2F3D' }}>
              <div className="h-10 flex items-center px-3 border-b" style={{ borderColor: '#2A2F3D' }}>
                <Eye className="w-3 h-3 text-blue-400 mr-2" />
                <span className="text-xs font-medium text-gray-400 uppercase">Direction Chat</span>
              </div>
              <div className="flex-1 overflow-y-auto p-3 space-y-2 scrollbar-thin">
                {chatMessages.length === 0 && (
                  <div className="text-center text-gray-600 text-xs mt-8">
                    <Film className="w-8 h-8 mx-auto mb-2 opacity-30" />
                    <p>Start directing your film</p>
                    <p className="text-[10px] mt-1">Type a prompt or upload a script</p>
                  </div>
                )}
                {chatMessages.map((msg, i) => (
                  <div key={i} className={`text-xs p-2 rounded ${msg.role === 'user' ? 'bg-blue-900/30 text-blue-200 ml-8' : 'bg-gray-800 text-gray-300 mr-8'}`}>
                    {msg.text}
                  </div>
                ))}
              </div>
              <div className="p-3 border-t" style={{ borderColor: '#2A2F3D' }}>
                <div className="flex gap-2">
                  <input
                    value={chatInput}
                    onChange={e => setChatInput(e.target.value)}
                    placeholder="Describe your scene..."
                    className="flex-1 bg-gray-800 text-xs px-3 py-2 rounded border text-white"
                    style={{ borderColor: '#2A2F3D' }}
                    onKeyDown={e => e.key === 'Enter' && sendChat()}
                  />
                  <button onClick={sendChat} className="px-3 py-2 bg-blue-600 rounded hover:bg-blue-500">
                    <Send className="w-3 h-3" />
                  </button>
                </div>
              </div>
            </div>

            <div className="w-96 flex flex-col">
              <div className="h-10 flex items-center px-3 border-b" style={{ borderColor: '#2A2F3D' }}>
                <Play className="w-3 h-3 text-emerald-400 mr-2" />
                <span className="text-xs font-medium text-gray-400 uppercase">4K Preview</span>
              </div>
              <div className="flex-1 flex items-center justify-center" style={{ backgroundColor: '#0D0F12' }}>
                {creativeResult ? (
                  <video
                    key={creativeResult.video_only}
                    controls
                    className="w-full h-full object-contain"
                    src={`http://localhost:8000/workspace/pipeline_output/${creativeResult.final_output.split(/[/\\]/).pop()}`}
                  />
                ) : (
                  <div className="text-center text-gray-600">
                    <Film className="w-12 h-12 mx-auto mb-2 opacity-20" />
                    <p className="text-xs">No preview available</p>
                    <p className="text-[10px] text-gray-700 mt-1">Render a video to preview</p>
                  </div>
                )}
              </div>
              <div className="p-3 border-t" style={{ borderColor: '#2A2F3D' }}>
                <div className="text-[10px] text-gray-500 uppercase mb-2">Render Controls</div>
                <div className="grid grid-cols-2 gap-2 text-xs mb-3">
                  <div className="p-2 rounded" style={{ backgroundColor: '#0D0F12' }}>
                    <div className="text-gray-500">Engine</div>
                    <div className="text-white font-medium">Auto-Route</div>
                  </div>
                  <div className="p-2 rounded" style={{ backgroundColor: '#0D0F12' }}>
                    <div className="text-gray-500">Resolution</div>
                    <div className="text-white font-medium">4K</div>
                  </div>
                  <div className="p-2 rounded" style={{ backgroundColor: '#0D0F12' }}>
                    <div className="text-gray-500">FPS</div>
                    <div className="text-white font-medium">24</div>
                  </div>
                  <div className="p-2 rounded" style={{ backgroundColor: '#0D0F12' }}>
                    <div className="text-gray-500">IP-Adapter</div>
                    <div className="text-white font-medium">0.85</div>
                  </div>
                </div>
                <button
                  onClick={startCreativeRender}
                  disabled={isRendering || shots.filter(s => s.video_path).length === 0}
                  className="w-full py-2 rounded text-xs font-medium flex items-center justify-center gap-2 disabled:opacity-40"
                  style={{ backgroundColor: isRendering ? '#2A2F3D' : '#4F46E5', color: 'white' }}
                >
                  {isRendering ? (
                    <>
                      <div className="w-3 h-3 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                      Rendering...
                    </>
                  ) : (
                    <>
                      <Sparkles className="w-3 h-3" />
                      Render Final ({shots.filter(s => s.video_path).length} clips)
                    </>
                  )}
                </button>
                {creativeResult && (
                  <div className="mt-2 p-2 rounded text-xs" style={{ backgroundColor: '#0D0F12' }}>
                    <div className="flex justify-between">
                      <span className="text-gray-500">Mood</span>
                      <span className="text-purple-400">{creativeResult.mood}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-500">Duration</span>
                      <span className="text-white">{creativeResult.duration.toFixed(1)}s</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-500">Shots</span>
                      <span className="text-white">{creativeResult.shots}</span>
                    </div>
                    <a
                      href={`http://localhost:8000/api/v1/creative/workspace`}
                      target="_blank"
                      className="mt-2 flex items-center justify-center gap-1 py-1 bg-emerald-600/20 text-emerald-400 rounded text-[10px]"
                    >
                      <Download className="w-3 h-3" /> View Output
                    </a>
                  </div>
                )}
              </div>
            </div>
          </div>

          <div className="h-40 border-t flex flex-col" style={{ borderColor: '#2A2F3D', backgroundColor: '#1A1D24' }}>
            <div className="h-8 flex items-center justify-between px-3 border-b" style={{ borderColor: '#2A2F3D' }}>
              <div className="flex items-center gap-2">
                <Clapperboard className="w-3 h-3 text-amber-400" />
                <span className="text-xs font-medium text-gray-400 uppercase">Shot Timeline</span>
              </div>
              <div className="flex items-center gap-2">
                <input
                  ref={videoUploadRef}
                  type="file"
                  accept="video/*"
                  multiple
                  className="hidden"
                  onChange={async (e) => {
                    const files = e.target.files;
                    if (!files) return;
                    for (const file of Array.from(files)) {
                      const reader = new FileReader();
                      reader.onload = async () => {
                        const base64 = (reader.result as string).split(',')[1];
                        try {
                          await fetch('/api/v1/creative/upload', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ file_name: file.name, file_data: base64 }),
                          });
                          setChatMessages(prev => [...prev, { role: 'system', text: `Uploaded: ${file.name}` }]);
                        } catch { /* api offline */ }
                      };
                      reader.readAsDataURL(file);
                    }
                    e.target.value = '';
                  }}
                />
                <button
                  onClick={() => videoUploadRef.current?.click()}
                  className="px-2 py-1 bg-blue-600 rounded text-xs text-white flex items-center gap-1"
                >
                  <Film className="w-3 h-3" /> Upload Clips
                </button>
                {selectedSceneId && (
                  <div className="flex gap-1">
                    <input
                      value={newShotPrompt}
                      onChange={e => setNewShotPrompt(e.target.value)}
                      placeholder="Shot prompt..."
                      className="w-48 bg-gray-800 text-xs px-2 py-1 rounded border text-white"
                      style={{ borderColor: '#2A2F3D' }}
                      onKeyDown={e => e.key === 'Enter' && createShot()}
                    />
                    <button onClick={createShot} className="px-2 py-1 bg-emerald-600 rounded text-xs"><Plus className="w-3 h-3" /></button>
                  </div>
                )}
              </div>
            </div>
            <div className="flex-1 overflow-x-auto p-2 flex gap-2 scrollbar-thin">
              {shots.length === 0 ? (
                <div className="flex-1 flex items-center justify-center text-gray-600 text-xs">
                  Select a scene and add shots to see them here
                </div>
              ) : (
                shots.map((shot) => (
                  <div
                    key={shot.id}
                    className="flex-shrink-0 w-48 rounded p-2 flex flex-col justify-between"
                    style={{ backgroundColor: '#0D0F12', border: '1px solid #2A2F3D' }}
                  >
                    <div>
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-[10px] text-gray-500">Shot #{shot.shot_number}</span>
                        {shot.video_path ? (
                          <span className="text-[9px] text-emerald-400 flex items-center gap-0.5">
                            <Film className="w-2.5 h-2.5" /> Clip
                          </span>
                        ) : (
                          statusIcon(shot.status)
                        )}
                      </div>
                      <p className="text-[10px] text-gray-300 line-clamp-2">{shot.prompt_text}</p>
                    </div>
                    {shot.video_path ? (
                      <div className="mt-2 text-[9px] text-emerald-400 truncate" title={shot.video_path}>
                        {shot.video_path.split(/[/\\]/).pop()}
                      </div>
                    ) : (
                      <label className="mt-2 w-full py-1 bg-gray-800 border border-gray-700 rounded text-[10px] text-gray-400 hover:bg-gray-700 flex items-center justify-center cursor-pointer">
                        <Film className="w-3 h-3 mr-1" /> Attach Clip
                        <input
                          type="file"
                          accept="video/*"
                          className="hidden"
                          onChange={async (e) => {
                            const file = e.target.files?.[0];
                            if (!file) return;
                            try {
                              const res = await shotsApi.uploadVideo(shot.id, file);
                              setShots(shots.map(s => s.id === shot.id ? res.data : s));
                            } catch { /* api offline */ }
                          }}
                        />
                      </label>
                    )}
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Drift Integration Panel */}
          <DriftPanel
            editPlan={editPlan}
            onPlanExecuted={() => {
              setChatMessages(prev => [
                ...prev,
                { role: 'system', text: 'Edit Plan executed in Drift. Open Drift Editor to see the timeline.' }
              ]);
            }}
          />
        </div>
      </div>
    </div>
  );
}

export default App;
