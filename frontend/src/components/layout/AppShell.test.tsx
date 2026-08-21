import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { firestoreService, type StoredChatSession } from "../../services/firestore";
import { useProjectStore } from "../../stores/projectStore";
import { AppShell, DashboardView } from "./AppShell";

const storedSession: StoredChatSession = {
  id: "chat-actions",
  projectId: null,
  name: "Important conversation",
  messages: [],
  stage: "welcome",
  analysis: null,
  clarificationQuestions: null,
  srs: null,
  srsVersionId: null,
  createdAt: "2026-08-21T01:00:00.000Z",
  updatedAt: "2026-08-21T01:00:00.000Z",
};

async function renderChatSession() {
  await firestoreService.saveChatSession(storedSession);
  await useProjectStore.getState().fetchChatSessions();
  render(<AppShell><div>Chat content</div></AppShell>);
}

describe("AppShell chat actions", () => {
  beforeEach(() => {
    localStorage.clear();
    useProjectStore.setState({
      chatSessions: [],
      currentSessionId: null,
      error: null,
    });
  });

  it("pins a chat into the pinned group", async () => {
    const user = userEvent.setup();
    await renderChatSession();

    await user.click(screen.getByRole("button", { name: "Open actions for Important conversation" }));
    await user.click(screen.getByRole("menuitem", { name: "Pin chat" }));

    expect(await screen.findByText("Pinned")).toBeInTheDocument();
    expect(useProjectStore.getState().chatSessions[0].pinnedAt).toBeTruthy();
  });

  it("confirms deletion and removes the chat without reloading", async () => {
    const user = userEvent.setup();
    await renderChatSession();

    await user.click(screen.getByRole("button", { name: "Open actions for Important conversation" }));
    await user.click(screen.getByRole("menuitem", { name: "Delete" }));
    await user.click(screen.getByRole("button", { name: "Delete" }));

    await waitFor(() => {
      expect(screen.queryByText("Important conversation")).not.toBeInTheDocument();
    });
    await expect(firestoreService.getChatSession("chat-actions")).resolves.toBeNull();
  });

  it("responds to global search and sidebar shortcut events", async () => {
    render(<AppShell><div>Chat content</div></AppShell>);
    const search = screen.getByPlaceholderText("Search chats...");

    fireEvent(window, new Event("cybersrs:focus-search"));
    await waitFor(() => expect(search).toHaveFocus());

    fireEvent(window, new Event("cybersrs:toggle-sidebar"));
    expect(screen.queryByPlaceholderText("Search chats...")).not.toBeInTheDocument();
  });
});

describe("Dashboard project actions", () => {
  it("requires confirmation before deleting a project", async () => {
    const user = userEvent.setup();
    const onDeleteProject = vi.fn().mockResolvedValue(undefined);
    render(
      <DashboardView
        projects={[{
          id: "project-1",
          name: "Old project",
          status: "draft",
          created_at: "2026-08-21T01:00:00.000Z",
        }]}
        chatSessions={[]}
        onSelectProject={vi.fn()}
        onDeleteProject={onDeleteProject}
        onNewChat={vi.fn()}
        onTourOpen={vi.fn()}
      />,
    );

    await user.click(screen.getByRole("button", { name: "Delete project Old project" }));
    expect(screen.getByText("Delete project?")).toBeInTheDocument();
    expect(onDeleteProject).not.toHaveBeenCalled();

    await user.click(screen.getByRole("button", { name: "Delete project" }));
    await waitFor(() => expect(onDeleteProject).toHaveBeenCalledWith("project-1"));
  });
});
