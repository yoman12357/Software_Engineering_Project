import { useCallback, useEffect, useState } from "react";
import { AppShell, DashboardView } from "./components/layout/AppShell";
import { WelcomeEmptyState } from "./components/chat/WelcomeEmptyState";
import { ChatThread } from "./components/chat/ChatThread";
import { Composer } from "./components/chat/Composer";
import { GenerationStatus } from "./components/chat/GenerationStatus";
import { SRSWorkspace } from "./components/srs/SRSWorkspace";
import { SRSEditor } from "./components/srs/SRSEditor";
import { useChat } from "./hooks/useChat";
import { useProjects } from "./hooks/useProjects";
import { SettingsDialog } from "./components/settings/SettingsDialog";
import { useKeyboardShortcuts } from "./hooks/useKeyboardShortcuts";
import { Tour } from "./components/tour/Tour";
import { useChatStore, type ChatStage } from "./stores/chatStore";
import { buildSrsRoute, normalizeHash, parseHashRoute } from "./lib/routes";

function ChatView({
  messages,
  stage,
  projectId,
  srsVersionId,
  isLoading,
  error,
  canRetry,
  generationProgress,
  composerDraft,
  setComposerDraft,
  sendChatMessage,
  submitClarificationAnswers,
  setStage,
  reset,
  retryLastOperation,
  cancelGeneration,
  setShowSRSWorkspace,
  pendingFiles,
  attachFiles,
  removePendingFile,
}: {
  messages: import("./api/types").ChatMessage[];
  stage: ChatStage;
  projectId: string | null;
  srsVersionId: string | null;
  isLoading: boolean;
  error: string | null;
  canRetry: boolean;
  generationProgress: import("./api/types").SRSGenerationProgressEvent | null;
  composerDraft: string;
  setComposerDraft: (v: string) => void;
  sendChatMessage: (content: string) => Promise<void>;
  submitClarificationAnswers: (answers: import("./api/types").ClarificationAnswerItem[]) => Promise<void>;
  setStage: (stage: ChatStage) => void;
  reset: () => void;
  retryLastOperation: () => Promise<void>;
  cancelGeneration: () => void;
  setShowSRSWorkspace: (v: boolean) => void;
  pendingFiles: File[];
  attachFiles: (files: File[]) => void | Promise<void>;
  removePendingFile: (index: number) => void;
}) {
  const hasChat = messages.length > 0;

  return (
    <div className="flex h-full min-h-0 flex-col overflow-hidden">
      <div className="flex-1 min-h-0">
        {!hasChat && stage === "welcome" ? (
          <div className="mx-auto flex h-full w-full max-w-[768px] flex-col overflow-y-auto px-4 py-6">
            <WelcomeEmptyState onPromptClick={(prompt) => setComposerDraft(prompt)} />
            <Composer
              value={composerDraft}
              onValueChange={setComposerDraft}
              disabled={isLoading}
              attachments={pendingFiles}
              onFilesSelected={attachFiles}
              onRemoveAttachment={removePendingFile}
              onSend={async (content) => {
                setComposerDraft("");
                await sendChatMessage(content);
              }}
            />
          </div>
        ) : (
          <div className="mx-auto flex h-full min-h-0 w-full max-w-[768px] flex-col px-4">
            {stage === "analyzing" && (
              <div className="pt-4">
                <div className="flex items-center gap-3 p-4 rounded-xl bg-[#2f2f2f]">
                  <div className="h-4 w-4 animate-spin rounded-full border-2 border-[#19c37d] border-t-transparent" />
                  <div>
                    <p className="font-medium text-sm text-white">Analyzing project...</p>
                    <p className="text-xs text-[#8e8e8e]">Extracting stakeholders, assets, constraints, and goals.</p>
                  </div>
                </div>
              </div>
            )}

            {stage === "generating" && (
              <div className="pt-4">
                <GenerationStatus progress={generationProgress} onCancel={cancelGeneration} />
              </div>
            )}

            {stage === "error" && error && (
              <div className="pt-4" role="alert">
                <div className="flex items-center gap-3 p-4 rounded-xl bg-[#2f2f2f] border border-red-500/20">
                  <p className="text-sm text-red-400">{error}</p>
                  <button
                    className="ml-auto px-3 py-1.5 text-sm font-medium rounded-lg border border-red-500/30 text-red-400 hover:bg-red-500/10 transition-colors"
                    onClick={() => {
                      if (canRetry) {
                        void retryLastOperation();
                      } else {
                        reset();
                        setStage("welcome");
                      }
                    }}
                  >
                    {canRetry ? "Retry" : "Start Over"}
                  </button>
                </div>
              </div>
            )}

            <ChatThread
              messages={messages}
              isLoading={isLoading}
              onSubmitClarifications={submitClarificationAnswers}
              onOpenSRS={() => {
                if (!projectId || !srsVersionId) return;
                setShowSRSWorkspace(true);
                window.location.hash = buildSrsRoute(projectId, srsVersionId);
              }}
            />

            <Composer
              disabled={isLoading || stage === "analyzing" || stage === "generating"}
              attachments={pendingFiles}
              onFilesSelected={attachFiles}
              onRemoveAttachment={removePendingFile}
              onSend={sendChatMessage}
              placeholder={
                stage === "clarifying"
                  ? "Answer the clarification question..."
                  : "Message CyberSRS..."
              }
            />
          </div>
        )}
      </div>
    </div>
  );
}

