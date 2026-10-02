"""Phase 4 — write the delivery backlog from a plan (master spec §11).

The planning agent proposes epics, their use cases, priorities, dependencies, readiness and user stories
(D-60) in a plan file; `tools/ba backlog plan --file <plan>` merges it into agile-project/backlog.yaml and
the user-story catalog. Derived fields (stage statuses, current_step, artifact links) are kept, and use
cases whose work has started keep their status, so a re-plan never loses progress. Stories keep their IDs:
a story given with its `id` is updated, one without is created, and stories the plan doesn't mention stay.
"""
from __future__ import annotations

from typing import Dict, List

from . import ids, paths, schema, store
from .ids import as_list, normalize_id
from .store import BAError

PLANNED_STATUSES = ("BACKLOG", "READY", "BLOCKED")
UC_FIELDS = ("priority", "status", "dependencies", "blocked_reason")
EPIC_FIELDS = ("name", "priority", "status", "description")
STAGE_FIELDS = ("ui_status", "spec_status", "technical_review_status", "coding_status", "testing_status",
                "documentation_status")


def _cycle(deps: Dict[str, List[str]]) -> List[str]:
    seen, stack = set(), []

    def visit(n) -> List[str]:
        if n in stack:
            return stack[stack.index(n):] + [n]
        if n in seen:
            return []
        seen.add(n)
        stack.append(n)
        for d in deps.get(n, []):
            c = visit(d)
            if c:
                return c
        stack.pop()
        return []

    for n in deps:
        c = visit(n)
        if c:
            return c
    return []


def apply_plan(plan: dict) -> dict:
    from .workspace import Workspace
    if not isinstance(plan.get("epics"), list) or not plan["epics"]:
        raise BAError("the plan needs a non-empty 'epics' list")
    with store.locked():
        ws = Workspace()
        errors: List[str] = []
        seen_uc: Dict[str, str] = {}
        deps: Dict[str, List[str]] = {}
        for e in plan["epics"]:
            if not isinstance(e, dict) or not e.get("name"):
                errors.append(f"every epic needs a name ({e!r:.60})")
                continue
            if e.get("epic_id"):
                e["epic_id"] = normalize_id(e["epic_id"])
                if not ids.id_format_ok(e["epic_id"], "EPIC"):
                    errors.append(f"epic_id {e['epic_id']!r} must look like EPIC-NNN")
                elif e["epic_id"] not in ws.epics:
                    errors.append(f"{e['epic_id']} is not in the backlog — omit epic_id for a new epic")
            if e.get("priority") not in ("HIGH", "MEDIUM", "LOW"):
                errors.append(f"epic {e.get('epic_id') or e['name']!r}: priority must be HIGH, MEDIUM or LOW")
            for u in as_list(e.get("use_cases")):
                uc = normalize_id(str((u or {}).get("use_case_id", "")))
                u["use_case_id"] = uc
                if ws.catalog_of(uc) != "use-cases":
                    errors.append(f"{uc} is not in {schema.catalogs()['use-cases']['path']}")
                for st in as_list(u.get("stories")):
                    if not isinstance(st, dict) or not st.get("name") or not st.get("story"):
                        errors.append(f"{uc}: every story needs a 'name' and a 'story' "
                                      f"(\"As a <actor>, I want …, so that …\") ({st!r:.60})")
                    elif st.get("id"):
                        sid = normalize_id(st["id"])
                        if (ws.item(sid) or {}).get("use_case") != uc:
                            errors.append(f"{uc}: story {sid} is not one of its user stories — omit 'id' for a new one")
                if uc in seen_uc:
                    errors.append(f"{uc} is planned twice ({seen_uc[uc]} and {e.get('epic_id') or e['name']})")
                seen_uc[uc] = e.get("epic_id") or e["name"]
                if u.get("priority") not in ("HIGH", "MEDIUM", "LOW"):
                    errors.append(f"{uc}: priority must be HIGH, MEDIUM or LOW")
                current = (ws.backlog_ucs.get(uc) or {}).get("item", {}).get("status")
                if u.get("status", "BACKLOG") not in PLANNED_STATUSES and u.get("status") != current:
                    errors.append(f"{uc}: a plan sets status to one of {PLANNED_STATUSES} "
                                  f"(IN_PROGRESS and DONE are derived by `tools/ba sync`)")
                u["dependencies"] = [normalize_id(d) for d in as_list(u.get("dependencies"))]
                deps[uc] = u["dependencies"]
        for uc, ds in deps.items():
            for d in ds:
                if d not in deps:
                    errors.append(f"{uc} depends on {d}, which is not in the plan")
        cyc = _cycle(deps)
        if cyc:
            errors.append("dependency cycle: " + " → ".join(cyc))
        dropped = [uc for uc in ws.backlog_ucs if uc not in deps]
        started = [uc for uc in dropped if ws.backlog_ucs[uc]["item"].get("status") in ("IN_PROGRESS", "DONE")]
        if started:
            errors.append("the plan drops use cases whose work has started: " + ", ".join(started))
        if errors:
            raise BAError("plan rejected:\n  " + "\n  ".join(errors))

        old_items = {uc: rec["item"] for uc, rec in ws.backlog_ucs.items()}
        epics_out = []
        for e in plan["epics"]:
            eid = e.get("epic_id") or ids.next_id("EPIC")
            old = ws.epics.get(eid) or {}
            epic = {"epic_id": eid}
            for f in EPIC_FIELDS:
                v = e.get(f, old.get(f))
                if v is not None:
                    epic[f] = v
            epic.setdefault("status", "BACKLOG")
            ucs = []
            for u in as_list(e.get("use_cases")):
                uc = u["use_case_id"]
                item = dict(old_items.get(uc) or {"use_case_id": uc})
                for f in UC_FIELDS:
                    if f == "status" and item.get("status") in ("IN_PROGRESS", "DONE"):
                        continue                         # progress is never undone by a re-plan
                    if f in u:
                        item[f] = u[f]
                item.setdefault("status", "BACKLOG")
                item.setdefault("dependencies", [])
                for f in STAGE_FIELDS:
                    item.setdefault(f, "NOT_STARTED")      # `tools/ba sync` derives them from here on
                ucs.append(item)
            epic["use_cases"] = ucs
            epics_out.append(epic)
        backlog = dict(ws.backlog)
        backlog.setdefault("meta", {"title": "Delivery Backlog",
                                    "note": "Status fields are maintained by `tools/ba sync`. The BA edits "
                                            "priority, status (BACKLOG/READY/BLOCKED) and dependencies."})
        backlog["epics"] = epics_out
        store.save_yaml(paths.BACKLOG, backlog)
        created, updated = [], []
        for e in plan["epics"]:
            for u in as_list(e.get("use_cases")):
                for st in as_list(u.get("stories")):
                    data = {k: st[k] for k in ("name", "story", "acceptance_criteria") if st.get(k)}
                    if st.get("id"):
                        updated.append(ids.catalog_update(st["id"], data))
                    else:
                        created.append(ids.catalog_add("user-stories", {**data, "use_case": u["use_case_id"]}))
    return {"epics": [e["epic_id"] for e in epics_out], "use_cases": len(deps), "dropped": dropped,
            "stories_created": created, "stories_updated": updated}
