"""MODE_B end-to-end derivation tests on a throw-away fixture workspace.

Run:  .venv/bin/python -m unittest discover -s tools/tests -v      (from the workspace root)

Gate decisions are never written: a stub stands in for gates.status, so the tests only exercise
how `tools/ba` derives the next action from artifacts + gate states (master §40). AI pre-reviews
(D-40) are recorded through the real `prereview.record`, which is not a gate decision.

The fixture uses the company SRS layout (addendum §14, D-45 – D-64).
"""
from __future__ import annotations

import atexit
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

KIT = Path(__file__).resolve().parents[2]
FIXTURE = Path(tempfile.mkdtemp(prefix="ba-mode-b-"))
REPOS = Path(tempfile.mkdtemp(prefix="ba-repos-")).resolve()       # product repositories live outside the kit
atexit.register(shutil.rmtree, str(FIXTURE), True)
atexit.register(shutil.rmtree, str(REPOS), True)
os.environ["BA_ROOT"] = str(FIXTURE)
sys.path.insert(0, str(KIT / "tools"))

from ba_cli import (coding, compile as spec_compile, engine, graph, ids, migrate, paths, planning,  # noqa: E402
                    prereview, schema, srs, store, sync, views)
from ba_cli.validate import errors_by_rel, validate  # noqa: E402
from ba_cli.workspace import Workspace  # noqa: E402

UC = "UC-001"
SPEC = "functional-requirements/use-case-specifications"


class Gates:
    """Stub for gates.status: every gate NOT_REQUESTED unless set."""

    def __init__(self, **st):
        self.st = {}
        for k, v in st.items():
            self.set(k, v)

    def set(self, key: str, status: str, comments: str = None):
        gid, subject = key.split("@") if "@" in key else (key, None)
        self.st[(gid.replace("_", "-"), subject)] = (status, comments)
        return self

    def __call__(self, gid, subject):
        status, comments = self.st.get((gid, subject)) or self.st.get((gid, None)) or ("NOT_REQUESTED", None)
        dec = None
        if status in ("APPROVED", "CHANGES_REQUESTED", "BLOCKED"):
            dec = {"decision": status, "comments": comments, "reviewer": "test"}
        req = None if status == "NOT_REQUESTED" else {"n": 1, "requested_at": "2026-10-02T00:00:00Z"}
        return {"gate": gid, "subject": subject, "status": status, "comments": comments, "decision": dec,
                "request": req, "stale": []}


def write(rel: str, text: str) -> Path:
    p = paths.BA / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")
    return p


def front(did: str, atype: str, **fm) -> str:
    data = {"id": did, "artifact_type": atype, "title": f"{did} {atype}", "status": "DRAFT", "version": 1,
            "baseline": "TO_BE", "origin": "FIXTURE", "updated_at": "", **fm}
    return "---\n" + store.dump_yaml(data) + "---\n"


def doc(rel: str, did: str, atype: str, headings, body: str = "", **fm) -> Path:
    text = "".join(f"## {h}\n\nText.\n\n" for h in headings)
    return write(rel, front(did, atype, **fm) + "# " + did + "\n\n" + text + body)


def add(cname: str, **data) -> str:
    return ids.catalog_add(cname, data, force_gated=True)


def stamp(rel: str):
    ws = Workspace()
    sync.stamp_doc(ws, ws.docs[rel])


def derive(gs=None, validate_docs=True):
    ws = Workspace()
    errs = errors_by_rel(validate(ws)) if validate_docs else {}
    return ws, engine.derive_run(ws, ws.active_run(), gs or Gates(), errs)


def heads(atype):
    return schema.artifact_type(atype)["headings"]


def passed(gid, subject=UC):
    """The AI reviewer found nothing (D-40)."""
    prereview.record(gid, subject, "PASS", [])


def errors(rel=None):
    return [str(i) for i in validate(Workspace()) if i.level == "ERROR" and (rel is None or i.path == rel)]


FIELD_CONTROLS = """## Common Field Controls

| Control | Also written as | Attributes | Format and Behaviors |
|---|---|---|---|
| Free Text (Single Line of Text) | Text box | Max 255 | One line |
| Single Choice Dropdown List | Dropdown list | Placeholder | Sorted |
| Date Time – Date Only | Date picker | N/A | DD/MM/YYYY |

## Other Component Types

| Component type | Use |
|---|---|
| Button | Starts an action |
| Label | Read-only text |
"""


def ui_doc(uc: str = UC, scr: str = "SCR-001", msg: str = "IEM-001", text: str = "Please input in this field.",
           button: str = "Refer to UC-001.", source: str = "ENT-001.start", **relations) -> str:
    rel = {"screens": [scr], "messages": [msg], **relations}
    return (front(uc, "ui-markdown", relations=rel, built_from=[{"ref": uc, "hash": "x"}])
            + f"# {uc}\n\n## Purpose\n\nBook.\n\n## Screens\n\n### {scr} — Booking form screen\n"
            f"- **Description:** Book a room.\n\n#### Components\n\n"
            "| # | Component | Component Type | Editable | Mandatory | Default Value | Description |\n"
            "|---|---|---|---|---|---|---|\n"
            f"| 1 | Start | Date picker | Yes | Yes | <Today> | The start date ({source}). |\n"
            f"| 2 | Book | Button | N/A | N/A | N/A | Enabled when the form is valid. {button} |\n\n"
            "#### States\n\n| State | What the user sees |\n|---|---|\n| Loading | Skeleton |\n\n"
            f"#### Messages\n\n| Code | Message | Trigger | Rule |\n|---|---|---|---|\n"
            f"| {msg} | \"{text}\" | Start is blank | BR-001 |\n\n"
            "## Navigation\n\n```mermaid\nflowchart LR\n  A-->B\n```\n\n## Open Questions\n\nNone.\n")


def behaviour_doc(uc: str = UC, rules: str = None, flow: str = None, **fm) -> str:
    flow = flow if flow is not None else ("```mermaid\nflowchart TD\n  S1[\"(1) User opens the form\"] --> "
                                          "S2[\"(2) System validates\"]\n```\n1. (1) User opens the form.\n"
                                          "2. (2) System validates and saves.\n")
    rules = rules if rules is not None else (
        f"### {uc}-BR-01 — Validating Rules\n- **Step:** (2)\n- **Type:** Validating\n\n"
        "The system validates [Start]. If it is blank, show IEM-001 under it.\n\n"
        f"### {uc}-BR-02 — Submitting Rules\n- **Step:** (2)\n- **Type:** Processing\n"
        "- **State change:** (new) -> REQUESTED\n\nThe system creates {Booking} (BR-001) and sends ET-001.\n")
    rel = {"business_rules": ["BR-001"], "messages": ["IEM-001"], "email_templates": ["ET-001"]}
    return (front(uc, "use-case-behaviour", relations=fm.pop("relations", rel), built_from=[{"ref": uc, "hash": "x"}],
                  **fm)
            + f"# {uc}\n\n## Use Case Description\n- **Trigger:** User clicks \"Book\".\n"
            "- **Pre-condition:** User signed in as Employee.\n- **Post-condition:** The booking is requested.\n\n"
            f"## Activities Flow\n\n{flow}\n## Business Rules\n\n{rules}\n"
            f"## Alternate Flows\n\nNone.\n\n## Error Flows\n\n### {uc}-EF-01 — Room taken\n- **Trigger:** overlap\n")


