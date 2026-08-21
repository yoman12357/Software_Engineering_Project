import { afterEach, describe, expect, it, vi } from "vitest";
import { api } from "./client";

describe("chat API recovery", () => {
  afterEach(() => {
    vi.useRealTimers();
    vi.unstubAllGlobals();
  });

  it("retries transient backend connection failures", async () => {
    vi.useFakeTimers();
    const fetchMock = vi
      .fn<typeof fetch>()
      .mockRejectedValueOnce(new TypeError("connection refused"))
      .mockRejectedValueOnce(new TypeError("server restarting"))
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            intent: "general_question",
            confidence: 0.8,
            extracted_data: {},
          }),
          { status: 200, headers: { "Content-Type": "application/json" } },
        ),
      );
    vi.stubGlobal("fetch", fetchMock);

    const pending = api.classifyIntent("hello");
    await vi.runAllTimersAsync();

    await expect(pending).resolves.toMatchObject({ intent: "general_question" });
    expect(fetchMock).toHaveBeenCalledTimes(3);
  });
});

describe("runtime readiness API", () => {
  afterEach(() => vi.unstubAllGlobals());

  it("loads backend health and allow-listed model configuration", async () => {
    const fetchMock = vi
      .fn<typeof fetch>()
      .mockResolvedValueOnce(new Response(
        JSON.stringify({ status: "ok", service: "cybersrs-api", database_ok: true }),
        { status: 200, headers: { "Content-Type": "application/json" } },
      ))
      .mockResolvedValueOnce(new Response(
        JSON.stringify({
          active_model_variant: "base",
          active_model_name: "qwen3:4b",
          provider: "ollama",
          rag_enabled: true,
          embedding_model: "nomic-embed-text",
          knowledge_base_version: "local",
        }),
        { status: 200, headers: { "Content-Type": "application/json" } },
      ));
    vi.stubGlobal("fetch", fetchMock);

    await expect(api.getHealth()).resolves.toMatchObject({ status: "ok" });
    await expect(api.getModelInfo()).resolves.toMatchObject({ provider: "ollama" });
    expect(fetchMock.mock.calls.map(([url]) => url)).toEqual([
      "/api/v1/health",
      "/api/v1/system/model-info",
    ]);
  });
});

describe("SRS generation stream failures", () => {
  afterEach(() => vi.unstubAllGlobals());

  it("rejects immediately when the backend emits a terminal failure event", async () => {
    const event = {
      phase: "failed",
      progress: 100,
      message: "The model output was incomplete. Please retry.",
      result: null,
      error_code: "invalid_generated_output",
    };
    vi.stubGlobal("fetch", vi.fn<typeof fetch>().mockResolvedValue(
      new Response(`data: ${JSON.stringify(event)}\n\n`, {
        status: 200,
        headers: { "Content-Type": "text/event-stream" },
      }),
    ));

    await expect(api.generateSrsStream("project-1", vi.fn())).rejects.toMatchObject({
      code: "invalid_generated_output",
      message: "The model output was incomplete. Please retry.",
    });
  });
});
