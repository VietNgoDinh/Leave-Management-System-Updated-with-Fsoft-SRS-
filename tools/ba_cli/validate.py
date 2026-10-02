"""Deterministic artifact checks (D-19, D-64). Errors block gate requests."""
from __future__ import annotations

import re
from typing import Callable, Dict, List, Optional, Set

from . import paths, schema, store
from .ids import CODE_REF_RE, MESSAGE_PREFIXES, as_list, find_refs, id_format_ok, prefix_of
from .workspace import (Doc, Workspace, column, field, iter_headings, norm_heading, sections, subsection,
                        tables)

TRANSITION_RE = re.compile(r"^\s*(\(new\)|[A-Za-z0-9_ ]+?)\s*->\s*([A-Za-z0-9_ ]+?)\s*:\s*(\S.*)$")
PAIR_RE = re.compile(r"^\s*(\(new\)|[A-Za-z0-9_]+)\s*->\s*([A-Za-z0-9_]+)\s*$")
PLACEHOLDER_RE = re.compile(r"<<\s*([^<>]+?)\s*>>")
STEP_NO_RE = re.compile(r"\((\d+(?:\.\d+)*)\)")
ATTR_RE = re.compile(r"\bENT-\d{3,4}\.[A-Za-z_][A-Za-z0-9_]*")
COMPONENT_COLUMNS = ["#", "Component", "Component Type", "Editable", "Mandatory", "Default Value", "Description"]
YES_NO_NA = {"yes", "no", "n/a", "na"}


class Issue:
    def __init__(self, level: str, path: str, msg: str):
        self.level, self.path, self.msg = level, path, msg

    def __str__(self) -> str:
        return f"{self.level:5} ba-ai/{self.path}: {self.msg}"


def _norm_text(s: str) -> str:
    s = s.strip().strip('"“”').replace("“", '"').replace("”", '"').replace("’", "'")
    return " ".join(s.split())


# ------------------------------------------------------------------ catalog items

def validate_item(ws: Workspace, cname: str, item: dict, known: Set[str]) -> List[str]:
    cdef = schema.catalogs()[cname]
    iid = item.get("id")
    msgs: List[str] = []
    prefix = schema.prefix_for_item(cname, item)
    if prefix is None:
        allowed = schema.catalog_prefixes(cname)
        if not any(id_format_ok(iid, p) for p in allowed):
            msgs.append(f"{iid}: ID must look like {'/'.join(allowed)}-NNN")
    elif not id_format_ok(iid, prefix):
        msgs.append(f"{iid}: ID must look like {prefix}-NNN"
                    + (f" (its {cdef['prefix_by']['field']} decides the code)" if cdef.get("prefix_by") else ""))
    for f in cdef.get("required", []):
        if item.get(f) is None or item.get(f) == "":
            msgs.append(f"{iid}: missing required field '{f}'")
    for f, cond in (cdef.get("required_when") or {}).items():
        if all(item.get(k) == v for k, v in cond.items()) and item.get(f) in (None, "", []):
            msgs.append(f"{iid}: missing '{f}', required when "
                        + " and ".join(f"{k} is {v}" for k, v in cond.items()))
    for f, allowed in (cdef.get("enums") or {}).items():
        v = item.get(f)
        if v is not None and v not in allowed:
            msgs.append(f"{iid}: {f}={v!r} must be one of {allowed}")
    for f in cdef.get("booleans") or []:
        if item.get(f) is not None and not isinstance(item.get(f), bool):
            msgs.append(f"{iid}: {f} must be true or false")
    for f, allowed in (cdef.get("list_enums") or {}).items():
        for v in as_list(item.get(f)):
            if v not in allowed:
                msgs.append(f"{iid}: {f} value {v!r} must be one of {allowed}")
    if item.get("baseline") is not None and item["baseline"] not in schema.enum("baseline"):
        msgs.append(f"{iid}: baseline must be one of {schema.enum('baseline')}")
    for f, ref in (cdef.get("refs") or {}).items():
        msgs += _ref_msgs(iid, f, as_list(item.get(f)), ref["targets"], known)
    for f, ref in (cdef.get("item_refs") or {}).items():
        for e in as_list(item.get(f)):
            if not isinstance(e, dict):
                msgs.append(f"{iid}: every entry of {f} must be a mapping with '{ref['key']}' ({e!r:.60})")
                continue
            msgs += _ref_msgs(iid, f"{f}.{ref['key']}", as_list(e.get(ref["key"])), ref["targets"], known)
    check = ITEM_CHECKS.get(cname)
    if check:
        msgs += check(ws, iid, item, known)
    return msgs


def _ref_msgs(iid, f, vals, targets, known) -> List[str]:
    out = []
    for v in vals:
        if not isinstance(v, str):
            out.append(f"{iid}: {f} must list IDs, got {v!r}")
        elif v not in known:
            out.append(f"{iid}: {f} references unknown ID {v}")
        elif targets != "ANY" and prefix_of(v) not in targets:
            out.append(f"{iid}: {f} must reference {'/'.join(targets)}, got {v}")
    return out


def _bp_msgs(ws, iid, item, known) -> List[str]:
    msgs = []
    step_ids = {st.get("id") for st in as_list(item.get("steps")) if isinstance(st, dict)}
    for st in as_list(item.get("steps")):
        sid = st.get("id") if isinstance(st, dict) else None
        if not sid or not re.fullmatch(re.escape(str(iid)) + r"-S\d{2}", sid):
            msgs.append(f"{iid}: step id {sid!r} must look like {iid}-S01")
            continue
        if not st.get("name"):
            msgs.append(f"{sid}: missing name")
        if st.get("actor") and st["actor"] not in known:
            msgs.append(f"{sid}: actor {st['actor']} unknown")
        for uc in as_list(st.get("use_cases")):
            if uc not in known:
                msgs.append(f"{sid}: use case {uc} unknown")
        nexts = as_list(st.get("next"))
        for nx in nexts:
            to = nx.get("to") if isinstance(nx, dict) else None
            if to != "END" and to not in step_ids:
                msgs.append(f"{sid}: branch target {to!r} must be a step of {iid} (or END)")
            if len(nexts) > 1 and isinstance(nx, dict) and not nx.get("when"):
                msgs.append(f"{sid}: a step with several next steps needs a 'when' condition on each")
    return msgs


