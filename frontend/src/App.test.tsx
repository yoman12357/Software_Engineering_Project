import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import App from "./App";
import { api } from "./api/client";
import { useChatStore } from "./stores/chatStore";
import { useProjectStore } from "./stores/projectStore";
import {
  SAMPLE_ANALYSIS_RESPONSE,
  SAMPLE_CLARIFICATIONS,
  SAMPLE_PROJECT,
  SAMPLE_SRS_GENERATION,
  SAMPLE_SRS_PROVENANCE,
  SAMPLE_SRS_VERSION,
} from "./test/fixtures";

vi.mock("./api/client", () => ({
  api: {
    listChatSessions: vi.fn(),
    getChatSession: vi.fn(),
    saveChatSession: vi.fn(),
    updateChatSession: vi.fn(),
    deleteChatSession: vi.fn(),
    createProject: vi.fn(),
    getProject: vi.fn(),
    listProjects: vi.fn(),
    deleteProject: vi.fn(),
    updateProject: vi.fn(),
    analyseProject: vi.fn(),
    generateClarificationQuestions: vi.fn(),
    submitClarificationAnswers: vi.fn(),
    generateSrs: vi.fn(),
    generateSrsStream: vi.fn(),
    getLatestSrs: vi.fn(),
    listSrsVersions: vi.fn(),
    getSrsVersion: vi.fn(),
    getSrsProvenance: vi.fn(),
    editSrsVersion: vi.fn(),
    validateSrsVersion: vi.fn(),
    chatCompletion: vi.fn(),
    classifyIntent: vi.fn(),
    editSrsViaChat: vi.fn(),
  },
}));

const mockedApi = vi.mocked(api);
const description =
  "I want to build a firewall and monitoring system for my college network.";

async function submitProjectDescription() {
  await userEvent.type(screen.getByLabelText("Message input"), description);
  await userEvent.click(screen.getByRole("button", { name: "Send message" }));
}

