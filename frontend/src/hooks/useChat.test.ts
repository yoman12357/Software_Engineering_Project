import { describe, expect, it } from "vitest";

import { SAMPLE_CLARIFICATIONS } from "../test/fixtures";
import { createProjectName, parseClarificationAnswers } from "./useChat";

describe("createProjectName", () => {
  it("uses an explicitly declared project name", () => {
    expect(
      createProjectName("Generate an SRS for a cybersecurity project called VaultGate."),
    ).toBe("VaultGate");
  });
});

describe("parseClarificationAnswers", () => {
  it("maps numbered lines to the displayed question IDs", () => {
    expect(
      parseClarificationAnswers(
        "1. 500 nodes\n2. GDPR and ISO 27001",
        SAMPLE_CLARIFICATIONS.questions,
      ),
    ).toEqual([
      { question_id: "q-001", answer_text: "500 nodes", skipped: false },
      { question_id: "q-002", answer_text: "GDPR and ISO 27001", skipped: false },
    ]);
  });

  it("supports verbose Question and Answer formatting", () => {
    const answers = parseClarificationAnswers(
      "Question 1: How many? Answer: 250\nQuestion 2: Compliance? Answer: HIPAA",
      SAMPLE_CLARIFICATIONS.questions,
    );
    expect(answers?.map((answer) => answer.answer_text)).toEqual(["250", "HIPAA"]);
  });

  it("rejects an ambiguous unnumbered response for multiple questions", () => {
    expect(
      parseClarificationAnswers("About five hundred", SAMPLE_CLARIFICATIONS.questions),
    ).toBeNull();
  });
});
