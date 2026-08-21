import { beforeEach, describe, expect, it, vi } from "vitest";
import { api } from "../api/client";
import {
  firestoreService,
  type StoredChatSession,
} from "../services/firestore";
import { useProjectStore } from "./projectStore";

function chatSession(id: string, updatedAt: string): StoredChatSession {
  return {
    id,
    projectId: null,
    name: `Chat ${id}`,
    messages: [],
    stage: "welcome",
    analysis: null,
    clarificationQuestions: null,
    srs: null,
    srsVersionId: null,
    pendingProjectDescription: null,
    createdAt: updatedAt,
    updatedAt,
  };
}

describe("chat session management", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    localStorage.clear();
    useProjectStore.setState({
      chatSessions: [],
      currentSessionId: null,
      error: null,
    });
  });

  it("deletes a chat from sidebar state and local persistence", async () => {
    await firestoreService.saveChatSession(chatSession("delete-me", "2026-08-21T01:00:00.000Z"));
    await useProjectStore.getState().fetchChatSessions();
    useProjectStore.getState().setCurrentSession("delete-me");

    const deletion = useProjectStore.getState().deleteChatSession("delete-me");

    expect(useProjectStore.getState().chatSessions).toHaveLength(0);
    expect(useProjectStore.getState().currentSessionId).toBeNull();
    await deletion;
    await expect(firestoreService.getChatSession("delete-me")).resolves.toBeNull();
  });

  it("persists pin state and keeps pinned chats above recent chats", async () => {
    await firestoreService.saveChatSession(chatSession("older", "2026-08-20T01:00:00.000Z"));
    await firestoreService.saveChatSession(chatSession("newer", "2026-08-21T01:00:00.000Z"));
    await useProjectStore.getState().fetchChatSessions();

    await useProjectStore.getState().setChatSessionPinned("older", true);

    expect(useProjectStore.getState().chatSessions.map((session) => session.id)).toEqual([
      "older",
      "newer",
    ]);
    expect((await firestoreService.getChatSession("older"))?.pinnedAt).toBeTruthy();

    await useProjectStore.getState().fetchChatSessions();
    expect(useProjectStore.getState().chatSessions[0]).toMatchObject({
      id: "older",
      pinnedAt: expect.any(String),
    });
  });

  it("preserves pin state when a chat is saved again", async () => {
    const session = chatSession("pinned", "2026-08-21T01:00:00.000Z");
    await firestoreService.saveChatSession(session);
    await firestoreService.updateChatSessionPinned("pinned", true);
    await firestoreService.saveChatSession({ ...session, name: "Updated chat" });

    expect((await firestoreService.getChatSession("pinned"))?.pinnedAt).toBeTruthy();
  });

  it("deletes a project and its associated local chats", async () => {
    vi.spyOn(api, "deleteProject").mockResolvedValue(undefined);
    const session = { ...chatSession("project-chat", "2026-08-21T01:00:00.000Z"), projectId: "project-1" };
    await firestoreService.saveChatSession(session);
    useProjectStore.setState({
      projects: [{
        id: "project-1",
        name: "Old project",
        description: "An old cybersecurity project.",
        status: "draft",
        inferred_categories: [],
        created_at: "2026-08-21T01:00:00.000Z",
        updated_at: "2026-08-21T01:00:00.000Z",
      }],
      chatSessions: [{
        id: session.id,
        projectId: session.projectId,
        name: session.name,
        lastMessage: "",
        updatedAt: session.updatedAt,
        messageCount: 0,
        stage: session.stage,
        pinnedAt: null,
      }],
      currentProjectId: "project-1",
      currentSessionId: session.id,
    });

    await useProjectStore.getState().deleteProject("project-1");

    expect(useProjectStore.getState()).toMatchObject({
      projects: [],
      chatSessions: [],
      currentProjectId: null,
      currentSessionId: null,
    });
    await expect(firestoreService.getChatSession(session.id)).resolves.toBeNull();
  });
});
