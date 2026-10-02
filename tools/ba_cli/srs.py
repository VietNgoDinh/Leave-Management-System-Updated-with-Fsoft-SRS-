"""The company SRS views (addendum D-59) and the SRS publication (D-61).

Everything here is generated from the catalogs and documents and is deterministic: no model writes it, so it
costs no tokens and can't drift. The same renderers serve two outputs:

- `tools/ba sync` writes read-only `*.view.md` pages next to the BA's working files (ORD, state transition,
  use case diagram, permission matrix, one page per object, screen and epic, the NFR list and the appendices);
- `tools/ba publish` writes `ba-ai/srs/`: one page per node of the company documentation tree, and `SRS.md`,
  the whole specification in the company's chapter order (Word on request, through the docx skill).

Views and publication pages have no frontmatter: they are never validated, hashed or put under a gate.
"""
from __future__ import annotations

import os
import re
from typing import Callable, Dict, List, Optional, Tuple

from . import paths, schema, store
from .ids import MESSAGE_PREFIXES, as_list, find_refs, prefix_of
from .workspace import Workspace, field, sections, subsection

ACCESS_SYMBOL = {"ALL": "O", "OWN": "O*", "SCOPED": "O**", "NONE": "X"}
MESSAGE_GROUPS = [("ERROR_DIALOG", "Error Message", "EMSG",
                   "A pop-up with the title \"Error Message\", the message and a \"Close\" button."),
                  ("INLINE_ERROR", "Inline Error Message", "IEM",
                   "Shown in red under the field that does not pass validation."),
                  ("CONFIRMATION", "Confirmation Dialog", "CFD",
                   "A dialog with the title \"Confirmation\", the message, and Yes/OK and No/Cancel buttons."),
                  ("SUCCESS", "Success Dialog", "SCD",
                   "A dialog with the title \"Success\", the message and an \"OK\" button; closes after 5 seconds."),
                  ("INFORMING", "Informing Message", "INF",
                   "An information or warning that does not block the user.")]

# Where an ID "lives": its anchor page, for the working views and for the publication.
VIEW_HOMES = {
    "REQ": "input-management/elicitation/requirements.view.md", "Q": "input-management/elicitation/open-questions.view.md",
    "ASM": "input-management/elicitation/assumptions.view.md", "ACT": "high-level-requirements/actors.view.md",
    "APP": "high-level-requirements/applications.view.md", "INT": "high-level-requirements/integrations.view.md",
    "BP": "high-level-requirements/business-processes.view.md", "BR": "high-level-requirements/business-rules.view.md",
    "UC": "high-level-requirements/use-cases.view.md", "ENT": "functional-requirements/objects/{ID}.view.md",
    "SCR": "functional-requirements/mockup-screens/screens/{ID}.view.md",
    "CMUC": "functional-requirements/common-use-cases.view.md", "EPIC": "agile-project/epics/{ID}.view.md",
    "US": "agile-project/user-stories.view.md", "ET": "appendices/email-templates.view.md",
    "TERM": "appendices/glossary.view.md",
    **{p: "appendices/messages.view.md" for p in MESSAGE_PREFIXES},
}
SRS_HOMES = {
    "REQ": "srs/input-management/user-requirements.md", "Q": "srs/appendices/open-questions-and-assumptions.md",
    "ASM": "srs/appendices/open-questions-and-assumptions.md", "ACT": "srs/high-level-requirements/actor.md",
    "APP": "srs/high-level-requirements/site-map.md", "INT": "srs/integration.md",
    "BP": "srs/high-level-requirements/workflow.md", "BR": "srs/functional-requirements/common-business-rule.md",
    "UC": "srs/functional-requirements/use-case-specifications.md", "ENT": "srs/functional-requirements/object.md",
    "SCR": "srs/mockups-screen.md", "CMUC": "srs/functional-requirements/common-use-cases.md",
    "EPIC": "srs/agile-project/epic.md", "US": "srs/agile-project/user-story.md",
    "ET": "srs/appendices/email-templates.md", "TERM": "srs/appendices/glossary.md",
    **{p: "srs/appendices/message-list.md" for p in MESSAGE_PREFIXES},
}


# ------------------------------------------------------------------ helpers

def _cell(text) -> str:
    return str(text if text is not None else "").replace("|", "\\|").replace("\n", "<br>").strip()


def _mid(iid: str) -> str:
    return re.sub(r"\W", "_", iid)


def _mlabel(text) -> str:
    return '"' + " ".join(str(text).split()).replace('"', "#quot;") + '"'


def _state_label(text) -> str:
    return " ".join(str(text).replace(":", " –").replace(";", ",").replace("#", "").split())


def demote(md: str, levels: int) -> str:
    """Move every heading (outside code fences) down by `levels` levels (up when negative; never above H1,
    never below H6)."""
    if not levels:
        return md
    out, fence = [], False
    for ln in md.split("\n"):
        if re.match(r"^\s*(```|~~~)", ln):
            fence = not fence
        else:
            m = re.match(r"^(#{1,6})(\s.*)$", ln) if not fence else None
            if m:
                ln = "#" * max(1, min(6, len(m.group(1)) + levels)) + m.group(2)
        out.append(ln)
    return "\n".join(out)


def generated_note(sources: str) -> List[str]:
    return [f"<!-- GENERATED by tools/ba from {sources}. Do not edit: change the sources, then run `tools/ba sync`. -->"]


class Page:
    """Renders one page; links are relative to where the page is written."""

    def __init__(self, ws: Workspace, here: str, homes: Dict[str, str]):
        self.ws, self.here, self.homes = ws, here, homes

    def link(self, target: str, anchor: str = "") -> str:
        if target == self.here:
            return f"#{anchor}" if anchor else "#"
        rel = os.path.relpath(target, os.path.dirname(self.here) or ".").replace(os.sep, "/")
        return rel + (f"#{anchor}" if anchor else "")

    def home(self, iid: str) -> Optional[str]:
        h = self.homes.get(prefix_of(iid))
        return h.replace("{ID}", iid) if h else None

    def ref(self, iid: str, name: bool = True) -> str:
        label = self.ws.label(iid) if name else ""
        h = self.home(iid)
        if not h or self.ws.label(iid) == "" and iid not in self.ws.epics:
            return f"{iid} {label}".strip()
        anchor = "" if "{ID}" in (self.homes.get(prefix_of(iid)) or "") else iid
        return f"[{iid}]({self.link(h, anchor)}) {label}".strip()

    def name(self, iid: str) -> str:
        return self.ws.label(iid) or iid


def _sentence(text) -> str:
    """Text that ends like a sentence, so generated sentences can follow it."""
    t = str(text or "").strip()
    return t if not t or t[-1] in ".!?:" else t + "."


