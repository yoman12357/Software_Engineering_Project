"use client";

import { useCallback, useEffect, useState } from "react";
import { createPortal } from "react-dom";
import { X, Sun, Moon, Monitor, Shield, Database, Zap, FileText, Settings as SettingsIcon } from "lucide-react";
import { cn } from "../../lib/utils";
import { Button } from "../../components/ui/Button";
import { Badge } from "../../components/ui/Badge";
import { ScrollArea } from "../../components/ui/ScrollArea";
import { ThemeToggle } from "../../components/ui/ThemeToggle";
import { useThemeStore } from "../../stores/themeStore";
import { api } from "../../api/client";
import type { HealthResponse, ModelInfoResponse } from "../../api/types";

interface SettingsDialogProps {
  open: boolean;
  onClose: () => void;
}

export function SettingsDialog({ open, onClose }: SettingsDialogProps) {
  const [activeTab, setActiveTab] = useState("general");
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [modelInfo, setModelInfo] = useState<ModelInfoResponse | null>(null);
  const [runtimeLoading, setRuntimeLoading] = useState(false);
  const [runtimeError, setRuntimeError] = useState<string | null>(null);

  const loadRuntimeStatus = useCallback(async () => {
    setRuntimeLoading(true);
    setRuntimeError(null);
    const [healthResult, modelResult] = await Promise.allSettled([
      api.getHealth(),
      api.getModelInfo(),
    ]);
    setHealth(healthResult.status === "fulfilled" ? healthResult.value : null);
    setModelInfo(modelResult.status === "fulfilled" ? modelResult.value : null);
    if (healthResult.status === "rejected" || modelResult.status === "rejected") {
      setRuntimeError("Some runtime information could not be loaded. Check that the backend is running.");
    }
    setRuntimeLoading(false);
  }, []);

  useEffect(() => {
    if (open) void loadRuntimeStatus();
  }, [loadRuntimeStatus, open]);

  if (!open) return null;

  const tabs = [
    { id: "general", label: "General", icon: SettingsIcon },
    { id: "appearance", label: "Appearance", icon: Sun },
    { id: "about", label: "About", icon: FileText },
  ];

  return createPortal(
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4" onClick={onClose} role="dialog" aria-modal="true" aria-labelledby="settings-title">
      <div className="fixed inset-0 bg-black/50 backdrop-blur-sm animate-in fade-in" aria-hidden="true" onClick={onClose} />
      <div className="relative z-50 w-full max-w-2xl max-h-[85vh] bg-card rounded-xl border border-border shadow-elevated animate-in slide-in-right overflow-hidden flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-border">
          <h2 id="settings-title" className="text-lg font-semibold">Settings</h2>
          <Button variant="ghost" size="icon" onClick={onClose} className="h-8 w-8">
            <X className="h-4 w-4" />
          </Button>
        </div>

        {/* Tabs */}
        <div className="border-b border-border">
          <nav className="flex gap-1 p-1" role="tablist">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                role="tab"
                aria-selected={activeTab === tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={cn(
                  "flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors",
                  "hover:bg-muted",
                  activeTab === tab.id
                    ? "bg-primary/10 text-primary"
                    : "text-muted-foreground"
                )}
              >
                <tab.icon className="h-4 w-4" />
                {tab.label}
              </button>
            ))}
          </nav>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-hidden">
          <ScrollArea className="h-full p-4 space-y-6">
            {activeTab === "general" && (
              <GeneralSettings
                health={health}
                modelInfo={modelInfo}
                loading={runtimeLoading}
                error={runtimeError}
                onRetry={loadRuntimeStatus}
              />
            )}
            {activeTab === "appearance" && <AppearanceSettings />}
            {activeTab === "about" && <AboutSettings />}
          </ScrollArea>
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-border flex justify-end">
          <Button variant="primary" onClick={onClose}>Close</Button>
        </div>
      </div>
    </div>,
    document.body
  );
}

