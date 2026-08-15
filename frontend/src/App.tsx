import { useCallback, useEffect, useState } from "react";
import { AppShell } from "./components/layout/AppShell";
import { WelcomeEmptyState } from "./components/chat/WelcomeEmptyState";
import { ChatThread } from "./components/chat/ChatThread";
import { Composer } from "./components/chat/Composer";
import { GenerationStatus } from "./components/chat/GenerationStatus";
import { SRSWorkspace } from "./components/srs/SRSWorkspace";
import { useChat } from "./hooks/useChat";
import { useProjects } from "./hooks/useProjects";
import { SettingsDialog } from "./components/settings/SettingsDialog";

const normalizeHash = () => window.location.hash.slice(1).replace(/^\/+/, "");

const createProjectName = (description: string) => {
  const words = description
    .trim()
    .replace(/\s+/g, " ")
    .split(" ")
    .filter(Boolean)
    .slice(0, 8);

  const name = words.join(" ");
  if (!name) return "Cybersecurity Project";
  return name.length > 64 ? `${name.slice(0, 61)}...` : name;
};

export default function App() {
  const {
    stage,
    projectId,
    messages,
    srs,
    srsVersionId,
    isLoading,
    error,
    handleCreateProject,
    submitClarificationAnswers,
    loadExistingProject,
    setStage,
    reset,
  } = useChat();

  const { projects, fetchProjects, setCurrentProject } = useProjects();
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [showSRSWorkspace, setShowSRSWorkspace] = useState(false);
  const [composerDraft, setComposerDraft] = useState("");

  // Load projects on mount
  useEffect(() => {
    fetchProjects();
  }, [fetchProjects]);

  // Handle project selection from URL hash
  useEffect(() => {
    const hash = normalizeHash();
    if (hash === "new") {
      reset();
      setStage("welcome");
      setShowSRSWorkspace(false);
      setSettingsOpen(false);
    } else if (hash && hash !== "new" && hash !== "settings") {
      if (hash.startsWith("srs/")) {
        setShowSRSWorkspace(true);
        setSettingsOpen(false);
      } else {
        const project = projects.find((p) => p.id === hash);
        if (project) {
          setCurrentProject(project.id);
          setShowSRSWorkspace(false);
          loadExistingProject(project.id);
        }
      }
    } else if (hash === "settings") {
      setSettingsOpen(true);
    }
  }, [projects, loadExistingProject, setCurrentProject, reset, setStage]);

  const handleHashChange = useCallback(() => {
    const hash = normalizeHash();
    if (hash === "settings") {
      setSettingsOpen(true);
    } else if (hash === "new") {
      setSettingsOpen(false);
      setShowSRSWorkspace(false);
      reset();
      setStage("welcome");
    } else if (hash.startsWith("srs/")) {
      setSettingsOpen(false);
      setShowSRSWorkspace(true);
    } else if (hash && hash !== "new" && hash !== "settings") {
      setSettingsOpen(false);
      setShowSRSWorkspace(false);
    }
  }, [reset, setStage]);

  useEffect(() => {
    window.addEventListener("hashchange", handleHashChange);
    return () => window.removeEventListener("hashchange", handleHashChange);
  }, [handleHashChange]);

  // Welcome screen - new project
  if (stage === "welcome" && !projectId) {
    return (
      <AppShell>
        <div className="flex h-full min-h-[calc(100vh-8rem)] flex-col">
          <WelcomeEmptyState
            onPromptClick={(prompt) => {
              setComposerDraft(prompt);
            }}
          />
          <Composer
            value={composerDraft}
            onValueChange={setComposerDraft}
            disabled={isLoading}
            onSend={async (content) => {
              setComposerDraft("");
              await handleCreateProject(createProjectName(content), content);
            }}
            placeholder="Describe your cybersecurity project..."
          />
        </div>
        <SettingsDialog
          open={settingsOpen}
          onClose={() => {
            setSettingsOpen(false);
            window.location.hash = "new";
          }}
        />
      </AppShell>
    );
  }

  // Settings dialog
  if (settingsOpen) {
    return (
      <AppShell>
        <SettingsDialog
          open={settingsOpen}
          onClose={() => {
            setSettingsOpen(false);
            window.location.hash = projectId ? projectId : "new";
          }}
        />
      </AppShell>
    );
  }

  // SRS Workspace view
  if (showSRSWorkspace && projectId && srs && srsVersionId) {
    return (
      <AppShell>
        <SRSWorkspace projectId={projectId} srs={srs} versionId={srsVersionId} />
        <SettingsDialog
          open={settingsOpen}
          onClose={() => {
            setSettingsOpen(false);
            window.location.hash = `srs/${srsVersionId}`;
          }}
        />
      </AppShell>
    );
  }

  return (
    <AppShell>
      <div className="flex h-full flex-col">
        {/* Stage-specific loading/error content above chat */}
        {stage === "analyzing" && (
          <div className="mb-4 rounded-xl border border-primary/20 bg-primary/5 p-4">
            <p className="font-medium">Analyzing project...</p>
            <p className="mt-1 text-sm text-muted-foreground">Qwen is extracting stakeholders, assets, constraints, goals, and missing information.</p>
          </div>
        )}

        {stage === "generating" && (
          <div className="mb-4">
            <GenerationStatus />
          </div>
        )}

        {stage === "error" && error && (
          <div className="mb-4" role="alert">
            <div className="flex items-center gap-3 p-4 rounded-lg bg-destructive/10 border border-destructive/20">
              <span className="flex-shrink-0 text-destructive">
                <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0z" />
                </svg>
              </span>
              <p className="text-destructive">{error}</p>
              <button
                className="ml-auto px-3 py-1.5 text-sm font-medium rounded-lg border border-destructive text-destructive hover:bg-destructive/10 transition-colors"
                onClick={() => { reset(); setStage("welcome"); }}
              >
                Try Again
              </button>
            </div>
          </div>
        )}

        {/* Chat Thread */}
        <ChatThread
          messages={messages}
          onSubmitClarifications={submitClarificationAnswers}
          onOpenSRS={() => {
            if (!srsVersionId) return;
            setShowSRSWorkspace(true);
            window.location.hash = `srs/${srsVersionId}`;
          }}
        />

        {/* Composer */}
        <Composer
          disabled={isLoading || stage === "analyzing" || stage === "generating"}
          onSend={async (content) => {
            if (!projectId) {
              await handleCreateProject(createProjectName(content), content);
            }
          }}
          placeholder={
            stage === "clarifying"
              ? "Answer the clarification question..."
              : "Describe your cybersecurity project..."
          }
        />
        <SettingsDialog
          open={settingsOpen}
          onClose={() => {
            setSettingsOpen(false);
            window.location.hash = projectId ? projectId : "new";
          }}
        />
      </div>
    </AppShell>
  );
}
