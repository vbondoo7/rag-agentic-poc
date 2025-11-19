# ai_agents/utils.py
import logging
import sys
from datetime import datetime
import json
from typing import Any

def setup_logging(logfile: str = "agentic_app.log"):
    logger = logging.getLogger()
    if logger.handlers:
        return
    logger.setLevel(logging.INFO)
    fmt = logging.Formatter("%(asctime)s %(levelname)s [%(name)s] %(message)s")
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    ch.setFormatter(fmt)
    logger.addHandler(ch)
    try:
        fh = logging.FileHandler(logfile)
        fh.setLevel(logging.INFO)
        fh.setFormatter(fmt)
        logger.addHandler(fh)
    except Exception:
        logger.warning("Cannot create file log handler for %s", logfile)

def extract_vrom(answer: str) -> str:
    for size in ["XS", "S", "M", "L", "XL", "XXL"]:
        if "T-shirt size" in answer and size in answer:
            return size
    n_words = len(answer.split())
    if n_words < 30:
        return "XS"
    if n_words < 80:
        return "S"
    if n_words < 150:
        return "M"
    if n_words < 250:
        return "L"
    if n_words < 350:
        return "XL"
    return "XXL"

def safe_json_load(s: str):
    try:
        return json.loads(s)
    except Exception:
        return None

def to_md_impact(impact_dict: dict, query: str) -> str:
    lines = [f"# Impact Analysis\n\n**Query:** {query}\n\n"]
    for comp in impact_dict.get("components", []):
        lines.append(f"## {comp.get('name')}\n")
        lines.append(f"- **Impact:** {comp.get('impact')}")
        lines.append(f"- **Level:** {comp.get('level')}")
        lines.append(f"- **T-shirt:** {comp.get('tshirt_size')}")
        lines.append(f"- **Justification:** {comp.get('justification')}")
        if comp.get("sources"):
            lines.append("- **Sources:**")
            for s in comp.get("sources", []):
                lines.append(f"  - {s}")
        lines.append("\n")
    return "\n".join(lines)

def to_md_blueprint(bp_dict: dict, query: str) -> str:
    lines = [f"# Solution Blueprint\n\n**Query:** {query}\n\n"]
    sol = bp_dict.get("solution", {})
    for module in sol.get("modules", []):
        lines.append(f"## {module.get('name')}\n")
        lines.append(f"- **Purpose:** {module.get('purpose')}")
        lines.append(f"- **Pattern:** {module.get('pattern')}")
        lines.append(f"- **T-shirt:** {module.get('tshirt_size')}")
        if module.get("data_flow"):
            lines.append("- **Data flows:**")
            for df in module.get("data_flow", []):
                lines.append(f"  - {df}")
        if module.get("risks"):
            lines.append("- **Risks:**")
            for r in module.get("risks", []):
                lines.append(f"  - {r}")
        lines.append("\n")
    if bp_dict.get("recommendations"):
        lines.append("## Recommendations")
        for r in bp_dict.get("recommendations"):
            lines.append(f"- {r}")
    return "\n".join(lines)