def _entity_msgs(ws, iid, item, known) -> List[str]:
    msgs = []
    for a in as_list(item.get("attributes")):
        if not isinstance(a, dict) or not a.get("name") or not a.get("type"):
            msgs.append(f"{iid}: every attribute needs 'name' and 'type' ({a!r:.60})")
            continue
        for b in ("mandatory", "unique"):
            if a.get(b) is not None and not isinstance(a.get(b), bool):
                msgs.append(f"{iid}.{a['name']}: {b} must be true or false")
        ml = a.get("max_length")
        if ml is not None and (not isinstance(ml, int) or isinstance(ml, bool) or ml <= 0):
            msgs.append(f"{iid}.{a['name']}: max_length must be a positive whole number")
        if a.get("allowed_values") is not None and not isinstance(a.get("allowed_values"), list):
            msgs.append(f"{iid}.{a['name']}: allowed_values must be a list")
    for r in as_list(item.get("relationships")):
        to = r.get("to") if isinstance(r, dict) else None
        if to not in known or prefix_of(str(to)) != "ENT":
            msgs.append(f"{iid}: relationship target {to!r} must be a known ENT")
        elif not r.get("cardinality"):
            msgs.append(f"{iid}: relationship to {to} needs a cardinality")
    msgs += _lifecycle_msgs(iid, item.get("lifecycle"))
    return msgs


def _lifecycle_msgs(iid: str, lc) -> List[str]:
    """State model (master §9 3.4) kept on the entity: states, transitions, invalid transitions."""
    if lc is None:
        return []
    if not isinstance(lc, dict) or not as_list(lc.get("states")):
        return [f"{iid}: lifecycle needs a 'states' list"]
    states = {str(x) for x in as_list(lc.get("states"))}
    msgs = []
    for key in ("transitions", "invalid_transitions"):
        for t in as_list(lc.get(key)):
            parsed = parse_transition(t)
            if parsed is None:
                msgs.append(f"{iid}: lifecycle {key} entry {t!r:.60} must read 'FROM -> TO: event' "
                            f"or be a mapping with from / to / event")
                continue
            frm, to, ev = parsed
            for s_ in (frm, to):
                if s_ not in states and s_ not in ("(new)", None):
                    msgs.append(f"{iid}: lifecycle {key} uses state {s_!r}, which is not in states")
            if not ev:
                msgs.append(f"{iid}: lifecycle {key} {frm} -> {to} needs a triggering event")
    return msgs


def parse_transition(t):
    """(from, to, event) of a lifecycle entry, or None when it can't be read."""
    if isinstance(t, dict):
        return t.get("from"), t.get("to"), t.get("event")
    m = TRANSITION_RE.match(str(t))
    return (m.group(1).strip(), m.group(2).strip(), m.group(3)) if m else None


def lifecycle_pairs(ent: Optional[dict]) -> Set[tuple]:
    out = set()
    for t in as_list(((ent or {}).get("lifecycle") or {}).get("transitions")):
        p = parse_transition(t)
        if p:
            out.add((p[0], p[1]))
    return out


def _use_case_msgs(ws, iid, item, known) -> List[str]:
    msgs = []
    obj = ws.item(item.get("object")) if item.get("object") in known else None
    states = {str(s) for s in as_list(((obj or {}).get("lifecycle") or {}).get("states"))}
    for s in as_list(item.get("allowed_states")):
        if obj is not None and str(s) not in states:
            msgs.append(f"{iid}: allowed state {s!r} is not a state of {item.get('object')}'s lifecycle")
    pairs = lifecycle_pairs(obj)
    for t in as_list(item.get("transitions")):
        m = PAIR_RE.match(str(t))
        if not m:
            msgs.append(f"{iid}: transition {t!r} must read 'FROM -> TO' ((new) for creation)")
        elif obj is not None and (m.group(1), m.group(2)) not in pairs:
            msgs.append(f"{iid}: transition {t} is not in {item.get('object')}'s lifecycle")
    access = schema.enum("access")
    granted = set()
    for p in as_list(item.get("permissions")):
        if not isinstance(p, dict):
            continue
        if p.get("access") not in access:
            msgs.append(f"{iid}: permission of {p.get('actor')}: access must be one of {access}")
        if p.get("access") == "SCOPED" and not p.get("scope"):
            msgs.append(f"{iid}: permission of {p.get('actor')} is SCOPED (O**): state its scope rule in 'scope'")
        if p.get("access") not in (None, "NONE"):
            granted.add(p.get("actor"))
    for a in as_list(item.get("actor")):
        if item.get("permissions") is not None and a not in granted:
            msgs.append(f"{iid}: its actor {a} needs a permission other than NONE")
    obj_text = str(item.get("objective") or "")
    if re.match(r"\s*this\s+(function|use case)\b", obj_text, re.I):
        msgs.append(f"{iid}: write the objective as the end of \"This function allows <actors> to …\", "
                    f"e.g. \"submit a leave request\"")
    return msgs


def _message_msgs(ws, iid, item, known) -> List[str]:
    return [] if str(item.get("text") or "").strip() else [f"{iid}: the message text is empty"]


