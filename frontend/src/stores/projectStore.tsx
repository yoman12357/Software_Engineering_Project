import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";
import { api } from "../api/client";

export interface Project {
  id: string;
  name: string;
  description: string;
  status: string;
  inferred_categories: string[];
  created_at: string;
  updated_at: string;
}

interface ProjectState {
  projects: Project[];
  currentProjectId: string | null;
  isLoading: boolean;
  error: string | null;
  fetchProjects: () => Promise<void>;
  createProject: (name: string, description: string) => Promise<Project>;
  setCurrentProject: (id: string | null) => void;
  deleteProject: (id: string) => Promise<void>;
  updateProject: (id: string, data: Partial<Project>) => Promise<void>;
}

export const useProjectStore = create<ProjectState>()(
  persist(
    (set) => ({
      projects: [],
      currentProjectId: null,
      isLoading: false,
      error: null,

      fetchProjects: async () => {
        set({ isLoading: true, error: null });
        try {
          const data = await api.listProjects();
          set({ projects: data.projects });
        } catch (error) {
          set({ error: error instanceof Error ? error.message : "Failed to load projects" });
        } finally {
          set({ isLoading: false });
        }
      },

      createProject: async (name: string, description: string) => {
        set({ isLoading: true, error: null });
        try {
          const project = await api.createProject({ name, description });
          set((state) => ({ projects: [project, ...state.projects] }));
          return project;
        } catch (error) {
          set({ error: error instanceof Error ? error.message : "Failed to create project" });
          throw error;
        } finally {
          set({ isLoading: false });
        }
      },

      setCurrentProject: (id: string | null) => {
        set({ currentProjectId: id });
      },

      deleteProject: async (id: string) => {
        set({ isLoading: true, error: null });
        try {
          await api.deleteProject(id);
          set((state) => ({
            projects: state.projects.filter((p) => p.id !== id),
            currentProjectId: state.currentProjectId === id ? null : state.currentProjectId,
          }));
        } catch (error) {
          set({ error: error instanceof Error ? error.message : "Failed to delete project" });
          throw error;
        } finally {
          set({ isLoading: false });
        }
      },

      updateProject: async (id: string, data: Partial<Project>) => {
        set({ isLoading: true, error: null });
        try {
          const updated = await api.updateProject(id, data);
          set((state) => ({
            projects: state.projects.map((p) => (p.id === id ? updated : p)),
          }));
        } catch (error) {
          set({ error: error instanceof Error ? error.message : "Failed to update project" });
          throw error;
        } finally {
          set({ isLoading: false });
        }
      },
    }),
    {
      name: "cybersrs-projects",
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        currentProjectId: state.currentProjectId,
      }),
      onRehydrateStorage: () => (state) => {
        if (state) {
          state.fetchProjects();
        }
      },
    }
  )
);
