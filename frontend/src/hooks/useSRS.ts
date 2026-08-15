import { useState, useCallback } from "react";
import { api } from "../api/client";
import type { SRSSchema, SRSVersionRead, SRSEditRequest } from "../api/types";

export function useSRS(projectId: string | null) {
  const [srs, setSrs] = useState<SRSSchema | null>(null);
  const [versions, setVersions] = useState<SRSVersionRead[]>([]);
  const [currentVersionId, setCurrentVersionId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadLatest = useCallback(async () => {
    if (!projectId) return;
    setIsLoading(true);
    setError(null);
    try {
      const version = await api.getLatestSrs(projectId);
      if (version.srs) {
        setSrs(version.srs);
        setCurrentVersionId(version.id);
      }
      setVersions([version]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load SRS");
    } finally {
      setIsLoading(false);
    }
  }, [projectId]);

  const loadVersion = useCallback(async (versionId: string) => {
    if (!projectId) return;
    setIsLoading(true);
    setError(null);
    try {
      const version = await api.getSrsVersion(projectId, versionId);
      if (version.srs) {
        setSrs(version.srs);
        setCurrentVersionId(version.id);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load SRS version");
    } finally {
      setIsLoading(false);
    }
  }, [projectId]);

  const editVersion = useCallback(async (versionId: string, updates: SRSEditRequest) => {
    if (!projectId) return;
    setIsLoading(true);
    setError(null);
    try {
      const version = await api.editSrsVersion(projectId, versionId, updates);
      if (version.srs) {
        setSrs(version.srs);
      }
      return version;
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to edit SRS");
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [projectId]);

  const validateVersion = useCallback(async (versionId: string) => {
    if (!projectId) return;
    setIsLoading(true);
    setError(null);
    try {
      const result = await api.validateSrsVersion(projectId, versionId);
      return result;
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to validate SRS");
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [projectId]);

  const generateNew = useCallback(async () => {
    if (!projectId) return;
    setIsLoading(true);
    setError(null);
    try {
      const generation = await api.generateSrs(projectId);
      const version = await api.getSrsVersion(projectId, generation.version_id);
      if (version.srs) {
        setSrs(version.srs);
        setCurrentVersionId(version.id);
        setVersions((prev) => [version, ...prev]);
      }
      return version;
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to generate SRS");
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [projectId]);

  return {
    srs,
    versions,
    currentVersionId,
    isLoading,
    error,
    loadLatest,
    loadVersion,
    editVersion,
    validateVersion,
    generateNew,
    setSrs,
    setCurrentVersionId,
  };
}