def _email_msgs(ws, iid, item, known) -> List[str]:
    msgs = []
    declared = {}
    for p in as_list(item.get("placeholders")):
        if not isinstance(p, dict) or not p.get("name") or not p.get("source"):
            msgs.append(f"{iid}: every placeholder needs a 'name' and a 'source' ({p!r:.60})")
            continue
        declared[_norm_text(str(p["name"])).lower()] = p
        src = str(p["source"])
        if not ATTR_RE.search(src) and not re.search(r"<[^<>]+>", src):
            msgs.append(f"{iid}: placeholder <<{p['name']}>> needs a source: an object attribute "
                        f"(ENT-….attribute) or a special value such as <Link to …>")
    for f in ("subject", "body"):
        for name in PLACEHOLDER_RE.findall(str(item.get(f) or "")):
            if _norm_text(name).lower() not in declared:
                msgs.append(f"{iid}: <<{name}>> in the {f} is not bound to a source in 'placeholders'")
    for f in ("to", "cc"):
        for v in find_refs(str(item.get(f) or "")):
            if v not in known:
                msgs.append(f"{iid}: {f} mentions unknown ID {v}")
    return msgs


def _cmuc_msgs(ws, iid, item, known) -> List[str]:
    msgs = []
    if not as_list(item.get("activities_flow")):
        msgs.append(f"{iid}: activities_flow needs the numbered steps")
    types = schema.enum("step_rule_type")
    for r in as_list(item.get("step_rules")):
        if not isinstance(r, dict):
            msgs.append(f"{iid}: every step rule must be a mapping")
            continue
        rid = r.get("id")
        if not re.fullmatch(re.escape(str(iid)) + r"-BR-\d{2}", str(rid)):
            msgs.append(f"{iid}: step rule id {rid!r} must look like {iid}-BR-01")
        for f in ("step", "type", "title", "description"):
            if not r.get(f):
                msgs.append(f"{rid}: missing '{f}'")
        if r.get("type") and r["type"] not in types:
            msgs.append(f"{rid}: type must be one of {types}")
        if r.get("title") and not str(r["title"]).strip().endswith("Rules"):
            msgs.append(f"{rid}: the title names the rule type, e.g. \"Validating Rules\"")
    blob = " ".join(str(v) for v in item.values() if isinstance(v, str)) + " ".join(
        str(r.get("description", "")) for r in as_list(item.get("step_rules")) if isinstance(r, dict))
    if "[[" in blob:
        msgs.append(f"{iid}: replace every [[message: …]] / [[rule: …]] placeholder with the message code or BR ID")
    for v in find_refs(blob):
        if v not in known and not v.startswith(str(iid)):
            msgs.append(f"{iid}: mentions unknown ID {v}")
    return msgs


def _story_msgs(ws, iid, item, known) -> List[str]:
    uc = item.get("use_case")
    return [f"{iid}: acceptance criterion {ac} must be one of {uc}'s ({uc}-AC-nn)"
            for ac in as_list(item.get("acceptance_criteria")) if not str(ac).startswith(f"{uc}-AC-")]


ITEM_CHECKS: Dict[str, Callable] = {
    "business-processes": _bp_msgs,
    "entities": _entity_msgs,
    "use-cases": _use_case_msgs,
    "messages": _message_msgs,
    "email-templates": _email_msgs,
    "common-use-cases": _cmuc_msgs,
    "user-stories": _story_msgs,
}


# ------------------------------------------------------------------ document checks

def _headings_with(doc: Doc, pattern: str) -> List[str]:
    rx = re.compile(pattern)
    out = []
    for _, _, text in iter_headings(doc.body):
        m = rx.match(text)
        if m:
            out.append(m.group(1))
    return out


def _check_mermaid(ws, doc, E, W):
    if "```mermaid" not in doc.body:
        E(doc.rel, "needs a Mermaid diagram (```mermaid block)")


def screen_sections(doc: Doc) -> List[tuple]:
    """(SCR ID, heading, section text) for every screen section of a UI document."""
    out = []
    for _lvl, h, text in sections(doc.body):
        m = re.match(r"^(SCR-\d{3,4})\b", h)
        if m:
            out.append((m.group(1), h, text))
    return out


def _check_screen_sections(ws, doc, E, W):
    scrs = [s for s, _h, _t in screen_sections(doc)]
    if not scrs:
        E(doc.rel, "no screen sections — each screen needs a heading like '### SCR-001 — Name screen'")
    rel_screens = set(as_list((doc.fm.get("relations") or {}).get("screens")))
    cat = schema.catalogs()["screens"]["path"]
    for s in scrs:
        if ws.catalog_of(s) != "screens":
            E(doc.rel, f"{s} is not in {cat} — add it with `tools/ba catalog add screens`")
        if s not in rel_screens:
            W(doc.rel, f"{s} has a section but is missing from relations.screens")


def known_component_types(ws) -> Set[str]:
    """Control names and aliases from the project's field controls (else the company standard)."""
    doc = ws.docs.get(schema.artifact_type("field-controls")["path"])
    text = doc.body if doc else ((paths.STANDARDS / "field-controls.md").read_text(encoding="utf-8")
                                 if (paths.STANDARDS / "field-controls.md").exists() else "")
    names: Set[str] = set()
    for header, rows in tables(text):
        ci = column(header, "Control")
        if ci is None:
            ci = column(header, "Component type")
        ai = column(header, "Also written as")
        if ci is None:
            continue
        for r in rows:
            if ci < len(r):
                names |= _type_names(r[ci])
            if ai is not None and ai < len(r):
                for alias in re.split(r"[;,]", r[ai]):
                    names |= _type_names(alias)
    return {n for n in names if n and n not in ("—", "-")}


def _type_names(cell: str) -> Set[str]:
    cell = cell.replace("–", "-")
    base = re.sub(r"\([^)]*\)", "", cell)
    out = {_norm_type(base)}
    out |= {_norm_type(x) for x in re.findall(r"\(([^)]*)\)", cell)}
    return out


def _norm_type(s: str) -> str:
    return " ".join(re.sub(r"[^a-z0-9/ ]+", " ", s.lower()).split())


