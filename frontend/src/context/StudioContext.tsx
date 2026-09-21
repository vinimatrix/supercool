import React, { createContext, useContext, useState, ReactNode } from 'react';
import * as API from '../api/client';

interface StudioContextType {
  // Core Data
  projects: API.Project[];
  setProjects: React.Dispatch<React.SetStateAction<API.Project[]>>;
  selectedProject: API.Project | null;
  setSelectedProject: (project: API.Project | null) => void;
  characters: API.Character[];
  setCharacters: React.Dispatch<React.SetStateAction<API.Character[]>>;
  scenes: API.Scene[];
  setScenes: React.Dispatch<React.SetStateAction<API.Scene[]>>;
  shots: API.Shot[];
  setShots: React.Dispatch<React.SetStateAction<API.Shot[]>>;
  anchorFaces: Record<string, API.AnchorFace[]>;
  setAnchorFaces: React.Dispatch<React.SetStateAction<Record<string, API.AnchorFace[]>>>;

  // Contextual IDs
  selectedSceneId: string | null;
  setSelectedSceneId: (id: string | null) => void;
  selectedCharId: string | null;
  setSelectedCharId: (id: string | null) => void;

  // UI State
  activeTab: 'story' | 'qa' | 'analytics';
  setActiveTab: (tab: 'story' | 'qa' | 'analytics') => void;
  isRendering: boolean;
  setIsRendering: (rendering: boolean) => void;
}

const StudioContext = createContext<StudioContextType | undefined>(undefined);

export const StudioProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [projects, setProjects] = useState<API.Project[]>([]);
  const [selectedProject, setSelectedProject] = useState<API.Project | null>(null);
  const [characters, setCharacters] = useState<API.Character[]>([]);
  const [scenes, setScenes] = useState<API.Scene[]>([]);
  const [shots, setShots] = useState<API.Shot[]>([]);
  const [anchorFaces, setAnchorFaces] = useState<Record<string, API.AnchorFace[]>>({});

  const [selectedSceneId, setSelectedSceneId] = useState<string | null>(null);
  const [selectedCharId, setSelectedCharId] = useState<string | null>(null);

  const [activeTab, setActiveTab] = useState<'story' | 'qa' | 'analytics'>('story');
  const [isRendering, setIsRendering] = useState(false);

  return (
    <StudioContext.Provider
      value={{
        projects, setProjects,
        selectedProject, setSelectedProject,
        characters, setCharacters,
        scenes, setScenes,
        shots, setShots,
        anchorFaces, setAnchorFaces,
        selectedSceneId, setSelectedSceneId,
        selectedCharId, setSelectedCharId,
        activeTab, setActiveTab,
        isRendering, setIsRendering
      }}
    >
      {children}
    </StudioContext.Provider>
  );
};

export const useStudioContext = () => {
  const context = useContext(StudioContext);
  if (!context) {
    throw new Error('useStudioContext must be used within a StudioProvider');
  }
  return context;
};
