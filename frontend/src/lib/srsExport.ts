import type { Requirement, SRSSchema } from "../api/types";

function requirementMarkdown(requirement: Requirement): string {
  return [
    `### ${requirement.id}: ${requirement.title}`,
    "",
    requirement.statement,
    "",
    `- Priority: ${requirement.priority}`,
    `- Rationale: ${requirement.rationale}`,
    `- Acceptance criteria: ${requirement.acceptance_criteria}`,
  ].join("\n");
}

/** Render validated canonical SRS JSON as deterministic Markdown. */
export function srsToMarkdown(srs: SRSSchema): string {
  const sections: Array<[string, Requirement[]]> = [
    ["Functional Requirements", srs.functional_requirements],
    ["Non-Functional Requirements", srs.non_functional_requirements],
    ["Security Requirements", srs.security_requirements],
    ["Data Requirements", srs.data_requirements],
    ["Network Requirements", srs.network_requirements],
  ];
  const requirements = sections
    .map(([title, items]) => `## ${title}\n\n${items.map(requirementMarkdown).join("\n\n")}`)
    .join("\n\n");
  return [
    `# ${srs.metadata.project_name}`,
    "",
    `Version ${srs.metadata.version}`,
    "",
    "## Project Overview",
    "",
    srs.project_overview.description,
    "",
    requirements,
    "",
    "## Architecture",
    "",
    srs.architecture_summary.overview,
  ].join("\n");
}

/** Download deterministic text content without contacting an external service. */
export function downloadTextFile(content: string, filename: string, mediaType: string): void {
  const url = URL.createObjectURL(new Blob([content], { type: mediaType }));
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}