def _check_component_tables(ws, doc, E, W):
    """D-51: every screen has the company component table; inputs name their source attribute and
    every button refers to the use case it triggers."""
    types = known_component_types(ws)
    for scr, _h, text in screen_sections(doc):
        comp = subsection(text, "Components")
        found = None
        for header, rows in tables(comp or ""):
            if column(header, "Component Type") is not None:
                found = (header, rows)
                break
        if found is None:
            E(doc.rel, f"{scr}: needs a '#### Components' table with the columns {' | '.join(COMPONENT_COLUMNS)}")
            continue
        header, rows = found
        missing = [c for c in COMPONENT_COLUMNS if column(header, c) is None]
        if missing:
            E(doc.rel, f"{scr}: the component table lacks the column(s) {', '.join(missing)}")
            continue
        idx = {c: column(header, c) for c in COMPONENT_COLUMNS}
        if not rows:
            E(doc.rel, f"{scr}: the component table has no rows")
        for r in rows:
            def cell(c):
                return r[idx[c]].strip() if idx[c] < len(r) else ""
            name, ctype, desc = cell("Component"), cell("Component Type"), cell("Description")
            label = f"{scr} component '{name}'"
            for c in ("Editable", "Mandatory"):
                if cell(c).lower() not in YES_NO_NA:
                    E(doc.rel, f"{label}: {c} must be Yes, No or N/A (got {cell(c)!r})")
            if types and _norm_type(re.sub(r"\([^)]*\)", "", ctype)) not in types:
                W(doc.rel, f"{label}: component type {ctype!r} is not in other-requirements/field-controls.md")
            if cell("Editable").lower() == "yes" and not ATTR_RE.search(desc):
                E(doc.rel, f"{label}: an editable component names its source attribute (ENT-xxx.attribute) "
                           f"in its Description")
            if _norm_type(ctype) == "button" and not re.search(r"\bUC-\d{3,4}\b", desc):
                E(doc.rel, f"{label}: a button refers to the use case it triggers (\"Refer to UC-…\")")
        if re.search(r"(?i)\b(table|column header)\b", " ".join(r[idx['Component Type']] for r in rows
                                                                 if idx["Component Type"] < len(r))):
            for f in ("Data Source", "Default Sorting"):
                if field(text, f) is None:
                    W(doc.rel, f"{scr}: a list screen states its **{f}:**")


def step_rule_type(value: Optional[str]) -> str:
    """'Screen Displaying' → SCREEN_DISPLAYING, 'Processing (Submitting)' → PROCESSING, 'Display/Search' →
    DISPLAY_SEARCH."""
    v = re.sub(r"\(.*?\)", "", value or "").strip().upper()
    return re.sub(r"[\s/-]+", "_", v)


def message_codes(text: str) -> Set[str]:
    return {r for r in find_refs(text) if prefix_of(r) in MESSAGE_PREFIXES}


def _check_message_texts(ws, doc, E, W):
    """R3: messages show their code, and the text next to it is the catalog's text (D-52)."""
    used = message_codes(doc.body)
    for scr, _h, text in screen_sections(doc):
        msg = subsection(text, "Messages")
        for header, rows in tables(msg or ""):
            ci, ti = column(header, "Code"), column(header, "Message")
            if ci is None or ti is None:
                E(doc.rel, f"{scr}: the Messages table needs the columns Code and Message")
                continue
            for r in rows:
                code = r[ci].strip() if ci < len(r) else ""
                text_ = r[ti] if ti < len(r) else ""
                if not code:
                    E(doc.rel, f"{scr}: message {text_.strip()[:50]!r} has no code — add it to the message "
                               f"catalog (`tools/ba catalog add messages`) and show its code")
                    continue
                item = ws.item(code)
                if item is None or ws.catalog_of(code) != "messages":
                    continue                                  # reported as an unknown ID
                if _norm_text(text_) != _norm_text(str(item.get("text", ""))):
                    E(doc.rel, f"{scr}: {code} reads {_norm_text(text_)[:60]!r} here but "
                               f"{_norm_text(str(item.get('text', '')))[:60]!r} in the message catalog")
    rel_msgs = set(as_list((doc.fm.get("relations") or {}).get("messages")))
    for c in sorted(used - rel_msgs):
        W(doc.rel, f"{c} is used but missing from relations.messages")


