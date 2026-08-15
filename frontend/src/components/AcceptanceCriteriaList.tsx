import type { Requirement } from "../api/types";

interface AcceptanceCriteriaListProps {
  requirements: Requirement[];
}

export function AcceptanceCriteriaList({ requirements }: AcceptanceCriteriaListProps) {
  if (requirements.length === 0) {
    return <p className="empty-state">No acceptance criteria available.</p>;
  }
  return (
    <ul>
      {requirements.map((requirement) => (
        <li key={requirement.id}>
          <strong>{requirement.id}:</strong> {requirement.acceptance_criteria}
        </li>
      ))}
    </ul>
  );
}