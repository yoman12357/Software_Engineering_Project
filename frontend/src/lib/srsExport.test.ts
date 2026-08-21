import { describe, expect, it } from "vitest";

import { SAMPLE_SRS } from "../test/fixtures";
import { srsToMarkdown } from "./srsExport";

describe("srsToMarkdown", () => {
  it("renders canonical metadata and requirement identifiers", () => {
    const markdown = srsToMarkdown(SAMPLE_SRS);
    expect(markdown).toContain("# Campus Firewall");
    expect(markdown).toContain("## Functional Requirements");
    expect(markdown).toContain("### FR-001: Traffic Filtering");
    expect(markdown).toContain("Acceptance criteria");
  });
});
