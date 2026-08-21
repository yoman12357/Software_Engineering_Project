import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";
import type { ProjectAnalysis, ClarificationQuestionRead, SRSSchema, ChatMessage } from "../api/types";
import { firestoreService, type StoredChatSession, type StoredChatMessage } from "../services/firestore";

export type ChatStage = "welcome" | "analyzing" | "clarifying" | "generating" | "ready" | "error";

interface ChatState {
  stage: ChatStage;
  projectId: string | null;
  sessionId: string | null;
  messages: ChatMessage[];
  analysis: ProjectAnalysis | null;
  clarificationQuestions: ClarificationQuestionRead[] | null;
  srs: SRSSchema | null;
  srsVersionId: string | null;
  pendingProjectDescription: string | null;
  isLoading: boolean;
  error: string | null;
  isSyncing: boolean;
  syncError: string | null;
  tourOpen: boolean;

  setStage: (stage: ChatStage) => void;
  setProjectId: (id: string | null) => void;
  setSessionId: (id: string | null) => void;
  addMessage: (message: Omit<ChatMessage, "id" | "timestamp"> & { id?: string; timestamp?: string }) => void;
  clearMessages: () => void;
  setAnalysis: (analysis: ProjectAnalysis) => void;
  setClarificationQuestions: (questions: ClarificationQuestionRead[]) => void;
  setSRS: (srs: SRSSchema, versionId: string) => void;
  clearSRS: () => void;
  setPendingProjectDescription: (description: string | null) => void;
  setLoading: (loading: boolean) => void;
  setTourOpen: (open: boolean) => void;
  setError: (error: string | null) => void;
  setSyncing: (syncing: boolean) => void;
  setSyncError: (error: string | null) => void;
  reset: () => void;
  loadChatSession: (sessionId: string) => Promise<void>;
  saveChatSession: () => Promise<void>;
  createNewChatSession: (projectId?: string) => Promise<string>;
}

export const useChatStore = create<ChatState>()(
  persist(
    (set, get) => ({
      stage: "welcome",
      projectId: null,
      sessionId: null,
      messages: [],
      analysis: null,
      clarificationQuestions: null,
      srs: null,
      srsVersionId: null,
      pendingProjectDescription: null,
      isLoading: false,
      error: null,
      isSyncing: false,
      syncError: null,
      tourOpen: false,

      setStage: (stage) => set({ stage }),
      setProjectId: (id) => set({ projectId: id }),
      setSessionId: (id) => set({ sessionId: id }),
      addMessage: (message) =>
        set((state) => {
          const previous = state.messages[state.messages.length - 1];
          if (
            message.type === "error" &&
            previous?.type === "error" &&
            previous.content === message.content
          ) {
            return state;
          }
          return {
            messages: [
              ...state.messages,
              { ...message, id: message.id ?? crypto.randomUUID(), timestamp: message.timestamp ?? new Date().toISOString() },
            ],
          };
        }),
      clearMessages: () => set({ messages: [] }),
      setAnalysis: (analysis) => set({ analysis }),
      setClarificationQuestions: (questions) => set({ clarificationQuestions: questions }),
      setSRS: (srs, versionId) => set({ srs, srsVersionId: versionId }),
      clearSRS: () => set({ srs: null, srsVersionId: null }),
      setPendingProjectDescription: (pendingProjectDescription) => set({ pendingProjectDescription }),
      setLoading: (isLoading) => set({ isLoading }),
      setError: (error) => set({ error }),
      setSyncing: (isSyncing) => set({ isSyncing }),
      setSyncError: (error) => set({ syncError: error }),
      setTourOpen: (open) => set({ tourOpen: open }),
      reset: () => {
        const { tourOpen } = get();
        set({
          stage: "welcome",
          projectId: null,
          sessionId: null,
          messages: [],
          analysis: null,
          clarificationQuestions: null,
          srs: null,
          srsVersionId: null,
          pendingProjectDescription: null,
          isLoading: false,
          error: null,
          isSyncing: false,
          syncError: null,
          tourOpen,
        });
      },

      loadChatSession: async (sessionId: string) => {
        try {
          set({ isSyncing: true, syncError: null });
          const session = await firestoreService.getChatSession(sessionId);
          if (session) {
            const messages: ChatMessage[] = session.messages.map((m) => ({
              id: m.id,
              role: m.role,
              content: m.content,
              type: m.type,
              metadata: m.metadata,
              timestamp: m.timestamp,
            }));
            set({
              messages,
              projectId: session.projectId,
              sessionId: session.id,
              stage: session.stage as ChatStage,
              analysis: session.analysis as ProjectAnalysis | null,
              clarificationQuestions: session.clarificationQuestions as ClarificationQuestionRead[] | null,
              srs: session.srs as SRSSchema | null,
              srsVersionId: session.srsVersionId,
              pendingProjectDescription: session.pendingProjectDescription ?? null,
            });
          }
        } catch {
          set({ syncError: "Failed to load chat session" });
        } finally {
          set({ isSyncing: false });
        }
      },

      saveChatSession: async () => {
        const { sessionId, projectId, messages, stage, analysis, clarificationQuestions, srs, srsVersionId, pendingProjectDescription } = get();
        if (!sessionId || messages.length === 0) return;
        try {
          set({ isSyncing: true, syncError: null });
          const storedMessages: StoredChatMessage[] = messages.map((m) => ({
            id: m.id,
            role: m.role,
            content: m.content,
            type: m.type,
            metadata: m.metadata,
            timestamp: m.timestamp,
          }));
          const session: StoredChatSession = {
            id: sessionId,
            projectId,
            name: `Chat ${new Date().toLocaleDateString()}`,
            messages: storedMessages,
            stage,
            analysis: analysis as Record<string, unknown> | null,
            clarificationQuestions: clarificationQuestions as unknown[] | null,
            srs: srs as unknown | null,
            srsVersionId,
            pendingProjectDescription,
            createdAt: new Date().toISOString(),
            updatedAt: new Date().toISOString(),
          };
          await firestoreService.saveChatSession(session);
        } catch {
          set({ syncError: "Failed to save chat session" });
        } finally {
          set({ isSyncing: false });
        }
      },

      createNewChatSession: async (projectId?: string) => {
        const newSessionId = `chat_${crypto.randomUUID()}`;
        set({
          sessionId: newSessionId,
          projectId: projectId ?? null,
          messages: [],
          stage: "welcome",
          analysis: null,
          clarificationQuestions: null,
          srs: null,
          srsVersionId: null,
          pendingProjectDescription: null,
          isLoading: false,
          error: null,
          isSyncing: false,
          syncError: null,
        });
        // Save initial empty session
        const session: StoredChatSession = {
          id: newSessionId,
          projectId: projectId ?? null,
          name: `Chat ${new Date().toLocaleDateString()}`,
          messages: [],
          stage: "welcome",
          analysis: null,
          clarificationQuestions: null,
          srs: null,
          srsVersionId: null,
          pendingProjectDescription: null,
          createdAt: new Date().toISOString(),
          updatedAt: new Date().toISOString(),
        };
        await firestoreService.saveChatSession(session);
        return newSessionId;
      },
    }),
    {
      name: "cybersrs-chat",
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        stage: state.stage,
        projectId: state.projectId,
        sessionId: state.sessionId,
        messages: state.messages,
        analysis: state.analysis,
        clarificationQuestions: state.clarificationQuestions,
        srs: state.srs,
        srsVersionId: state.srsVersionId,
        pendingProjectDescription: state.pendingProjectDescription,
        tourOpen: state.tourOpen,
      }),
    }
  )
);