def _check_behaviour(ws, doc, E, W):
    """D-47, D-48: the use case description, the activities flow and its step rules."""
    head = subsection(doc.body, "Use Case Description") or ""
    for f in ("Trigger", "Pre-condition", "Post-condition"):
        if not field(head, f):
            E(doc.rel, f"Use Case Description needs a '- **{f}:** …' line")
    flow = subsection(doc.body, "Activities Flow") or ""
    flow_steps = set(STEP_NO_RE.findall(flow))
    uc_item = ws.item(doc.id) or {}
    follows = as_list(uc_item.get("follows"))
    cmuc_steps = {c: set(STEP_NO_RE.findall(" ".join(str(x) for x in as_list((ws.item(c) or {})
                                                                                .get("activities_flow")))))
                  for c in follows}
    obj = ws.item(uc_item.get("object"))
    pairs = lifecycle_pairs(obj)
    types = schema.enum("step_rule_type")
    rules = {sid: s for sid, s in ws.scoped.items() if s["doc"] == doc.rel and s["kind"] == "BR"}
    if not rules and not follows:
        E(doc.rel, "no step rules — each needs a heading like '### UC-001-BR-01 — Screen Displaying Rules'")
    for sid, s in sorted(rules.items()):
        if s["uc"] != doc.id:
            E(doc.rel, f"{sid} belongs to {s['uc']}, not {doc.id}")
        if not s["title"].strip().endswith("Rules"):
            E(doc.rel, f"{sid}: the title names the rule type, e.g. \"{sid} — Validating Rules\"")
        step = field(s["text"], "Step")
        if not step:
            E(doc.rel, f"{sid} needs a '- **Step:** (n)' line keyed to the activities flow")
        else:
            for m in re.finditer(r"(CMUC-\d{3,4})?\s*\((\d+(?:\.\d+)*)\)", step):
                cm, n = m.group(1), m.group(2)
                if cm:
                    if cm not in follows:
                        E(doc.rel, f"{sid}: step {cm} ({n}) belongs to a common use case {doc.id} does not follow")
                    elif n not in cmuc_steps.get(cm, set()):
                        E(doc.rel, f"{sid}: {cm} has no step ({n})")
                elif n not in flow_steps:
                    E(doc.rel, f"{sid}: step ({n}) is not in the Activities Flow")
            if not STEP_NO_RE.search(step):
                E(doc.rel, f"{sid}: **Step:** must name step numbers like (2) or CMUC-002 (4)")
        rtype = step_rule_type(field(s["text"], "Type"))
        if rtype not in types:
            E(doc.rel, f"{sid}: **Type:** must be one of {', '.join(t.replace('_', ' ').title() for t in types)}")
        codes = message_codes(s["text"])
        if rtype == "VALIDATING" and not any(prefix_of(c) in ("IEM", "EMSG") for c in codes):
            E(doc.rel, f"{sid}: a Validating rule names the message the user sees (IEM-… or EMSG-…)")
        if rtype == "CONFIRMATION" and not any(prefix_of(c) == "CFD" for c in codes):
            E(doc.rel, f"{sid}: a Confirmation rule names its confirmation message (CFD-…)")
        change = field(s["text"], "State change")
        if change:
            m = PAIR_RE.match(re.sub(r"^ENT-\d{3,4}:?\s*", "", change))
            if not m or (obj is not None and (m.group(1), m.group(2)) not in pairs):
                E(doc.rel, f"{sid}: state change {change!r} is not a transition of "
                           f"{uc_item.get('object')}'s lifecycle ('FROM -> TO')")
    for kind in ("AF", "EF"):
        for sid, s in ws.scoped.items():
            if s["doc"] == doc.rel and s["kind"] == kind and s["uc"] != doc.id:
                E(doc.rel, f"{sid} belongs to {s['uc']}, not {doc.id}")
    for c in follows:
        if c not in doc.body:
            W(doc.rel, f"{doc.id} follows {c}; say which of its steps differ (or that none do)")
    rel = doc.fm.get("relations") or {}
    for key, prefixes in (("email_templates", ("ET",)), ("messages", MESSAGE_PREFIXES)):
        used = {r for r in find_refs(doc.body) if prefix_of(r) in prefixes}
        for c in sorted(used - set(as_list(rel.get(key)))):
            W(doc.rel, f"{c} is used but missing from relations.{key}")


def _check_workflow_steps(ws, doc, E, W):
    """D-56: the workflow shows every step of its process."""
    if ws.catalog_of(doc.id) != "business-processes":
        return
    for sid in sorted(s for s, rec in ws.steps.items() if rec["bp"] == doc.id):
        if sid not in doc.body:
            E(doc.rel, f"{sid} ({ws.label(sid)[:50]}) is not in the workflow — show every step of {doc.id}")


def _check_site_map_pages(ws, doc, E, W):
    """D-58: the company's Page | Description | Permission table, covering the application's screens."""
    pages = subsection(doc.body, "Pages") or ""
    table = next(((h, r) for h, r in tables(pages) if column(h, "Page") is not None), None)
    if table is None or any(column(table[0], c) is None for c in ("Description", "Permission")):
        E(doc.rel, "Pages needs a table with the columns Page | Description | Permission")
        return
    for s in ws.items_in("screens"):
        if s.get("application") == doc.id and s["id"] not in pages:
            W(doc.rel, f"{s['id']} {s.get('name')} is not in the Pages table")


def _check_field_controls(ws, doc, E, W):
    text = subsection(doc.body, "Common Field Controls") or ""
    if not any(column(h, "Control") is not None for h, _r in tables(text)):
        E(doc.rel, "Common Field Controls needs a table with a Control column")


def _check_prototype_index(ws, doc, E, W):
    if not (doc.path.parent / "index.html").exists():
        E(doc.rel, "prototype folder has no index.html")


def _check_api_sections(ws, doc, E, W):
    apis = _headings_with(doc, r"^(API-\d{3,4})\b")
    if not apis:
        E(doc.rel, "no API sections — each API needs a heading like '### API-001 — POST /api/v1/…'")
    rel_apis = set(as_list((doc.fm.get("relations") or {}).get("apis")))
    for a in apis:
        if ws.catalog_of(a) != "apis":
            E(doc.rel, f"{a} is not in technical/api/api-catalog.yaml — add it with `tools/ba catalog add apis`")
        if a not in rel_apis:
            W(doc.rel, f"{a} has a section but is missing from relations.apis")


def _own_scoped(ws, doc, kind):
    return {sid: s for sid, s in ws.scoped.items() if s["doc"] == doc.rel and s["kind"] == kind}


VAGUE_RE = re.compile(r"\b(works? (correctly|properly|as expected|fine)|user[- ]friendly|"
                      r"intuitive|fast enough|quickly|appropriate(ly)?|etc\.?)(?=\W|$)", re.I)