def _actor_names(ws: Workspace, ids) -> str:
    return ", ".join(ws.label(a) or a for a in ids)


# ------------------------------------------------------------------ High Level Requirements

def ord_body(pg: Page) -> List[str]:
    ws = pg.ws
    ents, actors, ints = ws.items_in("entities"), ws.items_in("actors"), ws.items_in("integrations")
    if not ents:
        return ["No objects yet."]
    lines = ["```mermaid", "flowchart LR"]
    lines += ["  subgraph Actors"] + [f"    {_mid(a['id'])}([{_mlabel(a.get('name'))}])" for a in actors] + ["  end"]
    lines += ["  subgraph Objects"] + [f"    {_mid(e['id'])}[{_mlabel(e.get('name'))}]" for e in ents] + ["  end"]
    if ints:
        lines += ["  subgraph External[\"External systems\"]"]
        lines += [f"    {_mid(i['id'])}[[{_mlabel(i.get('system') or i.get('name'))}]]" for i in ints] + ["  end"]
    acts: Dict[Tuple[str, str], List[str]] = {}
    for uc in ws.items_in("use-cases"):
        if uc.get("object") and ws.item(uc["object"]):
            for a in ws.use_case_actors(uc["id"]):
                acts.setdefault((a, uc["object"]), []).append(str(uc.get("name")))
    for (a, e), names in acts.items():
        if ws.item(a):
            label = ", ".join(names[:3]) + (", …" if len(names) > 3 else "")
            lines.append(f"  {_mid(a)} -->|{_mlabel(label)}| {_mid(e)}")
    for e in ents:
        for r in as_list(e.get("relationships")):
            if isinstance(r, dict) and ws.item(r.get("to")):
                label = f"{r.get('description') or 'relates to'} ({r.get('cardinality', '')})"
                lines.append(f"  {_mid(e['id'])} -->|{_mlabel(label)}| {_mid(r['to'])}")
    for i in ints:
        for e in as_list(i.get("entities")):
            if ws.item(e):
                if i.get("direction") == "OUTBOUND":
                    lines.append(f"  {_mid(e)} -.-> {_mid(i['id'])}")
                elif i.get("direction") == "INBOUND":
                    lines.append(f"  {_mid(i['id'])} -.-> {_mid(e)}")
                else:
                    lines.append(f"  {_mid(i['id'])} <-.-> {_mid(e)}")
    lines += ["```", "", "Object Description:", "", "| # | Object | Description |", "|---|---|---|", "| **Object** | | |"]
    for n, e in enumerate(ents, 1):
        attrs = [str(a.get("name")) for a in as_list(e.get("attributes")) if isinstance(a, dict)]
        managed = sorted({f"{uc.get('name')} ({uc['id']})" for uc in ws.items_in("use-cases") if uc.get("object") == e["id"]})
        desc = _sentence(e.get("description"))
        if attrs:
            desc += f" This object contains fields such as {', '.join(attrs[:6])}{' and others' if len(attrs) > 6 else ''}."
        desc += f" Owner: {e.get('owner', '')}."
        if managed:
            desc += f" Functions: {', '.join(managed)}."
        lines.append(f"| {n} | {pg.ref(e['id'])} | {_cell(desc)} |")
    lines.append("| **Actor** | | |")
    for n, a in enumerate(actors, 1):
        lines.append(f"| {n} | {pg.ref(a['id'])} | {_cell(actor_description(ws, a))} |")
    if ints:
        lines.append("| **External System** | | |")
        for n, i in enumerate(ints, 1):
            ents_ = ", ".join(ws.label(x) for x in as_list(i.get("entities")) if ws.item(x))
            desc = f"{i.get('purpose', '')} ({i.get('direction', '').lower()}; owner: {i.get('owner', '')})"
            if ents_:
                desc += f" Provides or receives: {ents_}."
            lines.append(f"| {n} | {pg.ref(i['id'])} | {_cell(desc)} |")
    return lines


def actor_description(ws: Workspace, a: dict) -> str:
    """The company's actor paragraph: description, permissions (from the matrix), role mapping."""
    out = _sentence(a.get("description"))
    perms = []
    for uc in ws.items_in("use-cases"):
        for p in as_list(uc.get("permissions")):
            if isinstance(p, dict) and p.get("actor") == a["id"] and p.get("access") not in (None, "NONE"):
                perms.append(f"{uc.get('name')} ({ACCESS_SYMBOL[p['access']]})")
    if perms:
        out += f" This actor has the permission to: {'; '.join(perms)}."
    if a.get("role_mapping"):
        out += f" The system recognises the user as \"{a.get('name')}\" when {str(a['role_mapping']).rstrip('.')}."
    return out


def workflow_fallback(ws: Workspace, bp: dict) -> List[str]:
    """A swimlane diagram generated from the process steps, for a process with no workflow document yet."""
    steps = [s for s in as_list(bp.get("steps")) if isinstance(s, dict) and s.get("id")]
    lanes: Dict[str, List[dict]] = {}
    for s in steps:
        lanes.setdefault(s.get("actor") or "SYSTEM", []).append(s)
    lines = ["```mermaid", "flowchart LR"]
    for lane, ss in lanes.items():
        lines.append(f"  subgraph L_{_mid(lane)}[{_mlabel(ws.label(lane) or 'System')}]")
        lines += [f"    {_mid(s['id'])}[{_mlabel(s['id'][-3:] + ' ' + str(s.get('name')))}]" for s in ss]
        lines.append("  end")
    for i, s in enumerate(steps):
        nxt = [n for n in as_list(s.get("next")) if isinstance(n, dict)]
        if nxt:
            for n in nxt:
                if n.get("to") and n["to"] != "END":
                    lab = f"|{_mlabel(n['when'])}|" if n.get("when") else ""
                    lines.append(f"  {_mid(s['id'])} -->{lab} {_mid(n['to'])}")
        elif i + 1 < len(steps):
            lines.append(f"  {_mid(s['id'])} --> {_mid(steps[i + 1]['id'])}")
    return lines + ["```"]


def workflow_body(pg: Page) -> List[str]:
    ws, out = pg.ws, []
    for bp in ws.items_in("business-processes"):
        out += [f'<a id="{bp["id"]}"></a>', f"## {bp['id']} — {bp.get('name', '')}", "",
                f"**Objective:** {bp.get('objective', '')}  ", f"**Trigger:** {bp.get('trigger', '')}  ",
                f"**Actors:** {_actor_names(ws, as_list(bp.get('actors')))}", ""]
        doc = ws.docs.get(f"high-level-requirements/workflows/{bp['id']}.md")
        if doc:
            body = re.sub(r"^#\s.*\n", "", doc.body.strip() + "\n", count=1)
            out += [demote(body.strip(), 1), ""]
        else:
            out += ["_No workflow document yet: the diagram below is generated from the process steps._", ""]
            out += workflow_fallback(ws, bp) + [""]
    return out or ["No business processes yet."]


