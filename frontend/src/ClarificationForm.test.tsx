import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { ClarificationForm } from "./components/ClarificationForm";
import { SAMPLE_CLARIFICATIONS } from "./test/fixtures";

const questions = SAMPLE_CLARIFICATIONS.questions;

describe("ClarificationForm", () => {
  it("renders clarification questions with required/optional badges", () => {
    render(<ClarificationForm questions={questions} onSubmit={vi.fn()} />);
    expect(
      screen.getByText("How many network nodes will the firewall protect?"),
    ).toBeInTheDocument();
    expect(
      screen.getByText("Are there specific compliance standards to meet?"),
    ).toBeInTheDocument();
    expect(screen.getByText("Required")).toBeInTheDocument();
    expect(screen.getByText("Optional")).toBeInTheDocument();
  });

  it("blocks submission when a critical question is unanswered", async () => {
    const onSubmit = vi.fn();
    render(<ClarificationForm questions={questions} onSubmit={onSubmit} />);

    await userEvent.click(screen.getByRole("button", { name: "Submit answers" }));

    expect(
      screen.getByText(
        "Please answer all required (critical) questions before continuing.",
      ),
    ).toBeInTheDocument();
    expect(onSubmit).not.toHaveBeenCalled();
  });

  it("submits answers for critical questions and marks empty as skipped", async () => {
    const onSubmit = vi.fn().mockResolvedValue(undefined);
    render(<ClarificationForm questions={questions} onSubmit={onSubmit} />);

    await userEvent.type(
      screen.getByLabelText(/How many network nodes/),
      "500 nodes",
    );
    await userEvent.click(screen.getByRole("button", { name: "Submit answers" }));

    expect(onSubmit).toHaveBeenCalledWith(
      expect.arrayContaining([
        expect.objectContaining({ question_id: "q-001", answer_text: "500 nodes", skipped: false }),
        expect.objectContaining({ question_id: "q-002", answer_text: "", skipped: true }),
      ]),
    );
  });

  it("shows an error when submission fails", async () => {
    const onSubmit = vi
      .fn()
      .mockRejectedValue(new Error("A clarification question can only be answered once."));
    render(<ClarificationForm questions={questions} onSubmit={onSubmit} />);

    await userEvent.type(
      screen.getByLabelText(/How many network nodes/),
      "500 nodes",
    );
    await userEvent.click(screen.getByRole("button", { name: "Submit answers" }));

    await screen.findByText("A clarification question can only be answered once.");
  });
});