"""
services/wiring_service.py
Uses the circuit_engine (ported from circuit-generator) to produce real
schematic + breadboard SVG diagrams for every project.
"""
from database.models import Project
from circuit_engine.bridge import build_circuit_for_project


class WiringService:

    @classmethod
    def generate_svg(cls, project_id: str, view_mode: str = "breadboard") -> dict:
        """
        Generate a circuit diagram for the given project.

        Returns a dict with:
            project_id, project_name, view_mode, svg,
            valid, checks, components_used, connection_count
        """
        project = Project.query.filter_by(id=project_id).first()
        if not project:
            return {"error": f"Project '{project_id}' not found"}

        try:
            result = build_circuit_for_project(project)
        except Exception as exc:
            return {"error": f"Circuit engine error: {exc}"}

        svg = result["svg_schematic"] if view_mode == "schematic" else result["svg_breadboard"]

        return {
            "project_id":       project.id,
            "project_name":     project.name,
            "view_mode":        view_mode,
            "svg":              svg,
            "valid":            result["valid"],
            "checks":           result["checks"],
            "components_used":  result["components_used"],
            "connection_count": svg.count('<path') + svg.count('<line'),
        }

    @classmethod
    def generate_both_views(cls, project_id: str) -> dict:
        """
        Return schematic + breadboard SVG and validation in one call.
        Used by the /api/wiring/both endpoint.
        """
        project = Project.query.filter_by(id=project_id).first()
        if not project:
            return {"error": f"Project '{project_id}' not found"}

        try:
            result = build_circuit_for_project(project)
        except Exception as exc:
            return {"error": f"Circuit engine error: {exc}"}

        return {
            "project_id":        project.id,
            "project_name":      project.name,
            "svg_schematic":     result["svg_schematic"],
            "svg_breadboard":    result["svg_breadboard"],
            "valid":             result["valid"],
            "checks":            result["checks"],
            "components_used":   result["components_used"],
        }