def state_transition_body(pg: Page) -> List[str]:
    ws, out = pg.ws, []
    for e in ws.items_in("entities"):
        lc = e.get("lifecycle")
        if not isinstance(lc, dict) or not as_list(lc.get("states")):
            continue
        out += [f'<a id="{e["id"]}"></a>', f"## {e['id']} — {e.get('name', '')} State Transition", ""]
        out += lifecycle_diagram(lc)
        invalid = as_list(lc.get("invalid_transitions"))
        if invalid:
            out += ["", "Not allowed:", ""] + [f"- {x}" for x in invalid]
        rows = []
        for s in as_list(lc.get("states")):
            fns = [pg.ref(uc["id"]) for uc in ws.items_in("use-cases")
                   if uc.get("object") == e["id"] and s in as_list(uc.get("allowed_states"))]
            if fns:
                rows.append(f"| {s} | {'<br>'.join(fns)} |")
        if rows:
            out += ["", "Functions allowed in each state:", "", "| State | Functions |", "|---|---|"] + rows
        out.append("")
    return out or ["No object has a lifecycle yet."]


def lifecycle_diagram(lc: dict) -> List[str]:
    from .validate import parse_transition
    merged: Dict[Tuple[str, str], List[str]] = {}
    for t in as_list(lc.get("transitions")):
        p = parse_transition(t)
        if p:
            merged.setdefault((p[0], p[1]), []).append(_state_label(p[2] or ""))
    lines = ["```mermaid", "stateDiagram-v2"]
    for (frm, to), evs in merged.items():
        a = "[*]" if frm == "(new)" else frm
        label = " / ".join(e for e in evs if e)
        lines.append(f"    {a} --> {to}" + (f": {label}" if label else ""))
    return lines + ["```"]


def use_case_diagram_body(pg: Page) -> List[str]:
    ws, out = pg.ws, []
    groups: Dict[str, List[dict]] = {}
    for uc in ws.items_in("use-cases"):
        groups.setdefault(uc.get("business_process") or "", []).append(uc)
    for bp_id, ucs in groups.items():
        title = f"{bp_id} — {ws.label(bp_id)}" if bp_id else "Other use cases"
        out += [f"## {title} Use Case Diagram", "", "```mermaid", "flowchart LR"]
        actors = list(dict.fromkeys(a for uc in ucs for a in ws.use_case_actors(uc["id"])))
        out += [f"  {_mid(a)}[{_mlabel(ws.label(a) or a)}]" for a in actors]
        apps = list(dict.fromkeys(uc.get("application") for uc in ucs))
        for app in apps:
            out.append(f"  subgraph {_mid(str(app))}[{_mlabel(ws.label(str(app)) or 'System')}]")
            out += [f"    {_mid(uc['id'])}([{_mlabel(uc.get('name'))}])" for uc in ucs if uc.get("application") == app]
            out.append("  end")
        for uc in ucs:
            out += [f"  {_mid(a)} --- {_mid(uc['id'])}" for a in ws.use_case_actors(uc["id"])]
        out += ["```", "", "| # | UC Name | Description |", "|---|---|---|"]
        for n, uc in enumerate(ucs, 1):
            out.append(f"| {n} | {pg.ref(uc['id'])} | {_cell(function_sentence(ws, uc))} |")
        out.append("")
    return out or ["No use cases yet."]


def function_sentence(ws: Workspace, uc: dict) -> str:
    obj = str(uc.get("objective") or "").strip().rstrip(".")
    if not obj:
        return f"_Objective not set yet._ {uc.get('description', '')}"
    return f"This function allows {_actor_names(ws, ws.use_case_actors(uc['id']))} to {obj}."


def permission_matrix_body(pg: Page) -> List[str]:
    ws = pg.ws
    actors = ws.items_in("actors")
    ucs = ws.items_in("use-cases")
    if not ucs:
        return ["No use cases yet."]
    apps = ", ".join(a.get("name", a["id"]) for a in ws.items_in("applications"))
    out = [f"Permission matrix mapping functions and user roles for {apps}:", "",
           "- \"O\": the actor may perform the function. What the actor can do is described in the use case.",
           "- \"O*\": the actor may perform the function on the items they created or own.",
           "- \"O**\": the actor may perform the function within a scope; the scope rule is listed under the matrix.",
           "- \"X\": the actor may not perform the function.", "",
           "| Function | " + " | ".join(_cell(a.get("name")) for a in actors) + " |",
           "|---|" + "---|" * len(actors)]

    def row(uc):
        perms = {p.get("actor"): p.get("access") for p in as_list(uc.get("permissions")) if isinstance(p, dict)}
        return (f"| {pg.ref(uc['id'])} | "
                + " | ".join(ACCESS_SYMBOL.get(perms.get(a["id"]) or "NONE", "X") for a in actors) + " |")

    blank = " |" * len(actors)
    order = [e["id"] for e in ws.items_in("entities")]
    by_obj: Dict[str, List[dict]] = {}
    for uc in ucs:
        by_obj.setdefault(uc.get("object") or "", []).append(uc)
    for obj in sorted(by_obj, key=lambda o: order.index(o) if o in order else len(order)):
        group = by_obj[obj]
        out.append(f"| **{_cell(ws.label(obj) or obj or 'No object')}** |" + blank)
        out += [row(uc) for uc in group if not as_list(uc.get("allowed_states"))]
        states = as_list(((ws.item(obj) or {}).get("lifecycle") or {}).get("states"))
        extra = [s for uc in group for s in as_list(uc.get("allowed_states")) if s not in states]
        for s in states + list(dict.fromkeys(extra)):
            in_state = [uc for uc in group if s in as_list(uc.get("allowed_states"))]
            if in_state:
                out.append(f"| *Status is \"{s}\"* |" + blank)
                out += [row(uc) for uc in in_state]
    scopes = []
    for uc in ucs:
        for p in as_list(uc.get("permissions")):
            if isinstance(p, dict) and p.get("access") in ("OWN", "SCOPED"):
                scopes.append(f"| {pg.ref(uc['id'])} | {_cell(ws.label(p.get('actor')))} | "
                              f"{ACCESS_SYMBOL[p['access']]} | {_cell(p.get('scope') or 'items they created or own')} |")
    if scopes:
        out += ["", "Scope rules:", "", "| Function | Actor | Access | Scope |", "|---|---|---|---|"] + scopes
    return out


