import { create } from "zustand";
import type { ProjectAnalysis, ClarificationQuestionRead, SRSSchema } from "../api/types";

export type ChatStage = "welcome" | "analyzing" | "clarifying" | "generating" | "ready" | "error";

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  type?: "text" | "analysis" | "clarification" | "generation" | "srs" | "error";
  metadata?: Record<string, unknown>;
  timestamp: Date;
}

interface ChatState {
  stage: ChatStage;
  projectId: string | null;
  messages: ChatMessage[];
  analysis: ProjectAnalysis | null;
  clarificationQuestions: ClarificationQuestionRead[] | null;
  srs: SRSSchema | null;
  srsVersionId: string | null;
  isLoading: boolean;
  error: string | null;

  setStage: (stage: ChatStage) => void;
  setProjectId: (id: string | null) => void;
  addMessage: (message: Omit<ChatMessage, "id" | "timestamp">) => void;
  clearMessages: () => void;
  setAnalysis: (analysis: ProjectAnalysis) => void;
  setClarificationQuestions: (questions: ClarificationQuestionRead[]) => void;
  setSRS: (srs: SRSSchema, versionId: string) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  reset: () => void;
}

export const useChatStore = create<ChatState>((set) => ({
  stage: "welcome",
  projectId: null,
  messages: [],
  analysis: null,
  clarificationQuestions: null,
  srs: null,
  srsVersionId: null,
  isLoading: false,
  error: null,

  setStage: (stage) => set({ stage }),
  setProjectId: (id) => set({ projectId: id }),
  addMessage: (message) =>
    set((state) => ({
      messages: [
        ...state.messages,
        { ...message, id: crypto.randomUUID(), timestamp: new Date() },
      ],
    })),
  clearMessages: () => set({ messages: [] }),
  setAnalysis: (analysis) => set({ analysis }),
  setClarificationQuestions: (questions) => set({ clarificationQuestions: questions }),
  setSRS: (srs, versionId) => set({ srs, srsVersionId: versionId }),
  setLoading: (isLoading) => set({ isLoading }),
  setError: (error) => set({ error }),
  reset: () =>
    set({
      stage: "welcome",
      projectId: null,
      messages: [],
      analysis: null,
      clarificationQuestions: null,
      srs: null,
      srsVersionId: null,
      isLoading: false,
      error: null,
    }),
}));