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
  type SRSGenerationResponse,
  type SRSValidationResponse,
  type SRSVersionRead,
  type ApiErrorEnvelope,
  type ArtifactProvenanceResponse,
} from "./types";

interface ProjectListResponse {
  projects: ProjectRead[];
}

const BASE = "/api/v1";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${BASE}${path}`, {
      headers: {
        "Content-Type": "application/json",
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

export const api = {
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
};