def site_map_body(pg: Page) -> List[str]:
    ws, out = pg.ws, []
    for app in ws.items_in("applications"):
        doc = ws.docs.get(f"high-level-requirements/site-map/{app['id']}.md")
        out += [f'<a id="{app["id"]}"></a>', f"## Site Map for {app.get('name', app['id'])}", ""]
        if doc:
            for title in ("Site Map", "Pages"):
                sec = subsection(doc.body, title)
                if sec:
                    out += [f"### {title}", "", sec.strip(), ""]
        else:
            out += ["Not written yet (Phase 4A)." if ws.user_facing_applications().count(app)
                    else "Not applicable: no human actor uses this application.", ""]
    return out or ["No applications yet."]


# ------------------------------------------------------------------ Functional Requirements

def object_section(pg: Page, e: dict, level: int = 1) -> List[str]:
    ws, h = pg.ws, "#" * level
    out = [f'<a id="{e["id"]}"></a>', f"{h} {e['id']} — {e.get('name', '')}", "", str(e.get("description") or ""), "",
           f"**Owner:** {e.get('owner', '')}", "", f"{h}# Attributes", "",
           "| Attribute | Type | Mandatory | Unique | Max length | Format | Allowed values | Default | Description |",
           "|---|---|---|---|---|---|---|---|---|"]
    for a in as_list(e.get("attributes")):
        if not isinstance(a, dict):
            continue
        yn = {True: "Yes", False: "No", None: ""}
        fmt = a.get("format") or (f"generated: {a['generated']}" if a.get("generated") else "")
        out.append(f"| {_cell(a.get('name'))} | {_cell(a.get('type'))} | {yn.get(a.get('mandatory'), '')} | "
                   f"{yn.get(a.get('unique'), '')} | {_cell(a.get('max_length'))} | {_cell(fmt)} | "
                   f"{_cell(', '.join(str(v) for v in as_list(a.get('allowed_values'))))} | {_cell(a.get('default'))} | "
                   f"{_cell(a.get('description'))} |")
    rels = [r for r in as_list(e.get("relationships")) if isinstance(r, dict)]
    if rels:
        out += ["", f"{h}# Relationships", "", "| Relationship | Object | Cardinality |", "|---|---|---|"]
        out += [f"| {_cell(r.get('description'))} | {pg.ref(r.get('to'))} | {_cell(r.get('cardinality'))} |" for r in rels]
    lc = e.get("lifecycle")
    if isinstance(lc, dict) and as_list(lc.get("states")):
        out += ["", f"{h}# State Transition", ""] + lifecycle_diagram(lc)
    fns = [uc for uc in ws.items_in("use-cases") if uc.get("object") == e["id"]]
    if fns:
        out += ["", f"{h}# Functions", "", "| Function | Allowed in states | Permissions |", "|---|---|---|"]
        for uc in fns:
            perms = "; ".join(f"{ws.label(p.get('actor'))}: {ACCESS_SYMBOL.get(p.get('access'), 'X')}"
                              for p in as_list(uc.get("permissions")) if isinstance(p, dict)
                              and p.get("access") not in (None, "NONE"))
            out.append(f"| {pg.ref(uc['id'])} | {_cell(', '.join(as_list(uc.get('allowed_states'))) or 'any')} | "
                       f"{_cell(perms)} |")
    return out + [""]


def screen_designs(ws: Workspace, scr: str) -> List[Tuple[str, str, str]]:
    """(use case, heading, section text) of every UI document that specifies screen `scr`."""
    out = []
    for doc in ws.docs.values():
        if doc.type != "ui-markdown":
            continue
        for _lvl, h, text in sections(doc.body):
            if re.match(r"^" + re.escape(scr) + r"\b", h):
                out.append((doc.id, h, text))
    order = as_list((ws.item(scr) or {}).get("use_cases"))
    return sorted(out, key=lambda x: order.index(x[0]) if x[0] in order else len(order))


def screen_section(pg: Page, s: dict, level: int = 1) -> List[str]:
    ws, h = pg.ws, "#" * level
    designs = screen_designs(ws, s["id"])
    out = [f'<a id="{s["id"]}"></a>', f"{h} {s['id']} — {s.get('name', '')}", "",
           "| Application | Route | Actors | Use cases |", "|---|---|---|---|",
           f"| {_cell(ws.label(s.get('application')))} | {_cell(s.get('route'))} | "
           f"{_cell(_actor_names(ws, as_list(s.get('actors'))))} | "
           f"{', '.join(pg.ref(u, name=False) for u in as_list(s.get('use_cases')))} |", "",
           str(s.get("purpose") or ""), ""]
    if not designs:
        return out + ["_Not designed yet: planned by the site map, specified at step 5.2 of its use case._", ""]
    for i, (uc, _heading, text) in enumerate(designs):
        proto = f"functional-requirements/mockup-screens/prototypes/{uc}/index.html"
        title = "Specified in" if i == 0 else "Extended in"
        out += [f"{h}# {title} {uc} — {ws.label(uc)}", ""]
        if (paths.BA / proto).exists():
            out += [f"Mockup: [interactive prototype]({pg.link(proto)}#/{s['id'].lower()})", ""]
        out += [demote(text.strip(), level - 2), ""]       # the design's '#### …' sit under '{h}# Specified in'
    return out


def common_use_case_section(pg: Page, c: dict, level: int = 2) -> List[str]:
    ws, h = pg.ws, "#" * level
    followers = [pg.ref(uc["id"]) for uc in ws.items_in("use-cases") if c["id"] in as_list(uc.get("follows"))]
    out = [f'<a id="{c["id"]}"></a>', f"{h} {c['id']}: {c.get('name', '')}", "",
           "| | |", "|---|---|",
           f"| Objective | This function allows the user to {_cell(c.get('objective'))}. |",
           f"| Actor | {_cell(c.get('actor') or 'The actors of the use case that follows this common use case.')} |",
           f"| Trigger | {_cell(c.get('trigger'))} |", f"| Pre-condition | {_cell(c.get('pre_condition'))} |",
           f"| Post-condition | {_cell(c.get('post_condition'))} |", "", "Activities Flow", ""]
    out += [f"- {s}" for s in as_list(c.get("activities_flow"))]
    out += ["", "Business Rules", "", "| Step | BR Code | Description |", "|---|---|---|"]
    for r in as_list(c.get("step_rules")):
        if isinstance(r, dict):
            out.append(f"| {_cell(r.get('step'))} | {r.get('id', '')} | "
                       f"{_cell('**' + str(r.get('title', '')) + ':**' + chr(10) + str(r.get('description', '')))} |")
    if followers:
        out += ["", f"Followed by: {', '.join(followers)}"]
    return out + [""]


