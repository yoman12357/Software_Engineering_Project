// Centralized typed API client. All backend calls go through this module;
// components never perform raw fetch calls.

import {
  ApiRequestError,
  type AnalysisResponse,
  type ClarificationAnswerItem,
  type ClarificationAnswerSubmissionResponse,
  type ClarificationQuestionListResponse,
  type ProjectCreatePayload,
  type ProjectRead,
  type ProjectContextRead,
  type SRSEditRequest,
  type SRSRegeneratableSection,
  type SRSGenerationResponse,
  type SRSGenerationProgressEvent,
  type SRSValidationResponse,
  type SRSVersionRead,
  type SRSVersionListResponse,
  type ApiErrorEnvelope,
  type ArtifactProvenanceResponse,
  type SRSSourcesResponse,
  type SourceChunk,
  type ChatCompletionResponse,
  type ProjectDocumentRead,
  type ChatSessionListResponse,
  type ChatSessionSnapshot,
  type ChatSessionWrite,
  type HealthResponse,
  type ModelInfoResponse,
} from "./types";

interface ProjectListResponse {
  projects: ProjectRead[];
}

const BASE = "/api/v1";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    const isFormData = typeof FormData !== "undefined" && init?.body instanceof FormData;
    response = await fetch(`${BASE}${path}`, {
      headers: {
        ...(isFormData ? {} : { "Content-Type": "application/json" }),
        ...(init?.headers ?? {}),
      },
      ...init,
    });
  } catch {
    // Network-level failure (backend unreachable).
    throw new ApiRequestError(0, {
      error: {
        code: "network_error",
        message: "Could not reach the CyberSRS backend. Is it running?",
        details: {},
      },
    });
  }

  if (response.status === 204) {
    return undefined as T;
  }

  const body = (await response.json()) as T | ApiErrorEnvelope;

  if (!response.ok) {
    const envelope = body as ApiErrorEnvelope;
    const message =
      envelope.error?.message ?? `Request failed with status ${response.status}`;
    const code = envelope.error?.code ?? "unknown_error";
    throw new ApiRequestError(response.status, {
      error: { code, message, details: envelope.error?.details ?? {} },
    });
  }

  return body as T;
}

async function requestWithNetworkRetry<T>(
  path: string,
  init?: RequestInit,
  maxAttempts = 4,
): Promise<T> {
  let lastError: unknown;
  for (let attempt = 1; attempt <= maxAttempts; attempt += 1) {
    try {
      return await request<T>(path, init);
    } catch (error) {
      lastError = error;
      const isNetworkError = error instanceof ApiRequestError && error.code === "network_error";
      if (!isNetworkError || attempt === maxAttempts) throw error;
      await new Promise((resolve) => window.setTimeout(resolve, attempt * 500));
    }
  }
  throw lastError;
}

