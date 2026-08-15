import type { ProjectAnalysis } from "../api/types";

interface ProjectContextViewProps {
  analysis: ProjectAnalysis;
}

function StringList({ items }: { items: string[] }) {
  if (!items || items.length === 0) {
    return <p className="empty-state">None identified.</p>;
  }
  return (
    <ul className="list-inline">
      {items.map((item) => (
        <li key={item}>{item}</li>
      ))}
    </ul>
  );
}

export function ProjectContextView({ analysis }: ProjectContextViewProps) {
  return (
    <section className="card" aria-label="Project context">
      <h2>Project Analysis</h2>
      <p>{analysis.project_summary}</p>

      <div>
        <strong>Inferred subdomain</strong>
        <div>
          {analysis.inferred_categories.map((category) => (
            <span className="tag" key={category}>
              {category}
            </span>
          ))}
        </div>
      </div>

      <h3>Stakeholders</h3>
      <StringList items={analysis.stakeholders} />

      <h3>Assets</h3>
      <StringList items={analysis.assets} />

      <h3>User roles</h3>
      <StringList items={analysis.users} />

      <h3>Constraints</h3>
      <StringList items={analysis.constraints} />

      <h3>Goals</h3>
      <StringList items={analysis.goals} />
    </section>
  );
}