def use_case_spec_section(pg: Page, uc: dict, level: int = 2) -> List[str]:
    """The company's use case specification: header table, activities flow, step-keyed business rules,
    alternate and error flows. Technical sections stay in the BA workspace (the SRS ends at requirements)."""
    from . import compile as comp
    ws, h = pg.ws, "#" * level
    out = [f'<a id="{uc["id"]}"></a>', f"{h} {uc['id']}: {uc.get('name', '')}", ""]
    beh = ws.docs.get(ws.doc_rel("use-case-behaviour", uc["id"]))
    actors = _actor_names(ws, as_list(uc.get("actor")))
    head = subsection(beh.body, "Use Case Description") if beh else ""
    out += ["| | |", "|---|---|",
            f"| Objective | This use case allows {_cell(actors)} to {_cell(str(uc.get('objective', '')).rstrip('.'))}. |",
            f"| Actor | {_cell(actors)} |"]
    for f in ("Trigger", "Pre-condition", "Post-condition"):
        v = comp.field_block(head or "", f) if beh else None
        out.append(f"| {f} | {_cell(v) if v else '_not specified yet_'} |")
    if uc.get("follows"):
        out.append("| Follows | " + ", ".join(pg.ref(c) for c in as_list(uc.get("follows"))) + " |")
    out.append("")
    if not beh:
        bl = ws.backlog_ucs.get(uc["id"])
        now = (bl or {}).get("item", {}).get("current_step") or ("planned" if bl else "not planned yet")
        return out + [f"_Activities flow and business rules not specified yet (current step: {now})._", ""]
    flow = (subsection(beh.body, "Activities Flow") or "").strip()
    out += [f"{h}# Activities Flow", ""]
    for c in as_list(uc.get("follows")):
        out += [f"Follows {pg.ref(c)}:", ""] + [f"- {s}" for s in as_list((ws.item(c) or {}).get("activities_flow"))] + [""]
    out += [demote(flow, level) if flow else "As the common use cases above.", "",
            f"{h}# Business Rules", "", comp.business_rules_table(ws, uc["id"], beh), ""]
    for kind, title in (("AF", "Alternate Flows"), ("EF", "Error Flows")):
        text = comp._scoped(ws, beh, kind)
        if text != "None.":
            out += [f"{h}# {title}", "", demote(text, level - 1 if level > 1 else 0), ""]
    screens = [s["id"] for s in ws.screens_of(uc["id"])]
    if screens:
        out += [f"Screens: {', '.join(pg.ref(s) for s in screens)}", ""]
    return out


def nfr_body(pg: Page) -> List[str]:
    ws, out = pg.ws, []
    reqs = [r for r in ws.items_in("requirements") if r.get("type") == "NON_FUNCTIONAL"]
    for title, cats in schema.nfr_sections().items():
        rows = [r for r in reqs if r.get("category") in cats]
        out += [f"## {title}", ""]
        if not rows:
            out += ["None stated.", ""]
            continue
        out += ["| Title | Variables / Criteria | Remarks |", "|---|---|---|"]
        for r in rows:
            out.append(f'| <a id="{r["id"]}"></a>{pg.ref(r["id"])} ({str(r.get("category", "")).title()}) | '
                       f"{_cell(r.get('criteria'))} | {_cell(r.get('description'))} |")
        out.append("")
    untyped = [r["id"] for r in ws.items_in("requirements") if not r.get("type")]
    if untyped:
        out += [f"_Not typed yet (FUNCTIONAL or NON_FUNCTIONAL): {', '.join(untyped)}._", ""]
    return out


# ------------------------------------------------------------------ Agile Project

def epic_section(pg: Page, eid: str, level: int = 1) -> List[str]:
    ws, h = pg.ws, "#" * level
    epic = ws.epics.get(eid) or {}
    out = [f'<a id="{eid}"></a>', f"{h} {eid} — {epic.get('name', '')}", "",
           f"Priority: {epic.get('priority', '')} · Status: {epic.get('status', '')}", ""]
    if epic.get("description"):
        out += [str(epic["description"]), ""]
    out += [f"{h}# Use cases", "", "| Use case | Priority | Status | Now at |", "|---|---|---|---|"]
    ucs = [u for u in as_list(epic.get("use_cases")) if isinstance(u, dict)]
    for u in ucs:
        out.append(f"| {pg.ref(str(u.get('use_case_id')))} | {u.get('priority', '')} | {u.get('status', '')} | "
                   f"{_cell(u.get('workflow_note') or u.get('current_step') or '')} |")
    stories = [s for s in ws.items_in("user-stories") if s.get("use_case") in {u.get("use_case_id") for u in ucs}]
    out += ["", f"{h}# User stories", ""]
    out += story_table(pg, stories) if stories else ["No user stories yet."]
    return out + [""]


def story_table(pg: Page, stories: List[dict]) -> List[str]:
    ws = pg.ws
    out = ["| ID | User story | Use case | Status | Acceptance criteria |", "|---|---|---|---|---|"]
    for s in stories:
        bl = ws.backlog_ucs.get(s.get("use_case"))
        status = (bl or {}).get("item", {}).get("status", "") if bl else "not planned"
        acs = as_list(s.get("acceptance_criteria")) or sorted(
            sid for sid, x in ws.scoped.items() if x["kind"] == "AC" and x["uc"] == s.get("use_case"))
        out.append(f'| <a id="{s["id"]}"></a>{s["id"]} | **{_cell(s.get("name"))}**<br>{_cell(s.get("story"))} | '
                   f"{pg.ref(str(s.get('use_case')))} | {status} | {_cell(', '.join(acs)) or '—'} |")
    return out


# ------------------------------------------------------------------ Appendices

def messages_body(pg: Page) -> List[str]:
    ws, out = pg.ws, []
    usage = _usage(ws, MESSAGE_PREFIXES)
    for mtype, title, code, desc in MESSAGE_GROUPS:
        items = [m for m in ws.items_in("messages") if m.get("type") == mtype]
        out += [f"## {title} ({code})", "", desc, ""]
        if not items:
            out += ["None.", ""]
            continue
        out += ["| Code | Message | Used in |", "|---|---|---|"]
        out += [f'| <a id="{m["id"]}"></a>{m["id"]} | {_cell(m.get("text"))} | '
                f"{', '.join(pg.ref(u, name=False) for u in usage.get(m['id'], [])) or '—'} |" for m in items]
        out.append("")
    return out


def _usage(ws: Workspace, prefixes) -> Dict[str, List[str]]:
    """Code → the use cases whose documents show or send it."""
    out: Dict[str, List[str]] = {}
    for doc in ws.docs.values():
        if doc.type in ("ui-markdown", "use-case-behaviour"):
            for r in find_refs(doc.body):
                if prefix_of(r) in prefixes and doc.id not in out.setdefault(r, []):
                    out[r].append(doc.id)
    return out