export default function App() {
  const {
    stage,
    projectId,
    sessionId,
    messages,
    srs,
    srsVersionId,
    isLoading,
    error,
    canRetry,
    generationProgress,
    sendChatMessage,
    submitClarificationAnswers,
    loadChatSession,
    loadExistingProject,
    loadSrsVersion,
    cancelPendingNavigation,
    retryLastOperation,
    cancelGeneration,
    createNewChatSession,
    setStage,
    reset,
    pendingFiles,
    attachFiles,
    removePendingFile,
  } = useChat();

  const {
    projects,
    fetchProjects,
    setCurrentProject,
    setCurrentSession,
    fetchChatSessions,
    chatSessions,
    deleteProject,
    deleteChatSession,
  } = useProjects();
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [showSRSWorkspace, setShowSRSWorkspace] = useState(false);
  const [showSRSEditor, setShowSRSEditor] = useState(false);
  const [tourOpen, setTourOpen] = useState(false);
  const [composerDraft, setComposerDraft] = useState("");
  const [routeHash, setRouteHash] = useState(() => normalizeHash());

  useEffect(() => {
    fetchProjects();
    fetchChatSessions();
  }, [fetchProjects, fetchChatSessions]);

  const syncFromHash = useCallback(() => {
    const hash = normalizeHash();
    const route = parseHashRoute(hash);
    setRouteHash(hash);

    if (route.kind !== "srs" && route.kind !== "legacy-srs") {
      cancelPendingNavigation();
    }

    if (route.kind === "settings") {
      setSettingsOpen(true);
      return;
    }

    if (route.kind === "dashboard") {
      setSettingsOpen(false);
      setShowSRSWorkspace(false);
      setShowSRSEditor(false);
      return;
    }

    setSettingsOpen(false);

    if (route.kind === "new-chat") {
      setShowSRSWorkspace(false);
      setShowSRSEditor(false);
      setCurrentProject(null);
      setCurrentSession(null);
      reset();
      setStage("welcome");
      createNewChatSession();
      return;
    }

    if (route.kind === "srs") {
      setShowSRSEditor(route.edit);
      setShowSRSWorkspace(!route.edit);
      void loadSrsVersion(route.projectId, route.versionId);
      return;
    }

    if (route.kind === "legacy-srs") {
      const currentProjectId = useChatStore.getState().projectId;
      if (currentProjectId) {
        window.location.hash = buildSrsRoute(currentProjectId, route.versionId, route.edit);
      } else {
        setShowSRSEditor(route.edit);
        setShowSRSWorkspace(!route.edit);
      }
      return;
    }

    if (route.kind === "chat") {
      setCurrentSession(route.sessionId);
      setShowSRSWorkspace(false);
      setShowSRSEditor(false);
      void loadChatSession(route.sessionId);
      return;
    }

    if (route.kind === "project") {
      setShowSRSWorkspace(false);
      setShowSRSEditor(false);
      void loadExistingProject(route.projectId);
      return;
    }

    setShowSRSWorkspace(false);
    setShowSRSEditor(false);
  }, [
    createNewChatSession,
    cancelPendingNavigation,
    loadChatSession,
    loadExistingProject,
    loadSrsVersion,
    reset,
    setCurrentProject,
    setCurrentSession,
    setStage,
  ]);

  useEffect(() => {
    syncFromHash();
    window.addEventListener("hashchange", syncFromHash);
    return () => window.removeEventListener("hashchange", syncFromHash);
  }, [syncFromHash]);

  const startNewChat = useCallback(() => {
    if (parseHashRoute().kind === "new-chat") {
      setRouteHash("new");
      setSettingsOpen(false);
      setShowSRSWorkspace(false);
      setShowSRSEditor(false);
      setCurrentProject(null);
      setCurrentSession(null);
      reset();
      setStage("welcome");
      createNewChatSession();
      return;
    }

    window.location.hash = "new";
  }, [
    createNewChatSession,
    reset,
    setCurrentProject,
    setCurrentSession,
    setStage,
  ]);

  const handleDeleteChat = useCallback(async (targetSessionId: string) => {
    const deletingActiveChat =
      sessionId === targetSessionId || normalizeHash() === `chat/${targetSessionId}`;

    if (deletingActiveChat) {
      // Clear the active store before deleting so an in-flight request cannot
      // save the removed session back into local persistence.
      reset();
      setCurrentProject(null);
      setCurrentSession(null);
    }

    await deleteChatSession(targetSessionId);

    if (deletingActiveChat) startNewChat();
  }, [deleteChatSession, reset, sessionId, setCurrentProject, setCurrentSession, startNewChat]);

  const handleDeleteProject = useCallback(async (targetProjectId: string) => {
    await deleteProject(targetProjectId);
    if (projectId === targetProjectId) {
      reset();
      setCurrentProject(null);
      setCurrentSession(null);
    }
  }, [deleteProject, projectId, reset, setCurrentProject, setCurrentSession]);

  useKeyboardShortcuts({
    onNewChat: startNewChat,
    onSearch: () => window.dispatchEvent(new Event("cybersrs:focus-search")),
    onExport: () => {
      document.querySelector<HTMLButtonElement>('[data-action="export-pdf"]')?.click();
    },
    onEscape: () => {
      if (settingsOpen) {
        setSettingsOpen(false);
      } else if (stage === "error") {
        reset();
        setStage("welcome");
      } else if (showSRSWorkspace) {
        setShowSRSWorkspace(false);
        window.location.hash = projectId ? projectId : "new";
      } else if (showSRSEditor) {
        setShowSRSEditor(false);
        window.location.hash = projectId && srsVersionId
          ? buildSrsRoute(projectId, srsVersionId)
          : "new";
      }
    },
    onRegenerate: () => {
      document.querySelector<HTMLButtonElement>('[data-action="regenerate-section"]')?.click();
    },
    onToggleSidebar: () => window.dispatchEvent(new Event("cybersrs:toggle-sidebar")),
  });

  const parsedRoute = parseHashRoute(routeHash);
  const routeIsSrs = parsedRoute.kind === "srs" || parsedRoute.kind === "legacy-srs";
  const activeView =
    showSRSEditor || (routeIsSrs && parsedRoute.edit)
      ? "editor"
      : showSRSWorkspace || routeIsSrs
      ? "srs"
      : parsedRoute.kind === "root" || parsedRoute.kind === "new-chat" || parsedRoute.kind === "chat"
      ? "chat"
      : parsedRoute.kind === "settings"
      ? "chat"
      : parsedRoute.kind === "dashboard"
      ? "dashboard"
      : parsedRoute.kind === "project"
      ? "chat"
      : "dashboard";

  return (
    <>
      <AppShell
        activeView={activeView}
        onNewChat={startNewChat}
        onDeleteChat={handleDeleteChat}
      >
        {activeView === "srs" && projectId && srsVersionId && srs && (
          <SRSWorkspace projectId={projectId} srs={srs} versionId={srsVersionId} />
        )}
        {activeView === "editor" && projectId && srsVersionId && srs && (
          <SRSEditor
            projectId={projectId}
            versionId={srsVersionId}
            srs={srs}
            onSaved={(updated) => {
              if (updated.srs) useChatStore.getState().setSRS(updated.srs, updated.id);
            }}
            onBack={() => {
              setShowSRSEditor(false);
              setShowSRSWorkspace(true);
              window.location.hash = buildSrsRoute(projectId, srsVersionId);
            }}
          />
        )}
        {(activeView === "srs" || activeView === "editor") && isLoading && !srs && (
          <div className="flex h-full items-center justify-center" role="status">
            <div className="flex items-center gap-3 rounded-xl border border-border bg-card p-4 text-sm text-muted-foreground">
              <div className="h-4 w-4 animate-spin rounded-full border-2 border-primary border-t-transparent" />
              Loading SRS version...
            </div>
          </div>
        )}
        {(activeView === "srs" || activeView === "editor") && !isLoading && error && !srs && (
          <div className="flex h-full items-center justify-center px-4" role="alert">
            <div className="max-w-lg rounded-xl border border-red-500/20 bg-card p-5 text-sm text-red-400">
              <p>{error}</p>
              {canRetry && (
                <button
                  className="mt-4 rounded-lg border border-red-500/30 px-3 py-1.5 font-medium hover:bg-red-500/10"
                  onClick={() => void retryLastOperation()}
                >
                  Retry loading
                </button>
              )}
            </div>
          </div>
        )}
        {activeView === "chat" && (
          <ChatView
            messages={messages}
            stage={stage}
            projectId={projectId}
            srsVersionId={srsVersionId}
            isLoading={isLoading}
            error={error}
            canRetry={canRetry}
            generationProgress={generationProgress}
            composerDraft={composerDraft}
            setComposerDraft={setComposerDraft}
            sendChatMessage={sendChatMessage}
            submitClarificationAnswers={submitClarificationAnswers}
            setStage={setStage}
            reset={reset}
            retryLastOperation={retryLastOperation}
            cancelGeneration={cancelGeneration}
            setShowSRSWorkspace={setShowSRSWorkspace}
            pendingFiles={pendingFiles}
            attachFiles={attachFiles}
            removePendingFile={removePendingFile}
          />
        )}
        {activeView === "dashboard" && (
          <DashboardView
            projects={projects}
            chatSessions={chatSessions}
            onSelectProject={(id) => {
              setCurrentProject(id);
              window.location.hash = id;
            }}
            onDeleteProject={handleDeleteProject}
            onNewChat={startNewChat}
            onTourOpen={() => setTourOpen(true)}
          />
        )}
      </AppShell>
      <SettingsDialog
        open={settingsOpen}
        onClose={() => {
          setSettingsOpen(false);
          window.location.hash = sessionId ? `chat/${sessionId}` : projectId ?? "new";
        }}
      />
      <Tour isOpen={tourOpen} onClose={() => setTourOpen(false)} onComplete={() => {}} />
    </>
  );
}
