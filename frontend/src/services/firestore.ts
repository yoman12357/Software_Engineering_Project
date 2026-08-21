/**
 * Local chat persistence.
 *
 * The historical export name is retained to avoid a broad store migration,
 * but all data is stored in browser localStorage. No Firebase or cloud API is
 * contacted, preserving CyberSRS's local-first boundary.
 */

import { api } from "../api/client";
import { ApiRequestError, type ChatSessionSnapshot, type ChatSessionWrite, type ProjectRead, type SRSVersionRead } from "../api/types";

export interface StoredProject {
  id: string;
  name: string;
  description: string;
  status: string;
  inferredCategories: string[];
  createdAt: string;
  updatedAt: string;
  userId?: string;
}

export interface StoredChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  type?: "text" | "analysis" | "clarification" | "generation" | "srs" | "error";
  metadata?: Record<string, unknown>;
  timestamp: string;
}

export interface StoredChatSession {
  id: string;
  projectId: string | null;
  name: string;
  messages: StoredChatMessage[];
  stage: ChatSessionWrite["stage"];
  analysis: Record<string, unknown> | null;
  clarificationQuestions: unknown[] | null;
  srs: unknown | null;
  srsVersionId: string | null;
  pendingProjectDescription?: string | null;
  /** ISO timestamp while pinned; null/undefined represents an unpinned legacy session. */
  pinnedAt?: string | null;
  createdAt: string;
  updatedAt: string;
  userId?: string;
}

export interface StoredSRSVersion {
  id: string;
  projectId: string;
  versionNumber: number;
  status: string;
  qualityScore: number | null;
  srs: unknown;
  createdAt: string;
  modelVariant: string;
  modelName: string;
  adapterName: string | null;
  ragEnabled: boolean;
  generationMetadata: Record<string, unknown>;
}

const PROJECTS_KEY = "cybersrs-local-projects";
const SESSIONS_KEY = "cybersrs-local-chat-sessions";
const SRS_KEY = "cybersrs-local-srs-versions";

function readArray<T>(key: string): T[] {
  try {
    const raw = localStorage.getItem(key);
    return raw ? (JSON.parse(raw) as T[]) : [];
  } catch {
    return [];
  }
}

function writeArray<T>(key: string, value: T[]): void {
  localStorage.setItem(key, JSON.stringify(value));
}

function isBackendUnavailable(error: unknown): boolean {
  return error instanceof ApiRequestError && error.code === "network_error";
}

function sortChatSessions(sessions: StoredChatSession[]): StoredChatSession[] {
  return sessions.sort((a, b) => {
    const aPinned = a.pinnedAt ?? "";
    const bPinned = b.pinnedAt ?? "";
    if (aPinned && !bPinned) return -1;
    if (!aPinned && bPinned) return 1;
    if (aPinned && bPinned) return bPinned.localeCompare(aPinned);
    return b.updatedAt.localeCompare(a.updatedAt);
  });
}

function fromApiSession(session: ChatSessionSnapshot): StoredChatSession {
  return {
    id: session.id,
    projectId: session.project_id,
    name: session.name,
    messages: session.messages,
    stage: session.stage,
    analysis: session.analysis,
    clarificationQuestions: session.clarification_questions,
    srs: session.srs,
    srsVersionId: session.srs_version_id,
    pendingProjectDescription: session.pending_project_description,
    pinnedAt: session.pinned_at,
    createdAt: session.created_at,
    updatedAt: session.updated_at,
  };
}

function toApiSession(session: StoredChatSession): ChatSessionWrite {
  return {
    project_id: session.projectId,
    name: session.name,
    messages: session.messages,
    stage: session.stage,
    analysis: session.analysis,
    clarification_questions: session.clarificationQuestions,
    srs: session.srs as Record<string, unknown> | null,
    srs_version_id: session.srsVersionId,
    pending_project_description: session.pendingProjectDescription ?? null,
  };
}

class LocalPersistenceService {
  async saveProject(project: StoredProject): Promise<void> {
    const projects = readArray<StoredProject>(PROJECTS_KEY);
    const next = projects.filter((item) => item.id !== project.id);
    next.push(project);
    writeArray(PROJECTS_KEY, next);
  }

  async getProject(projectId: string): Promise<StoredProject | null> {
    return readArray<StoredProject>(PROJECTS_KEY).find((item) => item.id === projectId) ?? null;
  }

  async getAllProjects(): Promise<StoredProject[]> {
    return readArray<StoredProject>(PROJECTS_KEY);
  }

  async getUserProjects(): Promise<StoredProject[]> {
    return this.getAllProjects();
  }

  async saveChatSession(session: StoredChatSession): Promise<void> {
    const sessions = readArray<StoredChatSession>(SESSIONS_KEY);
    const existing = sessions.find((item) => item.id === session.id);
    const nextSession = {
      ...session,
      name:
        existing?.name && session.name.startsWith("Chat ")
          ? existing.name
          : session.name,
      pinnedAt: session.pinnedAt === undefined ? existing?.pinnedAt ?? null : session.pinnedAt,
      createdAt: existing?.createdAt ?? session.createdAt,
      updatedAt: new Date().toISOString(),
    };
    writeArray(
      SESSIONS_KEY,
      [...sessions.filter((item) => item.id !== session.id), nextSession],
    );
    try {
      await api.saveChatSession(session.id, toApiSession(nextSession));
    } catch (error) {
      if (!isBackendUnavailable(error)) throw error;
    }
  }

