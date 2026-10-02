"""`tools/ba migrate` — move a workspace from the milestone-2 layout to the company SRS layout (addendum D-63).

It moves the BA files to the company folders, rewrites the paths recorded in documents (`built_from`, and
`ba-ai/...` mentions in frontmatter and text), removes the old generated views (`tools/ba sync` writes them
again at their new place) and the placeholder folders the company layout drops (R4). It never touches
`reviews/`: gate requests and decisions are records of what was reviewed, under the paths of the time.

Approvals do not survive the move, because gate decisions are keyed by path (gates.py is protected, D-36).
For a workspace whose gated artifacts change content anyway (D-46 – D-58 change every one of them), nothing
is lost: the BA re-approves the regenerated artifacts. Running it twice is harmless.
"""
from __future__ import annotations

import os
import re
import shutil
from pathlib import Path
from typing import Dict, List, Tuple

from . import paths, store
from .ids import as_list

# old path (relative to ba-ai/) → new path; a trailing / moves a folder's content. Order matters: specific first.
PATH_MAP: List[Tuple[str, str]] = [
    ("requirements/raw/", "input-management/user-requirements/"),
    ("requirements/meetings/", "input-management/meeting-minutes/"),
    ("requirements/elicitation/", "input-management/elicitation/"),
    ("requirements/requirements.yaml", "input-management/elicitation/requirements.yaml"),
    ("requirements/clarification-log/open-questions.yaml", "input-management/elicitation/open-questions.yaml"),
    ("requirements/assumptions/assumptions.yaml", "input-management/elicitation/assumptions.yaml"),
    ("overview/product-overview.md", "high-level-requirements/product-overview.md"),
    ("overview/actors.yaml", "high-level-requirements/actors.yaml"),
    ("overview/applications.yaml", "high-level-requirements/applications.yaml"),
    ("overview/integrations.yaml", "high-level-requirements/integrations.yaml"),
    ("overview/business-processes.yaml", "high-level-requirements/business-processes.yaml"),
    ("overview/business-rules.yaml", "high-level-requirements/business-rules.yaml"),
    ("overview/use-cases.yaml", "high-level-requirements/use-cases.yaml"),
    ("overview/data-model/entities.yaml", "high-level-requirements/objects.yaml"),
    ("planning/information-architecture/", "high-level-requirements/site-map/"),
    ("planning/backlog.yaml", "agile-project/backlog.yaml"),
    ("ui/screen-catalog.yaml", "functional-requirements/mockup-screens/screen-catalog.yaml"),
    ("ui/markdown/", "functional-requirements/mockup-screens/"),
    ("ui/prototypes/", "functional-requirements/mockup-screens/prototypes/"),
    ("ui/design-system.md", "technical/design-system.md"),
]
# per-use-case specification files move into one folder per use case
SPEC_MAP = [(re.compile(r"^specifications/use-cases/(UC-\d{3,4})\.md$"),
             "functional-requirements/use-case-specifications/{uc}/spec.md"),
            (re.compile(r"^specifications/analysis/(UC-\d{3,4})-acceptance\.md$"),
             "functional-requirements/use-case-specifications/{uc}/acceptance.md"),
            (re.compile(r"^specifications/analysis/(UC-\d{3,4})-activity\.md$"),
             "functional-requirements/use-case-specifications/{uc}/behaviour.md")]
OLD_ROOTS = ("requirements", "overview", "planning", "specifications", "ui")
NEW_FOLDERS = ("input-management/user-requirements", "input-management/meeting-minutes",
               "input-management/reference-documents", "input-management/elicitation",
               "high-level-requirements/workflows", "high-level-requirements/site-map",
               "functional-requirements/use-case-specifications", "functional-requirements/mockup-screens/prototypes",
               "agile-project", "other-requirements", "appendices")


def new_path(old: str) -> str:
    """Where a path of the old layout lives now (unchanged when it did not move)."""
    for rx, tmpl in SPEC_MAP:
        m = rx.match(old)
        if m:
            return tmpl.format(uc=m.group(1))
    for frm, to in PATH_MAP:
        if frm.endswith("/") and (old == frm or old.startswith(frm)):
            return to + old[len(frm):]
        if old == frm:
            return to
    return old


