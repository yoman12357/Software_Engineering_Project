import type { Requirement, SRSSchema } from "../api/types";
import { AcceptanceCriteriaList } from "./AcceptanceCriteriaList";
import { SRSSection } from "./SRSSection";

interface SRSViewProps {
  srs: SRSSchema;
  onSaveRequirement: (
    section: string,
    requirement: Requirement,
    field: string,
    value: string,
  ) => Promise<void>;
}

export function SRSView({ srs, onSaveRequirement }: SRSViewProps) {
  const allRequirements = [
    ...srs.functional_requirements,
    ...srs.non_functional_requirements,
    ...srs.security_requirements,
  ];

  return (
    <section className="card" aria-label="SRS">
      <h2>
        Software Requirements Specification
        <span className="badge">v{srs.metadata.version}</span>
      </h2>
      <p className="meta">
        Generated at {new Date(srs.metadata.generated_at).toLocaleString()} by{" "}
        {srs.metadata.model_name}
      </p>

      <SRSSection
        title="Functional Requirements"
        requirements={srs.functional_requirements}
        onSaveRequirement={onSaveRequirement}
      />
      <SRSSection
        title="Non-Functional Requirements"
        requirements={srs.non_functional_requirements}
        onSaveRequirement={onSaveRequirement}
      />
      <SRSSection
        title="Security Requirements"
        requirements={srs.security_requirements}
        onSaveRequirement={onSaveRequirement}
      />

      <section className="card">
        <h2>Acceptance Criteria</h2>
        <AcceptanceCriteriaList requirements={allRequirements} />
      </section>
    </section>
  );
}