function GeneralSettings({
  health,
  modelInfo,
  loading,
  error,
  onRetry,
}: {
  health: HealthResponse | null;
  modelInfo: ModelInfoResponse | null;
  loading: boolean;
  error: string | null;
  onRetry: () => Promise<void>;
}) {
  const backendReady = health?.status === "ok" && health.database_ok;

  return (
    <div className="space-y-6">
      {error && (
        <div className="flex items-center gap-3 rounded-lg border border-yellow-500/30 bg-yellow-500/10 p-3 text-sm text-yellow-200" role="alert">
          <span>{error}</span>
          <Button className="ml-auto" variant="outline" size="sm" onClick={() => void onRetry()} disabled={loading}>
            Retry
          </Button>
        </div>
      )}
      <div>
        <h3 className="font-medium mb-3">AI Runtime</h3>
        <div className="p-4 rounded-lg bg-muted/50 border border-border space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-primary/10 text-primary">
                <Zap className="h-5 w-5" />
              </div>
              <div>
                <p className="font-medium">{modelInfo?.provider ?? "Local model provider"}</p>
                <p className="text-sm text-muted-foreground">
                  {loading
                    ? "Checking configured model..."
                    : modelInfo
                    ? `Configured: ${modelInfo.active_model_name}`
                    : "Model configuration unavailable"}
                </p>
              </div>
            </div>
            <Badge variant={backendReady ? "success" : "outline"} className="gap-1">
              <Shield className="h-3 w-3" />
              {loading ? "Checking" : backendReady ? "Backend ready" : "Backend unavailable"}
            </Badge>
          </div>
          <div className="text-sm text-muted-foreground">
            All AI processing happens locally on your machine. No data leaves your device.
          </div>
        </div>
      </div>

      <div>
        <h3 className="font-medium mb-3">Knowledge Base</h3>
        <div className="p-4 rounded-lg bg-muted/50 border border-border space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-primary/10 text-primary">
                <Database className="h-5 w-5" />
              </div>
              <div>
                <p className="font-medium">Local knowledge base</p>
                <p className="text-sm text-muted-foreground">
                  {modelInfo
                    ? `Version ${modelInfo.knowledge_base_version} · Embeddings: ${modelInfo.embedding_model ?? "not configured"}`
                    : "Knowledge-base configuration unavailable"}
                </p>
              </div>
            </div>
            <Badge variant="outline" className="gap-1">
              <FileText className="h-3 w-3" />
              {modelInfo?.rag_enabled ? "RAG enabled" : "RAG disabled"}
            </Badge>
          </div>
          <div className="text-sm text-muted-foreground">
            RAG retrieval is enabled by default. Sources are cited in generated requirements.
          </div>
        </div>
      </div>

      <div>
        <h3 className="font-medium mb-3">Data & Privacy</h3>
        <div className="space-y-3">
          <div className="p-4 rounded-lg bg-muted/50 border border-border">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-success/10 text-success">
                <Shield className="h-5 w-5" />
              </div>
              <div>
                <p className="font-medium">Local-First Architecture</p>
                <p className="text-sm text-muted-foreground">All data stored in local SQLite database</p>
              </div>
            </div>
          </div>
          <div className="p-4 rounded-lg bg-muted/50 border border-border">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-success/10 text-success">
                <Shield className="h-5 w-5" />
              </div>
              <div>
                <p className="font-medium">No Telemetry</p>
                <p className="text-sm text-muted-foreground">No analytics, tracking, or external API calls</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function AppearanceSettings() {
  const { mode, setMode, resolvedTheme } = useThemeStore();

  return (
    <div className="space-y-6">
      <div>
        <h3 className="font-medium mb-3">Theme</h3>
        <div className="p-4 rounded-lg bg-muted/50 border border-border">
          <ThemeToggle />
        </div>
        <div className="mt-3 grid gap-2 sm:grid-cols-3">
          {(["light", "dark", "system"] as const).map((theme) => (
            <button
              key={theme}
              onClick={() => setMode(theme)}
              className={cn(
                "p-4 rounded-lg border text-left transition-all",
                mode === theme
                  ? "border-primary bg-primary/5"
                  : "border-border hover:border-primary/50"
              )}
            >
              <div className="flex items-center gap-3">
                {theme === "light" && <Sun className="h-5 w-5" />}
                {theme === "dark" && <Moon className="h-5 w-5" />}
                {theme === "system" && <Monitor className="h-5 w-5" />}
                <div>
                  <p className="font-medium capitalize">{theme}</p>
                  <p className="text-xs text-muted-foreground">
                    {theme === "system" ? `Follows system (${resolvedTheme})` : `Always ${theme}`}
                  </p>
                </div>
              </div>
            </button>
          ))}
        </div>
      </div>

      <div>
        <h3 className="font-medium mb-3">Display</h3>
        <div className="p-4 rounded-lg bg-muted/50 border border-border space-y-3">
          <label className="flex items-center gap-3 cursor-pointer">
            <input type="checkbox" className="h-4 w-4 rounded border-border text-primary focus:ring-primary" defaultChecked />
            <div>
              <p className="font-medium">Compact Mode</p>
              <p className="text-sm text-muted-foreground">Reduce spacing for more content</p>
            </div>
          </label>
          <label className="flex items-center gap-3 cursor-pointer">
            <input type="checkbox" className="h-4 w-4 rounded border-border text-primary focus:ring-primary" defaultChecked />
            <div>
              <p className="font-medium">Show Source Citations</p>
              <p className="text-sm text-muted-foreground">Display RAG source badges in requirements</p>
            </div>
          </label>
          <label className="flex items-center gap-3 cursor-pointer">
            <input type="checkbox" className="h-4 w-4 rounded border-border text-primary focus:ring-primary" />
            <div>
              <p className="font-medium">Animations</p>
              <p className="text-sm text-muted-foreground">Enable UI transitions and animations</p>
            </div>
          </label>
        </div>
      </div>
    </div>
  );
}

function AboutSettings() {
  return (
    <div className="space-y-6">
      <div className="text-center py-4">
        <div className="mx-auto p-4 rounded-xl bg-primary/10 text-primary">
          <Shield className="h-12 w-12" />
        </div>
        <h3 className="mt-4 text-xl font-semibold">CyberSRS</h3>
        <p className="text-sm text-muted-foreground mt-1">v0.1.0</p>
      </div>

      <div className="p-4 rounded-lg bg-muted/50 border border-border">
        <h4 className="font-medium mb-3">Description</h4>
        <p className="text-sm text-muted-foreground">
          CyberSRS is a locally deployable, AI-assisted platform that generates complete
          Software Requirements Specifications (SRS) for cybersecurity and network-infrastructure projects.
        </p>
      </div>

      <div>
        <h4 className="font-medium mb-3">Technology Stack</h4>
        <div className="grid gap-2 sm:grid-cols-2">
          {[
            { name: "Frontend", value: "React 18 + TypeScript + Vite" },
            { name: "Styling", value: "Tailwind CSS" },
            { name: "State", value: "Zustand" },
            { name: "Backend", value: "FastAPI + Python 3.11+" },
            { name: "LLM", value: "Qwen3-4B-Instruct (via Ollama)" },
            { name: "RAG", value: "ChromaDB + Embeddings" },
            { name: "Database", value: "SQLite" },
            { name: "Fine-tuning", value: "QLoRA + PEFT" },
          ].map((tech) => (
            <div key={tech.name} className="p-3 rounded-lg bg-card border border-border">
              <p className="text-xs text-muted-foreground uppercase tracking-wider">{tech.name}</p>
              <p className="font-medium text-sm">{tech.value}</p>
            </div>
          ))}
        </div>
      </div>

      <div className="p-4 rounded-lg bg-muted/50 border border-border">
        <h4 className="font-medium mb-3">Security</h4>
        <div className="space-y-2 text-sm">
          <div className="flex items-center gap-2 text-success">
            <Shield className="h-4 w-4" />
            <span>No external network calls</span>
          </div>
          <div className="flex items-center gap-2 text-success">
            <Shield className="h-4 w-4" />
            <span>All data stays local</span>
          </div>
          <div className="flex items-center gap-2 text-success">
            <Shield className="h-4 w-4" />
            <span>No telemetry or analytics</span>
          </div>
        </div>
      </div>

      <div className="text-center text-sm text-muted-foreground border-t border-border pt-4">
        <p>Built for cybersecurity requirements engineering</p>
        <p className="mt-1">University/Research software product</p>
      </div>
    </div>
  );
}

export default SettingsDialog;
