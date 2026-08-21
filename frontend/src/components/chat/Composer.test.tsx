import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { Composer } from "./Composer";

describe("Composer attachments", () => {
  it("selects and removes supported project files", () => {
    const onFilesSelected = vi.fn();
    const onRemoveAttachment = vi.fn();
    const file = new File(["requirements"], "scope.md", { type: "text/markdown" });
    const { container, rerender } = render(
      <Composer onSend={vi.fn()} onFilesSelected={onFilesSelected} />,
    );
    const input = container.querySelector('input[type="file"]') as HTMLInputElement;
    fireEvent.change(input, { target: { files: [file] } });
    expect(onFilesSelected).toHaveBeenCalledWith([file]);

    rerender(
      <Composer
        onSend={vi.fn()}
        attachments={[file]}
        onFilesSelected={onFilesSelected}
        onRemoveAttachment={onRemoveAttachment}
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: "Remove scope.md" }));
    expect(onRemoveAttachment).toHaveBeenCalledWith(0);
  });
});