def email_templates_body(pg: Page) -> List[str]:
    from .compile import email_template_block
    ws, out = pg.ws, []
    usage = _usage(ws, ("ET",))
    for e in ws.items_in("email-templates"):
        out += [f'<a id="{e["id"]}"></a>', email_template_block(ws, e["id"]), ""]
        if usage.get(e["id"]):
            out += [f"Sent by: {', '.join(pg.ref(u) for u in usage[e['id']])}", ""]
    return out or ["No email templates yet."]


def glossary_body(pg: Page) -> List[str]:
    ws, out = pg.ws, []
    for kind, title, cols in (("ABBREVIATION", "Abbreviations", ("Acronym", "Reference")),
                              ("NOTATION", "Notation", ("Notation", "Meaning")),
                              ("TERM", "Terms", ("Term", "Definition"))):
        items = [t for t in ws.items_in("glossary") if t.get("kind") == kind]
        if not items:
            continue
        out += [f"## {title}", "", f"| {cols[0]} | {cols[1]} |", "|---|---|"]
        out += [f'| <a id="{t["id"]}"></a>{_cell(t.get("term"))} | {_cell(t.get("definition"))} |'
                for t in sorted(items, key=lambda t: str(t.get("term")).lower())]
        out.append("")
    return out or ["No glossary entries yet."]


# ------------------------------------------------------------------ working views (tools/ba sync)

def _view(title: str, sources: str, intro: str, body: List[str]) -> str:
    out = generated_note(sources) + [f"# {title}", "", f"_{intro} Generated by `tools/ba sync` from {sources}; "
                                                         "edit the sources, not this file._", ""]
    return "\n".join(out + body).rstrip("\n") + "\n"


def derived_views(ws: Workspace) -> Dict[str, str]:
    """Every generated company view, by path relative to ba-ai/."""
    v: Dict[str, str] = {}

    def page(rel):
        return Page(ws, rel, VIEW_HOMES)

    hl = "high-level-requirements/"
    rel = hl + "object-relationship-diagram.view.md"
    v[rel] = _view("Object Relationship Diagram", "objects.yaml, actors.yaml, integrations.yaml and use-cases.yaml",
                   "The static relationships between actors and objects, between objects, and with external systems.",
                   ord_body(page(rel)))
    rel = hl + "state-transition.view.md"
    v[rel] = _view("State Transition", "the lifecycles in objects.yaml",
                   "How each object's state changes in response to actions; each line is the action that causes it.",
                   state_transition_body(page(rel)))
    rel = hl + "use-case-diagram.view.md"
    v[rel] = _view("Use Case Diagram", "use-cases.yaml", "The functions each actor performs, per business process.",
                   use_case_diagram_body(page(rel)))
    rel = hl + "permission-matrix.view.md"
    v[rel] = _view("Permission Matrix", "the permissions in use-cases.yaml",
                   "Functions × roles, grouped by object and then by status.", permission_matrix_body(page(rel)))
    rel = hl + "workflows.view.md"
    v[rel] = _view("Workflow", "business-processes.yaml and workflows/", "One workflow per business process.",
                   workflow_body(page(rel)))
    for e in ws.items_in("entities"):
        rel = f"functional-requirements/objects/{e['id']}.view.md"
        v[rel] = "\n".join(generated_note("objects.yaml and use-cases.yaml") + object_section(page(rel), e)).rstrip() + "\n"
    for s in ws.items_in("screens"):
        rel = f"functional-requirements/mockup-screens/screens/{s['id']}.view.md"
        v[rel] = "\n".join(generated_note("screen-catalog.yaml and the screen designs") + screen_section(page(rel), s)).rstrip() + "\n"
    for eid in ws.epics:
        rel = f"agile-project/epics/{eid}.view.md"
        v[rel] = "\n".join(generated_note("backlog.yaml and user-stories.yaml") + epic_section(page(rel), eid)).rstrip() + "\n"
    rel = "non-functional-requirements/non-functional-requirements.view.md"
    v[rel] = _view("Non-Functional Requirements", "the NON_FUNCTIONAL requirements in requirements.yaml",
                   "Requirements typed NON_FUNCTIONAL, in the company's sections.", nfr_body(page(rel)))
    return v


def catalog_views(ws: Workspace) -> Dict[str, Callable[[], str]]:
    """Catalog views rendered in the company format instead of the generic table (views.py)."""
    v: Dict[str, Callable[[], str]] = {}

    def page(rel):
        return Page(ws, rel, VIEW_HOMES)

    if "messages" in ws.catalog_data:
        rel = "appendices/messages.view.md"
        v["messages"] = lambda rel=rel: _view("Message List", "messages.yaml", "Every message the user can see, by type.",
                                              messages_body(page(rel)))
    if "email-templates" in ws.catalog_data:
        rel = "appendices/email-templates.view.md"
        v["email-templates"] = lambda rel=rel: _view("Email Templates", "email-templates.yaml",
                                                     "Every email the system sends.", email_templates_body(page(rel)))
    if "glossary" in ws.catalog_data:
        rel = "appendices/glossary.view.md"
        v["glossary"] = lambda rel=rel: _view("Glossary", "glossary.yaml", "Abbreviations, notation and terms.",
                                              glossary_body(page(rel)))
    if "common-use-cases" in ws.catalog_data:
        rel = "functional-requirements/common-use-cases.view.md"
        v["common-use-cases"] = lambda rel=rel: _view(
            "Common Use Cases", "common-use-cases.yaml",
            "Standard functions on any object; a use case that follows one specifies only what differs.",
            sum((common_use_case_section(page(rel), c) for c in ws.items_in("common-use-cases")), []) or ["None yet."])
    if "user-stories" in ws.catalog_data:
        rel = "agile-project/user-stories.view.md"
        v["user-stories"] = lambda rel=rel: _view("User Stories", "user-stories.yaml and backlog.yaml",
                                                  "Tracking items: each realises a use case.",
                                                  story_table(page(rel), ws.items_in("user-stories")))
    return v


# ------------------------------------------------------------------ publication (tools/ba publish)

INTRO_PURPOSE = (
    "This System Requirements Specification is a formal statement of the system's functional and non-functional "
    "requirements. It lays out the capabilities that the system must provide and the constraints by which it must "
    "abide. It serves as a basis for an agreement between the customer and the supplier on how the system should "
    "function.\n\nSpecifically, this document:\n\n- defines the scope of business objectives, functions and "
    "structure;\n- identifies the business processes the solution supports;\n- develops a common understanding of "
    "the functional requirements for all parties;\n- establishes a basis for defining acceptance tests.")
INTRO_AUDIENCE = (
    "This document is intended for:\n\n- **Development team:** designs, implements and tests the application "
    "(unit, integration and system tests).\n- **Documentation team:** writes the user guide.\n- **UAT team:** runs "
    "the user acceptance test sessions with end users.")


