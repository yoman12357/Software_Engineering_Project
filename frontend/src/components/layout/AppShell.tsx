"use client";

import { useState, useEffect } from "react";
import { cn } from "../../lib/utils";
import { ChevronLeft, ChevronRight, Shield, Plus, FileText, Settings, LogOut, User } from "lucide-react";
import { ThemeToggle, ThemeToggleCompact } from "../../components/ui/ThemeToggle";
import { useProjectStore } from "../../stores/projectStore";
import { Button } from "../../components/ui/Button";
import { Toaster } from "../../components/ui/Toast";
import { Avatar, DropdownMenu, DropdownMenuTrigger, DropdownMenuContent, DropdownMenuItem, DropdownMenuSeparator, DropdownMenuLabel } from "../../components/ui";

interface AppShellProps {
  children: React.ReactNode;
}

export function AppShell({ children }: AppShellProps) {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false);
  const { projects, currentProjectId, setCurrentProject } = useProjectStore();

  // Handle responsive sidebar
  useEffect(() => {
    const handleResize = () => {
      if (window.innerWidth >= 1024) {
        setMobileSidebarOpen(false);
      }
    };
    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, []);

  const toggleSidebar = () => {
    if (window.innerWidth < 1024) {
      setMobileSidebarOpen(!mobileSidebarOpen);
    } else {
      setSidebarCollapsed(!sidebarCollapsed);
    }
  };

  const currentProject = projects.find((p) => p.id === currentProjectId);

  const closeMobileSidebar = () => {
    setMobileSidebarOpen(false);
  };

  const projectCountBadge = projects.length > 0 && !sidebarCollapsed && (
    <span className="px-2 py-0.5 rounded-full bg-muted text-muted-foreground text-[10px]">
      {projects.length}
    </span>
  );

  const projectListHeader = (
    <div className={cn("flex items-center justify-between px-2 py-2 text-xs font-medium text-muted-foreground uppercase tracking-wider", sidebarCollapsed && "px-0")}>
      <span>Projects</span>
      {projectCountBadge}
    </div>
  );

  const emptyProjectsView = (
    <div className="text-center py-8 text-muted-foreground text-sm">
      No projects yet
    </div>
  );

  const projectList = (
    <>
      <ul className="space-y-1" role="list">
        {projects.map((project) => (
          <li key={project.id}>
            <button
              onClick={() => {
                setCurrentProject(project.id);
                window.location.hash = project.id;
                closeMobileSidebar();
              }}
              className={cn(
                "w-full flex items-center gap-3 p-2.5 rounded-lg transition-all duration-200",
                "hover:bg-muted",
                currentProjectId === project.id
                  ? "bg-primary/10 text-primary border-l-2 border-primary"
                  : "text-foreground",
                sidebarCollapsed && "justify-center px-0"
              )}
              aria-current={currentProjectId === project.id ? "true" : "false"}
            >
              <FileText className="h-4 w-4 flex-shrink-0 text-muted-foreground" />
              <span className={cn("truncate font-medium", sidebarCollapsed && "hidden")}>
                {project.name}
              </span>
              {currentProjectId === project.id && !sidebarCollapsed && (
                <span className="ml-auto h-1.5 w-1.5 rounded-full bg-primary" />
              )}
            </button>
          </li>
        ))}
      </ul>
    </>
  );

  const displayProjectList = projects.length === 0 ? emptyProjectsView : projectList;

  const quickActions = !sidebarCollapsed && (
    <div className="mt-6 pt-4 border-t border-border space-y-2">
      <Button
        variant="ghost"
        className="w-full justify-start gap-2"
        onClick={() => { window.location.hash = "settings"; }}
      >
        <Settings className="h-4 w-4" />
        Settings
      </Button>
      <ThemeToggle />
    </div>
  );

  const footer = (
    <div className={cn("p-3 border-t border-border", sidebarCollapsed && "px-0")}>
      <div className={cn("flex items-center gap-2", sidebarCollapsed && "justify-center px-0")}>
        <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center">
          <Shield className="h-4 w-4 text-primary" />
        </div>
        <div className={cn("flex-1 min-w-0", sidebarCollapsed && "hidden")}>
          <p className="text-xs font-medium truncate">CyberSRS</p>
          <p className="text-[10px] text-muted-foreground truncate">v0.1.0</p>
        </div>
      </div>
    </div>
  );

  const sidebar = (
    <aside
      className={cn(
        "fixed lg:static inset-y-0 left-0 z-50 bg-secondary-surface border-r border-border",
        "flex flex-col transition-all duration-300 ease-spring",
        "overflow-y-auto",
        sidebarCollapsed ? "w-16" : "w-72",
        mobileSidebarOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0",
      )}
      aria-label="Sidebar navigation"
    >
      {/* Brand */}
      <div className={cn("flex items-center gap-3 p-4 border-b border-border", sidebarCollapsed && "justify-center px-0")}>
        <button
          onClick={toggleSidebar}
          className="lg:hidden p-2 rounded-lg hover:bg-muted text-foreground"
          aria-label={sidebarCollapsed ? "Expand sidebar" : "Collapse sidebar"}
        >
          {sidebarCollapsed ? <ChevronRight className="h-5 w-5" /> : <ChevronLeft className="h-5 w-5" />}
        </button>
        <div className={cn("flex items-center gap-2 overflow-hidden", sidebarCollapsed && "opacity-0 w-0")}>
          <div className="p-2 rounded-lg bg-primary text-primary-foreground">
            <Shield className="h-5 w-5" />
          </div>
          <span className="font-semibold text-lg font-mono">CyberSRS</span>
        </div>
      </div>

      {/* New Project Button */}
      <div className={cn("p-3 border-b border-border", sidebarCollapsed && "px-0")}>
        <Button
          className={cn("w-full justify-start gap-2", sidebarCollapsed && "p-2")}
          onClick={() => {
            setCurrentProject(null);
            window.location.hash = "new";
            closeMobileSidebar();
          }}
          aria-label="New Project"
        >
          <Plus className="h-4 w-4" />
          <span className={cn("truncate", sidebarCollapsed && "hidden")}>
            New Project
          </span>
        </Button>
      </div>

      {/* Projects List */}
      <div className="flex-1 overflow-y-auto p-3">
        {projectListHeader}
        {displayProjectList}
      </div>

      {/* Quick Actions */}
      {quickActions}

      {/* Footer */}
      {footer}
    </aside>
  );

  return (
    <div className="flex h-screen bg-background overflow-hidden">
      {/* Mobile sidebar overlay */}
      {mobileSidebarOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/50 lg:hidden"
          onClick={() => setMobileSidebarOpen(false)}
          aria-hidden="true"
        />
      )}

      {/* Sidebar */}
      {sidebar}

      {/* Main content */}
      <div className={cn(
        "flex-1 flex flex-col overflow-hidden transition-all duration-300",
        "lg:pl-0",
      )}>
        {/* Header */}
        <header className="sticky top-0 z-30 flex items-center justify-between gap-4 px-4 py-3 bg-background/80 backdrop-blur-sm border-b border-border">
          <div className="flex items-center gap-3">
            <button
              onClick={toggleSidebar}
              className="lg:hidden p-2 rounded-lg hover:bg-muted text-foreground"
              aria-label="Toggle sidebar"
            >
              <ChevronLeft className="h-5 w-5" />
            </button>
            <div className="hidden sm:block">
              <h1 className="text-xl font-semibold truncate max-w-xs">
                {currentProject?.name || "Welcome to CyberSRS"}
              </h1>
            </div>
          </div>

          <div className="flex items-center gap-2 ml-auto">
            <ThemeToggleCompact />
            
            {/* User menu */}
            <DropdownMenu>
              <DropdownMenuTrigger className="h-9 w-9 rounded-full p-0">
                <Avatar fallback="U" size="sm" />
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-48">
                <DropdownMenuLabel className="font-medium">Account</DropdownMenuLabel>
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={() => { window.location.hash = "settings"; }}>
                  <User className="h-4 w-4 mr-2" />
                  Settings
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem className="text-destructive">
                  <LogOut className="h-4 w-4 mr-2" />
                  Sign out
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </header>

        {/* Main content area */}
        <main className="flex-1 overflow-y-auto p-4 md:p-6 lg:p-8">
          <div className="mx-auto max-w-4xl">
            {children}
          </div>
        </main>
      </div>

      {/* Toaster */}
      <Toaster />
    </div>
  );
}
