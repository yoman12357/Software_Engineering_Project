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
    createProject: vi.fn(),
    listProjects: vi.fn(),
    deleteProject: vi.fn(),
    updateProject: vi.fn(),
    analyseProject: vi.fn(),
    generateClarificationQuestions: vi.fn(),
    submitClarificationAnswers: vi.fn(),
    generateSrs: vi.fn(),
    getSrsVersion: vi.fn(),
    getSrsProvenance: vi.fn(),
    editSrsVersion: vi.fn(),
    validateSrsVersion: vi.fn(),
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
      currentProjectId: null,
      isLoading: false,
      error: null,
    });
    mockedApi.listProjects.mockResolvedValue({ projects: [] });
  });

  it("creates, analyses, clarifies, generates SRS, and renders requirements", async () => {
    mockedApi.createProject.mockResolvedValue(SAMPLE_PROJECT);
    mockedApi.analyseProject.mockResolvedValue(SAMPLE_ANALYSIS_RESPONSE);
    mockedApi.generateClarificationQuestions.mockResolvedValue(SAMPLE_CLARIFICATIONS);
    mockedApi.submitClarificationAnswers.mockResolvedValue({
      project_id: SAMPLE_PROJECT.id,
      answers_saved: 2,
      context_updated: true,
    });
    mockedApi.generateSrs.mockResolvedValue(SAMPLE_SRS_GENERATION);
    mockedApi.getSrsVersion.mockResolvedValue(SAMPLE_SRS_VERSION);
    mockedApi.getSrsProvenance.mockResolvedValue(SAMPLE_SRS_PROVENANCE);

    render(<App />);

    await submitProjectDescription();

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

    expect(mockedApi.createProject).toHaveBeenCalledWith({
      name: "I want to build a firewall and monitoring",
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
    expect(mockedApi.generateSrs).toHaveBeenCalledWith(SAMPLE_PROJECT.id);
    expect(mockedApi.getSrsVersion).toHaveBeenCalledWith(
      SAMPLE_PROJECT.id,
      "version-1",
    );
  });

  it("shows loading states while analysing", async () => {
    let resolveAnalysis: (value: typeof SAMPLE_ANALYSIS_RESPONSE) => void = () => {};
    mockedApi.createProject.mockResolvedValue(SAMPLE_PROJECT);
    mockedApi.analyseProject.mockImplementation(
      () =>
        new Promise((resolve) => {
          resolveAnalysis = resolve;
        }),
    );
    mockedApi.generateClarificationQuestions.mockResolvedValue(SAMPLE_CLARIFICATIONS);

    render(<App />);

    await submitProjectDescription();

    expect(screen.getByText("Analyzing project...")).toBeInTheDocument();

    resolveAnalysis(SAMPLE_ANALYSIS_RESPONSE);
    await screen.findByText("How many network nodes will the firewall protect?");
  });

  it("displays API errors and allows restart", async () => {
    mockedApi.createProject.mockResolvedValue(SAMPLE_PROJECT);
    mockedApi.analyseProject.mockRejectedValue(
      new Error("The project is not in a valid state for this operation."),
    );

    render(<App />);

    await submitProjectDescription();

    await screen.findByRole("alert");
    expect(
      screen.getByText("The project is not in a valid state for this operation."),
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Try Again" })).toBeInTheDocument();
  });

  it("shows the composer-first welcome state", async () => {
    render(<App />);
    expect(screen.getByRole("heading", { name: "CyberSRS" })).toBeInTheDocument();
    expect(await screen.findByLabelText("Message input")).toBeInTheDocument();
  });
});
