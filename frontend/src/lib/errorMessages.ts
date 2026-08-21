import { ApiRequestError } from "../api/types";

const OLLAMA_HINTS =
  "Ensure Ollama is running (`ollama serve`) and the model is pulled (`ollama list`).";

const CODE_HINTS: Record<string, string> = {
  network_error: (
    "The backend is temporarily unavailable and may be restarting. " +
    "Wait a moment and try again; if it persists, make sure uvicorn is running on port 8000."
  ),
  llm_timeout: `The model took too long to respond. ${OLLAMA_HINTS}`,
  llm_output_error: `The model returned invalid output. ${OLLAMA_HINTS}`,
  srs_generation_error: "SRS generation failed. Check the backend logs for details.",
  analysis_error: "Project analysis failed. Check that the model is available.",
  clarification_generation_error: "Clarification generation failed. Check that the model is available.",
};

const MESSAGE_HINTS: Array<{ pattern: RegExp; hint: string }> = [
  { pattern: /connect/i, hint: "Could not connect to Ollama. Start it with `ollama serve`." },
  { pattern: /model .* not found|not found/i, hint: "The model is not installed. Run `ollama pull qwen3:4b-instruct-2507-q4_K_M`." },
  { pattern: /timeout|timed out/i, hint: "The request timed out. The model may still be loading; try again." },
  { pattern: /context length|context window/i, hint: "Context length exceeded. Increase CYBERSRS_OLLAMA_NUM_CTX in your .env file." },
  { pattern: /empty response/i, hint: "Ollama returned an empty response. Try regenerating." },
];

export function friendlyErrorMessage(error: unknown): string {
  if (!(error instanceof Error)) return "An unexpected error occurred.";

  if (error instanceof ApiRequestError) {
    const hint = CODE_HINTS[error.code];
    if (hint) return hint;
    return error.message || "Request failed.";
  }

  const message = error.message;
  for (const { pattern, hint } of MESSAGE_HINTS) {
    if (pattern.test(message)) return hint;
  }
  return message;
}