def _listing(rel: str) -> List[str]:
    p = paths.BA / rel
    if not p.is_dir():
        return []
    return sorted(paths.rel(f) for f in p.rglob("*") if f.is_file() and not f.name.startswith("."))


def _files_table(pg: Page, rels: List[str], kind: str) -> List[str]:
    if not rels:
        return ["N/A."]
    out = ["| Title | Reference | Description |", "|---|---|---|"]
    for r in rels:
        out.append(f"| {_cell(os.path.splitext(os.path.basename(r))[0])} | [{os.path.basename(r)}]({pg.link(r)}) | {kind} |")
    return out


def publication(ws: Workspace) -> List[Tuple[str, str, List[str]]]:
    """(page path, title, body lines) for every node of the company tree, in SRS.md order. Each title is
    tagged with its chapter number for SRS.md."""
    project = (ws.state.get("project") or {}).get("name") or "Product"
    pages: List[Tuple[str, str, List[str]]] = []

    def add(rel, title, render):
        pg = Page(ws, rel, SRS_HOMES)
        pages.append((rel, title, render(pg)))

    def intro(pg):
        ov = ws.docs.get(schema.artifact_type("product-overview")["path"])
        overview = []
        for t in ("Objective", "Scope"):
            sec = subsection(ov.body, t) if ov else None
            if sec:
                overview += [f"### {t}", "", sec.strip(), ""]
        abbrev = [t for t in ws.items_in("glossary") if t.get("kind") in ("ABBREVIATION", "NOTATION")]
        rows = ["| Acronym | Reference |", "|---|---|"] + [f"| {_cell(t.get('term'))} | {_cell(t.get('definition'))} |"
                                                           for t in abbrev]
        refs = (["User requirement documents:", ""]
                + _files_table(pg, _listing("input-management/user-requirements"), "User requirement document")
                + ["", "Reference documents:", ""]
                + _files_table(pg, _listing("input-management/reference-documents"), "Reference document"))
        return (["## Purpose", "", INTRO_PURPOSE, "", "## Overview", ""] + (overview or ["_No product overview yet._", ""])
                + ["## Intended Audience and Reading Suggestions", "", INTRO_AUDIENCE, "", "## Abbreviations", ""]
                + (rows if abbrev else ["See the glossary."]) + ["", "## References", ""] + refs)

    add("srs/introduction.md", "Introduction", intro)
    add("srs/input-management/meeting-minutes.md", "Meeting Minutes",
        lambda pg: _files_table(pg, _listing("input-management/meeting-minutes"), "Meeting minutes"))
    add("srs/input-management/user-requirements.md", "User Requirements", lambda pg: (
        _files_table(pg, _listing("input-management/user-requirements"), "User requirement document") + ["", "## Requirements", "",
        "| ID | Requirement | Type | Priority | Source |", "|---|---|---|---|---|"]
        + [f'| <a id="{r["id"]}"></a>{r["id"]} | **{_cell(r.get("name"))}**<br>{_cell(r.get("description"))} | '
           f"{_cell(str(r.get('type', '')).replace('_', ' ').title())} | {r.get('priority', '')} | {_cell(r.get('source'))} |"
           for r in ws.items_in("requirements")]))
    add("srs/input-management/reference-documents.md", "Reference Documents",
        lambda pg: _files_table(pg, _listing("input-management/reference-documents"), "Reference document"))
    add("srs/high-level-requirements/object-relationship-diagram.md", "Object Relationship Diagram", ord_body)
    add("srs/high-level-requirements/actor.md", "Actor", lambda pg: ["| # | Actor | Description |", "|---|---|---|"] + [
        f'| {n} | <a id="{a["id"]}"></a>{a["id"]} {_cell(a.get("name"))} | {_cell(actor_description(ws, a))} |'
        for n, a in enumerate(ws.items_in("actors"), 1)])
    add("srs/high-level-requirements/workflow.md", "Workflow", workflow_body)
    add("srs/high-level-requirements/state-transition.md", "State Transition", state_transition_body)
    add("srs/high-level-requirements/use-case-diagram.md", "Use Case Diagram", use_case_diagram_body)
    add("srs/high-level-requirements/permission-matrix.md", "Permission Matrix", permission_matrix_body)
    add("srs/high-level-requirements/site-map.md", "Site Map", site_map_body)
    add("srs/functional-requirements/object.md", "Object",
        lambda pg: sum((object_section(pg, e, 2) for e in ws.items_in("entities")), []) or ["No objects yet."])

    def specs(pg):
        out = []
        for app in ws.items_in("applications") or [{"id": None, "name": "System"}]:
            ucs = [u for u in ws.items_in("use-cases") if u.get("application") == app["id"]]
            if not ucs:
                continue
            out += [f"## {app.get('name')}", ""]
            for bp in ws.items_in("business-processes") + [{"id": None}]:
                group = [u for u in ucs if u.get("business_process") == bp["id"]]
                if group:
                    if bp["id"]:
                        out += [f"### {bp['id']} — {bp.get('name', '')}", ""]
                    for u in group:
                        out += use_case_spec_section(pg, u, 4)
        return out or ["No use cases yet."]

    add("srs/functional-requirements/use-case-specifications.md", "Use Case Specifications", specs)
    add("srs/functional-requirements/common-use-cases.md", "Common Use Cases", lambda pg: (
        ["This is the list of standard system functions that let users work with an object. Each provides a typical "
         "flow and business rules; a use case that follows one specifies only what differs.", ""]
        + (sum((common_use_case_section(pg, c, 2) for c in ws.items_in("common-use-cases")), []) or ["None."])))
    add("srs/functional-requirements/common-business-rule.md", "Common Business Rule", lambda pg: (
        ["Business rules used across use cases. Each applies only to the use cases that refer to it.", "",
         "| BR Code | Kind | Description |", "|---|---|---|"]
        + [f'| <a id="{b["id"]}"></a>{b["id"]} | {str(b.get("kind", "")).title()} | '
           f"**{_cell(b.get('name'))}:**<br>{_cell(b.get('description'))} |" for b in ws.items_in("business-rules")]))

    def mockups(pg):
        out = ["The screens and their components, associated with one or more use cases. The site map is under "
               "High Level Requirements.", ""]
        for app in ws.items_in("applications"):
            scr = [s for s in ws.items_in("screens") if s.get("application") == app["id"]]
            if scr:
                out += [f"## {app.get('name')}", ""]
                for s in scr:
                    out += screen_section(pg, s, 3)
        return out

    add("srs/mockups-screen.md", "Mockups Screen", mockups)
    add("srs/agile-project/epic.md", "Epic", lambda pg: sum((epic_section(pg, e, 2) for e in ws.epics), []) or ["No epics yet."])
    add("srs/agile-project/user-story.md", "User Story", lambda pg: story_table(pg, ws.items_in("user-stories"))
        if ws.items_in("user-stories") else ["No user stories yet."])
    add("srs/non-functional-requirements.md", "Non-Functional Requirements", nfr_body)

    def other(pg):
        out = []
        for t in ("field-controls", "message-configuration", "list-behaviour"):
            doc = ws.docs.get(schema.artifact_type(t)["path"])
            if doc:
                out += [demote(re.sub(r"^#\s.*\n", "", doc.body.strip() + "\n", count=1).strip(), 0), ""]
        return out or ["Not written yet (overview step)."]

    add("srs/other-requirements.md", "Other Requirements", other)
    add("srs/integration.md", "Integration", lambda pg: ["| ID | Integration | Direction | Purpose | Owner | Protocol |",
                                                          "|---|---|---|---|---|---|"] + [
        f'| <a id="{i["id"]}"></a>{i["id"]} | {_cell(i.get("system") or i.get("name"))} | {i.get("direction", "")} | '
        f"{_cell(i.get('purpose'))} | {_cell(i.get('owner'))} | {_cell(i.get('protocol'))} |" for i in ws.items_in("integrations")])
    add("srs/data-migration.md", "Data Migration", lambda pg: ["Not in scope (addendum D-62)."])
    add("srs/appendices/message-list.md", "Message List", messages_body)
    add("srs/appendices/email-templates.md", "Email Templates", email_templates_body)
    add("srs/appendices/glossary.md", "Glossary", glossary_body)
    add("srs/appendices/open-questions-and-assumptions.md", "Open Questions and Assumptions", lambda pg: (
        ["## Open Questions", "", "| ID | Question | Status | Stakeholder | Answer |", "|---|---|---|---|---|"]
        + [f'| <a id="{q["id"]}"></a>{q["id"]} | {_cell(q.get("question"))} | {q.get("status", "")} | '
           f"{q.get('target_stakeholder', '')} | {_cell(q.get('answer'))} |" for q in ws.items_in("open-questions")]
        + ["", "## Assumptions", "", "| ID | Assumption | Status |", "|---|---|---|"]
        + [f'| <a id="{a["id"]}"></a>{a["id"]} | {_cell(a.get("statement"))} | {a.get("status", "")} |'
           for a in ws.items_in("assumptions")]))
    return pages


