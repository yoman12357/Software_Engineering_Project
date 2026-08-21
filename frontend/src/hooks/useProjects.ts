import { useProjectStore } from "../stores/projectStore";

export function useProjects() {
  const {
    projects,
    chatSessions,
    currentProjectId,
    currentSessionId,
    isLoading,
    error,
    fetchProjects,
    fetchChatSessions,
    createProject,
    setCurrentProject,
    setCurrentSession,
    deleteProject,
    deleteChatSession,
    setChatSessionPinned,
  } = useProjectStore();

  return {
    projects,
    chatSessions,
    currentProjectId,
    currentSessionId,
    isLoading,
    error,
    fetchProjects,
    fetchChatSessions,
    createProject,
    setCurrentProject,
    setCurrentSession,
    deleteProject,
    deleteChatSession,
    setChatSessionPinned,
  };
}