def _files(root: Path) -> List[Path]:
    return sorted(f for f in root.rglob("*") if f.is_file())


def plan() -> List[Tuple[str, str]]:
    """(old, new) for every file that moves; old views and .gitkeep placeholders are dropped instead."""
    moves = []
    for top in OLD_ROOTS:
        for f in _files(paths.BA / top) if (paths.BA / top).is_dir() else []:
            rel = paths.rel(f)
            if rel.endswith(".view.md") or f.name in (".gitkeep", ".DS_Store"):
                continue
            to = new_path(rel)
            if to != rel:
                moves.append((rel, to))
    return moves


def _rewrite_text(text: str) -> str:
    """Rewrite `ba-ai/<old path>` mentions; the longest old paths first."""
    keys = sorted({frm for frm, _ in PATH_MAP}, key=len, reverse=True)

    def sub(m):
        return "ba-ai/" + new_path(m.group(1))
    alt = "|".join(re.escape(k) for k in keys)
    text = re.sub(r"ba-ai/((?:" + alt + r")[^\s`'\")\]]*)", sub, text)
    return re.sub(r"ba-ai/(specifications/(?:use-cases|analysis)/UC-\d{3,4}(?:-acceptance|-activity)?\.md)", sub, text)


def migrate(dry_run: bool = False) -> Dict[str, list]:
    report: Dict[str, list] = {"moved": [], "rewritten": [], "removed": [], "conflicts": []}
    with store.locked():
        moves = plan()
        for old, new in moves:
            if (paths.BA / new).exists():
                report["conflicts"].append(f"{old} → {new} (target exists)")
        if report["conflicts"] or dry_run:
            report["moved"] = [f"{o} → {n}" for o, n in moves]
            return report
        for d in NEW_FOLDERS:
            (paths.BA / d).mkdir(parents=True, exist_ok=True)
            keep = paths.BA / d / ".gitkeep"
            if not any((paths.BA / d).iterdir()):
                keep.write_text("")
        for old, new in moves:
            dst = paths.BA / new
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(paths.BA / old), str(dst))
            report["moved"].append(f"{old} → {new}")
        # rewrite recorded paths in every document and catalog (never under reviews/ or knowledge/)
        for f in _files(paths.BA):
            rel = paths.rel(f)
            if rel.startswith(("reviews/", "knowledge/", "workflow/context/", "srs/")) or f.suffix not in (".md", ".yaml", ".yml"):
                continue
            if rel.endswith(".view.md") or rel == "workflow/workflow.yaml":
                continue
            text = f.read_text(encoding="utf-8")
            new_text = _rewrite_text(text)
            if f.suffix == ".md":
                fm, body = store.split_frontmatter(new_text)
                if fm and isinstance(fm.get("built_from"), list):
                    changed = False
                    for e in fm["built_from"]:
                        if isinstance(e, dict) and e.get("path") and new_path(e["path"]) != e["path"]:
                            e["path"] = new_path(e["path"])
                            changed = True
                    if fm.get("artifact_type") == "activity-validation":
                        fm["artifact_type"] = "use-case-behaviour"
                        changed = True
                    if changed:
                        new_text = "---\n" + store.dump_yaml(fm) + "---\n" + body
            if new_text != text:
                store.write_atomic(f, new_text)
                report["rewritten"].append(rel)
        # old generated views and the now-empty old folders (R4: state-models/, business-processes/, epics/)
        for top in OLD_ROOTS:
            root = paths.BA / top
            if not root.is_dir():
                continue
            for f in _files(root):
                if f.name.endswith(".view.md") or f.name in (".gitkeep", ".DS_Store"):
                    f.unlink()
                    report["removed"].append(paths.rel(f))
            for d in sorted((p for p in root.rglob("*") if p.is_dir()), key=lambda p: -len(p.parts)):
                if not any(d.iterdir()):
                    d.rmdir()
            if not any(root.iterdir()):
                root.rmdir()
                report["removed"].append(top + "/")
            else:
                report["conflicts"].append(f"{top}/ still holds files the company layout has no place for: "
                                           + ", ".join(paths.rel(f) for f in _files(root)))
        ctx = paths.CONTEXT_DIR
        if ctx.is_dir():
            shutil.rmtree(ctx)              # stale context packages name old paths; they are rebuilt on demand
    return report
