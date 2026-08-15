import { useCallback } from "react";
import { useProjectStore } from "../stores/projectStore";
import type { Project } from "../stores/projectStore";

export function useProjects() {
  const {
    projects,
    currentProjectId,
    isLoading,
    error,
    fetchProjects,
    createProject,
    setCurrentProject,
    deleteProject,
    updateProject,
  } = useProjectStore();

  const getCurrentProject = useCallback((): Project | undefined => {
    return projects.find((p) => p.id === currentProjectId);
  }, [projects, currentProjectId]);

  const getProjectById = useCallback((id: string): Project | undefined => {
    return projects.find((p) => p.id === id);
  }, [projects]);

  return {
    projects,
    currentProjectId,
    currentProject: getCurrentProject(),
    isLoading,
    error,
    fetchProjects,
    createProject,
    setCurrentProject,
    deleteProject,
    updateProject,
    getProjectById,
  };
}