CHAPTERS = [  # (chapter title, page paths) — the company's docx order, with the sidebar's extra nodes
    ("Introduction", ["srs/introduction.md"]),
    ("Input Management", ["srs/input-management/meeting-minutes.md", "srs/input-management/user-requirements.md",
                          "srs/input-management/reference-documents.md"]),
    ("High Level Requirements", ["srs/high-level-requirements/object-relationship-diagram.md",
                                 "srs/high-level-requirements/actor.md", "srs/high-level-requirements/workflow.md",
                                 "srs/high-level-requirements/state-transition.md",
                                 "srs/high-level-requirements/use-case-diagram.md",
                                 "srs/high-level-requirements/permission-matrix.md",
                                 "srs/high-level-requirements/site-map.md"]),
    ("Functional Requirements", ["srs/functional-requirements/object.md",
                                 "srs/functional-requirements/use-case-specifications.md",
                                 "srs/functional-requirements/common-use-cases.md",
                                 "srs/functional-requirements/common-business-rule.md"]),
    ("Mockups Screen", ["srs/mockups-screen.md"]),
    ("Agile Project", ["srs/agile-project/epic.md", "srs/agile-project/user-story.md"]),
    ("Non-Functional Requirements", ["srs/non-functional-requirements.md"]),
    ("Other Requirements", ["srs/other-requirements.md"]),
    ("Integration", ["srs/integration.md"]),
    ("Data Migration", ["srs/data-migration.md"]),
    ("Appendices", ["srs/appendices/message-list.md", "srs/appendices/email-templates.md",
                    "srs/appendices/glossary.md", "srs/appendices/open-questions-and-assumptions.md"]),
]


def _gate_line(ws: Workspace) -> str:
    from .engine import GateCache
    run = ws.active_run()
    if not run:
        return ""
    gs = GateCache(ws)
    g2, g9 = gs("GATE-02", run["run_id"])["status"], gs("GATE-09", run["run_id"])["status"]
    specs = [uc for uc in ws.backlog_ucs if gs("GATE-05", uc)["status"] == "APPROVED"]
    return (f"Overview (GATE-02): {g2} · Technical baseline (GATE-09): {g9} · "
            f"Use case specifications approved (GATE-05): {len(specs)} of {len(ws.items_in('use-cases'))}")


def publish(ws: Workspace) -> List[str]:
    """Write ba-ai/srs/ (wiped first: it is generated). Returns the files written, relative to ba-ai/."""
    import shutil
    if paths.SRS.exists():
        shutil.rmtree(paths.SRS)
    project = (ws.state.get("project") or {}).get("name") or "Product"
    when = store.now()
    pages = publication(ws)
    by_rel = {rel: (title, body) for rel, title, body in pages}
    written = []
    note = f"<!-- GENERATED by `tools/ba publish` on {when}. Do not edit: change the BA artifacts, then publish again. -->"
    for rel, title, body in pages:
        store.write_atomic(paths.BA / rel, "\n".join([note, f"# {title}", "", f"_{project} — System Requirement "
                                                      f"Specification. Generated {when[:10]}._", ""] + body).rstrip() + "\n")
        written.append(rel)
    toc, full = [], []
    for n, (chapter, rels) in enumerate(CHAPTERS, 1):
        toc.append(f"{n}. [{chapter}](#{n}-{re.sub(r'[^a-z0-9]+', '-', chapter.lower()).strip('-')})")
        full += [f"# {n}. {chapter}", ""]
        for m, rel in enumerate(rels, 1):
            title, body = by_rel[rel]
            if len(rels) > 1 or title != chapter:
                full += [f"## {n}.{m}. {title}", "", demote("\n".join(body), 1), ""]
            else:
                full += ["\n".join(body), ""]
    srs = [note, f"# {project} — System Requirement Specification", "",
           f"Generated by `tools/ba publish` on {when}. {_gate_line(ws)}", "",
           "This document is generated from the BA workspace: its catalogs, the approved documents and the generated "
           "views. Each chapter also exists as a page of the company documentation tree in this folder.", "",
           "## Contents", ""] + toc + [""] + [demote("\n".join(full), 0)]
    store.write_atomic(paths.SRS / "SRS.md", "\n".join(srs).rstrip() + "\n")
    written.append("srs/SRS.md")
    return written