def _check_gherkin(ws, doc, E, W):
    acs = _own_scoped(ws, doc, "AC")
    if not acs:
        E(doc.rel, "no acceptance criteria — each needs a heading like '### UC-001-AC-01 — Title'")
    for sid, s in acs.items():
        if s["uc"] != doc.id:
            E(doc.rel, f"{sid} belongs to {s['uc']}, not {doc.id}")
        missing = [k for k in ("Given", "When", "Then") if not re.search(rf"\b{k}\b", s["text"])]
        if missing:
            E(doc.rel, f"{sid} is not testable — missing {', '.join(missing)}")
        vague = VAGUE_RE.search(s["title"] + "\n" + s["text"])
        if vague:
            W(doc.rel, f"{sid} uses vague wording '{vague.group(0)}' — state an observable result")
    covered = set()
    for s in acs.values():
        covered |= find_refs(s["text"])
    for sid, s in ws.scoped.items():
        if s["uc"] == doc.id and s["kind"] in ("BR", "AF", "EF") and sid not in covered:
            W(doc.rel, f"{sid} ({s['title'][:40]}) is covered by no acceptance criterion")


def _field(text: str, name: str) -> Optional[str]:
    return field(text, name)


def _check_test_cases(ws, doc, E, W):
    own = {tc: t for tc, t in ws.test_cases.items() if t["doc"] == doc.rel}
    if not own:
        E(doc.rel, "no test cases — each needs a heading like '### TC-001 — Title' (IDs from `tools/ba next-id TC`)")
    reg = (store.load_json(paths.REGISTRY, {}) or {}).get("counters", {}).get("TC", 0)
    cats = schema.enum("test_category")
    verified = set()
    for tc, t in own.items():
        if int(tc.split("-")[1]) > reg:
            E(doc.rel, f"{tc} was never allocated — get test case IDs from `tools/ba next-id TC`")
        acs = set(re.findall(r"\b" + re.escape(doc.id) + r"-AC-\d{2}\b", _field(t["text"], "Verifies") or ""))
        if not acs:
            E(doc.rel, f"{tc} needs a '**Verifies:** {doc.id}-AC-..' line naming the criteria it tests")
        for ac in acs:
            if ac not in ws.scoped:
                E(doc.rel, f"{tc} verifies {ac}, which is not declared in the acceptance criteria")
        verified |= acs
        cat = (_field(t["text"], "Category") or "").upper().replace(" ", "_")
        if cat not in cats:
            E(doc.rel, f"{tc}: **Category:** must be one of {cats}")
        for f in ("Steps", "Expected"):
            if _field(t["text"], f) is None and not re.search(r"\*\*" + f, t["text"], re.I):
                E(doc.rel, f"{tc} needs a **{f}:** part")
    for ac in sorted(sid for sid, x in ws.scoped.items() if x["kind"] == "AC" and x["uc"] == doc.id):
        if ac not in verified:
            E(doc.rel, f"{ac} is not verified by any test case")
    automated = [tc for tc, t in own.items()
                 if not (_field(t["text"], "Automation") or "").lower().startswith("manual")]
    files = as_list(doc.fm.get("test_files"))
    if automated and not files:
        E(doc.rel, "frontmatter 'test_files' must list the automated acceptance tests as CODE:<repo>/<path> "
                   "(the implementation may not edit them, D-38)")
    for f in files:
        if not CODE_REF_RE.match(str(f)):
            E(doc.rel, f"test file {f!r} must look like CODE:<repo-name>/<path>")
    if automated and not isinstance(doc.fm.get("tests_commit"), dict):
        E(doc.rel, "frontmatter 'tests_commit' must map each REPO-… to the commit that added the acceptance tests")


def _check_test_results(ws, doc, E, W):
    fm = doc.fm
    if fm.get("outcome") not in schema.enum("test_outcome"):
        E(doc.rel, f"frontmatter 'outcome' must be one of {schema.enum('test_outcome')}")
    if not fm.get("executed_at"):
        E(doc.rel, "frontmatter 'executed_at' must say when the tests ran")
    if fm.get("outcome") == "FAILED" and ws.doc_rel("defects", doc.id) not in ws.docs:
        E(doc.rel, f"outcome FAILED needs ba-ai/{ws.doc_rel('defects', doc.id)} with every failure classified")
    if fm.get("outcome") == "BLOCKED" and not fm.get("blocked_reason"):
        E(doc.rel, "outcome BLOCKED needs a 'blocked_reason'")
    mentioned = find_refs(doc.body)
    for tc, t in ws.test_cases.items():
        if t["uc"] == doc.id and tc not in mentioned:
            W(doc.rel, f"{tc} has no result row")


def _check_defects(ws, doc, E, W):
    max_attempts = int(schema.engine().get("max_fix_attempts", 3))
    declared = {sid for sid, x in ws.scoped.items() if x["doc"] == doc.rel and x["kind"] == "DEF"}
    listed = set()
    for d in as_list(doc.fm.get("defects")):
        if not isinstance(d, dict) or not d.get("id"):
            E(doc.rel, f"every entry of 'defects' needs an id ({d!r:.60})")
            continue
        did = d["id"]
        listed.add(did)
        if not re.fullmatch(re.escape(doc.id) + r"-DEF-\d{2}", str(did)):
            E(doc.rel, f"defect id {did} must look like {doc.id}-DEF-01")
        if did not in declared:
            E(doc.rel, f"{did} has no '### {did} — …' section with expected vs actual behaviour")
        if d.get("classification") not in schema.enum("defect_classification"):
            E(doc.rel, f"{did}: classification must be one of {schema.enum('defect_classification')}")
        if d.get("status") not in schema.enum("defect_status"):
            E(doc.rel, f"{did}: status must be one of {schema.enum('defect_status')}")
        n = d.get("fix_attempts", 0)
        if not isinstance(n, int) or n < 0 or n > max_attempts:
            E(doc.rel, f"{did}: fix_attempts must be 0–{max_attempts}")
        if d.get("test_case") and d["test_case"] not in ws.test_cases:
            E(doc.rel, f"{did}: test_case {d['test_case']} is not a declared test case")
    for did in sorted(declared - listed):
        E(doc.rel, f"{did} has a section but is missing from the frontmatter 'defects' list")


