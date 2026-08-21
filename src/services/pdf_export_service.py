"""Deterministic PDF export for SRS versions (Phase 1C, FR-067).

Renders the validated structured SRS JSON into a professional, template-based
PDF. Rendering is 100% deterministic Python (ADR-0003): the SRS JSON is the
canonical representation and this module only lays it out.

The export is recorded in the ``exported_document`` table so each download is
traceable (DATA_MODEL §2.15).
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from io import BytesIO
from typing import Any

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    HRFlowable,
    ListFlowable,
    ListItem,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from ..core.config import Settings
from ..core.exceptions import SRSVersionNotFoundError
from ..db.models import ExportedDocument
from ..repositories.srs_repository import SRSVersionRepository

# --- PDF styling -------------------------------------------------------------

_ACCENT = colors.HexColor("#1a5276")
_ACCENT_LIGHT = colors.HexColor("#eaf2f8")
_TEXT = colors.HexColor("#1c2833")
_MUTED = colors.HexColor("#5d6d7e")


def _styles() -> dict[str, ParagraphStyle]:
    """Build the set of paragraph styles used across the PDF."""
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "SRS_Title",
            parent=base["Title"],
            fontSize=24,
            leading=28,
            textColor=_ACCENT,
            spaceAfter=6,
        ),
        "subtitle": ParagraphStyle(
            "SRS_Subtitle",
            parent=base["Normal"],
            fontSize=11,
            leading=14,
            textColor=_MUTED,
            spaceAfter=2,
        ),
        "h1": ParagraphStyle(
            "SRS_H1",
            parent=base["Heading1"],
            fontSize=16,
            leading=20,
            textColor=_ACCENT,
            spaceBefore=18,
            spaceAfter=6,
        ),
        "h2": ParagraphStyle(
            "SRS_H2",
            parent=base["Heading2"],
            fontSize=13,
            leading=16,
            textColor=colors.HexColor("#154360"),
            spaceBefore=12,
            spaceAfter=4,
        ),
        "body": ParagraphStyle(
            "SRS_Body",
            parent=base["Normal"],
            fontSize=9.5,
            leading=13,
            textColor=_TEXT,
            alignment=TA_LEFT,
        ),
        "small": ParagraphStyle(
            "SRS_Small",
            parent=base["Normal"],
            fontSize=8,
            leading=11,
            textColor=_MUTED,
        ),
        "req_title": ParagraphStyle(
            "SRS_ReqTitle",
            parent=base["Normal"],
            fontSize=10,
            leading=13,
            textColor=_ACCENT,
            spaceBefore=8,
            spaceAfter=2,
        ),
        "cell": ParagraphStyle(
            "SRS_Cell",
            parent=base["Normal"],
            fontSize=8.5,
            leading=11,
            textColor=_TEXT,
        ),
    }


def _esc(text: Any) -> str:
    """Coerce a value to a safe PDF/XML string."""
    if text is None:
        return ""
    return str(text)


class PDFExportService:
    """Generates and persists PDF exports of SRS versions."""

    def __init__(self, session: Any, settings: Settings) -> None:
        """Initialize the export service.

        Args:
            session: SQLAlchemy session bound to the request.
            settings: Application settings (export directory config).
        """
        self._session = session
        self._settings = settings
        self._versions = SRSVersionRepository(session)

    def _version(self, project_id: str, version_id: str) -> Any:
        """Return the SRSVersion row or raise."""
        version = self._versions.get_version(project_id, version_id)
        if version is None:
            raise SRSVersionNotFoundError()
        return version

    def render_pdf_bytes(self, srs_data: dict[str, Any]) -> bytes:
        """Render an SRS JSON document to PDF bytes.

        Args:
            srs_data: The validated ``srs_json`` payload.

        Returns:
            PDF document as bytes.
        """
        st = _styles()
        buffer = BytesIO()

        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=1.8 * cm,
            leftMargin=1.8 * cm,
            topMargin=1.8 * cm,
            bottomMargin=1.8 * cm,
            title=f"SRS - {_esc(srs_data.get('metadata', {}).get('project_name', ''))}",
            author="CyberSRS",
        )

        story: list[Any] = []
        meta = srs_data.get("metadata", {})

        # --- Cover block ---
        default_title = "Software Requirements Specification"
        project_name = _esc(meta.get("project_name", default_title))
        story.append(Paragraph(project_name, st["title"]))
        story.append(Paragraph("Software Requirements Specification", st["subtitle"]))
        story.append(Paragraph(
            f"Version {meta.get('version', 1)} &nbsp;•&nbsp; "
            f"Generated {meta.get('generated_at', '')}",
            st["subtitle"],
        ))
        if meta.get("model_name"):
            story.append(
                Paragraph(f"Generated by {_esc(meta['model_name'])}", st["subtitle"])
            )
        story.append(
            HRFlowable(width="100%", thickness=1.5, color=_ACCENT, spaceBefore=8, spaceAfter=8)
        )

        # --- Overview ---
        overview = srs_data.get("project_overview", {})
        if overview:
            story.append(Paragraph("1. Project Overview", st["h1"]))
            story.append(Paragraph(_esc(overview.get("description", "")), st["body"]))
            if overview.get("purpose"):
                story.append(Paragraph("<b>Purpose:</b> " + _esc(overview["purpose"]), st["body"]))

        # --- Scope ---
        scope = srs_data.get("scope", {})
        if scope:
            story.append(Paragraph("2. Scope", st["h1"]))
            if scope.get("in_scope"):
                story.append(Paragraph("<b>In scope:</b>", st["body"]))
                story.append(self._bullet_list(scope["in_scope"], st))
            if scope.get("out_of_scope"):
                story.append(Paragraph("<b>Out of scope:</b>", st["body"]))
                story.append(self._bullet_list(scope["out_of_scope"], st))

        # --- Stakeholders & roles ---
        if srs_data.get("stakeholders"):
            story.append(Paragraph("3. Stakeholders", st["h1"]))
            story.append(self._bullet_list(srs_data["stakeholders"], st))
        if srs_data.get("user_roles"):
            story.append(Paragraph("4. User Roles", st["h1"]))
            story.append(self._bullet_list(srs_data["user_roles"], st))

        # --- Requirements ---
        self._append_requirements(
            story, st, "5. Functional Requirements",
            srs_data.get("functional_requirements", []),
        )
        self._append_requirements(
            story, st, "6. Non-Functional Requirements",
            srs_data.get("non_functional_requirements", []),
        )
        self._append_requirements(
            story, st, "7. Security Requirements",
            srs_data.get("security_requirements", []),
        )
        self._append_requirements(
            story, st, "8. Data Requirements",
            srs_data.get("data_requirements", []),
        )
        self._append_requirements(
            story, st, "9. Network Requirements",
            srs_data.get("network_requirements", []),
        )

        # --- Architecture ---
        arch = srs_data.get("architecture_summary", {})
        if arch:
            story.append(Paragraph("10. Architecture", st["h1"]))
            story.append(Paragraph(_esc(arch.get("description", "")), st["body"]))
            components = arch.get("components", [])
            if components:
                hdr_comp = Paragraph("<b>Component</b>", st["cell"])
                hdr_resp = Paragraph("<b>Responsibility</b>", st["cell"])
                rows = [[hdr_comp, hdr_resp]]
                for comp in components:
                    rows.append([
                        Paragraph("<b>" + _esc(comp.get("name", "")) + "</b>", st["cell"]),
                        Paragraph(_esc("; ".join(comp.get("responsibilities", []))), st["cell"]),
                    ])
                table = Table(rows, colWidths=[4.5 * cm, 11.5 * cm])
                table.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), _ACCENT),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, _ACCENT_LIGHT]),
                    ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#d5dbdb")),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ]))
                story.append(table)

        # --- Threats & mitigations ---
        threats = srs_data.get("threats", [])
        if threats:
            story.append(Paragraph("11. Threats", st["h1"]))
            hdr_id = Paragraph("<b>ID</b>", st["cell"])
            hdr_threat = Paragraph("<b>Threat</b>", st["cell"])
            hdr_sev = Paragraph("<b>Severity</b>", st["cell"])
            rows = [[hdr_id, hdr_threat, hdr_sev]]
            for threat in threats:
                rows.append([
                    Paragraph(_esc(threat.get("threat_id", "")), st["cell"]),
                    Paragraph(_esc(threat.get("description", "")), st["cell"]),
                    Paragraph(_esc(threat.get("severity", "")), st["cell"]),
                ])
            table = Table(rows, colWidths=[2.2 * cm, 10 * cm, 3 * cm])
            table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), _ACCENT),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, _ACCENT_LIGHT]),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#d5dbdb")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]))
            story.append(table)

        # --- Risks ---
        risks = srs_data.get("risks", [])
        if risks:
            story.append(Paragraph("12. Risks", st["h1"]))
            hdr_risk = Paragraph("<b>Risk</b>", st["cell"])
            hdr_mit = Paragraph("<b>Mitigation</b>", st["cell"])
            hdr_lvl = Paragraph("<b>Level</b>", st["cell"])
            rows = [[hdr_risk, hdr_mit, hdr_lvl]]
            for risk in risks:
                rows.append([
                    Paragraph(_esc(risk.get("description", "")), st["cell"]),
                    Paragraph(_esc(risk.get("mitigation", "")), st["cell"]),
                    Paragraph(_esc(risk.get("risk_level", "")), st["cell"]),
                ])
            table = Table(rows, colWidths=[6 * cm, 7 * cm, 2.5 * cm])
            table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), _ACCENT),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, _ACCENT_LIGHT]),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#d5dbdb")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]))
            story.append(table)

        # --- Assumptions ---
        if srs_data.get("assumptions"):
            story.append(Paragraph("13. Assumptions", st["h1"]))
            story.append(self._bullet_list(srs_data["assumptions"], st))

        # --- References ---
        if srs_data.get("references"):
            story.append(Paragraph("14. References", st["h1"]))
            for ref in srs_data["references"]:
                if isinstance(ref, dict):
                    title = _esc(ref.get("title", ref.get("source_id", "")))
                    story.append(Paragraph(f"• {title}", st["small"]))
                else:
                    story.append(Paragraph(f"• {_esc(ref)}", st["small"]))

        doc.build(story)
        return buffer.getvalue()

    def _bullet_list(self, items: list[Any], st: dict[str, ParagraphStyle]) -> ListFlowable:
        """Render a list of strings/paragraphs as bullets."""
        content = [ListItem(Paragraph(_esc(item), st["body"])) for item in items]
        return ListFlowable(
            content, bulletType="bullet", start="bullet", leftIndent=14, bulletFontSize=8
        )

    def _append_requirements(
        self,
        story: list[Any],
        st: dict[str, ParagraphStyle],
        heading: str,
        requirements: list[dict[str, Any]],
    ) -> None:
        """Append a requirements section with each requirement rendered fully."""
        if not requirements:
            return
        story.append(Paragraph(heading, st["h1"]))
        for req in requirements:
            req_id = _esc(req.get("id", ""))
            title = _esc(req.get("title", ""))
            story.append(Paragraph(
                f"<b>{req_id}</b> &nbsp;—&nbsp; {title}",
                st["req_title"],
            ))
            statement = "<b>Statement:</b> " + _esc(req.get("statement", ""))
            story.append(Paragraph(statement, st["body"]))
            if req.get("rationale"):
                rationale = "<b>Rationale:</b> " + _esc(req["rationale"])
                story.append(Paragraph(rationale, st["body"]))
            if req.get("acceptance_criteria"):
                criteria = "<b>Acceptance criteria:</b> " + _esc(req["acceptance_criteria"])
                story.append(Paragraph(criteria, st["body"]))
            meta_parts = [f"Priority: {_esc(req.get('priority', ''))}"]
            if req.get("confidence"):
                meta_parts.append(f"Confidence: {_esc(req['confidence'])}")
            if req.get("dependencies"):
                meta_parts.append("Depends on: " + ", ".join(_esc(d) for d in req["dependencies"]))
            meta_line = "<b>" + " • ".join(meta_parts) + "</b>"
            story.append(Paragraph(meta_line, st["small"]))
            if req.get("source_references"):
                refs = [
                    _esc(r.get("document_title", r.get("source_id", "")))
                    for r in req["source_references"]
                ]
                story.append(Paragraph("Sources: " + ", ".join(refs), st["small"]))
            story.append(Spacer(1, 4))

    def export_to_pdf(self, project_id: str, version_id: str) -> tuple[bytes, str]:
        """Generate and persist a PDF export for an SRS version.

        Args:
            project_id: Owning project ID.
            version_id: SRS version ID to export.

        Returns:
            A tuple of ``(pdf_bytes, filename)``.

        Raises:
            SRSVersionNotFoundErrorForExport: If the version does not exist.
        """
        version = self._version(project_id, version_id)
        srs_json = version.srs_json
        if not srs_json or not isinstance(srs_json, dict):
            raise SRSVersionNotFoundError()

        pdf_bytes = self.render_pdf_bytes(srs_json)

        # Persist an ExportedDocument record
        filename = self._filename(project_id, version)
        record = ExportedDocument(
            id=str(uuid.uuid4()),
            srs_version_id=version.id,
            file_path=f"exports/{filename}",
            file_size_bytes=len(pdf_bytes),
            exported_at=datetime.now(UTC),
        )
        self._session.add(record)
        self._session.commit()

        return pdf_bytes, filename

    @staticmethod
    def _filename(project_id: str, version: Any) -> str:
        """Build a stable, sortable export filename."""
        safe_project = "".join(c for c in project_id if c.isalnum())[:12] or "project"
        return f"srs_{safe_project}_v{version.version_number}.pdf"
