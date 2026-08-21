import { useCallback, useRef, useState } from "react";
import { api } from "../api/client";
import { ApiRequestError, type AnalysisResponse, type ClarificationAnswerItem, type SRSGenerationProgressEvent, type SRSSchema } from "../api/types";
import { applySlidingWindow } from "../lib/contextWindow";
import { friendlyErrorMessage } from "../lib/errorMessages";
import { useChatStore } from "../stores/chatStore";
import { useProjectStore } from "../stores/projectStore";

export function createProjectName(description: string): string {
  const declaredName = description.match(
    /\b(?:project\s+)?(?:called|named)\s+["“”']?([^\r\n.!?"“”']{1,64})/i,
  )?.[1]?.trim();
  if (declaredName) return declaredName;

  const firstMeaningfulLine = description
    .split(/\r?\n/)
    .map((line) => line.replace(/^\s*#{1,6}\s*/, "").trim())
    .find(Boolean) ?? description;
  const withoutDocumentPrefix = firstMeaningfulLine.replace(
    /^software requirements specification\s*(?:\(srs\))?\s*[:-]?\s*/i,
    "",
  );
  const name = withoutDocumentPrefix.trim().replace(/\s+/g, " ").split(" ").slice(0, 8).join(" ");
  if (!name) return "Cybersecurity Project";
  return name.length > 64 ? `${name.slice(0, 61)}...` : name;
}

/** Parse a one-message numbered answer set against the active clarification questions. */
export function parseClarificationAnswers(
  content: string,
  questions: import("../api/types").ClarificationQuestionRead[],
): ClarificationAnswerItem[] | null {
  const normalized = content.trim();
  if (/^skip(?:\s+all)?[.!]?$/i.test(normalized)) {
    return questions.map((question) => ({
      question_id: question.id,
      answer_text: "",
      skipped: true,
    }));
  }

  const byNumber = new Map<number, string>();
  const verbosePattern = /question\s+(\d+)\s*:[\s\S]*?answer\s*:\s*([\s\S]*?)(?=\s*question\s+\d+\s*:|$)/gi;
  for (const match of normalized.matchAll(verbosePattern)) {
    byNumber.set(Number(match[1]), match[2].trim());
  }
  for (const line of normalized.split(/\r?\n/)) {
    if (/^\s*question\s+\d+\s*:.*\banswer\s*:/i.test(line)) continue;
    const match = line.match(/^\s*(?:question\s*|answer\s*)?(\d+)\s*[.):-]\s*(?:answer\s*:\s*)?(.+)$/i);
    if (match) byNumber.set(Number(match[1]), match[2].trim());
  }

  if (byNumber.size === 0) {
    if (questions.length !== 1) return null;
    byNumber.set(1, normalized.replace(/^answer\s*:\s*/i, "").trim());
  }

  return questions.map((question, index) => {
    const answerText = byNumber.get(index + 1)?.trim() ?? "";
    return {
      question_id: question.id,
      answer_text: answerText,
      skipped: answerText.length === 0,
    };
  });
}

/** Coordinate conversational chat and the project-to-SRS workflow. */
export function useChat() {
  const [pendingFiles, setPendingFiles] = useState<File[]>([]);
  const [projectContextDirty, setProjectContextDirty] = useState(false);
  const [canRetry, setCanRetry] = useState(false);
  const [generationProgress, setGenerationProgress] = useState<SRSGenerationProgressEvent | null>(null);
  const retryActionRef = useRef<(() => Promise<void>) | null>(null);
  const routeRequestIdRef = useRef(0);
  const generationControllerRef = useRef<AbortController | null>(null);
  const {
    stage, projectId, sessionId, messages, analysis, clarificationQuestions, srs,
    srsVersionId, pendingProjectDescription, isLoading, error, setStage,
    setProjectId, addMessage, setAnalysis, setClarificationQuestions, setSRS, clearSRS,
    setPendingProjectDescription, setLoading, setError, reset, loadChatSession,
    saveChatSession, createNewChatSession,
  } = useChatStore();
  const { createProject: createProjectApi, setCurrentProject, setCurrentSession } = useProjectStore();

  const registerRetry = useCallback((action: () => Promise<void>) => {
    retryActionRef.current = action;
    setCanRetry(true);
  }, []);

  const clearRetry = useCallback(() => {
    retryActionRef.current = null;
    setCanRetry(false);
  }, []);

  const retryLastOperation = useCallback(async () => {
    const action = retryActionRef.current;
    if (!action) return;
    setCanRetry(false);
    await action();
  }, []);

  const cancelPendingNavigation = useCallback(() => {
    routeRequestIdRef.current += 1;
  }, []);

  const addVisibleError = useCallback((failure: unknown) => {
    const message = typeof failure === "string" ? failure : friendlyErrorMessage(failure);
    setError(message);
    addMessage({ role: "assistant", content: message, type: "error" });
  }, [addMessage, setError]);

  const attachFiles = useCallback(async (files: File[]) => {
    const supported = new Set(["pdf", "md", "markdown", "txt", "csv"]);
    const accepted = files.filter((file) => {
      const extension = file.name.split(".").pop()?.toLowerCase() ?? "";
      return supported.has(extension) && file.size > 0 && file.size <= 10 * 1024 * 1024;
    });
    if (accepted.length !== files.length) {
      addVisibleError("Only non-empty PDF, Markdown, text, and CSV files up to 10 MB are supported.");
    }
    if (!accepted.length) return;
    const activeProjectId = useChatStore.getState().projectId;
    if (activeProjectId) {
      try {
        setLoading(true);
        const uploaded = [];
        for (const file of accepted) {
          uploaded.push(await api.uploadProjectDocument(activeProjectId, file));
        }
        addMessage({
          role: "assistant",
          content: `Attached ${uploaded.map((item) => item.original_filename).join(", ")} to this project.`,
          type: "text",
        });
        setProjectContextDirty(true);
      } catch (failure) {
        addVisibleError(failure);
      } finally {
        setLoading(false);
      }
      return;
    }
    setPendingFiles((current) => {
      const unique = [...current];
      for (const file of accepted) {
        if (!unique.some((item) => item.name === file.name && item.size === file.size)) {
          unique.push(file);
        }
      }
      if (unique.length > 5) addVisibleError("A project can have at most 5 reference documents.");
      return unique.slice(0, 5);
    });
  }, [addMessage, addVisibleError, setLoading]);

  const removePendingFile = useCallback((index: number) => {
    setPendingFiles((files) => files.filter((_, itemIndex) => itemIndex !== index));
  }, []);

  const resetChat = useCallback(() => {
    cancelPendingNavigation();
    generationControllerRef.current?.abort();
    setGenerationProgress(null);
    clearRetry();
    setPendingFiles([]);
    setProjectContextDirty(false);
    reset();
  }, [cancelPendingNavigation, clearRetry, reset]);

  const setWorkflowError = useCallback((failure: unknown) => {
    setError(typeof failure === "string" ? failure : friendlyErrorMessage(failure));
  }, [setError]);

  const runGeneration = useCallback(async (targetProjectId: string) => {
    registerRetry(() => runGeneration(targetProjectId));
    generationControllerRef.current?.abort();
    const controller = new AbortController();
    generationControllerRef.current = controller;
    try {
      setStage("generating");
      setLoading(true);
      setError(null);
      setGenerationProgress({
        phase: "preparing",
        progress: 0,
        message: "Starting SRS generation.",
        result: null,
      });
      const generation = await api.generateSrsStream(
        targetProjectId,
        setGenerationProgress,
        controller.signal,
      );
      const version = await api.getSrsVersion(targetProjectId, generation.version_id);
      if (!version.srs) throw new Error("The backend completed generation without returning an SRS document.");
      setSRS(version.srs, version.id);
      setStage("ready");
      addMessage({
        role: "assistant", content: "", type: "srs",
        metadata: { srs: version.srs, versionId: version.id, projectId: targetProjectId },
      });
      clearRetry();
    } catch (failure) {
      setStage("error");
      if (failure instanceof Error && failure.name === "AbortError") {
        setError("SRS generation was cancelled. You can retry when ready.");
      } else {
        setWorkflowError(failure);
      }
    } finally {
      if (generationControllerRef.current === controller) {
        generationControllerRef.current = null;
      }
      setLoading(false);
    }
  }, [addMessage, clearRetry, registerRetry, setError, setLoading, setSRS, setStage, setWorkflowError]);

  const cancelGeneration = useCallback(() => {
    generationControllerRef.current?.abort();
  }, []);

  const generateClarifications = useCallback(async (targetProjectId: string) => {
    const response = await api.generateClarificationQuestions(targetProjectId);
    setClarificationQuestions(response.questions);
    addMessage({
      role: "assistant", content: "", type: "clarification",
      metadata: { questions: response.questions },
    });
  }, [addMessage, setClarificationQuestions]);

  const runAnalysis = useCallback(async (targetProjectId: string) => {
    registerRetry(() => runAnalysis(targetProjectId));
    try {
      setStage("analyzing");
      setLoading(true);
      setError(null);
      const response: AnalysisResponse = await api.analyseProject(targetProjectId);
      setProjectContextDirty(false);
      setAnalysis(response.analysis);
      addMessage({
        role: "assistant", content: "", type: "analysis",
        metadata: { analysis: response.analysis },
      });
      setStage("clarifying");
      await generateClarifications(targetProjectId);
      clearRetry();
    } catch (failure) {
      setStage("error");
      setWorkflowError(failure);
    } finally {
      setLoading(false);
    }
  }, [addMessage, clearRetry, generateClarifications, registerRetry, setAnalysis, setError, setLoading, setStage, setWorkflowError]);

  const handleCreateProject = useCallback(async (name: string, description: string) => {
    const trimmed = description.trim();
    if (trimmed.length < 10) {
      addVisibleError("Project description must be at least 10 characters. Please provide more details.");
      return;
    }
    registerRetry(() => handleCreateProject(name, description));
    try {
      setLoading(true);
      setError(null);
      const project = await createProjectApi(name, trimmed);
      setProjectId(project.id);
      setCurrentProject(project.id);
      setCurrentSession(useChatStore.getState().sessionId);
      setPendingProjectDescription(null);
      if (pendingFiles.length) {
        for (const file of pendingFiles) {
          await api.uploadProjectDocument(project.id, file);
        }
        addMessage({
          role: "assistant",
          content: `Added ${pendingFiles.length} reference document${pendingFiles.length === 1 ? "" : "s"} to the project context.`,
          type: "text",
        });
        setPendingFiles([]);
      }
      await runAnalysis(project.id);
    } catch (failure) {
      setStage("error");
      setWorkflowError(failure);
    } finally {
      setLoading(false);
    }
  }, [addMessage, addVisibleError, createProjectApi, pendingFiles, registerRetry, runAnalysis, setCurrentProject, setCurrentSession, setError, setLoading, setPendingProjectDescription, setProjectId, setStage, setWorkflowError]);

  const submitClarificationAnswers = useCallback(async (answers: ClarificationAnswerItem[]) => {
    if (!projectId) return;
    registerRetry(() => submitClarificationAnswers(answers));
    try {
      setLoading(true);
      setError(null);
      await api.submitClarificationAnswers(projectId, answers);
      addMessage({ role: "user", content: "Answers submitted. Generating SRS...", type: "text" });
      await runGeneration(projectId);
    } catch (failure) {
      setStage("error");
      setWorkflowError(failure);
    } finally {
      setLoading(false);
      await saveChatSession();
    }
  }, [addMessage, projectId, registerRetry, runGeneration, saveChatSession, setError, setLoading, setStage, setWorkflowError]);

  const sendChatMessage = useCallback(async (rawContent: string) => {
    const content = rawContent.trim();
    if (!content) return;
    try {
      setLoading(true);
      setError(null);
      if (!useChatStore.getState().sessionId) await createNewChatSession();
      addMessage({ role: "user", content, type: "text" });

      const current = useChatStore.getState();
      const chatHistory = applySlidingWindow(current.messages.map((message) => ({
        role: message.role,
        content: message.content,
      })));
      const intentResult = await api.classifyIntent(
        content,
        current.projectId ?? undefined,
        Boolean(current.srs),
        current.stage,
      );

      if (
        intentResult.intent === "clarification" &&
        current.projectId &&
        current.clarificationQuestions
      ) {
        const parsedAnswers = parseClarificationAnswers(content, current.clarificationQuestions);
        if (!parsedAnswers) {
          addMessage({
            role: "assistant",
            content: "Please answer all clarification questions in one message using `1. answer`, `2. answer`, and so on, or use the form above.",
            type: "error",
          });
        } else {
          await submitClarificationAnswers(parsedAnswers);
        }
      } else if (intentResult.intent === "srs_modification" && current.projectId && current.srsVersionId) {
        const editResult = await api.editSrsViaChat(current.projectId, current.srsVersionId, content);
        addMessage({ role: "assistant", content: editResult.message, type: editResult.success ? "text" : "error" });
        if (editResult.updated_srs) setSRS(editResult.updated_srs as unknown as SRSSchema, current.srsVersionId);
      } else if (intentResult.intent === "srs_project_request") {
        setPendingProjectDescription(content);
        await handleCreateProject(createProjectName(content), content);
      } else if (intentResult.intent === "srs_generation") {
        if (current.projectId) {
          if (current.stage === "clarifying") {
            addMessage({
              role: "assistant",
              content: "Please answer or skip the clarification questions first. I will generate the SRS immediately after you submit them.",
              type: "error",
            });
          } else if (projectContextDirty || (!current.analysis && !current.srs)) {
            await runAnalysis(current.projectId);
          } else {
            await runGeneration(current.projectId);
          }
        } else if (current.pendingProjectDescription) {
          await handleCreateProject(createProjectName(current.pendingProjectDescription), current.pendingProjectDescription);
        } else if (pendingFiles.length) {
          await handleCreateProject(
            createProjectName(pendingFiles[0].name.replace(/\.[^.]+$/, "")),
            "Generate an SRS from the attached project reference documents and confirm all material requirements with the user.",
          );
        } else {
          addMessage({
            role: "assistant",
            content: "Describe the cybersecurity or network project first. I will retain that description, answer questions about it, and generate the SRS when you ask.",
            type: "error",
          });
        }
      } else {
        if (intentResult.intent === "project_description") setPendingProjectDescription(content);
        const response = await api.chatCompletion(chatHistory, current.projectId ?? undefined);
        addMessage({
          role: "assistant", content: response.content, type: "text",
          metadata: {
            citations: response.citations, ragEnabled: response.rag_enabled,
            warnings: response.warnings, modelName: response.model_name,
          },
        });
      }
    } catch (failure) {
      addVisibleError(failure);
    } finally {
      setLoading(false);
      await useChatStore.getState().saveChatSession();
    }
  }, [addMessage, addVisibleError, createNewChatSession, handleCreateProject, pendingFiles, projectContextDirty, runAnalysis, runGeneration, setError, setLoading, setPendingProjectDescription, setSRS, submitClarificationAnswers]);

  const loadExistingProject = useCallback(async (targetProjectId: string) => {
    registerRetry(() => loadExistingProject(targetProjectId));
    try {
      setPendingFiles([]);
      setProjectContextDirty(false);
      setLoading(true);
      setError(null);
      const current = useChatStore.getState();
      if (!current.sessionId || current.projectId !== targetProjectId) {
        await createNewChatSession(targetProjectId);
      }
      const project = await api.getProject(targetProjectId);
      setProjectId(project.id);
      setCurrentProject(project.id);
      setCurrentSession(useChatStore.getState().sessionId);
      setPendingProjectDescription(project.description);

      try {
        const version = await api.getLatestSrs(project.id);
        if (version.srs) {
          setSRS(version.srs, version.id);
          setStage("ready");
          if (useChatStore.getState().messages.length === 0) {
            addMessage({
              role: "assistant", content: "", type: "srs",
              metadata: { srs: version.srs, versionId: version.id, projectId: project.id },
            });
          }
        }
      } catch (failure) {
        if (!(failure instanceof ApiRequestError && failure.status === 404)) throw failure;
        setStage("welcome");
      }
      clearRetry();
    } catch (failure) {
      setStage("error");
      setWorkflowError(failure);
    } finally {
      setLoading(false);
      await useChatStore.getState().saveChatSession();
    }
  }, [addMessage, clearRetry, createNewChatSession, registerRetry, setCurrentProject, setCurrentSession, setError, setLoading, setPendingProjectDescription, setProjectId, setSRS, setStage, setWorkflowError]);

  const loadSrsVersion = useCallback(async (targetProjectId: string, targetVersionId: string) => {
    const current = useChatStore.getState();
    if (
      current.projectId === targetProjectId &&
      current.srsVersionId === targetVersionId &&
      current.srs
    ) {
      setCurrentProject(targetProjectId);
      setStage("ready");
      return;
    }

    const requestId = ++routeRequestIdRef.current;
    registerRetry(() => loadSrsVersion(targetProjectId, targetVersionId));
    try {
      setPendingFiles([]);
      setProjectContextDirty(false);
      setLoading(true);
      setError(null);
      clearSRS();

      const [project, version] = await Promise.all([
        api.getProject(targetProjectId),
        api.getSrsVersion(targetProjectId, targetVersionId),
      ]);
      if (requestId !== routeRequestIdRef.current) return;
      if (!version.srs) {
        throw new Error("This SRS version does not contain a document.");
      }

      setProjectId(project.id);
      setCurrentProject(project.id);
      setCurrentSession(null);
      setPendingProjectDescription(project.description);
      setSRS(version.srs, version.id);
      setStage("ready");
      clearRetry();
    } catch (failure) {
      if (requestId !== routeRequestIdRef.current) return;
      setStage("error");
      setWorkflowError(failure);
    } finally {
      if (requestId === routeRequestIdRef.current) setLoading(false);
    }
  }, [clearRetry, clearSRS, registerRetry, setCurrentProject, setCurrentSession, setError, setLoading, setPendingProjectDescription, setProjectId, setSRS, setStage, setWorkflowError]);

  return {
    stage, projectId, sessionId, messages, analysis, clarificationQuestions, srs,
    srsVersionId, pendingProjectDescription, isLoading, error, canRetry,
    generationProgress, sendChatMessage,
    handleCreateProject, submitClarificationAnswers, loadChatSession,
    loadExistingProject, loadSrsVersion, cancelPendingNavigation, retryLastOperation,
    cancelGeneration,
    createNewChatSession, saveChatSession, reset: resetChat, setStage, setError,
    pendingFiles, attachFiles, removePendingFile,
  };
}