describe("App end-to-end mock flow", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    window.location.hash = "";
    useChatStore.getState().reset();
    useProjectStore.setState({
      projects: [],
      chatSessions: [],
      currentProjectId: null,
      isLoading: false,
      error: null,
    });
    mockedApi.listProjects.mockResolvedValue({ projects: [] });
    mockedApi.listChatSessions.mockResolvedValue({ sessions: [], total: 0 });
    mockedApi.listSrsVersions.mockResolvedValue({ project_id: SAMPLE_PROJECT.id, versions: [] });
    mockedApi.saveChatSession.mockImplementation(async (id, payload) => ({
      id,
      ...payload,
      pinned_at: null,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    }));
    mockedApi.classifyIntent.mockImplementation(async (message) => ({
      intent: message.toLowerCase().includes("generate srs")
        ? "srs_generation"
        : "project_description",
      confidence: 0.95,
      extracted_data: {},
    }));
  });

  it("creates, analyses, clarifies, generates SRS, and renders requirements", async () => {
    mockedApi.chatCompletion.mockResolvedValue({
      content: "I understand you want to build a firewall. Would you like me to generate an SRS for this project?",
      is_project_description: true,
      model_name: "qwen3",
      rag_enabled: true,
      citations: [],
      warnings: [],
    });
    mockedApi.createProject.mockResolvedValue(SAMPLE_PROJECT);
    mockedApi.analyseProject.mockResolvedValue(SAMPLE_ANALYSIS_RESPONSE);
    mockedApi.generateClarificationQuestions.mockResolvedValue(SAMPLE_CLARIFICATIONS);
    mockedApi.submitClarificationAnswers.mockResolvedValue({
      project_id: SAMPLE_PROJECT.id,
      answers_saved: 2,
      context_updated: true,
    });
    mockedApi.generateSrs.mockResolvedValue(SAMPLE_SRS_GENERATION);
    mockedApi.generateSrsStream.mockImplementation(async (_projectId, onProgress) => {
      onProgress({
        phase: "completed",
        progress: 100,
        message: "SRS generation completed.",
        result: SAMPLE_SRS_GENERATION,
      });
      return SAMPLE_SRS_GENERATION;
    });
    mockedApi.getSrsVersion.mockResolvedValue(SAMPLE_SRS_VERSION);
    mockedApi.getSrsProvenance.mockResolvedValue(SAMPLE_SRS_PROVENANCE);

    render(<App />);

    // First message goes to chatCompletion
    await submitProjectDescription();

    // User message appears
    await screen.findByText(description);
    // Assistant response appears
    await screen.findByText(/I understand you want to build a firewall/);

    // Now type "generate srs" to trigger project creation
    await userEvent.type(screen.getByLabelText("Message input"), "generate srs");
    await userEvent.click(screen.getByRole("button", { name: "Send message" }));

    // Analysis should run
    await screen.findByText("Campus IT department");
    expect(screen.getByText("CAT-02")).toBeInTheDocument();
    expect(screen.getByText("CAT-03")).toBeInTheDocument();

    await screen.findByText("How many network nodes will the firewall protect?");

    await userEvent.type(screen.getByLabelText(/How many network nodes/), "500 nodes");
    await userEvent.click(screen.getByRole("button", { name: "Submit Answers" }));

    await screen.findByText("Software Requirements Specification Generated");
    await userEvent.click(screen.getByRole("button", { name: "View Full SRS" }));
    await screen.findByText("Traffic Filtering");
    expect(
      screen.getByText(
        "The system shall filter inbound and outbound traffic by default.",
      ),
    ).toBeInTheDocument();
    expect(screen.getByText("Functional")).toBeInTheDocument();
    expect(screen.getByText("Non-Functional")).toBeInTheDocument();
    expect(await screen.findByText("Base Qwen")).toBeInTheDocument();
    expect(screen.getByText("RAG enabled")).toBeInTheDocument();
    expect(screen.getByText("1 source / 2 chunks")).toBeInTheDocument();

    expect(mockedApi.chatCompletion).toHaveBeenCalled();
    expect(mockedApi.createProject).toHaveBeenCalledWith({
      name: expect.any(String),
      description,
    });
    expect(mockedApi.analyseProject).toHaveBeenCalledWith(SAMPLE_PROJECT.id);
    expect(mockedApi.generateClarificationQuestions).toHaveBeenCalledWith(
      SAMPLE_PROJECT.id,
    );
    expect(mockedApi.submitClarificationAnswers).toHaveBeenCalledWith(
      SAMPLE_PROJECT.id,
      expect.arrayContaining([
        expect.objectContaining({
          question_id: "q-001",
          answer_text: "500 nodes",
          skipped: false,
        }),
        expect.objectContaining({ question_id: "q-002", skipped: true }),
      ]),
    );
    expect(mockedApi.generateSrsStream).toHaveBeenCalledWith(
      SAMPLE_PROJECT.id,
      expect.any(Function),
      expect.any(AbortSignal),
    );
    expect(mockedApi.getSrsVersion).toHaveBeenCalledWith(
      SAMPLE_PROJECT.id,
      "version-1",
    );
  });

  it("starts analysis and clarification immediately for a detailed SRS request", async () => {
    const srsRequest = [
      "# Software Requirements Specification (SRS): Secure Zero-Trust VPN Gateway",
      "## Overview",
      "Create a secure VPN gateway for remote employees with MFA and device attestation.",
      "## Functional Requirements",
      "The system shall verify user identity and device posture before access.",
    ].join("\n");
    mockedApi.classifyIntent.mockResolvedValue({
      intent: "srs_project_request",
      confidence: 0.99,
      extracted_data: {},
    });
    mockedApi.createProject.mockResolvedValue(SAMPLE_PROJECT);
    mockedApi.analyseProject.mockResolvedValue(SAMPLE_ANALYSIS_RESPONSE);
    mockedApi.generateClarificationQuestions.mockResolvedValue(SAMPLE_CLARIFICATIONS);

    render(<App />);
    await userEvent.type(screen.getByLabelText("Message input"), srsRequest);
    await userEvent.click(screen.getByRole("button", { name: "Send message" }));

    await screen.findByText("How many network nodes will the firewall protect?");
    expect(mockedApi.createProject).toHaveBeenCalledWith({
      name: "Secure Zero-Trust VPN Gateway",
      description: srsRequest,
    });
    expect(mockedApi.analyseProject).toHaveBeenCalledWith(SAMPLE_PROJECT.id);
    expect(mockedApi.generateClarificationQuestions).toHaveBeenCalledWith(
      SAMPLE_PROJECT.id,
    );
    expect(mockedApi.generateSrs).not.toHaveBeenCalled();
    expect(mockedApi.chatCompletion).not.toHaveBeenCalled();
  });

  it("shows loading states while analysing", async () => {
    let resolveAnalysis: (value: typeof SAMPLE_ANALYSIS_RESPONSE) => void = () => {};
    mockedApi.chatCompletion.mockResolvedValue({
      content: "Got it!",
      is_project_description: true,
      model_name: "qwen3",
      rag_enabled: true,
      citations: [],
      warnings: [],
    });
    mockedApi.createProject.mockResolvedValue(SAMPLE_PROJECT);
    mockedApi.analyseProject.mockImplementation(
      () =>
        new Promise((resolve) => {
          resolveAnalysis = resolve;
        }),
    );
    mockedApi.generateClarificationQuestions.mockResolvedValue(SAMPLE_CLARIFICATIONS);

    render(<App />);

    // First message: general chat
    await submitProjectDescription();
    await screen.findByText(/Got it!/);

    // Second message: trigger project creation
    await userEvent.type(screen.getByLabelText("Message input"), "generate srs for this project");
    await userEvent.click(screen.getByRole("button", { name: "Send message" }));

    expect(screen.getByText("Analyzing project...")).toBeInTheDocument();

    resolveAnalysis(SAMPLE_ANALYSIS_RESPONSE);
    await screen.findByText("How many network nodes will the firewall protect?");
  });

  it("displays API errors and retries without clearing the conversation", async () => {
    mockedApi.chatCompletion.mockResolvedValue({
      content: "OK let me create that for you.",
      is_project_description: true,
      model_name: "qwen3",
      rag_enabled: true,
      citations: [],
      warnings: [],
    });
    mockedApi.createProject.mockResolvedValue(SAMPLE_PROJECT);
    mockedApi.analyseProject
      .mockRejectedValueOnce(new Error("The project is not in a valid state for this operation."))
      .mockResolvedValueOnce(SAMPLE_ANALYSIS_RESPONSE);
    mockedApi.generateClarificationQuestions.mockResolvedValue(SAMPLE_CLARIFICATIONS);

    render(<App />);

    // First message: general chat
    await submitProjectDescription();
    await screen.findByText(/OK let me create that for you/);

    // Second message: trigger project creation
    await userEvent.type(screen.getByLabelText("Message input"), "generate srs");
    await userEvent.click(screen.getByRole("button", { name: "Send message" }));

    await screen.findByRole("alert");
    expect(
      screen.getByText("The project is not in a valid state for this operation."),
    ).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: "Retry" }));
    await screen.findByText("How many network nodes will the firewall protect?");
    expect(screen.getByText(description)).toBeInTheDocument();
    expect(mockedApi.analyseProject).toHaveBeenCalledTimes(2);
  });

  it("shows the composer-first welcome state", async () => {
    render(<App />);
    expect(screen.getByRole("heading", { name: "CyberSRS" })).toBeInTheDocument();
    expect(await screen.findByLabelText("Message input")).toBeInTheDocument();
  });

  it("restores an exact SRS version from its canonical direct route", async () => {
    window.location.hash = "projects/project-123/srs/version-1";
    mockedApi.getProject.mockResolvedValue(SAMPLE_PROJECT);
    mockedApi.getSrsVersion.mockResolvedValue(SAMPLE_SRS_VERSION);
    mockedApi.getSrsProvenance.mockResolvedValue(SAMPLE_SRS_PROVENANCE);

    render(<App />);

    expect(await screen.findByText("Traffic Filtering")).toBeInTheDocument();
    expect(mockedApi.getProject).toHaveBeenCalledWith("project-123");
    expect(mockedApi.getSrsVersion).toHaveBeenCalledWith("project-123", "version-1");
    expect(useChatStore.getState().srsVersionId).toBe("version-1");
    expect(useProjectStore.getState().currentProjectId).toBe("project-123");
  });
});