class ModeBTest(unittest.TestCase):
    def setUp(self):
        for d in (FIXTURE, REPOS):
            if d.exists():
                shutil.rmtree(d)
        REPOS.mkdir()
        (FIXTURE / "tools").mkdir(parents=True)
        shutil.copytree(KIT / "tools" / "schemas", FIXTURE / "tools" / "schemas")
        shutil.copytree(KIT / "company-standards", FIXTURE / "company-standards")
        (paths.BA / "workflow").mkdir(parents=True)
        shutil.copy(KIT / "ba-ai" / "workflow" / "workflow.yaml", paths.BA / "workflow" / "workflow.yaml")
        store.save_json(paths.STATE, {"schema_version": 1, "project": {"name": "Fixture"}, "active_run": "RUN-001",
                                      "runs": [{"run_id": "RUN-001", "workflow_type": "MODE_B", "status": "NOT_STARTED",
                                                "scope": {"epic": None, "use_cases": []}}],
                                      "coding_authorization": None})
        for d in ("input-management/user-requirements", "input-management/meeting-minutes",
                  "input-management/reference-documents"):
            (paths.BA / d).mkdir(parents=True)
            (paths.BA / d / ".gitkeep").write_text("")

    # ------------------------------------------------------------ fixture builders

    def elicitation(self):
        write("input-management/user-requirements/brief.md", "Stakeholders want a way to book meeting rooms.\n")
        doc("input-management/elicitation/elicitation-summary.md", "ELICITATION", "elicitation-summary",
            heads("elicitation-summary"))
        add("requirements", name="Book a room", description="Employees book rooms.", source="brief.md",
            priority="HIGH", type="FUNCTIONAL")
        add("requirements", name="Fast booking", description="A booking is confirmed quickly.", source="brief.md",
            priority="MEDIUM", type="NON_FUNCTIONAL", category="PERFORMANCE",
            criteria="95% of bookings are confirmed within 2 seconds")
        add("glossary", term="Booking", kind="TERM", definition="A reserved room for a time slot.")
        stamp("input-management/elicitation/elicitation-summary.md")

    def overview(self):
        doc("high-level-requirements/product-overview.md", "PRODUCT", "product-overview", heads("product-overview"))
        act = add("actors", name="Employee", type="HUMAN", description="Books rooms",
                  role_mapping="the HR role assignments include EMPLOYEE")
        app = add("applications", name="Room app", type="WEB", description="Web app", actors=[act],
                  information_architecture="REQUIRED")
        ent = add("entities", name="Booking", description="A booking", owner="Room app",
                  attributes=[{"name": "id", "type": "identifier"},
                              {"name": "start", "type": "date", "mandatory": True}],
                  lifecycle={"states": ["REQUESTED", "CONFIRMED"],
                             "transitions": ["(new) -> REQUESTED: employee books",
                                             {"from": "REQUESTED", "to": "CONFIRMED", "event": "system confirms"}]})
        bp = add("business-processes", name="Booking", objective="Book rooms", actors=[act], trigger="Need a room",
                 steps=[{"name": "Book", "actor": act}])
        br = add("business-rules", name="No overlap", description="Bookings may not overlap.", source="brief.md",
                 kind="POLICY", related_entities=[ent])
        add("common-use-cases", **dict(store.load_yaml(KIT / "company-standards" / "common-use-cases.yaml")["items"][0]))
        uc = add("use-cases", name="Book a room", objective="book a meeting room", business_process=bp, actor=act,
                 application=app, object=ent, permissions=[{"actor": act, "access": "OWN"}],
                 transitions=["(new) -> REQUESTED", "REQUESTED -> CONFIRMED"],
                 description="Employee books a room.", complexity="LOW", risk_level="LOW",
                 business_rules=[br], entities_written=[ent])
        stamp("high-level-requirements/product-overview.md")
        ids.catalog_init("integrations")              # this product has no integrations
        doc("other-requirements/field-controls.md", "FIELD-CONTROLS", "field-controls", [], body=FIELD_CONTROLS)
        doc("other-requirements/message-configuration.md", "MESSAGE-CONFIGURATION", "message-configuration",
            heads("message-configuration"))
        doc("other-requirements/list-behaviour.md", "LIST-BEHAVIOUR", "list-behaviour", heads("list-behaviour"))
        write("high-level-requirements/workflows/BP-001.md", front("BP-001", "workflow")
              + "# Booking workflow\n\n## Workflow Diagram\n\n```mermaid\nflowchart LR\n  BP-001-S01\n```\n\n"
                "## Workflow Explanation\n\n- BP-001-S01: the employee books.\n")
        for rel in ("other-requirements/field-controls.md", "other-requirements/message-configuration.md",
                    "other-requirements/list-behaviour.md", "high-level-requirements/workflows/BP-001.md"):
            stamp(rel)
        return uc

    def baseline(self):
        for rel, atype, did in (("technical/architecture/architecture.md", "technical-architecture", "ARCH"),
                                ("technical/coding-rules/frontend.md", "coding-rules", "CODING-FRONTEND"),
                                ("technical/coding-rules/backend.md", "coding-rules", "CODING-BACKEND"),
                                ("technical/security/security-rules.md", "security-rules", "SECURITY"),
                                ("technical/design-system.md", "design-system", "DESIGN-SYSTEM")):
            doc(rel, did, atype, heads(atype))
        repo = add("repositories", name="room-api", type="backend", status="PLANNED", path=str(REPOS / "room-api"))
        add("services", name="Booking service", responsibility="Bookings", repository=repo)
        for rel in ("technical/architecture/architecture.md", "technical/coding-rules/frontend.md",
                    "technical/coding-rules/backend.md", "technical/security/security-rules.md",
                    "technical/design-system.md"):
            stamp(rel)

    def plan(self, status="READY"):
        return planning.apply_plan({"epics": [{"name": "Booking", "priority": "HIGH", "use_cases": [
            {"use_case_id": UC, "priority": "HIGH", "status": status, "stories": [
                {"name": "Book a room", "story": "As an Employee, I want to book a room, so that I can meet."}]}]}]})

    def ia(self):
        write("high-level-requirements/site-map/APP-001.md", front("APP-001", "site-map")
              + "# Room app site map\n\n## Site Map\n\n```mermaid\nflowchart TD\n  A-->B\n```\n\n"
                "## Pages\n\n| Page | Description | Permission |\n|---|---|---|\n| Home | Start | Employee |\n\n"
                "## Application Structure\n\nText.\n\n## Menu\n\nText.\n\n## Entry Points\n\nText.\n")
        stamp("high-level-requirements/site-map/APP-001.md")

    def upstream(self):
        self.elicitation()
        self.overview()
        self.baseline()
        self.plan()
        self.ia()

    def repos_ready(self):
        (REPOS / "room-api").mkdir(exist_ok=True)
        ids.catalog_update("REPO-001", {"status": "ACTIVE"})

    def spec_docs(self, uc=UC):
        for st in schema.engine_steps():
            if st["phase"] == "SPECIFICATION":
                doc(Workspace().doc_rel(st["artifact_type"], uc), uc, st["artifact_type"], [], relations={})
        write(f"functional-requirements/mockup-screens/prototypes/{uc}/index.html", "<html></html>")

    def delivery_doc(self, atype, **fm):
        doc(Workspace().doc_rel(atype, UC), UC, atype, [], relations={}, **fm)

    def message_and_email(self):
        add("messages", type="INLINE_ERROR", text="Please input in this field.")
        add("email-templates", name="Sending email to Employee after booking is requested", trigger="UC-001 books",
            to="[email] of {Employee} who booked", subject="[ROOMS] <<Room>> booked",
            body="Dear <<Employee Name>>, your booking of <<Room>> has been requested.",
            placeholders=[{"name": "Room", "source": "ENT-001.id of the current {Booking}"},
                          {"name": "Employee Name", "source": "<Current User>"}])

    # ------------------------------------------------------------ run-level steps

    def test_fresh_template_waits_for_raw_material(self):
        _, d = derive()
        self.assertEqual(d["phase"], "ELICITATION")
        self.assertEqual(d["status"], "NOT_STARTED")
        self.assertIn("input-management/user-requirements/", d["blocked_reason"])

    def test_elicitation_generate_then_stakeholder_wait_then_consolidate(self):
        write("input-management/user-requirements/brief.md", "Stakeholder brief\n")
        _, d = derive()
        self.assertEqual(d["run_action"]["action"], "GENERATE")
        self.assertEqual(d["run_action"]["agent"], "elicitation-agent")

        self.elicitation()
        q = add("open-questions", question="Which rooms are bookable?", reason="Scope", impact_if_unanswered="Scope unknown",
                target_stakeholder="BUSINESS", priority="HIGH", status="OPEN", blocking=True)
        _, d = derive()
        self.assertEqual(d["status"], "WAITING_FOR_HUMAN")
        self.assertEqual(d["run_action"]["action"], "WAIT_FOR_STAKEHOLDERS")
        self.assertEqual([x["id"] for x in d["run_action"]["questions"]], [q])

        write("input-management/meeting-minutes/2026-10-02-workshop.md", "Answer: all rooms on floor 3.\n")
        _, d = derive()
        self.assertEqual(d["run_action"]["action"], "REGENERATE")      # step 2.6 consolidate the notes
        self.assertIn("input-management/meeting-minutes/", d["run_action"]["reason"])

        stamp("input-management/elicitation/elicitation-summary.md")
        ids.catalog_update(q, {"status": "ANSWERED", "answer": "Floor 3"})
        _, d = derive()
        self.assertEqual(d["phase"], "OVERVIEW")
        self.assertEqual(d["run_action"]["agent"], "overview-analysis-agent")

    def test_requirements_must_be_typed_and_nfrs_measurable(self):
        self.elicitation()
        with self.assertRaises(store.BAError) as e:
            add("requirements", name="Secure", description="Secure.", source="brief.md", priority="HIGH")
        self.assertIn("missing required field 'type'", str(e.exception))
        with self.assertRaises(store.BAError) as e:
            add("requirements", name="Secure", description="Secure.", source="brief.md", priority="HIGH",
                type="NON_FUNCTIONAL")
        self.assertIn("missing 'category', required when type is NON_FUNCTIONAL", str(e.exception))
        self.assertIn("missing 'criteria'", str(e.exception))
        text = views.write_all(Workspace()) and (paths.BA / "non-functional-requirements/non-functional-requirements.view.md").read_text()
        self.assertIn("95% of bookings are confirmed within 2 seconds", text)
        self.assertIn("## Performance Requirements", text)

    def test_overview_pre_review_then_gate_02_and_revise_goes_to_overview_agent(self):
        self.elicitation()
        self.overview()
        (paths.BA / "high-level-requirements/integrations.yaml").unlink()
        _, d = derive()                          # GATE-02 reviews integrations.yaml: the step must create it
        self.assertEqual((d["run_action"]["action"], d["run_action"]["step"]), ("FIX", "OVERVIEW"))
        self.assertIn("catalog init", d["run_action"]["reason"])
        ids.catalog_init("integrations")
        _, d = derive()
        self.assertEqual((d["run_action"]["action"], d["run_action"]["agent"], d["run_action"]["round"]),
                         ("PRE_REVIEW", "review-agent", 1))
        passed("GATE-02", "RUN-001")
        _, d = derive()
        self.assertEqual(d["run_action"], {"action": "REQUEST_GATE", "gate": "GATE-02", "subject": "RUN-001",
                                           "reason": "NOT_REQUESTED"})
        _, d = derive(Gates().set("GATE-02@RUN-001", "CHANGES_REQUESTED", "add a cancellation rule"))
        self.assertEqual(d["run_action"]["action"], "REVISE")
        self.assertEqual((d["run_action"]["agent"], d["run_action"]["step"]), ("overview-analysis-agent", "OVERVIEW"))

    def test_overview_needs_a_workflow_per_process_and_the_company_conventions(self):
        self.elicitation()
        self.overview()
        (paths.BA / "high-level-requirements/workflows/BP-001.md").unlink()
        (paths.BA / "other-requirements/list-behaviour.md").unlink()
        _, d = derive()
        ra = d["run_action"]
        self.assertEqual((ra["action"], ra["step"]), ("GENERATE", "OVERVIEW"))
        self.assertIn("high-level-requirements/workflows/BP-001.md is missing", ra["reason"])
        self.assertIn("other-requirements/list-behaviour.md is missing", ra["reason"])

    def test_workflow_document_shows_every_step(self):
        self.elicitation()
        self.overview()
        ids.catalog_update("BP-001", {"steps": [{"id": "BP-001-S01", "name": "Book", "actor": "ACT-001",
                                                 "next": [{"to": "S02", "when": "room free"}, {"to": "END", "when": "taken"}]},
                                                {"name": "Confirm"}]}, force_gated=True)
        bp = Workspace().item("BP-001")
        self.assertEqual(bp["steps"][0]["next"][0]["to"], "BP-001-S02")    # short branch target expanded
        msgs = "\n".join(errors("high-level-requirements/workflows/BP-001.md"))
        self.assertIn("BP-001-S02 (Confirm) is not in the workflow", msgs)
        with self.assertRaises(store.BAError) as e:
            ids.catalog_update("BP-001", {"steps": [{"id": "BP-001-S01", "name": "Book", "next": [{"to": "BP-001-S09"}]}]},
                               force_gated=True)
        self.assertIn("branch target 'BP-001-S09' must be a step of BP-001", str(e.exception))

    def test_pre_review_findings_route_to_owner_then_resolve_or_round_limit(self):
        self.elicitation()
        self.overview()
        prereview.record("GATE-02", "RUN-001", "FINDINGS", [
            {"artifact": "ba-ai/high-level-requirements/use-cases.yaml", "severity": "MAJOR",
             "issue": "UC-001 lacks a requirement"}])
        _, d = derive()
        ra = d["run_action"]
        self.assertEqual((ra["action"], ra["agent"], ra["pre_review"]), ("REVISE", "overview-analysis-agent", True))
        self.assertIn("lacks a requirement", ra["comments"])

        prereview.resolve("GATE-02", "RUN-001", "REQ-001 covers it; the link is implicit")
        _, d = derive()
        self.assertEqual(d["run_action"]["action"], "REQUEST_GATE")
        self.assertIn("lacks a requirement", d["run_action"]["pre_review_findings"])

        # A changed artifact needs a fresh review, until the round limit (2) is reached.
        ids.catalog_update("UC-001", {"requirements": ["REQ-001"]}, force_gated=True)
        _, d = derive()
        self.assertEqual((d["run_action"]["action"], d["run_action"]["round"]), ("PRE_REVIEW", 2))
        prereview.record("GATE-02", "RUN-001", "FINDINGS", [
            {"artifact": "high-level-requirements/use-cases.yaml", "severity": "MINOR", "issue": "wording"}])
        _, d = derive()
        self.assertEqual(d["run_action"]["action"], "REQUEST_GATE")       # 2 rounds done: the human decides

        with self.assertRaises(store.BAError):
            prereview.record("GATE-02", "RUN-001", "FINDINGS", [{"artifact": "ui/x.md", "issue": "not a gate artifact"}])
        brief = store.load_yaml(paths.BA / prereview.brief("GATE-02", "RUN-001")[len("ba-ai/"):])
        folder = next(a for a in brief["artifacts"] if a["artifact"].endswith("workflows/"))
        self.assertIn(".claude/skills/model-business-processes/SKILL.md", folder["method_skills"])

    def test_baseline_planning_and_site_map_lead_into_the_spec_engine(self):
        self.elicitation()
        self.overview()
        g = Gates(GATE_02="APPROVED")
        _, d = derive(g)
        self.assertEqual((d["phase"], d["run_action"]["agent"]), ("TECH_BASELINE", "technical-baseline-agent"))
        self.baseline()
        _, d = derive(g)
        self.assertEqual((d["run_action"]["action"], d["run_action"]["gate"]), ("PRE_REVIEW", "GATE-09"))
        g.set("GATE-09", "APPROVED")
        _, d = derive(g)
        self.assertEqual((d["phase"], d["run_action"]["action"]), ("PLANNING", "GENERATE"))
        self.plan()
        _, d = derive(g)
        self.assertEqual((d["phase"], d["run_action"]["agent"]), ("INFORMATION_ARCHITECTURE", "planning-agent"))
        self.assertIn("site-map/APP-001.md", d["run_action"]["reason"])
        self.ia()
        ws, d = derive(g)
        self.assertEqual(d["phase"], "SPECIFICATION")
        r = d["use_cases"][UC]
        self.assertEqual((r["action"], r["step"], r["agent"]), ("GENERATE", "5.2", "ui-agent"))

    def test_site_map_for_every_user_facing_application(self):
        self.upstream()
        ids.catalog_update("APP-001", {"information_architecture": "NOT_REQUIRED"})
        app = add("applications", name="Admin console", type="BACKOFFICE", description="Admin", actors=["ACT-001"])
        add("actors", name="Scheduler", type="SYSTEM", description="Jobs")
        add("applications", name="Batch", type="BACKOFFICE", description="Jobs only", actors=["ACT-002"])
        _, d = derive(Gates(GATE_02="APPROVED", GATE_09="APPROVED"))
        self.assertEqual(d["phase"], "INFORMATION_ARCHITECTURE")
        self.assertIn(f"site-map/{app}.md is missing", d["run_action"]["reason"])
        self.assertNotIn("site-map/APP-003.md", d["run_action"]["reason"])      # no human uses it

    def test_new_use_case_after_planning_reopens_planning(self):
        self.upstream()
        add("use-cases", name="Cancel booking", objective="cancel a booking", business_process="BP-001",
            actor="ACT-001", application="APP-001", object="ENT-001",
            permissions=[{"actor": "ACT-001", "access": "OWN"}], description="Cancel.", complexity="LOW",
            risk_level="LOW")
        _, d = derive(Gates(GATE_02="APPROVED", GATE_09="APPROVED"))
        self.assertEqual((d["phase"], d["run_action"]["action"]), ("PLANNING", "REGENERATE"))
        self.assertIn("UC-002", d["run_action"]["reason"])

    def test_approved_gate_freezes_upstream_steps(self):
        """Hand-written overviews (milestone 1 projects) are not regenerated once GATE-02 is approved."""
        self.elicitation()
        self.overview()
        (paths.BA / "input-management/elicitation/elicitation-summary.md").unlink()
        _, d = derive(Gates(GATE_02="APPROVED"))
        self.assertEqual(d["phase"], "TECH_BASELINE")

    # ------------------------------------------------------------ use cases as functions (D-46)

    def test_function_fields_are_checked(self):
        self.elicitation()
        self.overview()
        base = dict(name="Confirm booking", business_process="BP-001", actor="ACT-001", application="APP-001",
                    object="ENT-001", description="x", complexity="LOW", risk_level="LOW")
        cases = [
            (dict(objective="confirm a booking", permissions=[{"actor": "ACT-001", "access": "SCOPED"}]),
             "state its scope rule"),
            (dict(objective="confirm a booking", permissions=[{"actor": "ACT-001", "access": "OWN"}],
                  allowed_states=["DONE"]), "allowed state 'DONE' is not a state"),
            (dict(objective="confirm a booking", permissions=[{"actor": "ACT-001", "access": "OWN"}],
                  transitions=["CONFIRMED -> REQUESTED"]), "is not in ENT-001's lifecycle"),
            (dict(objective="confirm a booking", permissions=[]), "its actor ACT-001 needs a permission"),
            (dict(objective="This function allows Employee to confirm", permissions=[{"actor": "ACT-001", "access": "ALL"}]),
             "write the objective as the end of"),
            (dict(objective="confirm", permissions=[{"actor": "ACT-009", "access": "ALL"}]),
             "permissions.actor references unknown ID ACT-009"),
        ]
        for extra, msg in cases:
            with self.assertRaises(store.BAError, msg=msg) as e:
                add("use-cases", **base, **extra)
            self.assertIn(msg, str(e.exception))

    def test_company_views_permission_matrix_use_case_diagram_and_state_transition(self):
        self.upstream()
        pm = add("actors", name="Facility Manager", type="HUMAN", description="Runs rooms",
                 role_mapping="the HR role assignments include FACILITY_MANAGER")
        add("use-cases", name="Confirm booking", objective="confirm a requested booking", business_process="BP-001",
            actor=pm, application="APP-001", object="ENT-001", allowed_states=["REQUESTED"],
            permissions=[{"actor": pm, "access": "SCOPED", "scope": "bookings of the rooms they run"}],
            description="x", complexity="LOW", risk_level="LOW")
        views.write_all(Workspace())
        matrix = (paths.BA / "high-level-requirements/permission-matrix.view.md").read_text()
        self.assertIn("| Function | Employee | Facility Manager |", matrix)
        self.assertIn("Book a room | O* | X |", matrix)
        self.assertIn('*Status is "REQUESTED"*', matrix)
        self.assertIn("Confirm booking | X | O** |", matrix)
        self.assertIn("bookings of the rooms they run", matrix)
        diagram = (paths.BA / "high-level-requirements/use-case-diagram.view.md").read_text()
        self.assertIn("This function allows Facility Manager to confirm a requested booking.", diagram)
        self.assertIn("flowchart LR", diagram)
        states = (paths.BA / "high-level-requirements/state-transition.view.md").read_text()
        self.assertIn("[*] --> REQUESTED: employee books", states)
        self.assertIn("| REQUESTED |", states)
        ord_ = (paths.BA / "high-level-requirements/object-relationship-diagram.view.md").read_text()
        self.assertIn("| **Actor** | | |", ord_)
        self.assertIn('recognises the user as "Facility Manager" when the HR role assignments include', ord_)
        self.assertTrue((paths.BA / "functional-requirements/objects/ENT-001.view.md").exists())
        self.assertTrue((paths.BA / "agile-project/epics/EPIC-001.view.md").exists())

    # ------------------------------------------------------------ planning and user stories (D-60)

    def test_plan_rejects_duplicates_cycles_and_keeps_progress(self):
        self.elicitation()
        self.overview()
        add("use-cases", name="Cancel", objective="cancel a booking", business_process="BP-001", actor="ACT-001",
            application="APP-001", object="ENT-001", permissions=[{"actor": "ACT-001", "access": "OWN"}],
            description="Cancel.", complexity="LOW", risk_level="LOW")
        with self.assertRaises(store.BAError) as e:
            planning.apply_plan({"epics": [{"name": "A", "priority": "HIGH", "use_cases": [
                {"use_case_id": "UC-001", "priority": "HIGH", "dependencies": ["UC-002"]},
                {"use_case_id": "UC-002", "priority": "HIGH", "dependencies": ["UC-001"]}]}]})
        self.assertIn("cycle", str(e.exception))
        with self.assertRaises(store.BAError):
            planning.apply_plan({"epics": [
                {"name": "A", "priority": "HIGH", "use_cases": [{"use_case_id": "UC-001", "priority": "HIGH"}]},
                {"name": "B", "priority": "LOW", "use_cases": [{"use_case_id": "UC-001", "priority": "LOW"}]}]})
        res = self.plan()
        self.assertEqual(res["epics"], ["EPIC-001"])
        self.assertEqual(res["stories_created"], ["US-001"])
        bl = store.load_yaml(paths.BACKLOG)
        bl["epics"][0]["use_cases"][0]["status"] = "IN_PROGRESS"
        bl["epics"][0]["use_cases"][0]["ui_status"] = "WAITING_FOR_REVIEW"
        store.save_yaml(paths.BACKLOG, bl)
        res = planning.apply_plan({"epics": [{"epic_id": "EPIC-001", "name": "Booking", "priority": "LOW", "use_cases": [
            {"use_case_id": UC, "priority": "LOW", "status": "BACKLOG",
             "stories": [{"id": "US-001", "name": "Book", "story": "As an Employee, I want to book, so that I meet."}]},
            {"use_case_id": "UC-002", "priority": "LOW", "status": "READY"}]}]})
        self.assertEqual(res["stories_updated"], ["US-001"])
        item = store.load_yaml(paths.BACKLOG)["epics"][0]["use_cases"][0]
        self.assertEqual((item["status"], item["ui_status"], item["priority"]), ("IN_PROGRESS", "WAITING_FOR_REVIEW", "LOW"))
        self.assertEqual(Workspace().item("US-001")["name"], "Book")
        with self.assertRaises(store.BAError) as e:
            planning.apply_plan({"epics": [{"epic_id": "EPIC-001", "name": "Booking", "priority": "LOW", "use_cases": [
                {"use_case_id": UC, "priority": "LOW", "stories": [{"id": "US-001", "name": "x", "story": "y"}]},
                {"use_case_id": "UC-002", "priority": "LOW", "stories": [{"id": "US-001", "name": "x", "story": "y"}]}]}]})
        self.assertIn("story US-001 is not one of its user stories", str(e.exception))

    def test_planning_needs_a_user_story_per_use_case(self):
        self.elicitation()
        self.overview()
        g = Gates(GATE_02="APPROVED", GATE_09="APPROVED")
        self.baseline()
        planning.apply_plan({"epics": [{"name": "Booking", "priority": "HIGH", "use_cases": [
            {"use_case_id": UC, "priority": "HIGH", "status": "READY"}]}]})
        _, d = derive(g)
        self.assertEqual((d["phase"], d["run_action"]["action"]), ("PLANNING", "GENERATE"))
        self.assertIn("agile-project/user-stories.yaml has no items", d["run_action"]["reason"])

    # ------------------------------------------------------------ delivery per use case

    def approved_spec(self, **more):
        g = Gates(GATE_02="APPROVED", GATE_09="APPROVED", GATE_03="APPROVED", GATE_04="APPROVED",
                  GATE_05="APPROVED")
        for k, v in more.items():
            g.set(k, v)
        return g

    def uc(self, g, uc=UC):
        _, d = derive(g, validate_docs=False)
        return d["use_cases"][uc], d

    def test_spec_engine_order_behaviour_before_sequence_and_api(self):
        """D-48: 5.4 behaviour (spec-agent) → 5.5 sequence, 5.6 API (technical-analysis-agent) → 5.7, 5.8."""
        self.upstream()
        g = Gates(GATE_02="APPROVED", GATE_09="APPROVED", GATE_03="APPROVED", GATE_04="APPROVED")
        doc(Workspace().doc_rel("ui-markdown", UC), UC, "ui-markdown", [], relations={})
        doc(Workspace().doc_rel("ui-prototype", UC), UC, "ui-prototype", [], relations={})
        r, _ = self.uc(g)
        self.assertEqual((r["action"], r["step"], r["agent"], r["steps"]), ("GENERATE", "5.4", "spec-agent", ["5.4"]))
        self.assertEqual(r["skills"], ["write-use-case-behaviour"])
        doc(Workspace().doc_rel("use-case-behaviour", UC), UC, "use-case-behaviour", [], relations={})
        r, _ = self.uc(g)
        self.assertEqual((r["step"], r["agent"], r["steps"]), ("5.5", "technical-analysis-agent", ["5.5", "5.6"]))

    def test_system_use_case_skips_the_ui_steps(self):
        """D-57: a scheduled job has no screens, so it starts at the behaviour step and skips GATE-03/04."""
        self.upstream()
        sch = add("actors", name="Scheduler", type="SYSTEM", description="Runs jobs")
        job = add("use-cases", name="Confirm bookings nightly", objective="confirm requested bookings every night",
                  business_process="BP-001", actor=sch, application="APP-001", object="ENT-001",
                  allowed_states=["REQUESTED"], permissions=[{"actor": sch, "access": "ALL"}],
                  description="x", complexity="LOW", risk_level="LOW")
        planning.apply_plan({"epics": [{"epic_id": "EPIC-001", "name": "Booking", "priority": "HIGH", "use_cases": [
            {"use_case_id": UC, "priority": "HIGH", "status": "READY"},
            {"use_case_id": job, "priority": "HIGH", "status": "READY",
             "stories": [{"name": "Nightly confirmation", "story": "As the system, I confirm bookings nightly."}]}]}]})
        self.ia()                                # a new use case re-opens the site map; re-stamp it
        g = Gates(GATE_02="APPROVED", GATE_09="APPROVED")
        r, _ = self.uc(g, job)
        self.assertEqual((r["action"], r["step"], r["agent"]), ("GENERATE", "5.4", "spec-agent"))
        ws = Workspace()
        self.assertFalse(ws.ui_required(job))
        self.assertFalse(engine.gate_required(ws, job, "GATE-03"))
        self.assertEqual(sync.stage_status(ws, g, job, schema.engine()["stages"]["ui_status"], r), "NOT_APPLICABLE")
        # The same job with a screen listed (e.g. a monitoring page) gets its UI steps back.
        add("screens", name="Job monitor screen", application="APP-001", purpose="Watch jobs", use_cases=[job])
        r, _ = self.uc(g, job)
        self.assertEqual((r["step"], r["agent"]), ("5.2", "ui-agent"))

    def test_delivery_order_tests_first_qa_before_code_review(self):
        """D-37/D-38: GATE-06 → acceptance tests → code → QA → GATE-10 → user guide → GATE-08."""
        self.upstream()
        self.spec_docs()
        g = self.approved_spec()
        r, d = self.uc(g)
        self.assertEqual((r["action"], r["gate"], d["phase"]), ("PRE_REVIEW", "GATE-06", "TECHNICAL_REVIEW"))
        passed("GATE-06")
        r, _ = self.uc(g)
        self.assertEqual((r["action"], r["gate"]), ("REQUEST_GATE", "GATE-06"))

        g.set("GATE-06", "CHANGES_REQUESTED", "use PATCH")
        r, _ = self.uc(g)
        self.assertEqual((r["action"], r["agent"], r["steps"]), ("REVISE", "technical-analysis-agent", ["5.5", "5.6"]))

        g.set("GATE-06", "APPROVED")
        r, _ = self.uc(g)                        # the repository doesn't exist yet (D-39)
        self.assertEqual((r["action"], r["agent"], r["shared"]), ("SETUP_REPOSITORIES", "coding-agent", True))
        self.repos_ready()
        r, d = self.uc(g)
        self.assertEqual((r["action"], r["step"], r["agent"], d["phase"]), ("GENERATE", "8.1", "qa-agent", "TEST_DESIGN"))
        self.assertEqual(r["pre_command"], f"tools/ba coding authorize {UC}")

        self.delivery_doc("test-cases")
        r, _ = self.uc(g)
        self.assertEqual((r["action"], r["step"], r["agent"]), ("GENERATE", "7", "coding-agent"))
        self.delivery_doc("implementation", repositories=["REPO-001"], branch="ba/UC-001-book",
                          code_refs=["CODE:room-api/src/booking.py"])
        r, _ = self.uc(g)
        self.assertEqual((r["action"], r["step"], r["agent"]), ("GENERATE", "8.2", "qa-agent"))

        self.delivery_doc("test-results", outcome="PASSED", executed_at="2026-10-02T10:00:00Z")
        r, _ = self.uc(g)                        # QA passed → code review of the final code
        self.assertEqual((r["action"], r["gate"]), ("PRE_REVIEW", "GATE-10"))
        passed("GATE-10")
        r, _ = self.uc(g)
        self.assertEqual((r["action"], r["gate"]), ("REQUEST_GATE", "GATE-10"))
        g.set("GATE-10", "CHANGES_REQUESTED", "extract the overlap check")
        r, _ = self.uc(g)
        self.assertEqual((r["action"], r["agent"], r["steps"]), ("REVISE", "coding-agent", ["7"]))

        g.set("GATE-10", "APPROVED")
        r, _ = self.uc(g)                        # LOW risk: GATE-07 is skipped (D-23)
        self.assertEqual((r["action"], r["step"], r["agent"]), ("GENERATE", "9", "documentation-agent"))
        ws = Workspace()
        self.assertEqual(sync.stage_status(ws, g, UC, schema.engine()["stages"]["testing_status"], r), "DONE")
        self.assertEqual(sync.stage_status(ws, g, UC, schema.engine()["stages"]["coding_status"], r), "DONE")

        self.delivery_doc("user-guide")
        passed("GATE-08")
        r, _ = self.uc(g)
        self.assertEqual((r["action"], r["gate"]), ("REQUEST_GATE", "GATE-08"))
        g.set("GATE-08", "APPROVED")
        r, d = self.uc(g)
        self.assertEqual(r["state"], "DONE")
        self.assertEqual(d["status"], "COMPLETED")

    def test_high_risk_use_case_needs_critical_flow_test_after_code_review(self):
        self.upstream()
        ids.catalog_update(UC, {"risk_level": "HIGH", "risk_flags": ["FINANCIAL"]}, force_gated=True)
        _, d = derive(Gates(GATE_02="APPROVED", GATE_09="APPROVED"))
        self.assertEqual((d["phase"], d["run_action"]["action"]), ("INFORMATION_ARCHITECTURE", "REGENERATE"))
        self.ia()
        self.spec_docs()
        self.repos_ready()
        g = self.approved_spec(GATE_06="APPROVED", GATE_10="APPROVED")
        for t in ("test-cases", "implementation"):
            self.delivery_doc(t)
        self.delivery_doc("test-results", outcome="PASSED", executed_at="x")
        r, _ = self.uc(g)                        # GATE-07 has no AI pre-review: it is a human test
        self.assertEqual((r["action"], r["gate"]), ("REQUEST_GATE", "GATE-07"))
        ws = Workspace()
        self.assertEqual(sync.stage_status(ws, g, UC, schema.engine()["stages"]["testing_status"], r), "IN_PROGRESS")
        g.set("GATE-07", "CHANGES_REQUESTED", "booking overlaps were accepted")
        r, _ = self.uc(g)
        self.assertEqual((r["action"], r["agent"]), ("REVISE", "qa-agent"))

    def qa_failure(self, cls, attempts=0, status="OPEN"):
        self.upstream()
        self.spec_docs()
        self.repos_ready()
        g = self.approved_spec(GATE_06="APPROVED")
        for t in ("test-cases", "implementation"):
            self.delivery_doc(t)
        self.delivery_doc("test-results", outcome="FAILED", executed_at="2026-10-02T10:00:00Z")
        self.delivery_doc("defects", defects=[{"id": "UC-001-DEF-01", "classification": cls, "status": status,
                                               "fix_attempts": attempts}])
        return g

    def test_code_defect_goes_to_the_fix_loop_before_any_human_review(self):
        g = self.qa_failure("CODE_DEFECT", attempts=1)
        r, _ = self.uc(g)
        self.assertEqual((r["action"], r["step"], r["agent"]), ("FIX_DEFECT", "8.4", "coding-agent"))
        self.assertIn("attempt 2 of 3", r["reason"])
        self.assertEqual(r["pre_command"], f"tools/ba coding authorize {UC}")

    def test_fix_loop_stops_after_three_attempts(self):
        g = self.qa_failure("CODE_DEFECT", attempts=3)
        r, d = self.uc(g)
        self.assertEqual(r["state"], "NEEDS_HUMAN")
        self.assertEqual(d["status"], "WAITING_FOR_HUMAN")
        ws = Workspace()
        self.assertEqual(sync.stage_status(ws, g, UC, schema.engine()["stages"]["testing_status"], r), "BLOCKED")

    def test_test_issue_and_spec_gap_routing(self):
        g = self.qa_failure("TEST_ISSUE")
        r, _ = self.uc(g)
        self.assertEqual((r["action"], r["agent"], r["steps"]), ("FIX_TESTS", "qa-agent", ["8.1"]))
        self.setUp()
        g = self.qa_failure("SPECIFICATION_GAP")
        r, _ = self.uc(g)
        self.assertEqual(r["state"], "NEEDS_HUMAN")
        self.assertIn("SPECIFICATION_GAP", r["reason"])

    def test_retest_request_reruns_tests(self):
        g = self.qa_failure("ENVIRONMENT_ISSUE")
        Workspace().docs[f"qa/test-results/{UC}.md"].write_fm({"retest_requested_at": "2026-10-03T00:00:00Z"})
        r, _ = self.uc(g)
        self.assertEqual((r["action"], r["step"]), ("REGENERATE", "8.2"))

    # ------------------------------------------------------------ coding authorization and worktrees

    def test_coding_authorization_governs_repositories_and_their_worktrees(self):
        self.upstream()
        ws = Workspace()
        self.assertTrue(coding.problems(ws, Gates(), UC))
        self.assertEqual(coding.problems(ws, self.approved_spec(GATE_06="APPROVED"), UC), [])
        repo = REPOS / "room-api"
        wt = coding.worktree_path(repo, UC)
        self.assertEqual(wt, REPOS / "room-api-worktrees" / UC)
        for target in (repo / "src" / "x.py", wt / "src" / "x.py"):
            ok, why = coding.write_allowed(target, ws)
            self.assertFalse(ok, target)
            self.assertIn("coding authorize", why)
        self.assertEqual(coding.write_allowed(FIXTURE / "ba-ai" / "x.md", ws), (True, None))
        self.assertEqual(coding.write_allowed(REPOS / "unrelated" / "x.txt", ws), (True, None))
        ws.state["coding_authorization"] = {"use_cases": [UC]}
        real = engine.GateCache
        engine.GateCache = lambda _ws: self.approved_spec(GATE_06="APPROVED")
        try:
            self.assertEqual(coding.write_allowed(wt / "src" / "x.py", ws), (True, None))
        finally:
            engine.GateCache = real
        self.assertEqual(coding.repositories_ready(ws)[0], False)
        self.repos_ready()
        self.assertEqual(coding.repositories_ready(Workspace()), (True, []))

    # ------------------------------------------------------------ screens, messages, emails (D-51, D-52)

    def test_screen_component_table_and_message_codes(self):
        self.upstream()
        self.message_and_email()
        add("screens", name="Booking form screen", application="APP-001", purpose="Book", use_cases=[UC])
        rel = Workspace().doc_rel("ui-markdown", UC)
        write(rel, ui_doc())
        self.assertEqual(errors(rel), [])
        write(rel, ui_doc(text="Fill this in."))
        self.assertIn("IEM-001 reads 'Fill this in.' here but 'Please input in this field.' in the message catalog",
                      "\n".join(errors(rel)))
        write(rel, ui_doc(button="It books."))
        self.assertIn("a button refers to the use case it triggers", "\n".join(errors(rel)))
        write(rel, ui_doc(source="the start date"))
        self.assertIn("an editable component names its source attribute", "\n".join(errors(rel)))
        write(rel, ui_doc().replace("#### Components", "#### Fields"))
        self.assertIn("needs a '#### Components' table", "\n".join(errors(rel)))
        write(rel, ui_doc(msg="IEM-009"))
        self.assertIn("mentions unknown ID IEM-009", "\n".join(errors(rel)))
        with self.assertRaises(store.BAError) as e:
            add("messages", type="WARNING", text="x")
        self.assertIn("'type' must be one of", str(e.exception))
        self.assertEqual(add("messages", type="CONFIRMATION", text="Are you sure?"), "CFD-001")

    def test_email_placeholders_must_be_bound(self):
        self.upstream()
        with self.assertRaises(store.BAError) as e:
            add("email-templates", name="Sending email to Employee after booking", trigger="booked", to="Employee",
                subject="<<Room>> booked", body="Hi <<Name>>", placeholders=[{"name": "Room", "source": "the room"}])
        msg = str(e.exception)
        self.assertIn("<<Name>> in the body is not bound to a source", msg)
        self.assertIn("placeholder <<Room>> needs a source", msg)
        self.message_and_email()
        self.assertEqual(Workspace().item("ET-001")["subject"], "[ROOMS] <<Room>> booked")

    # ------------------------------------------------------------ behaviour, CMUC and the compiled spec

    def test_behaviour_step_rules_are_checked(self):
        self.upstream()
        self.message_and_email()
        rel = Workspace().doc_rel("use-case-behaviour", UC)
        write(rel, behaviour_doc())
        self.assertEqual(errors(rel), [])
        bad = (f"### {UC}-BR-01 — Validating\n- **Step:** (7)\n- **Type:** Checking\n\nThe system validates.\n\n"
               f"### {UC}-BR-02 — Validating Rules\n- **Type:** Validating\n\nNo message here.\n\n"
               f"### {UC}-BR-03 — Confirmation Rules\n- **Step:** (1)\n- **Type:** Confirmation\n\nAsks.\n\n"
               f"### {UC}-BR-04 — Approving Rules\n- **Step:** (2)\n- **Type:** Processing\n"
               f"- **State change:** CONFIRMED -> REQUESTED\n\nApproves.\n")
        write(rel, behaviour_doc(rules=bad))
        text = "\n".join(errors(rel))
        for msg in ("UC-001-BR-01: the title names the rule type", "UC-001-BR-01: step (7) is not in the Activities Flow",
                    "UC-001-BR-01: **Type:** must be one of", "UC-001-BR-02 needs a '- **Step:** (n)' line",
                    "UC-001-BR-02: a Validating rule names the message", "UC-001-BR-03: a Confirmation rule names",
                    "UC-001-BR-04: state change 'CONFIRMED -> REQUESTED' is not a transition"):
            self.assertIn(msg, text)

    def test_common_use_case_numbering_placeholders_and_delta_steps(self):
        self.upstream()
        self.message_and_email()
        cm = store.load_yaml(KIT / "company-standards" / "common-use-cases.yaml")["items"][1]      # Create Item
        with self.assertRaises(store.BAError) as e:
            add("common-use-cases", **cm)
        self.assertIn("replace every [[message: …]]", str(e.exception))
        text = store.dump_yaml(cm).replace("[[message: Please input in this field.]]", "IEM-001")
        add("business-rules", name="Logging basic audit trail", description="Audit.", source="CBR1", kind="COMMON")
        text = text.replace("[[rule: Logging basic audit trail]]", "BR-002")
        import yaml
        cid = add("common-use-cases", **yaml.safe_load(text))
        self.assertEqual(cid, "CMUC-002")
        ws = Workspace()
        self.assertEqual([r["id"] for r in ws.item(cid)["step_rules"]], ["CMUC-002-BR-01", "CMUC-002-BR-02", "CMUC-002-BR-03"])
        self.assertIn("CMUC-002-BR-02", ws.known_ids())
        ids.catalog_update(UC, {"follows": [cid]}, force_gated=True)
        rel = Workspace().doc_rel("use-case-behaviour", UC)
        delta = (f"Follows {cid}; only what differs:\n\n"
                 f"### {UC}-BR-01 — Validating Rules\n- **Step:** {cid} (4)\n- **Type:** Validating\n\n"
                 "[Start] must be in the future; otherwise show IEM-001.\n\n"
                 f"### {UC}-BR-02 — Creating Rules\n- **Step:** {cid} (9)\n- **Type:** Processing\n\nSaves.\n")
        write(rel, behaviour_doc(rules=delta))
        text = "\n".join(errors(rel))
        self.assertNotIn("UC-001-BR-01", text)
        self.assertIn(f"UC-001-BR-02: {cid} has no step (9)", text)

    def test_compile_assembles_the_company_skeleton_and_guards_it(self):
        self.upstream()
        self.message_and_email()
        add("screens", name="Booking form screen", application="APP-001", purpose="Book", use_cases=[UC])
        self.spec_docs()
        write(Workspace().doc_rel("ui-markdown", UC), ui_doc())
        stamp(Workspace().doc_rel("ui-markdown", UC))
        write(Workspace().doc_rel("use-case-behaviour", UC), behaviour_doc())
        stamp(Workspace().doc_rel("use-case-behaviour", UC))
        write(f"technical/sequence/{UC}.md", front(UC, "sequence", relations={})
              + "## Main Flow\n```mermaid\nsequenceDiagram\n  U->>W: book\n```\n1. Book.\n")
        res = spec_compile.compile_spec(UC)
        self.assertEqual(len(res["narrative_todo"]), 2)
        ws = Workspace()
        spec = ws.docs[f"{SPEC}/{UC}/spec.md"]
        self.assertIn("| Objective | This use case allows Employee to book a meeting room. |", spec.body)
        self.assertIn('| Trigger | User clicks "Book". |', spec.body)
        self.assertIn("| Step | BR Code | Description |", spec.body)
        self.assertIn("| (2) | UC-001-BR-01 | **Validating Rules:**", spec.body)
        self.assertIn("| IEM-001 | Inline Error | Please input in this field. |", spec.body)
        self.assertIn("### ET-001 — Sending email to Employee after booking is requested", spec.body)
        self.assertIn("<<Room>>: ENT-001.id of the current {Booking}", spec.body)
        self.assertIn("### SCR-001 — Booking form screen", spec.body)
        self.assertIn("sequenceDiagram", spec.body)
        self.assertIn("BR-001 — No overlap** (Policy): Bookings may not overlap.", spec.body)
        self.assertIn("**User stories:** US-001 Book a room", spec.body)
        self.assertTrue(any("TODO placeholder" in m for m in spec_compile.check(ws, spec)))

        # The agent writes the narrative; a recompile keeps it.
        p = paths.BA / f"{SPEC}/{UC}/spec.md"
        hint = "<!-- TODO(spec-agent): " + spec_compile.NARRATIVE[11] + " -->"
        p.write_text(p.read_text().replace(hint, "Employees need rooms for meetings."))
        spec_compile.compile_spec(UC)
        self.assertIn("Employees need rooms for meetings.", p.read_text())

        # A hand edit to a generated section is caught.
        p.write_text(p.read_text().replace("Bookings may not overlap.", "Bookings may overlap."))
        ws = Workspace()
        msgs = spec_compile.check(ws, ws.docs[f"{SPEC}/{UC}/spec.md"])
        self.assertTrue(any("6. Common Business Rules differs from its source" in m for m in msgs), msgs)

    # ------------------------------------------------------------ graph, publication, migration

    def test_graph_reverse_lookup_from_a_message_and_an_email(self):
        self.upstream()
        self.message_and_email()
        add("screens", name="Booking form screen", application="APP-001", purpose="Book", use_cases=[UC])
        write(Workspace().doc_rel("ui-markdown", UC), ui_doc())
        write(Workspace().doc_rel("use-case-behaviour", UC), behaviour_doc())
        g = graph.build(Workspace())
        edges = {(e["from"], e["type"], e["to"]) for e in g["edges"]}
        for e in (("SCR-001", "SHOWS", "IEM-001"), ("SCR-001", "REFERS_TO", "UC-001"), ("UC-001-BR-01", "SHOWS", "IEM-001"),
                  ("UC-001-BR-02", "SENDS", "ET-001"), ("UC-001-BR-02", "APPLIES", "BR-001"),
                  ("UC-001-BR-02", "CHANGES_STATE", "ENT-001"), ("ET-001", "READS", "ENT-001"),
                  ("ACT-001", "MAY_PERFORM", "UC-001"), ("UC-001", "ACTS_ON", "ENT-001"),
                  ("EPIC-001", "CONTAINS", "US-001"), ("US-001", "REALIZES", "UC-001")):
            self.assertIn(e, edges)
        lines = "\n".join(graph.neighborhood(g, "IEM-001", 3))
        self.assertIn("UC-001 (UseCase)", lines)
        self.assertIn("BP-001 (BusinessProcess)", lines)

    def test_publish_writes_the_company_tree_and_srs(self):
        self.upstream()
        files = srs.publish(Workspace())
        self.assertIn("srs/SRS.md", files)
        text = (paths.SRS / "SRS.md").read_text()
        for chapter in ("# 1. Introduction", "# 3. High Level Requirements", "## 3.6. Permission Matrix",
                        "# 4. Functional Requirements", "## 4.2. Use Case Specifications", "# 5. Mockups Screen",
                        "# 6. Agile Project", "# 7. Non-Functional Requirements", "# 10. Data Migration",
                        "## 11.1. Message List", "## 11.3. Glossary"):
            self.assertIn(chapter, text)
        self.assertIn("Not in scope", (paths.SRS / "data-migration.md").read_text())
        self.assertIn("Booking | A reserved room for a time slot. |", text)
        self.assertTrue((paths.SRS / "high-level-requirements/permission-matrix.md").exists())
        self.assertIn("brief.md", (paths.SRS / "introduction.md").read_text())

    def test_migrate_moves_a_milestone_two_workspace(self):
        write("requirements/raw/brief.md", "Brief\n")
        (paths.BA / "input-management").exists() and shutil.rmtree(paths.BA / "input-management")
        write("requirements/requirements.yaml", store.dump_yaml({"meta": {}, "items": []}))
        write("requirements/requirements.view.md", "old view\n")
        write("overview/state-models/.gitkeep", "")
        write("ui/markdown/UC-001.md", "---\nid: UC-001\nartifact_type: ui-markdown\nbuilt_from:\n"
                                      "- {path: overview/use-cases.yaml, hash: abc}\n---\nSee ba-ai/ui/prototypes/UC-001/index.html\n")
        write("ui/prototypes/UC-001/README.md", "---\nid: UC-001\nartifact_type: ui-prototype\nbuilt_from:\n"
                                                "- {path: ui/markdown/UC-001.md, hash: def}\n---\nOpen it.\n")
        write("specifications/analysis/UC-001-acceptance.md", "---\nid: UC-001\nartifact_type: acceptance-criteria\n---\nAC\n")
        rep = migrate.migrate()
        self.assertEqual(rep["conflicts"], [])
        ws_files = {paths.rel(p) for p in paths.BA.rglob("*") if p.is_file()}
        for f in ("input-management/user-requirements/brief.md", "input-management/elicitation/requirements.yaml",
                  "functional-requirements/mockup-screens/UC-001.md",
                  "functional-requirements/mockup-screens/prototypes/UC-001/README.md",
                  f"{SPEC}/UC-001/acceptance.md"):
            self.assertIn(f, ws_files)
        ui = (paths.BA / "functional-requirements/mockup-screens/UC-001.md").read_text()
        self.assertIn("path: high-level-requirements/use-cases.yaml", ui)
        self.assertIn("ba-ai/functional-requirements/mockup-screens/prototypes/UC-001/index.html", ui)
        readme = (paths.BA / "functional-requirements/mockup-screens/prototypes/UC-001/README.md").read_text()
        self.assertIn("path: functional-requirements/mockup-screens/UC-001.md", readme)
        for old in ("requirements", "overview", "ui", "specifications"):
            self.assertFalse((paths.BA / old).exists(), old)
        self.assertEqual(migrate.migrate(), {"moved": [], "rewritten": [], "removed": [], "conflicts": []})

    # ------------------------------------------------------------ validation

    def test_validation_of_test_cases_defects_and_lifecycle(self):
        self.upstream()
        write(f"{SPEC}/{UC}/acceptance.md", front(UC, "acceptance-criteria", relations={},
                                                  built_from=[{"ref": UC, "hash": "x"}]) + "## Acceptance Criteria\n\n"
              f"### {UC}-AC-01 — Books\n- **Given** a room\n- **When** booked\n- **Then** saved\n\n"
              f"### {UC}-AC-02 — Rejects overlap\n- **Given** a booking\n- **When** overlapping\n- **Then** 409\n\n"
              "## Coverage\n")
        tc = ids.next_id("TC")
        write(f"qa/test-cases/{UC}.md", front(UC, "test-cases", relations={}, built_from=[{"ref": UC, "hash": "x"}])
              + "## Test Cases\n\n"
              f"### {tc} — Book a free room\n- **Verifies:** {UC}-AC-01\n- **Category:** Functional\n"
              "- **Automation:** api\n- **Steps:** book\n- **Expected:** saved\n\n"
              "### TC-999 — Invented\n- **Verifies:** UC-001-AC-01\n\n## Coverage\n")
        write(f"qa/defects/{UC}.md", front(UC, "defects", relations={}, built_from=[{"ref": UC, "hash": "x"}],
                                           defects=[{"id": f"{UC}-DEF-01", "classification": "BUG", "status": "OPEN",
                                                     "fix_attempts": 5}])
              + "## Defects\n\n### UC-001-DEF-02 — Undeclared\n")
        text = "\n".join(errors())
        self.assertIn(f"{UC}-AC-02 is not verified by any test case", text)
        self.assertIn("TC-999 was never allocated", text)
        self.assertIn("'test_files' must list the automated acceptance tests", text)
        self.assertIn("'tests_commit' must map", text)
        self.assertIn("classification must be one of", text)
        self.assertIn("fix_attempts must be 0–3", text)
        self.assertIn("UC-001-DEF-02 has a section but is missing", text)
        self.assertIn("UC-001-DEF-01 has no", text)

        with self.assertRaises(store.BAError) as e:
            add("entities", name="Room", description="A room", owner="x", attributes=[{"name": "id", "type": "id",
                                                                                     "max_length": -1}],
                lifecycle={"states": ["FREE"], "transitions": ["FREE -> BOOKED: booked"]})
        self.assertIn("'BOOKED', which is not in states", str(e.exception))
        self.assertIn("max_length must be a positive whole number", str(e.exception))

    def test_run_step_stamp_records_optional_empty_input(self):
        self.elicitation()
        fm = Workspace().docs["input-management/elicitation/elicitation-summary.md"].fm
        entries = {e["path"]: e for e in fm["built_from"]}
        self.assertTrue(entries["input-management/meeting-minutes/"]["optional"])
        self.assertIsNone(entries["input-management/meeting-minutes/"]["hash"])
        self.assertIsNotNone(entries["input-management/user-requirements/"]["hash"])


if __name__ == "__main__":
    unittest.main()