export const api = {
  getHealth(): Promise<HealthResponse> {
    return request<HealthResponse>("/health");
  },

  getModelInfo(): Promise<ModelInfoResponse> {
    return request<ModelInfoResponse>("/system/model-info");
  },

  listChatSessions(limit = 50): Promise<ChatSessionListResponse> {
    return request<ChatSessionListResponse>(`/chat/sessions?limit=${limit}`);
  },

  getChatSession(sessionId: string): Promise<ChatSessionSnapshot> {
    return request<ChatSessionSnapshot>(`/chat/sessions/${encodeURIComponent(sessionId)}`);
  },

  saveChatSession(sessionId: string, payload: ChatSessionWrite): Promise<ChatSessionSnapshot> {
    return request<ChatSessionSnapshot>(`/chat/sessions/${encodeURIComponent(sessionId)}`, {
      method: "PUT",
      body: JSON.stringify(payload),
    });
  },

  updateChatSession(
    sessionId: string,
    payload: { name?: string; pinned?: boolean },
  ): Promise<ChatSessionSnapshot> {
    return request<ChatSessionSnapshot>(`/chat/sessions/${encodeURIComponent(sessionId)}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    });
  },

  deleteChatSession(sessionId: string): Promise<void> {
    return request<void>(`/chat/sessions/${encodeURIComponent(sessionId)}`, {
      method: "DELETE",
    });
  },

  // Projects
  createProject(payload: ProjectCreatePayload): Promise<ProjectRead> {
    return request<ProjectRead>("/projects", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  listProjects(): Promise<ProjectListResponse> {
    return request<ProjectListResponse>("/projects");
  },

  getProject(projectId: string): Promise<ProjectRead> {
    return request<ProjectRead>(`/projects/${projectId}`);
  },

  deleteProject(projectId: string): Promise<void> {
    return request<void>(`/projects/${projectId}`, {
      method: "DELETE",
    });
  },

  updateProject(projectId: string, payload: Partial<ProjectRead>): Promise<ProjectRead> {
    return request<ProjectRead>(`/projects/${projectId}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    });
  },

  uploadProjectDocument(projectId: string, file: File): Promise<ProjectDocumentRead> {
    const body = new FormData();
    body.append("file", file);
    return request<ProjectDocumentRead>(`/projects/${projectId}/documents`, {
      method: "POST",
      body,
    });
  },

  listProjectDocuments(projectId: string): Promise<{ documents: ProjectDocumentRead[]; total: number }> {
    return request(`/projects/${projectId}/documents`);
  },

  deleteProjectDocument(projectId: string, documentId: string): Promise<void> {
    return request<void>(`/projects/${projectId}/documents/${documentId}`, { method: "DELETE" });
  },

  // Analysis
  analyseProject(projectId: string): Promise<AnalysisResponse> {
    return request<AnalysisResponse>(`/projects/${projectId}/analyse`, {
      method: "POST",
    });
  },

  getProjectContext(projectId: string): Promise<ProjectContextRead> {
    return request<ProjectContextRead>(`/projects/${projectId}/context`);
  },

  // Clarifications
  generateClarificationQuestions(
    projectId: string,
  ): Promise<ClarificationQuestionListResponse> {
    return request<ClarificationQuestionListResponse>(
      `/projects/${projectId}/clarifications/generate`,
      { method: "POST" },
    );
  },

  submitClarificationAnswers(
    projectId: string,
    answers: ClarificationAnswerItem[],
  ): Promise<ClarificationAnswerSubmissionResponse> {
    return request<ClarificationAnswerSubmissionResponse>(
      `/projects/${projectId}/clarifications`,
      { method: "POST", body: JSON.stringify({ answers }) },
    );
  },

  // SRS
  generateSrs(projectId: string): Promise<SRSGenerationResponse> {
    return request<SRSGenerationResponse>(`/projects/${projectId}/srs/generate`, {
      method: "POST",
    });
  },

  getLatestSrs(projectId: string): Promise<SRSVersionRead> {
    return request<SRSVersionRead>(`/projects/${projectId}/srs`);
  },

  getSrsVersion(projectId: string, versionId: string): Promise<SRSVersionRead> {
    return request<SRSVersionRead>(
      `/projects/${projectId}/srs/versions/${versionId}`,
    );
  },

  listSrsVersions(projectId: string): Promise<SRSVersionListResponse> {
    return request<SRSVersionListResponse>(`/projects/${projectId}/srs/versions`);
  },

  async generateSrsStream(
    projectId: string,
    onProgress: (event: SRSGenerationProgressEvent) => void,
    signal?: AbortSignal,
  ): Promise<SRSGenerationResponse> {
    const response = await fetch(`${BASE}/projects/${projectId}/srs/generate/stream`, {
      method: "POST",
      headers: { Accept: "text/event-stream" },
      signal,
    });
    if (!response.ok) {
      const body = (await response.json()) as ApiErrorEnvelope;
      throw new ApiRequestError(response.status, {
        error: {
          code: body.error?.code ?? "generation_failed",
          message: body.error?.message ?? "SRS generation failed.",
          details: body.error?.details ?? {},
        },
      });
    }
    if (!response.body) throw new Error("The backend returned no generation stream.");

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";
    let result: SRSGenerationResponse | null = null;
    while (true) {
      const chunk = await reader.read();
      buffer += decoder.decode(chunk.value, { stream: !chunk.done });
      const frames = buffer.split("\n\n");
      buffer = frames.pop() ?? "";
      for (const frame of frames) {
        const data = frame
          .split("\n")
          .find((line) => line.startsWith("data: "))
          ?.slice(6);
        if (!data) continue;
        const event = JSON.parse(data) as SRSGenerationProgressEvent;
        onProgress(event);
        if (event.phase === "failed") {
          throw new ApiRequestError(event.error_code === "llm_timeout" ? 504 : 422, {
            error: {
              code: event.error_code ?? "generation_failed",
              message: event.message,
              details: {},
            },
          });
        }
        if (event.phase === "completed" && event.result) result = event.result;
      }
      if (chunk.done) break;
    }
    if (!result) throw new Error("Generation ended without a validated completion event.");
    return result;
  },

  getSrsProvenance(
    projectId: string,
    versionId: string,
  ): Promise<ArtifactProvenanceResponse> {
    return request<ArtifactProvenanceResponse>(
      `/projects/${projectId}/srs/versions/${versionId}/provenance`,
    );
  },

  editSrsVersion(
    projectId: string,
    versionId: string,
    payload: SRSEditRequest,
  ): Promise<SRSVersionRead> {
    return request<SRSVersionRead>(
      `/projects/${projectId}/srs/versions/${versionId}`,
      { method: "PUT", body: JSON.stringify(payload) },
    );
  },

  validateSrsVersion(
    projectId: string,
    versionId: string,
  ): Promise<SRSValidationResponse> {
    return request<SRSValidationResponse>(
      `/projects/${projectId}/srs/versions/${versionId}/validate`,
      { method: "POST" },
    );
  },

  getSrsSources(projectId: string, versionId: string): Promise<SRSSourcesResponse> {
    return request<SRSSourcesResponse>(`/projects/${projectId}/srs/versions/${versionId}/sources`);
  },

  getSrsSourceChunk(projectId: string, versionId: string, chunkId: string): Promise<SourceChunk> {
    return request<SourceChunk>(`/projects/${projectId}/srs/versions/${versionId}/sources/${chunkId}`);
  },

  async exportSrsPdf(projectId: string, versionId: string): Promise<Blob> {
    let response: Response;
    try {
      response = await fetch(`${BASE}/projects/${projectId}/srs/versions/${versionId}/export/pdf`);
    } catch {
      throw new ApiRequestError(0, {
        error: {
          code: "network_error",
          message: "Could not reach the CyberSRS backend. Is it running?",
          details: {},
        },
      });
    }
    if (!response.ok) {
      const body = (await response.json()) as ApiErrorEnvelope;
      throw new ApiRequestError(response.status, {
        error: {
          code: body.error?.code ?? "unknown_error",
          message: body.error?.message ?? `Request failed with status ${response.status}`,
          details: body.error?.details ?? {},
        },
      });
    }
    return response.blob();
  },

  // General chat
  chatCompletion(
    messages: { role: "user" | "assistant"; content: string }[],
    projectId?: string,
  ): Promise<ChatCompletionResponse> {
    return requestWithNetworkRetry("/chat/completions", {
      method: "POST",
      body: JSON.stringify({ messages, project_id: projectId }),
    });
  },

  regenerateSrsSection(
    projectId: string,
    versionId: string,
    section: SRSRegeneratableSection,
  ): Promise<SRSVersionRead> {
    return request<SRSVersionRead>(
      `/projects/${projectId}/srs/versions/${versionId}/regenerate`,
      { method: "POST", body: JSON.stringify({ section }) },
    );
  },

  // Intent classification
  classifyIntent(message: string, projectId?: string, hasSrs?: boolean, workflowStage?: string): Promise<{
    intent: "general_question" | "project_description" | "srs_project_request" | "srs_modification" | "srs_generation" | "clarification";
    confidence: number;
    extracted_data: Record<string, unknown>;
  }> {
    return requestWithNetworkRetry("/chat/intent", {
      method: "POST",
      body: JSON.stringify({
        message,
        project_id: projectId,
        has_srs: hasSrs,
        workflow_stage: workflowStage,
      }),
    });
  },

// SRS edit via chat
  editSrsViaChat(projectId: string, versionId: string, instruction: string): Promise<{
    success: boolean;
    message: string;
    updated_srs?: unknown;
  }> {
    return request("/chat/srs-edit", {
      method: "POST",
      body: JSON.stringify({ project_id: projectId, version_id: versionId, instruction }),
    });
  },

  // Export chat as markdown
  exportChatAsMarkdown(sessionId: string): Promise<{ markdown: string; filename: string }> {
    return request("/chat/export/markdown", {
      method: "POST",
      body: JSON.stringify({ session_id: sessionId }),
    });
  },
};
