import { describe, expect, it } from "vitest";

import { buildSrsRoute, normalizeHash, parseHashRoute } from "./routes";

describe("hash routes", () => {
  it("normalizes leading and trailing route separators", () => {
    expect(normalizeHash("#/chat/session-1/")).toBe("chat/session-1");
  });

  it("parses the canonical SRS viewer and editor routes", () => {
    expect(parseHashRoute("#projects/project-1/srs/version-2")).toEqual({
      kind: "srs",
      projectId: "project-1",
      versionId: "version-2",
      edit: false,
    });
    expect(parseHashRoute("#/projects/project-1/srs/version-2/edit")).toEqual({
      kind: "srs",
      projectId: "project-1",
      versionId: "version-2",
      edit: true,
    });
  });

  it("keeps legacy SRS links distinguishable for migration", () => {
    expect(parseHashRoute("#srs/version-2/edit")).toEqual({
      kind: "legacy-srs",
      versionId: "version-2",
      edit: true,
    });
  });

  it("builds encoded canonical SRS routes", () => {
    expect(buildSrsRoute("project one", "version/two", true)).toBe(
      "projects/project%20one/srs/version%2Ftwo/edit",
    );
  });

  it("parses chat, project, and static routes", () => {
    expect(parseHashRoute("#chat/chat-1")).toEqual({ kind: "chat", sessionId: "chat-1" });
    expect(parseHashRoute("#project-1")).toEqual({ kind: "project", projectId: "project-1" });
    expect(parseHashRoute("#new")).toEqual({ kind: "new-chat" });
    expect(parseHashRoute("#dashboard")).toEqual({ kind: "dashboard" });
    expect(parseHashRoute("#settings")).toEqual({ kind: "settings" });
  });
});
