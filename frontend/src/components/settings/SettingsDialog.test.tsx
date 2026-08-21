import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { api } from "../../api/client";
import { SettingsDialog } from "./SettingsDialog";

vi.mock("../../api/client", () => ({
  api: {
    getHealth: vi.fn(),
    getModelInfo: vi.fn(),
  },
}));

const mockedApi = vi.mocked(api);

describe("SettingsDialog runtime readiness", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockedApi.getHealth.mockResolvedValue({
      status: "ok",
      service: "cybersrs-api",
      database_ok: true,
    });
    mockedApi.getModelInfo.mockResolvedValue({
      active_model_variant: "base",
      active_model_name: "qwen3:4b",
      provider: "ollama",
      rag_enabled: true,
      embedding_model: "nomic-embed-text",
      knowledge_base_version: "local",
    });
  });

  it("shows live backend and configured model information", async () => {
    render(<SettingsDialog open onClose={vi.fn()} />);

    expect(await screen.findByText("Backend ready")).toBeInTheDocument();
    expect(screen.getByText("Configured: qwen3:4b")).toBeInTheDocument();
    expect(screen.getByText("RAG enabled")).toBeInTheDocument();
    expect(screen.queryByText("1,247 Documents")).not.toBeInTheDocument();
  });
});
