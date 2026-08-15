import { useCallback } from "react";
import { useChatStore } from "../stores/chatStore";
import { useProjectStore } from "../stores/projectStore";
import { api } from "../api/client";
import type { AnalysisResponse, ClarificationAnswerItem } from "../api/types";

export function useChat() {
  const {
    stage,
    projectId,
    messages,
    analysis,
    clarificationQuestions,
    srs,
    srsVersionId,
    isLoading,
    error,
    setStage,
    setProjectId,
    addMessage,
    setAnalysis,
    setClarificationQuestions,
    setSRS,
    setLoading,
    setError,
    reset,
  } = useChatStore();

  const { createProject: createProjectApi, setCurrentProject } = useProjectStore();

  const runGeneration = useCallback(async (projectId: string) => {
    try {
      setStage("generating");
      setLoading(true);
      setError(null);
      addMessage({
        role: "assistant",
        content: "",
        type: "generation",
      });
      const generation = await api.generateSrs(projectId);
      const version = await api.getSrsVersion(projectId, generation.version_id);
      if (version.srs) {
        setSRS(version.srs, version.id);
        setStage("ready");
        addMessage({
          role: "assistant",
          content: "",
          type: "srs",
          metadata: { srs: version.srs, versionId: version.id },
        });
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "SRS generation failed");
      setStage("error");
    } finally {
      setLoading(false);
    }
  }, [addMessage, setError, setLoading, setSRS, setStage]);

  const generateClarifications = useCallback(async (projectId: string) => {
    try {
      const response = await api.generateClarificationQuestions(projectId);
      setClarificationQuestions(response.questions);
      addMessage({
        role: "assistant",
        content: "",
        type: "clarification",
        metadata: { questions: response.questions },
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to generate clarifications");
    }
  }, [addMessage, setClarificationQuestions, setError]);

  const runAnalysis = useCallback(async (projectId: string) => {
    try {
      setStage("analyzing");
      setLoading(true);
      setError(null);
      const response: AnalysisResponse = await api.analyseProject(projectId);
      setAnalysis(response.analysis);
      addMessage({
        role: "assistant",
        content: "",
        type: "analysis",
        metadata: { analysis: response.analysis },
      });
      if (response.analysis.missing_information?.length) {
        setStage("clarifying");
        await generateClarifications(projectId);
      } else {
        await runGeneration(projectId);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Analysis failed");
      setStage("error");
    } finally {
      setLoading(false);
    }
  }, [addMessage, generateClarifications, runGeneration, setAnalysis, setError, setLoading, setStage]);

  const handleCreateProject = useCallback(async (name: string, description: string) => {
    try {
      setLoading(true);
      setError(null);
      const project = await createProjectApi(name, description);
      setProjectId(project.id);
      setCurrentProject(project.id);
      addMessage({
        role: "user",
        content: description,
        type: "text",
      });
      await runAnalysis(project.id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create project");
    } finally {
      setLoading(false);
    }
  }, [addMessage, createProjectApi, runAnalysis, setCurrentProject, setError, setLoading, setProjectId]);

  const submitClarificationAnswers = useCallback(async (answers: ClarificationAnswerItem[]) => {
    if (!projectId) return;
    try {
      setLoading(true);
      setError(null);
      await api.submitClarificationAnswers(projectId, answers);
      addMessage({
        role: "user",
        content: "Answers submitted. Generating SRS...",
        type: "text",
      });
      await runGeneration(projectId);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to submit answers");
    } finally {
      setLoading(false);
    }
  }, [addMessage, projectId, runGeneration, setError, setLoading]);

  const loadExistingProject = useCallback(async (projectId: string) => {
    try {
      setLoading(true);
      setError(null);
      setProjectId(projectId);
      setStage("analyzing");
      await runAnalysis(projectId);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load project");
      setStage("error");
    } finally {
      setLoading(false);
    }
  }, [runAnalysis, setError, setLoading, setProjectId, setStage]);

  return {
    stage,
    projectId,
    messages,
    analysis,
    clarificationQuestions,
    srs,
    srsVersionId,
    isLoading,
    error,
    handleCreateProject,
    submitClarificationAnswers,
    loadExistingProject,
    reset,
    setStage,
    setError,
  };
}
