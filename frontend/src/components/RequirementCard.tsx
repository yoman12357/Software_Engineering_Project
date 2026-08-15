import { useState } from "react";
import type { Requirement } from "../api/types";

interface RequirementCardProps {
  requirement: Requirement;
  onSave: (field: string, value: string) => Promise<void>;
}

export function RequirementCard({ requirement, onSave }: RequirementCardProps) {
  const [editingField, setEditingField] = useState<string | null>(null);
  const [draft, setDraft] = useState("");
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function beginEdit(field: string, currentValue: string) {
    setEditingField(field);
    setDraft(currentValue);
    setSaved(false);
    setError(null);
  }

  async function saveEdit() {
    if (editingField === null) return;
    setSaving(true);
    setError(null);
    try {
      await onSave(editingField, draft);
      setSaved(true);
      setEditingField(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save.");
    } finally {
      setSaving(false);
    }
  }

  function cancelEdit() {
    setEditingField(null);
    setDraft("");
    setError(null);
  }

  return (
    <article className="requirement" data-testid={`requirement-${requirement.id}`}>
      <h3>
        {requirement.id}
        <span className={`badge ${requirement.priority}`}>{requirement.priority}</span>
        {requirement.user_confirmed ? <span className="badge">confirmed</span> : null}
      </h3>

      {editingField === "title" ? (
        <>
          <input
            type="text"
            value={draft}
            onChange={(event) => setDraft(event.target.value)}
            aria-label="Title"
          />
          <div className="actions">
            <button type="button" className="primary" onClick={saveEdit} disabled={saving}>
              {saving ? "Saving…" : "Save"}
            </button>
            <button type="button" onClick={cancelEdit} disabled={saving}>
              Cancel
            </button>
          </div>
        </>
      ) : (
        <>
          <div>
            <strong>{requirement.title}</strong>
            <button type="button" onClick={() => beginEdit("title", requirement.title)}>
              Edit
            </button>
          </div>

          {editingField === "statement" ? (
            <>
              <textarea value={draft} onChange={(event) => setDraft(event.target.value)} aria-label="Statement" />
              <div className="actions">
                <button type="button" className="primary" onClick={saveEdit} disabled={saving}>
                  {saving ? "Saving…" : "Save"}
                </button>
                <button type="button" onClick={cancelEdit} disabled={saving}>
                  Cancel
                </button>
              </div>
            </>
          ) : (
            <>
              <p>
                {requirement.statement}
                <button type="button" onClick={() => beginEdit("statement", requirement.statement)}>
                  Edit
                </button>
              </p>

              {editingField === "acceptance_criteria" ? (
                <>
                  <textarea
                    value={draft}
                    onChange={(event) => setDraft(event.target.value)}
                    aria-label="Acceptance criteria"
                  />
                  <div className="actions">
                    <button type="button" className="primary" onClick={saveEdit} disabled={saving}>
                      {saving ? "Saving…" : "Save"}
                    </button>
                    <button type="button" onClick={cancelEdit} disabled={saving}>
                      Cancel
                    </button>
                  </div>
                </>
              ) : (
                <>
                  <p className="meta">
                    <strong>Rationale:</strong> {requirement.rationale}
                  </p>
                  <p className="meta">
                    <strong>Acceptance criteria:</strong> {requirement.acceptance_criteria}
                    <button type="button" onClick={() => beginEdit("acceptance_criteria", requirement.acceptance_criteria)}>
                      Edit
                    </button>
                  </p>
                </>
              )}
            </>
          )}
        </>
      )}

      {saved ? <span className="saved-note">Saved</span> : null}
      {error ? <span className="error-note">{error}</span> : null}
    </article>
  );
}