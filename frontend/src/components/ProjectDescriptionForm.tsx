import { useState, type FormEvent } from "react";

interface ProjectDescriptionFormProps {
  disabled?: boolean;
  onSubmit: (name: string, description: string) => void | Promise<void>;
}

export function ProjectDescriptionForm({
  disabled = false,
  onSubmit,
}: ProjectDescriptionFormProps) {
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const canSubmit = name.trim().length > 0 && description.trim().length >= 10;

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (!canSubmit) {
      setError("Project name is required and the description must be at least 10 characters.");
      return;
    }
    setError(null);
    setSubmitting(true);
    try {
      await onSubmit(name.trim(), description.trim());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create the project.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="card">
      <h2>Create a project</h2>
      <p>Enter a project name and an informal description of the cybersecurity system.</p>

      <label htmlFor="project-name">Project name</label>
      <input
        id="project-name"
        type="text"
        value={name}
        onChange={(event) => setName(event.target.value)}
        placeholder="e.g., Campus Firewall"
        disabled={disabled || submitting}
      />

      <label htmlFor="project-description">Informal description</label>
      <textarea
        id="project-description"
        value={description}
        onChange={(event) => setDescription(event.target.value)}
        placeholder="e.g., I want to build a firewall and network-monitoring system for my college campus."
        disabled={disabled || submitting}
      />

      {error ? <p className="error-note">{error}</p> : null}

      <button
        type="submit"
        className="primary"
        disabled={disabled || submitting || !canSubmit}
      >
        {submitting ? "Creating…" : "Create project"}
      </button>
    </form>
  );
}