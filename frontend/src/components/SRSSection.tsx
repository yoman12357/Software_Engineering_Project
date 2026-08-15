import type { Requirement } from "../api/types";
import { RequirementCard } from "./RequirementCard";

interface SRSSectionProps {
  title: string;
  requirements: Requirement[];
  onSaveRequirement: (
    section: string,
    requirement: Requirement,
    field: string,
    value: string,
  ) => Promise<void>;
}

export function SRSSection({ title, requirements, onSaveRequirement }: SRSSectionProps) {
  if (requirements.length === 0) {
    return (
      <section className="card">
        <h2>{title}</h2>
        <p className="empty-state">No requirements in this section.</p>
      </section>
    );
  }

  return (
    <section className="card">
      <h2>{title}</h2>
      {requirements.map((requirement) => (
        <RequirementCard
          key={requirement.id}
          requirement={requirement}
          onSave={(field, value) => onSaveRequirement(sectionName(title), requirement, field, value)}
        />
      ))}
    </section>
  );
}

// Map a display title to the backend section key.
const SECTION_KEYS: Record<string, string> = {
  "Functional Requirements": "functional_requirements",
  "Non-Functional Requirements": "non_functional_requirements",
  "Security Requirements": "security_requirements",
  "Data Requirements": "data_requirements",
  "Network Requirements": "network_requirements",
};

function sectionName(title: string): string {
  return SECTION_KEYS[title] ?? title;
}