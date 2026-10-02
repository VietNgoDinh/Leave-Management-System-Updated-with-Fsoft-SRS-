"""Access to tools/schemas/*.yaml and ba-ai/workflow/workflow.yaml."""
from __future__ import annotations

import re
from functools import lru_cache
from typing import Dict, List, Optional

from . import paths, store


@lru_cache(None)
def catalogs() -> dict:
    return store.load_yaml(paths.SCHEMAS / "catalogs.yaml")["catalogs"]


@lru_cache(None)
def artifacts() -> dict:
    return store.load_yaml(paths.SCHEMAS / "artifacts.yaml")


def artifact_type(name: str) -> Optional[dict]:
    return artifacts()["artifact_types"].get(name)


def enum(name: str) -> List[str]:
    return artifacts()["enums"][name]


def relation_edges() -> dict:
    return artifacts()["relation_edges"]


# ------------------------------------------------------------------ catalog prefixes

def catalog_prefixes(cname: str) -> List[str]:
    """Every ID prefix a catalog uses: one, or one per type for the message catalog (D-52)."""
    cdef = catalogs()[cname]
    pb = cdef.get("prefix_by")
    if pb:
        return list(dict.fromkeys(pb["prefixes"].values()))
    return [cdef["prefix"]]


def prefix_for_item(cname: str, item: dict) -> Optional[str]:
    """The prefix a new item gets. None when it depends on a field the item does not set correctly."""
    cdef = catalogs()[cname]
    pb = cdef.get("prefix_by")
    if pb:
        return pb["prefixes"].get(item.get(pb["field"]))
    return cdef["prefix"]


def catalog_of_prefix(prefix: str) -> Optional[str]:
    for name in catalogs():
        if prefix in catalog_prefixes(name):
            return name
    return None


# ------------------------------------------------------------------ workflow

@lru_cache(None)
def workflow() -> dict:
    return store.load_yaml(paths.WORKFLOW_YAML)


def gate(gate_id: str) -> Optional[dict]:
    return workflow()["gates"].get(gate_id)


def engine() -> dict:
    return workflow()["use_case_engine"]


def engine_steps() -> List[dict]:
    """Per-use-case steps that produce an artifact (5.2–5.8, 7, 8.1, 8.2, 9)."""
    return [s for s in engine()["steps"] if s.get("artifact_type")]


def uc_steps() -> List[dict]:
    """Per-use-case steps the engine walks: those with an artifact or a gate (5.1 is the orchestrator's)."""
    return [s for s in engine()["steps"] if s.get("artifact_type") or s.get("gate")]


def ui_gates() -> List[str]:
    """Gates that belong to the UI steps, which a system use case skips (D-57)."""
    return [s["gate"] for s in engine()["steps"] if s.get("ui") and s.get("gate")]


def ui_artifact_types() -> List[str]:
    return [s["artifact_type"] for s in engine()["steps"] if s.get("ui") and s.get("artifact_type")]


def step_for_type(artifact_type_name: str) -> Optional[dict]:
    for s in engine_steps():
        if s["artifact_type"] == artifact_type_name:
            return s
    return None


def run_steps() -> dict:
    return workflow().get("run_steps") or {}


def run_step(step_id: str) -> Optional[dict]:
    return run_steps().get(step_id)


def optional_input(entry: str):
    """'input-management/meeting-minutes/?' → ('input-management/meeting-minutes/', True)."""
    return (entry[:-1], True) if entry.endswith("?") else (entry, False)


def per_item_placeholder(cname: str) -> str:
    """{BP} for business processes, {APP} for applications: the catalog's prefix."""
    return "{" + catalog_prefixes(cname)[0] + "}"


def per_item_regex(path_template: str, cname: str) -> str:
    ph = per_item_placeholder(cname)
    prefix = catalog_prefixes(cname)[0]
    return "^" + re.escape(path_template).replace(re.escape(ph), "(" + prefix + r"-\d{3,4})") + "$"


def run_output_for(rel: str) -> Optional[dict]:
    """The run-step output definition (path + built_from) that produces document `rel`."""
    for sid, sdef in run_steps().items():
        for out in sdef.get("outputs") or []:
            if out["path"] == rel:
                return {"step": sid, **out}
        for pi in sdef.get("per_item") or []:
            m = re.match(per_item_regex(pi["path"], pi["catalog"]), rel)
            if m:
                return {"step": sid, "path": rel, "item": m.group(1), "catalog": pi["catalog"],
                        "built_from": pi.get("built_from", [])}
    return None


def run_step_for_folder(rel_folder: str) -> Optional[str]:
    """The run step whose outputs live under a folder (a gate may review a whole folder)."""
    for sid, sdef in run_steps().items():
        outs = [o["path"] for o in sdef.get("outputs") or []] + [p["path"] for p in sdef.get("per_item") or []]
        if any(o.startswith(rel_folder) for o in outs):
            return sid
    return None


def gate_required(gate_id: str, uc_item: Optional[dict]) -> bool:
    """D-23: GATE-07 applies only to risky use cases; every other gate always applies.
    (The UI gates of a system use case are decided by the engine, which knows the screens, D-57.)"""
    g = gate(gate_id) or {}
    if g.get("required_when") == "risk":
        item = uc_item or {}
        return item.get("risk_level") in ("HIGH", "CRITICAL") or bool(item.get("risk_flags"))
    return True


def catalog_for_path(rel: str) -> Optional[str]:
    for name, c in catalogs().items():
        if c["path"] == rel:
            return name
    return None


def nfr_sections() -> Dict[str, List[str]]:
    """The company SRS's Non-Functional Requirements sections and the categories each one holds (D-54)."""
    return {
        "Performance Requirements": ["PERFORMANCE", "SCALABILITY", "PLATFORM"],
        "Safety Requirements": ["SAFETY"],
        "Security Requirements": ["SECURITY"],
        "Software Quality Attributes": ["USABILITY", "ACCESSIBILITY", "INTERNATIONALISATION", "AVAILABILITY",
                                        "RELIABILITY", "ACCURACY", "COMPLIANCE", "CONSTRAINT"],
    }
