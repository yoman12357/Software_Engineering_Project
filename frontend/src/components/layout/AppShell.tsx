"use client";

import { useState, useEffect } from "react";
import { cn } from "../../lib/utils";
import {
  Plus,
  MessageSquare,
  Settings,
  Trash2,
  PanelLeftClose,
  PanelLeft,
  Search,
  Edit,
  LayoutDashboard,
  FileText,
  Clock,
  ChevronRight,
  HelpCircle,
  MoreHorizontal,
  Pin,
  PinOff,
} from "lucide-react";
import { useProjectStore } from "../../stores/projectStore";
import { Button } from "../../components/ui/Button";
import { Input } from "../../components/ui/Input";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "../../components/ui/Dialog";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "../../components/ui/DropdownMenu";

interface AppShellProps {
  children: React.ReactNode;
  activeView?: "chat" | "srs" | "editor" | "dashboard";
  onNewChat?: () => void;
  onDeleteChat?: (sessionId: string) => Promise<void>;
}

// ── DashboardView Component ────────────────────────────────────────────────

export function DashboardView({
  projects,
  chatSessions,
  onSelectProject,
  onDeleteProject,
  onNewChat,
  onTourOpen,
}: {
  projects: Array<{ id: string; name: string; status: string; created_at: string; updated_at?: string }>;
  chatSessions: Array<{ id: string; name: string; updatedAt: string; messageCount: number; stage: string }>;
  onSelectProject: (id: string) => void;
  onDeleteProject: (id: string) => Promise<void>;
  onNewChat: () => void;
  onTourOpen: () => void;
}) {
  const [projectToDelete, setProjectToDelete] = useState<(typeof projects)[number] | null>(null);
  const [isDeletingProject, setIsDeletingProject] = useState(false);
  const [projectDeleteError, setProjectDeleteError] = useState<string | null>(null);

  const handleProjectDelete = async () => {
    if (!projectToDelete || isDeletingProject) return;
    setIsDeletingProject(true);
    setProjectDeleteError(null);
    try {
      await onDeleteProject(projectToDelete.id);
      setProjectToDelete(null);
    } catch (error) {
      setProjectDeleteError(
        error instanceof Error ? error.message : "The project could not be deleted.",
      );
    } finally {
      setIsDeletingProject(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "generated": return "bg-green-500/20 text-green-400";
      case "analysed": return "bg-blue-500/20 text-blue-400";
      case "clarifying": return "bg-yellow-500/20 text-yellow-400";
      case "draft": return "bg-gray-500/20 text-gray-400";
      default: return "bg-gray-500/20 text-gray-400";
    }
  };

  const getStageColor = (stage: string) => {
    switch (stage) {
      case "ready": return "bg-green-500/20 text-green-400";
      case "generating": return "bg-blue-500/20 text-blue-400";
      case "clarifying": return "bg-yellow-500/20 text-yellow-400";
      case "analyzing": return "bg-blue-500/20 text-blue-400";
      case "error": return "bg-red-500/20 text-red-400";
      default: return "bg-gray-500/20 text-gray-400";
    }
  };

  const formatDate = (dateStr: string) => {
    try {
      return new Date(dateStr).toLocaleDateString();
    } catch {
      return dateStr;
    }
  };

  const recentSessions = chatSessions
    .slice()
    .sort((a, b) => new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime())
    .slice(0, 5);

  return (
    <div className="h-full min-h-0 overflow-y-auto bg-[#212121]">
      {/* Header */}
      <div className="flex items-center justify-between p-6 border-b border-white/10">
        <div className="flex items-center gap-4">
          <div className="p-3 rounded-xl bg-[#19c37d]/10">
            <LayoutDashboard className="h-6 w-6 text-[#19c37d]" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-white">Dashboard</h1>
            <p className="text-sm text-muted-foreground">Overview of your projects and SRS generations</p>
          </div>
        </div>
        <Button onClick={onNewChat} className="ml-auto">
          <Plus className="h-4 w-4 mr-2" />
          New Chat
        </Button>
        <Button variant="ghost" size="sm" onClick={onTourOpen} className="ml-2">
          <HelpCircle className="h-4 w-4" />
          <span className="hidden sm:inline">Help</span>
        </Button>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 p-6">
        <div className="bg-[#171717] border border-white/10 rounded-xl p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-muted-foreground">Total Projects</p>
              <p className="text-3xl font-bold text-white mt-1">{projects.length}</p>
            </div>
            <div className="p-3 rounded-xl bg-[#19c37d]/10">
              <LayoutDashboard className="h-6 w-6 text-[#19c37d]" />
            </div>
          </div>
        </div>
        <div className="bg-[#171717] border border-white/10 rounded-xl p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-muted-foreground">Active Sessions</p>
              <p className="text-3xl font-bold text-white mt-1">{chatSessions.length}</p>
            </div>
            <div className="p-3 rounded-xl bg-blue-500/10">
              <MessageSquare className="h-6 w-6 text-blue-400" />
            </div>
          </div>
        </div>
        <div className="bg-[#171717] border border-white/10 rounded-xl p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-muted-foreground">Completed SRS</p>
              <p className="text-3xl font-bold text-white mt-1">
                {projects.filter(p => p.status === "generated").length}
              </p>
            </div>
            <div className="p-3 rounded-xl bg-green-500/10">
              <FileText className="h-6 w-6 text-green-400" />
            </div>
          </div>
        </div>
        <div className="bg-[#171717] border border-white/10 rounded-xl p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-muted-foreground">In Progress</p>
              <p className="text-3xl font-bold text-white mt-1">
                {projects.filter(p => p.status !== "generated" && p.status !== "draft").length}
              </p>
            </div>
            <div className="p-3 rounded-xl bg-yellow-500/10">
              <Clock className="h-6 w-6 text-yellow-400" />
            </div>
          </div>
        </div>
      </div>

      {/* Recent Activity & Projects */}
      <div className="flex-1 p-6 space-y-6">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Recent Sessions */}
          <div className="lg:col-span-2 bg-[#171717] border border-white/10 rounded-xl overflow-hidden">
            <div className="p-4 border-b border-white/10 flex items-center justify-between">
              <h2 className="text-lg font-semibold">Recent Sessions</h2>
            </div>
            <div className="divide-y divide-white/10">
              {recentSessions.length === 0 ? (
                <div className="p-8 text-center text-muted-foreground">
                  <MessageSquare className="h-12 w-12 mx-auto mb-4 text-muted-foreground/50" />
                  <p>No recent sessions</p>
                  <p className="text-sm mt-1">Start a new chat to get started</p>
                </div>
              ) : (
                <div className="divide-y divide-white/10">
                  {recentSessions.map((session) => (
                    <div
                      key={session.id}
                      className="p-4 cursor-pointer hover:bg-white/5 transition-colors flex items-center justify-between border-b border-white/5"
                      onClick={() => window.location.hash = `chat/${session.id}`}
                    >
                      <div className="flex items-center gap-3">
                        <MessageSquare className="h-5 w-5 text-muted-foreground" />
                        <div>
                          <p className="font-medium text-white truncate max-w-xs">{session.name}</p>
                          <p className="text-xs text-muted-foreground">
                            {session.messageCount} messages • {formatDate(session.updatedAt)}
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className={"px-2 py-0.5 text-xs rounded-full " + getStageColor(session.stage)}>
                          {session.stage}
                        </span>
                        <ChevronRight className="h-4 w-4 text-muted-foreground" />
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Projects List */}
          <div className="bg-[#171717] border border-white/10 rounded-xl overflow-hidden">
            <div className="p-4 border-b border-white/10 flex items-center justify-between">
              <h2 className="text-lg font-semibold">Your Projects</h2>
            </div>
            <div className="divide-y divide-white/5">
              {projects.length === 0 ? (
                <div className="p-8 text-center text-muted-foreground">
                  <FileText className="h-12 w-12 mx-auto mb-4 text-muted-foreground/50" />
                  <p>No projects yet</p>
                  <p className="text-sm mt-1">Create your first project to get started</p>
                </div>
              ) : (
                <div className="divide-y divide-white/5">
                  {projects.map((project) => (
                    <div
                      key={project.id}
                      className="p-4 cursor-pointer hover:bg-white/5 transition-colors flex items-center justify-between border-b border-white/5"
                      onClick={() => onSelectProject(project.id)}
                    >
                      <div className="flex items-center gap-3">
                        <div className="p-2 rounded-lg bg-[#19c37d]/10">
                          <FileText className="h-5 w-5 text-[#19c37d]" />
                        </div>
                        <div>
                          <p className="font-medium text-white truncate max-w-xs">{project.name}</p>
                          <p className="text-xs text-muted-foreground">
                            {formatDate(project.created_at)} • {project.status}
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className={"px-2 py-0.5 text-xs rounded-full " + getStatusColor(project.status)}>
                          {project.status}
                        </span>
                        <button
                          type="button"
                          onClick={(event) => {
                            event.stopPropagation();
                            setProjectDeleteError(null);
                            setProjectToDelete(project);
                          }}
                          className="rounded p-1.5 text-muted-foreground transition-colors hover:bg-red-500/10 hover:text-red-400"
                          aria-label={`Delete project ${project.name}`}
                          title="Delete project"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                        <ChevronRight className="h-4 w-4 text-muted-foreground" />
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
      <Dialog
        open={!!projectToDelete}
        onOpenChange={(open) => !open && setProjectToDelete(null)}
      >
        <DialogContent className="bg-[#171717] border-white/10">
          <DialogHeader>
            <DialogTitle>Delete project?</DialogTitle>
          </DialogHeader>
          <p className="py-4 text-sm text-muted-foreground">
            This permanently removes <strong>{projectToDelete?.name}</strong>, its SRS versions,
            clarification answers, uploaded documents, and associated local chats.
          </p>
          {projectDeleteError && (
            <p className="text-sm text-red-400" role="alert">{projectDeleteError}</p>
          )}
          <DialogFooter className="border-t border-white/10">
            <Button
              variant="ghost"
              onClick={() => setProjectToDelete(null)}
              disabled={isDeletingProject}
            >
              Cancel
            </Button>
            <Button
              onClick={handleProjectDelete}
              disabled={isDeletingProject}
              className="bg-red-600 text-white hover:bg-red-500"
            >
              {isDeletingProject ? "Deleting..." : "Delete project"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

// ── AppShell Component ───────────────────────────────────────────────────

export function AppShell({ children, activeView = "chat", onNewChat, onDeleteChat }: AppShellProps) {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [renameSessionId, setRenameSessionId] = useState<string | null>(null);
  const [renameValue, setRenameValue] = useState("");
  const [deleteSessionId, setDeleteSessionId] = useState<string | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);
  const {
    chatSessions,
    currentSessionId,
    setCurrentSession,
    renameChatSession,
    deleteChatSession,
    setChatSessionPinned,
  } = useProjectStore();

  const handleRenameOpen = (session: typeof chatSessions[0]) => {
    setRenameSessionId(session.id);
    setRenameValue(session.name);
  };

  const handleRenameConfirm = async () => {
    if (!renameSessionId || !renameValue.trim()) return;
    try {
      await renameChatSession(renameSessionId, renameValue.trim());
      setRenameSessionId(null);
      setRenameValue("");
    } catch (err) {
      console.error("Failed to rename:", err);
    }
  };

  const handleDeleteConfirm = async () => {
    if (!deleteSessionId || isDeleting) return;
    setIsDeleting(true);
    try {
      if (onDeleteChat) await onDeleteChat(deleteSessionId);
      else await deleteChatSession(deleteSessionId);
      setDeleteSessionId(null);
    } catch (err) {
      console.error("Failed to delete chat:", err);
    } finally {
      setIsDeleting(false);
    }
  };

  const handlePinToggle = async (sessionId: string, pinned: boolean) => {
    try {
      await setChatSessionPinned(sessionId, pinned);
    } catch (err) {
      console.error("Failed to update pinned chat:", err);
    }
  };

  useEffect(() => {
    const handleResize = () => {
      if (window.innerWidth < 768) {
        setSidebarOpen(false);
      } else {
        setMobileSidebarOpen(false);
      }
    };

    handleResize();
    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, []);

  useEffect(() => {
    const toggleSidebar = () => {
      if (window.innerWidth < 768) {
        setMobileSidebarOpen((open) => !open);
      } else {
        setSidebarOpen((open) => !open);
      }
    };
    const focusSearch = () => {
      if (window.innerWidth < 768) setMobileSidebarOpen(true);
      else setSidebarOpen(true);
      window.requestAnimationFrame(() => {
        document.querySelector<HTMLInputElement>("[data-chat-search]")?.focus();
      });
    };
    window.addEventListener("cybersrs:toggle-sidebar", toggleSidebar);
    window.addEventListener("cybersrs:focus-search", focusSearch);
    return () => {
      window.removeEventListener("cybersrs:toggle-sidebar", toggleSidebar);
      window.removeEventListener("cybersrs:focus-search", focusSearch);
    };
  }, []);

  const filteredSessions = chatSessions.filter((s) =>
    s.name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const groupByDate = (items: typeof chatSessions) => {
    const now = new Date();
    const today: typeof items = [];
    const yesterday: typeof items = [];
    const thisWeek: typeof items = [];
    const older: typeof items = [];

    items.forEach((item) => {
      const d = new Date(item.updatedAt);
      const diff = now.getTime() - d.getTime();
      const dayMs = 86400000;
      if (diff < dayMs) today.push(item);
      else if (diff < dayMs * 2) yesterday.push(item);
      else if (diff < dayMs * 7) thisWeek.push(item);
      else older.push(item);
    });

    return { today, yesterday, thisWeek, older };
  };

  const pinnedSessions = filteredSessions.filter((session) => Boolean(session.pinnedAt));
  const groups = groupByDate(filteredSessions.filter((session) => !session.pinnedAt));

  const renderGroup = (label: string, items: typeof chatSessions) => {
    if (items.length === 0) return null;
    return (
      <div key={label} className="mb-2">
        <div className="px-3 py-1.5 text-xs font-medium text-muted-foreground">
          {label}
        </div>
        <ul className="space-y-0.5">
          {items.map((session) => (
            <li key={session.id}>
              <div className="w-full">
                <div
                  onClick={() => {
                    setCurrentSession(session.id);
                    window.location.hash = `chat/${session.id}`;
                    setMobileSidebarOpen(false);
                  }}
                  className={cn(
                    "w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm transition-colors cursor-pointer",
                    "hover:bg-muted/80 group",
                    currentSessionId === session.id
                      ? "bg-muted text-foreground"
                      : "text-muted-foreground"
                  )}
                >
                  <MessageSquare className="h-4 w-4 flex-shrink-0" />
                  <span className="truncate flex-1 text-left">{session.name}</span>
                  <div
                    className="flex-shrink-0 opacity-0 transition-opacity group-hover:opacity-100 group-focus-within:opacity-100"
                    onClick={(event) => event.stopPropagation()}
                  >
                    <DropdownMenu>
                      <DropdownMenuTrigger
                        className="h-7 w-7 p-0 text-muted-foreground hover:text-foreground"
                        aria-label={`Open actions for ${session.name}`}
                        title="Chat options"
                      >
                        <MoreHorizontal className="h-4 w-4" />
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end" className="min-w-[170px]">
                        <DropdownMenuItem
                          onSelect={() => handlePinToggle(session.id, !session.pinnedAt)}
                        >
                          {session.pinnedAt ? (
                            <PinOff className="h-4 w-4" />
                          ) : (
                            <Pin className="h-4 w-4" />
                          )}
                          {session.pinnedAt ? "Unpin chat" : "Pin chat"}
                        </DropdownMenuItem>
                        <DropdownMenuItem onSelect={() => handleRenameOpen(session)}>
                          <Edit className="h-4 w-4" />
                          Rename
                        </DropdownMenuItem>
                        <DropdownMenuSeparator />
                        <DropdownMenuItem
                          className="text-red-400 hover:text-red-300"
                          onSelect={() => setDeleteSessionId(session.id)}
                        >
                          <Trash2 className="h-4 w-4" />
                          Delete
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </div>
                </div>
              </div>
            </li>
          ))}
        </ul>
      </div>
    );
  };

  const sidebar = (
    <div
      className={cn(
        "flex h-full flex-col bg-[#171717] text-white transition-all duration-200",
        mobileSidebarOpen
          ? "fixed inset-y-0 left-0 z-50 w-[260px]"
          : sidebarOpen
          ? "w-[260px] shrink-0"
          : "w-0 overflow-hidden"
      )}
    >
      {/* New Chat + Toggle */}
      <div className="flex items-center justify-between p-2 border-b border-white/10">
        <button
          onClick={() => {
            setCurrentSession(null);
            setMobileSidebarOpen(false);

            if (onNewChat) {
              onNewChat();
            } else {
              window.location.hash = "new";
            }
          }}
          className="flex items-center gap-2 px-3 py-2 rounded-lg text-sm text-muted-foreground hover:bg-white/10 transition-colors"
        >
          <Plus className="h-4 w-4" />
          <span>New chat</span>
        </button>
        <button
          onClick={() => {
            if (window.innerWidth < 768) setMobileSidebarOpen(false);
            else setSidebarOpen(false);
          }}
          className="p-2 rounded-lg hover:bg-white/10 text-muted-foreground transition-colors"
        >
          <PanelLeftClose className="h-4 w-4" />
        </button>
      </div>

      {/* Search */}
      {(sidebarOpen || mobileSidebarOpen) && (
        <div className="px-2 py-2">
          <div className="relative">
            <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground" />
            <input
              data-chat-search
              type="text"
              placeholder="Search chats..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-8 pr-3 py-1.5 text-sm bg-white/5 border border-white/10 rounded-lg text-white placeholder:text-muted-foreground focus:outline-none focus:border-white/20"
            />
          </div>
        </div>
      )}

      {/* Chat list */}
      <div className="flex-1 overflow-y-auto px-2 py-1">
        {filteredSessions.length === 0 ? (
          <div className="text-center py-8 text-sm text-muted-foreground">
            {searchQuery ? "No results found" : "No conversations yet"}
          </div>
        ) : (
          <>
            {renderGroup("Pinned", pinnedSessions)}
            {renderGroup("Today", groups.today)}
            {renderGroup("Yesterday", groups.yesterday)}
            {renderGroup("This week", groups.thisWeek)}
            {renderGroup("Older", groups.older)}
          </>
        )}
      </div>

      {/* Bottom */}
      <div className="border-t border-white/10 p-2">
        <button
          onClick={() => {
            window.location.hash = "dashboard";
            setMobileSidebarOpen(false);
          }}
          className="flex items-center gap-2.5 w-full px-3 py-2 rounded-lg text-sm text-muted-foreground hover:bg-white/10 transition-colors"
        >
          <LayoutDashboard className="h-4 w-4" />
          <span>Dashboard</span>
        </button>
        <button
          onClick={() => {
            window.location.hash = "settings";
            setMobileSidebarOpen(false);
          }}
          className="flex items-center gap-2.5 w-full px-3 py-2 rounded-lg text-sm text-muted-foreground hover:bg-white/10 transition-colors"
        >
          <Settings className="h-4 w-4" />
          <span>Settings</span>
        </button>
      </div>

      {/* Rename Dialog */}
      <Dialog open={!!renameSessionId} onOpenChange={(open) => !open && setRenameSessionId(null)}>
        <DialogContent className="bg-[#171717] border-white/10">
          <DialogHeader>
            <DialogTitle>Rename Chat</DialogTitle>
          </DialogHeader>
          <div className="py-4">
            <Input
              value={renameValue}
              onChange={(e) => setRenameValue(e.target.value)}
              placeholder="Enter new name"
              autoFocus
              onKeyDown={(e) => e.key === "Enter" && handleRenameConfirm()}
            />
          </div>
          <DialogFooter className="border-t border-white/10">
            <Button variant="ghost" onClick={() => setRenameSessionId(null)}>
              Cancel
            </Button>
            <Button onClick={handleRenameConfirm} disabled={!renameValue.trim()}>
              Rename
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete confirmation */}
      <Dialog open={!!deleteSessionId} onOpenChange={(open) => !open && setDeleteSessionId(null)}>
        <DialogContent className="bg-[#171717] border-white/10">
          <DialogHeader>
            <DialogTitle>Delete chat?</DialogTitle>
          </DialogHeader>
          <p className="py-4 text-sm text-muted-foreground">
            This will permanently remove the conversation from this device.
          </p>
          <DialogFooter className="border-t border-white/10">
            <Button variant="ghost" onClick={() => setDeleteSessionId(null)} disabled={isDeleting}>
              Cancel
            </Button>
            <Button
              onClick={handleDeleteConfirm}
              disabled={isDeleting}
              className="bg-red-600 text-white hover:bg-red-500"
            >
              {isDeleting ? "Deleting..." : "Delete"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );

  return (
    <div className="flex h-screen min-h-0 overflow-hidden bg-[#212121]">
      {/* Mobile overlay */}
      {mobileSidebarOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/50 md:hidden"
          onClick={() => setMobileSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      {(sidebarOpen || mobileSidebarOpen) && sidebar}

      {/* Main content */}
      <div className="flex-1 flex flex-col min-w-0 h-full">
        {/* Top bar */}
        <div className="flex items-center h-12 px-2 border-b border-white/10 bg-[#212121]">
          {!sidebarOpen && (
            <button
              onClick={() => {
                if (window.innerWidth < 768) setMobileSidebarOpen(true);
                else setSidebarOpen(true);
              }}
              className="p-2 rounded-lg hover:bg-white/10 text-muted-foreground transition-colors mr-1"
            >
              <PanelLeft className="h-4 w-4" />
            </button>
          )}
          <div className="flex-1" />
          <div className="flex items-center gap-2">
            <span className="text-sm text-muted-foreground">
              {activeView === "srs"
                ? "SRS Workspace"
                : activeView === "editor"
                ? "SRS Editor"
                : activeView === "dashboard"
                ? "Dashboard"
                : "CyberSRS"}
            </span>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-hidden min-h-0">
          {children}
        </div>
      </div>
    </div>
  );
}

export default AppShell;