  async getChatSession(sessionId: string): Promise<StoredChatSession | null> {
    try {
      const remote = fromApiSession(await api.getChatSession(sessionId));
      const sessions = readArray<StoredChatSession>(SESSIONS_KEY);
      writeArray(SESSIONS_KEY, [...sessions.filter((item) => item.id !== sessionId), remote]);
      return remote;
    } catch (error) {
      const local = readArray<StoredChatSession>(SESSIONS_KEY).find((item) => item.id === sessionId) ?? null;
      if (local) {
        if (error instanceof ApiRequestError && error.status === 404) {
          await api.saveChatSession(local.id, toApiSession(local));
        }
        return local;
      }
      if (isBackendUnavailable(error) || (error instanceof ApiRequestError && error.status === 404)) {
        return null;
      }
      throw error;
    }
  }

  async getProjectChatSessions(projectId: string): Promise<StoredChatSession[]> {
    return sortChatSessions(
      readArray<StoredChatSession>(SESSIONS_KEY).filter((item) => item.projectId === projectId),
    );
  }

  async getRecentChatSessions(limit = 50): Promise<StoredChatSession[]> {
    try {
      const response = await api.listChatSessions(limit);
      const remote = response.sessions.map(fromApiSession);
      const local = readArray<StoredChatSession>(SESSIONS_KEY);
      const remoteIds = new Set(remote.map((session) => session.id));
      const sessionsToMigrate = local.filter((session) => !remoteIds.has(session.id));
      if (sessionsToMigrate.length > 0) {
        await Promise.all(
          sessionsToMigrate.map((session) =>
            api.saveChatSession(session.id, toApiSession(session)),
          ),
        );
      }
      const merged = sortChatSessions([...remote, ...sessionsToMigrate]);
      writeArray(SESSIONS_KEY, merged);
      return merged.slice(0, limit);
    } catch {
      return sortChatSessions(readArray<StoredChatSession>(SESSIONS_KEY)).slice(0, limit);
    }
  }

  async deleteChatSession(sessionId: string): Promise<void> {
    try {
      await api.deleteChatSession(sessionId);
    } catch (error) {
      if (!(isBackendUnavailable(error) || (error instanceof ApiRequestError && error.status === 404))) {
        throw error;
      }
    }
    writeArray(
      SESSIONS_KEY,
      readArray<StoredChatSession>(SESSIONS_KEY).filter((item) => item.id !== sessionId),
    );
  }

  async deleteProjectChatSessions(projectId: string): Promise<void> {
    writeArray(
      SESSIONS_KEY,
      readArray<StoredChatSession>(SESSIONS_KEY).filter(
        (item) => item.projectId !== projectId,
      ),
    );
  }

  async updateChatSessionName(sessionId: string, newName: string): Promise<void> {
    try {
      await api.updateChatSession(sessionId, { name: newName });
    } catch (error) {
      if (!isBackendUnavailable(error)) throw error;
    }
    const sessions = readArray<StoredChatSession>(SESSIONS_KEY).map((item) =>
      item.id === sessionId
        ? { ...item, name: newName, updatedAt: new Date().toISOString() }
        : item,
    );
    writeArray(SESSIONS_KEY, sessions);
  }

  async updateChatSessionPinned(sessionId: string, pinned: boolean): Promise<void> {
    try {
      await api.updateChatSession(sessionId, { pinned });
    } catch (error) {
      if (!isBackendUnavailable(error)) throw error;
    }
    const sessions = readArray<StoredChatSession>(SESSIONS_KEY).map((item) =>
      item.id === sessionId
        ? { ...item, pinnedAt: pinned ? new Date().toISOString() : null }
        : item,
    );
    writeArray(SESSIONS_KEY, sessions);
  }

  async saveSRSVersion(version: StoredSRSVersion): Promise<void> {
    const versions = readArray<StoredSRSVersion>(SRS_KEY);
    writeArray(SRS_KEY, [...versions.filter((item) => item.id !== version.id), version]);
  }

  async getSRSVersion(versionId: string): Promise<StoredSRSVersion | null> {
    return readArray<StoredSRSVersion>(SRS_KEY).find((item) => item.id === versionId) ?? null;
  }

  async getProjectSRSVersions(projectId: string): Promise<StoredSRSVersion[]> {
    return readArray<StoredSRSVersion>(SRS_KEY)
      .filter((item) => item.projectId === projectId)
      .sort((a, b) => b.versionNumber - a.versionNumber);
  }

  async deleteSRSVersion(versionId: string): Promise<void> {
    writeArray(
      SRS_KEY,
      readArray<StoredSRSVersion>(SRS_KEY).filter((item) => item.id !== versionId),
    );
  }

  async syncProjectFromAPI(project: ProjectRead): Promise<void> {
    await this.saveProject({
      id: project.id,
      name: project.name,
      description: project.description,
      status: project.status,
      inferredCategories: project.inferred_categories,
      createdAt: project.created_at,
      updatedAt: project.updated_at,
    });
  }

  async syncSRSVersionFromAPI(version: SRSVersionRead): Promise<void> {
    const srs = version.srs as unknown as Record<string, unknown> | null;
    const metadata = (srs?.metadata ?? {}) as Record<string, unknown>;
    const generation = (srs?.generation_metadata ?? {}) as Record<string, unknown>;
    await this.saveSRSVersion({
      id: version.id,
      projectId: version.project_id,
      versionNumber: version.version_number,
      status: version.status,
      qualityScore: version.quality_score,
      srs: version.srs,
      createdAt: version.created_at,
      modelVariant: (metadata.adapter_name as string) || "base",
      modelName: (metadata.model_name as string) || "",
      adapterName: (metadata.adapter_name as string) ?? null,
      ragEnabled: Boolean(generation.rag_enabled),
      generationMetadata: generation,
    });
  }
}

export const firestoreService = new LocalPersistenceService();

export async function isFirestoreReady(): Promise<boolean> {
  return true;
}
