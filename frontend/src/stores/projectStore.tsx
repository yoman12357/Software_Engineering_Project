import { create } from "zustand";
import { api } from "../api/client";
import { firestoreService } from "../services/firestore";

export interface Project {
  id: string;
  name: string;
  description: string;
  status: string;
  inferred_categories: string[];
  created_at: string;
  updated_at: string;
}

export interface ChatSession {
  id: string;
  projectId: string | null;
  name: string;
  lastMessage: string;
  updatedAt: string;
  messageCount: number;
  stage: string;
  pinnedAt: string | null;
}

function sortChatSessions(sessions: ChatSession[]): ChatSession[] {
  return [...sessions].sort((a, b) => {
    if (a.pinnedAt && !b.pinnedAt) return -1;
    if (!a.pinnedAt && b.pinnedAt) return 1;
    if (a.pinnedAt && b.pinnedAt) return b.pinnedAt.localeCompare(a.pinnedAt);
    return b.updatedAt.localeCompare(a.updatedAt);
  });
}

interface ProjectState {
  projects: Project[];
  chatSessions: ChatSession[];
  currentProjectId: string | null;
  currentSessionId: string | null;
  isLoading: boolean;
  error: string | null;
  fetchProjects: () => Promise<void>;
  fetchChatSessions: () => Promise<void>;
  createProject: (name: string, description: string) => Promise<Project>;
  setCurrentProject: (id: string | null) => void;
  setCurrentSession: (id: string | null) => void;
  deleteProject: (id: string) => Promise<void>;
  updateProject: (id: string, data: Partial<Project>) => Promise<void>;
  renameChatSession: (sessionId: string, newName: string) => Promise<void>;
  deleteChatSession: (sessionId: string) => Promise<void>;
  setChatSessionPinned: (sessionId: string, pinned: boolean) => Promise<void>;
}

export const useProjectStore = create<ProjectState>()((set) => ({
  projects: [],
  chatSessions: [],
  currentProjectId: null,
  currentSessionId: null,
  isLoading: false,
  error: null,

  fetchProjects: async () => {
    set({ isLoading: true, error: null });
    try {
      const data = await api.listProjects();
      set({ projects: data.projects });
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : "Failed to load projects",
      });
    } finally {
      set({ isLoading: false });
    }
  },

  fetchChatSessions: async () => {
    try {
      const sessions = await firestoreService.getRecentChatSessions(50);
      const chatSessions: ChatSession[] = sessions.map((session) => {
        const lastMsg = session.messages[session.messages.length - 1];
        const storedName = session.name?.trim();

        return {
          id: session.id,
          projectId: session.projectId,
          // Preserve the persisted session name. Falling back to the last
          // message is only for older sessions that do not have a name yet.
          name: storedName || lastMsg?.content?.slice(0, 50) || "New chat",
          lastMessage: lastMsg?.content || "",
          updatedAt: session.updatedAt,
          messageCount: session.messages.length,
          stage: session.stage,
          pinnedAt: session.pinnedAt ?? null,
        };
      });

      set({ chatSessions: sortChatSessions(chatSessions) });
    } catch {
      // Chat persistence may be unavailable while the backend is starting.
      // Keep the current UI state instead of clearing the sidebar.
    }
  },

  createProject: async (name: string, description: string) => {
    set({ isLoading: true, error: null });
    try {
      const project = await api.createProject({ name, description });
      set((state) => ({ projects: [project, ...state.projects] }));
      return project;
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : "Failed to create project",
      });
      throw error;
    } finally {
      set({ isLoading: false });
    }
  },

  setCurrentProject: (id: string | null) => {
    set({ currentProjectId: id });
  },

  setCurrentSession: (id: string | null) => {
    set({ currentSessionId: id });
  },

  deleteProject: async (id: string) => {
    set({ isLoading: true, error: null });
    try {
      await api.deleteProject(id);
      set((state) => ({
        projects: state.projects.filter((p) => p.id !== id),
        chatSessions: state.chatSessions.filter((session) => session.projectId !== id),
        currentProjectId:
          state.currentProjectId === id ? null : state.currentProjectId,
        currentSessionId: state.chatSessions.some(
          (session) => session.id === state.currentSessionId && session.projectId === id,
        )
          ? null
          : state.currentSessionId,
      }));
      try {
        await firestoreService.deleteProjectChatSessions(id);
      } catch {
        set({ error: "Project deleted, but its local chat history could not be cleaned up." });
      }
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : "Failed to delete project",
      });
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
      set({
        error: error instanceof Error ? error.message : "Failed to update project",
      });
      throw error;
    } finally {
      set({ isLoading: false });
    }
  },

  renameChatSession: async (sessionId: string, newName: string) => {
    const normalizedName = newName.trim();

    if (!normalizedName) {
      throw new Error("Chat name cannot be empty");
    }

    try {
      await firestoreService.updateChatSessionName(sessionId, normalizedName);

      set((state) => ({
        error: null,
        chatSessions: sortChatSessions(
          state.chatSessions.map((session) =>
            session.id === sessionId
              ? {
                  ...session,
                  name: normalizedName,
                  updatedAt: new Date().toISOString(),
                }
              : session,
          ),
        ),
      }));
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : "Failed to rename chat",
      });
      throw error;
    }
  },

  deleteChatSession: async (sessionId: string) => {
    const previousState = useProjectStore.getState();
    set((state) => ({
      error: null,
      chatSessions: state.chatSessions.filter((session) => session.id !== sessionId),
      currentSessionId:
        state.currentSessionId === sessionId ? null : state.currentSessionId,
    }));

    try {
      await firestoreService.deleteChatSession(sessionId);
    } catch (error) {
      set({
        chatSessions: previousState.chatSessions,
        currentSessionId: previousState.currentSessionId,
        error: error instanceof Error ? error.message : "Failed to delete chat",
      });
      throw error;
    }
  },

  setChatSessionPinned: async (sessionId: string, pinned: boolean) => {
    const previousSessions = useProjectStore.getState().chatSessions;
    const pinnedAt = pinned ? new Date().toISOString() : null;
    set((state) => ({
      error: null,
      chatSessions: sortChatSessions(
        state.chatSessions.map((session) =>
          session.id === sessionId ? { ...session, pinnedAt } : session,
        ),
      ),
    }));

    try {
      await firestoreService.updateChatSessionPinned(sessionId, pinned);
    } catch (error) {
      set({
        chatSessions: previousSessions,
        error: error instanceof Error ? error.message : "Failed to update pinned chat",
      });
      throw error;
    }
  },
}));

export type { ProjectState };