def _check_implementation_refs(ws, doc, E, W):
    fm = doc.fm
    repos = {r["id"]: r for r in ws.items_in("repositories")}
    names = {r.get("name"): r["id"] for r in repos.values()}
    for r in as_list(fm.get("repositories")):
        if r not in repos:
            E(doc.rel, f"repositories lists {r}, which is not in workflow/repositories.yaml")
    if not as_list(fm.get("repositories")):
        E(doc.rel, "frontmatter 'repositories' must list the REPO IDs changed")
    if not fm.get("branch"):
        E(doc.rel, "frontmatter 'branch' must name the working branch (ba/<UC>-<slug>, D-25)")
    if not as_list(fm.get("code_refs")):
        E(doc.rel, "frontmatter 'code_refs' must list the changed files as CODE:<repo>/<path>")
    for ref in as_list(fm.get("code_refs")):
        m = CODE_REF_RE.match(str(ref))
        if not m:
            E(doc.rel, f"code ref {ref!r} must look like CODE:<repo-name>/<path>")
        elif m.group(1) not in names:
            E(doc.rel, f"code ref {ref} names repository {m.group(1)!r}, which is not in workflow/repositories.yaml")


IMG_RE = re.compile(r"!\[[^\]]*\]\(([^)\s]+)")


def _check_user_guide(ws, doc, E, W):
    steps = [(t, sec) for _lvl, t, sec in sections(doc.body) if re.match(r"^step\s*\d+", t, re.I)]
    if not steps:
        E(doc.rel, "needs at least one '## Step 1 — …' section")
    for title, sec in steps:
        imgs = IMG_RE.findall(sec)
        if not imgs:
            W(doc.rel, f"'{title}' has no screenshot")
        for src in imgs:
            if not re.match(r"^[a-z]+://", src) and not (doc.path.parent / src).exists():
                E(doc.rel, f"'{title}' shows {src}, which does not exist")


def _check_compiled_spec(ws, doc, E, W):
    from .compile import check
    for m in check(ws, doc):
        E(doc.rel, m)


CHECKS: Dict[str, Callable] = {
    "mermaid": _check_mermaid,
    "screen_sections": _check_screen_sections,
    "component_tables": _check_component_tables,
    "message_texts": _check_message_texts,
    "prototype_index": _check_prototype_index,
    "api_sections": _check_api_sections,
    "behaviour": _check_behaviour,
    "workflow_steps": _check_workflow_steps,
    "site_map_pages": _check_site_map_pages,
    "field_controls": _check_field_controls,
    "gherkin": _check_gherkin,
    "test_cases": _check_test_cases,
    "test_results": _check_test_results,
    "defects": _check_defects,
    "implementation_refs": _check_implementation_refs,
    "user_guide": _check_user_guide,
    "compiled_spec": _check_compiled_spec,
}


def _validate_doc(ws: Workspace, doc: Doc, known: Set[str], E, W) -> None:
    tdef = schema.artifact_type(doc.type)
    if not tdef:
        E(doc.rel, f"unknown artifact_type '{doc.type}'")
        return
    fm = doc.fm
    for k in schema.artifacts()["required_frontmatter"]:
        if k not in fm:
            E(doc.rel, f"frontmatter is missing '{k}'")
    for key, enum_name in (("status", "artifact_status"), ("baseline", "baseline"), ("origin", "origin")):
        if key in fm and fm[key] not in schema.enum(enum_name):
            E(doc.rel, f"{key}={fm[key]!r} must be one of {schema.enum(enum_name)}")

    if tdef.get("per_use_case"):
        expected = tdef["path"].format(UC=doc.id)
        if doc.rel != expected:
            E(doc.rel, f"a {doc.type} for {doc.id} must live at ba-ai/{expected}")
        if ws.catalog_of(doc.id) != "use-cases":
            E(doc.rel, f"id {doc.id} is not a use case in {schema.catalogs()['use-cases']['path']}")
        if not fm.get("built_from"):
            E(doc.rel, f"not stamped — run `tools/ba stamp ba-ai/{doc.rel}`")
        if not isinstance(fm.get("relations"), dict):
            E(doc.rel, "frontmatter 'relations' must be a mapping")
    elif tdef.get("per_item"):
        cname = tdef["per_item"]
        expected = tdef["path"].replace(schema.per_item_placeholder(cname), str(doc.id))
        if ws.catalog_of(doc.id) != cname:
            E(doc.rel, f"id {doc.id} is not an item of {schema.catalogs()[cname]['path']}")
        elif doc.rel != expected:
            E(doc.rel, f"a {doc.type} for {doc.id} must live at ba-ai/{expected}")
    else:
        if tdef.get("path") and doc.rel != tdef["path"]:
            E(doc.rel, f"a {doc.type} must live at ba-ai/{tdef['path']}")
        if tdef.get("path_regex") and not re.match(tdef["path_regex"], doc.rel):
            E(doc.rel, f"path does not match {tdef['path_regex']}")
        if tdef.get("id") and doc.id != tdef["id"]:
            E(doc.rel, f"id must be {tdef['id']}")
        if tdef.get("id_regex") and not re.match(tdef["id_regex"], str(doc.id)):
            E(doc.rel, f"id must match {tdef['id_regex']}")

    relations = fm.get("relations") or {}
    if isinstance(relations, dict):
        allowed = schema.relation_edges()
        for k, vals in relations.items():
            if k not in allowed:
                E(doc.rel, f"unknown relation key '{k}' (allowed: {', '.join(allowed)})")
            for v in as_list(vals):
                if v not in known:
                    E(doc.rel, f"relations.{k} references unknown ID {v}")
    for key, prefix in (("open_questions", "Q"), ("assumptions", "ASM")):
        for v in as_list(fm.get(key)):
            if v not in known or prefix_of(str(v)) != prefix:
                E(doc.rel, f"{key} lists unknown {prefix} ID {v}")

    present = {norm_heading(t) for _, _, t in iter_headings(doc.body)}
    for h in tdef.get("headings", []):
        if norm_heading(h) not in present:
            E(doc.rel, f"missing section '{h}'")

    for ref in sorted(find_refs(doc.body)):
        if ref not in known:
            E(doc.rel, f"mentions unknown ID {ref} — never invent IDs; allocate with `tools/ba catalog add` or `tools/ba next-id`")

    for check in tdef.get("checks", []):
        CHECKS[check](ws, doc, E, W)

    for reason in ws.stale_reasons(doc):
        W(doc.rel, f"STALE — {reason}")


