"""ReportRenderer — render report_data + narrative into HTML via Jinja2."""
from __future__ import annotations

import argparse
import json
import logging
import os
from datetime import datetime

from jinja2 import Environment, FileSystemLoader, select_autoescape

logger = logging.getLogger(__name__)


class ReportRenderer:
    """Render factor report HTML from report_data.json and narrative.json."""

    def __init__(self):
        template_dir = os.path.join(os.path.dirname(__file__), "templates")
        self._env = Environment(
            loader=FileSystemLoader(template_dir),
            autoescape=select_autoescape(default=True),
        )

    def render(self, report_data: dict, narrative: dict) -> str:
        """Render HTML string from data and narrative dicts."""
        template = self._env.get_template("factor_report.html.j2")
        ctx = {
            "factor": report_data.get("factor", {}),
            "preprocessing": report_data.get("preprocessing", {}),
            "kpi": report_data.get("kpi", {}),
            "distribution": report_data.get("distribution", {}),
            "ic_analysis": report_data.get("ic_analysis", {}),
            "quintile": report_data.get("quintile", {}),
            "decay": report_data.get("decay", {}),
            "scores": report_data.get("scores", {}),
            "narrative": narrative,
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        return template.render(**ctx)

    def render_to_file(self, report_data: dict, narrative: dict, output_dir: str, factor_id: str) -> str:
        """Render and save HTML to output_dir/factor_{id}_report.html."""
        os.makedirs(output_dir, exist_ok=True)
        html = self.render(report_data, narrative)
        path = os.path.join(output_dir, f"factor_{factor_id}_report.html")
        with open(path, "w", encoding="utf-8") as f:
            f.write(html)
        logger.info("Report saved to %s", path)
        return path


def main():
    parser = argparse.ArgumentParser(description="Render factor report HTML")
    parser.add_argument("--input-dir", required=True, help="Dir containing report_data.json and narrative.json")
    parser.add_argument("--output-dir", required=True, help="Dir to save HTML report")
    args = parser.parse_args()

    with open(os.path.join(args.input_dir, "report_data.json"), encoding="utf-8") as f:
        report_data = json.load(f)
    with open(os.path.join(args.input_dir, "narrative.json"), encoding="utf-8") as f:
        narrative = json.load(f)

    factor_id = report_data["factor"]["id"]
    renderer = ReportRenderer()
    path = renderer.render_to_file(report_data, narrative, args.output_dir, factor_id)
    print(f"Report: {path}")


if __name__ == "__main__":
    main()
