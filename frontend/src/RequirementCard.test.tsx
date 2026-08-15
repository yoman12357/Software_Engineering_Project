import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { RequirementCard } from "./components/RequirementCard";
import { SAMPLE_SRS } from "./test/fixtures";

const requirement = SAMPLE_SRS.functional_requirements[0];

describe("RequirementCard", () => {
  it("renders the requirement details", () => {
    render(<RequirementCard requirement={requirement} onSave={vi.fn()} />);
    expect(screen.getByText("FR-001")).toBeInTheDocument();
    expect(screen.getByText("Traffic Filtering")).toBeInTheDocument();
    expect(
      screen.getByText(
        "The system shall filter inbound and outbound traffic by default.",
      ),
    ).toBeInTheDocument();
    expect(screen.getByText("Verify denied traffic is blocked.")).toBeInTheDocument();
  });

  it("edits the statement and saves through the callback", async () => {
    const onSave = vi.fn().mockResolvedValue(undefined);
    render(<RequirementCard requirement={requirement} onSave={onSave} />);

    // Click the "Edit" button next to the statement.
    const editButtons = screen.getAllByRole("button", { name: "Edit" });
    await userEvent.click(editButtons[1]);

    const statementTextarea = screen.getByLabelText("Statement");
    await userEvent.clear(statementTextarea);
    await userEvent.type(
      statementTextarea,
      "The system shall filter all inbound traffic by default.",
    );

    await userEvent.click(screen.getByRole("button", { name: "Save" }));

    expect(onSave).toHaveBeenCalledWith(
      "statement",
      "The system shall filter all inbound traffic by default.",
    );
    await screen.findByText("Saved");
  });

  it("shows an error when saving fails", async () => {
    const onSave = vi
      .fn()
      .mockRejectedValue(new Error("The requirement statement is invalid."));
    render(<RequirementCard requirement={requirement} onSave={onSave} />);

    const editButtons = screen.getAllByRole("button", { name: "Edit" });
    await userEvent.click(editButtons[1]);

    await userEvent.clear(screen.getByLabelText("Statement"));
    await userEvent.type(screen.getByLabelText("Statement"), "Invalid");
    await userEvent.click(screen.getByRole("button", { name: "Save" }));

    await screen.findByText("The requirement statement is invalid.");
  });
});