import { beforeEach, describe, expect, it } from "vitest";
import { useChatStore } from "./chatStore";

describe("chat error messages", () => {
  beforeEach(() => {
    useChatStore.getState().reset();
  });

  it("does not append the same consecutive error twice", () => {
    const error = {
      role: "assistant" as const,
      content: "The backend is temporarily unavailable.",
      type: "error" as const,
    };

    useChatStore.getState().addMessage(error);
    useChatStore.getState().addMessage(error);

    expect(useChatStore.getState().messages).toHaveLength(1);
  });
});