# ------------------------------------------------------------------ cross-catalog consistency (D-64)

def _validate_model(ws: Workspace, E, W) -> None:
    uc_path = schema.catalogs()["use-cases"]["path"]
    performed: Dict[str, Set[tuple]] = {}
    for uc in ws.items_in("use-cases"):
        for t in as_list(uc.get("transitions")):
            m = PAIR_RE.match(str(t))
            if m:
                performed.setdefault(uc.get("object"), set()).add((m.group(1), m.group(2)))
    ent_path = schema.catalogs()["entities"]["path"]
    if ws.items_in("use-cases"):
        for ent in ws.items_in("entities"):
            for frm, to in sorted(lifecycle_pairs(ent) - performed.get(ent["id"], set())):
                W(ent_path, f"{ent['id']} lifecycle transition {frm} -> {to} is performed by no use case "
                            f"(list it in that use case's 'transitions' in {uc_path})")
    for et in ws.items_in("email-templates"):
        used = {_norm_text(n).lower() for f in ("subject", "body") for n in PLACEHOLDER_RE.findall(str(et.get(f) or ""))}
        for p in as_list(et.get("placeholders")):
            if isinstance(p, dict) and p.get("name") and _norm_text(str(p["name"])).lower() not in used:
                W(schema.catalogs()["email-templates"]["path"],
                  f"{et['id']}: placeholder <<{p['name']}>> is declared but not used in the subject or body")
        if not str(et.get("name") or "").lower().startswith("sending email to"):
            W(schema.catalogs()["email-templates"]["path"],
              f"{et['id']}: name it \"Sending email to <recipient> after <event>\"")


# ------------------------------------------------------------------ backlog / state

def _validate_backlog(ws: Workspace, E, W) -> None:
    rel = paths.BACKLOG_REL
    item_status = schema.enum("backlog_item_status")
    stage_status = schema.enum("backlog_stage_status")
    prio = schema.enum("priority")
    for eid, epic in ws.epics.items():
        if not id_format_ok(eid, "EPIC"):
            E(rel, f"epic id {eid!r} must look like EPIC-NNN")
        if epic.get("priority") not in prio:
            E(rel, f"{eid}: priority must be one of {prio}")
        if epic.get("status") not in item_status:
            E(rel, f"{eid}: status must be one of {item_status}")
    for uc, bl in ws.backlog_ucs.items():
        item = bl["item"]
        if ws.catalog_of(uc) != "use-cases":
            E(rel, f"{uc} is not in {schema.catalogs()['use-cases']['path']}")
        if item.get("status") not in item_status:
            E(rel, f"{uc}: status must be one of {item_status}")
        if item.get("priority") not in prio:
            E(rel, f"{uc}: priority must be one of {prio}")
        for f in ("ui_status", "spec_status", "technical_review_status", "coding_status",
                  "testing_status", "documentation_status"):
            if item.get(f) not in stage_status:
                E(rel, f"{uc}: {f} must be one of {stage_status}")
        for dep in as_list(item.get("dependencies")):
            if dep not in ws.backlog_ucs:
                E(rel, f"{uc}: dependency {dep} is not in the backlog")


def _validate_state(ws: Workspace, E) -> None:
    rel = "workflow/state.json"
    modes = schema.workflow()["modes"]
    for r in ws.runs():
        rid = r.get("run_id")
        if not id_format_ok(rid, "RUN"):
            E(rel, f"run id {rid!r} must look like RUN-NNN")
        if r.get("workflow_type") not in modes:
            E(rel, f"{rid}: workflow_type must be one of {list(modes)}")
        if r.get("status") not in schema.enum("run_status"):
            E(rel, f"{rid}: status must be one of {schema.enum('run_status')}")
    if ws.state.get("active_run") and not ws.active_run():
        E(rel, f"active_run {ws.state.get('active_run')} is not a run")


# ------------------------------------------------------------------ entry point

def validate(ws: Workspace, only: Optional[Set[str]] = None) -> List[Issue]:
    issues: List[Issue] = []

    def E(path, msg):
        issues.append(Issue("ERROR", path, msg))

    def W(path, msg):
        issues.append(Issue("WARN", path, msg))

    for rel, msg in ws.load_errors:
        E(rel, msg)
    known = ws.known_ids()
    for cname, data in ws.catalog_data.items():
        cdef = schema.catalogs()[cname]
        meta = data.get("meta") or {}
        if meta.get("status") is not None and meta["status"] not in schema.enum("artifact_status"):
            E(cdef["path"], f"meta.status must be one of {schema.enum('artifact_status')}")
        for item in data["items"]:
            if isinstance(item, dict) and item.get("id"):
                for m in validate_item(ws, cname, item, known):
                    E(cdef["path"], m)
    _validate_model(ws, E, W)
    _validate_backlog(ws, E, W)
    _validate_state(ws, E)
    for doc in ws.docs.values():
        _validate_doc(ws, doc, known, E, W)
    if only is not None:
        issues = [i for i in issues if i.path in only]
    return issues


def errors_by_rel(issues: List[Issue]) -> Dict[str, List[str]]:
    out: Dict[str, List[str]] = {}
    for i in issues:
        if i.level == "ERROR":
            out.setdefault(i.path, []).append(i.msg)
    return out
