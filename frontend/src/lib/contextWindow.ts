/**
 * Context window management for LLM conversations.
 * Implements sliding window to keep conversation within token limits.
 */

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

export interface ContextWindowConfig {
  /** Maximum number of messages to keep in context (excluding system) */
  maxMessages: number;
  /** Always keep the first N messages (e.g., system prompt, initial context) */
  keepFirst: number;
  /** Always keep the last N messages (recent conversation) */
  keepLast: number;
}

/**
 * Default configuration for context window.
 * With num_ctx=8192 and ~4 chars/token, we have ~32k chars.
 * Roughly: system prompt (~1k) + 20 messages * ~500 chars = ~11k chars, well within limit.
 */
export const DEFAULT_CONTEXT_CONFIG: ContextWindowConfig = {
  maxMessages: 30,
  keepFirst: 2, // System prompt + first user message
  keepLast: 20, // Recent conversation
};

/**
 * Apply sliding window to chat history.
 * Keeps first N messages, last N messages, and drops middle if exceeding maxMessages.
 */
export function applySlidingWindow(
  messages: ChatMessage[],
  config: ContextWindowConfig = DEFAULT_CONTEXT_CONFIG
): ChatMessage[] {
  const { maxMessages, keepFirst, keepLast } = config;

  if (messages.length <= maxMessages) {
    return messages;
  }

  // Keep first N and last N messages
  const firstMessages = messages.slice(0, keepFirst);
  const lastMessages = messages.slice(-keepLast);

  // Combine, avoiding duplicates if ranges overlap
  const combined = [...firstMessages, ...lastMessages];

  // If still too many (due to overlap), just take last maxMessages
  if (combined.length > maxMessages) {
    return combined.slice(-maxMessages);
  }

  return combined;
}

/**
 * Estimate token count for a message array.
 * Rough approximation: 1 token ≈ 4 characters for English.
 */
export function estimateTokens(messages: ChatMessage[]): number {
  let totalChars = 0;
  for (const msg of messages) {
    totalChars += msg.content.length + msg.role.length + 10; // role + content + overhead
  }
  return Math.ceil(totalChars / 4);
}

/**
 * Check if messages fit within token budget.
 */
export function fitsInContext(
  messages: ChatMessage[],
  maxTokens: number = 8192
): boolean {
  return estimateTokens(messages) <= maxTokens;
}
