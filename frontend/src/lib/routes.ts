export type AppRoute =
  | { kind: "root" }
  | { kind: "new-chat" }
  | { kind: "dashboard" }
  | { kind: "settings" }
  | { kind: "chat"; sessionId: string }
  | { kind: "project"; projectId: string }
  | { kind: "srs"; projectId: string; versionId: string; edit: boolean }
  | { kind: "legacy-srs"; versionId: string; edit: boolean };

/** Return the application route without the leading hash or slash. */
export function normalizeHash(hash: string = window.location.hash): string {
  return hash.replace(/^#/, "").replace(/^\/+/, "").replace(/\/+$/, "");
}

function decodeSegment(segment: string): string {
  try {
    return decodeURIComponent(segment);
  } catch {
    return segment;
  }
}

/** Parse a hash route into a deterministic, typed representation. */
export function parseHashRoute(hash: string = window.location.hash): AppRoute {
  const normalized = normalizeHash(hash);
  if (!normalized) return { kind: "root" };
  if (normalized === "new") return { kind: "new-chat" };
  if (normalized === "dashboard") return { kind: "dashboard" };
  if (normalized === "settings") return { kind: "settings" };

  const segments = normalized.split("/");
  if (segments.length === 2 && segments[0] === "chat" && segments[1]) {
    return { kind: "chat", sessionId: decodeSegment(segments[1]) };
  }

  if (
    (segments.length === 4 || segments.length === 5) &&
    segments[0] === "projects" &&
    segments[1] &&
    segments[2] === "srs" &&
    segments[3] &&
    (segments.length === 4 || segments[4] === "edit")
  ) {
    return {
      kind: "srs",
      projectId: decodeSegment(segments[1]),
      versionId: decodeSegment(segments[3]),
      edit: segments[4] === "edit",
    };
  }

  if (
    (segments.length === 2 || segments.length === 3) &&
    segments[0] === "srs" &&
    segments[1] &&
    (segments.length === 2 || segments[2] === "edit")
  ) {
    return {
      kind: "legacy-srs",
      versionId: decodeSegment(segments[1]),
      edit: segments[2] === "edit",
    };
  }

  return { kind: "project", projectId: decodeSegment(normalized) };
}

/** Build the canonical route for viewing or editing one SRS version. */
export function buildSrsRoute(
  projectId: string,
  versionId: string,
  edit = false,
): string {
  const suffix = edit ? "/edit" : "";
  return `projects/${encodeURIComponent(projectId)}/srs/${encodeURIComponent(versionId)}${suffix}`;
}
