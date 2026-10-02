---
id: ELICITATION
artifact_type: elicitation-summary
title: Leave Request Management System — Elicitation Summary
status: DRAFT
version: 2
baseline: TO_BE
origin: AI
open_questions:
  - Q-001
  - Q-002
  - Q-003
  - Q-004
  - Q-005
  - Q-006
  - Q-007
  - Q-008
  - Q-009
  - Q-010
  - Q-011
  - Q-012
  - Q-013
  - Q-014
  - Q-015
  - Q-016
  - Q-017
  - Q-018
  - Q-019
  - Q-020
  - Q-021
  - Q-022
  - Q-023
  - Q-024
  - Q-025
  - Q-026
  - Q-027
  - Q-028
  - Q-030
  - Q-031
  - Q-032
  - Q-033
  - Q-034
  - Q-035
assumptions:
  - ASM-001
  - ASM-002
  - ASM-003
  - ASM-004
  - ASM-005
  - ASM-006
  - ASM-007
  - ASM-008
  - ASM-009
  - ASM-011
  - ASM-012
  - ASM-013
  - ASM-014
  - ASM-015
updated_at: '2026-10-02T09:13:38Z'
built_from:
  - path: input-management/user-requirements/
    hash: c0a11a60b02ead9c
  - path: input-management/meeting-minutes/
    hash: eb778a5f1dcc9a98
    optional: true
  - path: input-management/reference-documents/
    hash: null
    optional: true
  - ref: Q-001
    hash: 94e6d8f6de933f74
  - ref: Q-002
    hash: d8adfcdb6e5b2b20
  - ref: Q-003
    hash: eed78515ed2f8e5a
  - ref: Q-004
    hash: 6e491827ee406834
  - ref: Q-005
    hash: 99c8c729ee4e8bad
  - ref: Q-006
    hash: ed37804e798cf99e
  - ref: Q-007
    hash: 4b4a0ba0c4c10e7f
  - ref: Q-008
    hash: acb0f4c4c523febf
  - ref: Q-009
    hash: 9fb37450ed0f29f1
  - ref: Q-010
    hash: 2b5df2971dd23765
  - ref: Q-011
    hash: 7b7f593e00ef0790
  - ref: Q-012
    hash: 487c4cce7f278e00
  - ref: Q-013
    hash: 28bd824521271ad8
  - ref: Q-014
    hash: a3ce8605080eca69
  - ref: Q-015
    hash: 55f79c7dcf2ddf2f
  - ref: Q-016
    hash: 2c67bd98530ec1f5
  - ref: Q-017
    hash: 999b3c45f1c4ee4b
  - ref: Q-018
    hash: 47cd55b3f4137a9d
  - ref: Q-019
    hash: 50ecc194e7c1b999
  - ref: Q-020
    hash: ce1e587d4c84b6d3
  - ref: Q-021
    hash: 9426c9a8b60be452
  - ref: Q-022
    hash: 55f04c06e73a8c90
  - ref: Q-023
    hash: 67d8c9da3b7da752
  - ref: Q-024
    hash: 7f7da76f67dc544d
  - ref: Q-025
    hash: 2b8ca327d5fa1a2d
  - ref: Q-026
    hash: 7cc33001173c03c0
  - ref: Q-027
    hash: c056795eaa5e7edb
  - ref: Q-028
    hash: d68f5f76fdd84eef
  - ref: Q-030
    hash: ca4631a300f68dea
  - ref: Q-031
    hash: 5097a97f35c23699
  - ref: Q-032
    hash: b8dc27b0ee4af68d
  - ref: Q-033
    hash: c0d12fec8d5042db
  - ref: Q-034
    hash: e8e20757bec564ed
  - ref: Q-035
    hash: 28df7f83d6cf6839
  - ref: ASM-001
    hash: 4ff06de8db6d0768
  - ref: ASM-002
    hash: 05dfeb1f1a38e960
  - ref: ASM-003
    hash: 568c2a38c9cfa4ee
  - ref: ASM-004
    hash: 5afc92b463960c71
  - ref: ASM-005
    hash: 2f6629e1559a6a22
  - ref: ASM-006
    hash: a2743dae4a8f614d
  - ref: ASM-007
    hash: 4fc3981e04473aba
  - ref: ASM-008
    hash: 310aabffe95b266f
  - ref: ASM-009
    hash: 41a4bf8d191ab48b
  - ref: ASM-011
    hash: 10912ecf1d624d4c
  - ref: ASM-012
    hash: 73a7078dffbd6d2a
  - ref: ASM-013
    hash: 2a9bbec3d9759b2d
  - ref: ASM-014
    hash: a261af9056d3f8e1
  - ref: ASM-015
    hash: 50868849c91bbccc
---
# Leave Request Management System — Elicitation Summary

## Sources
| Source | Kind (user requirement / meeting minutes / reference document) | Date | Author / stakeholder |
|---|---|---|---|
| [Leave_Request_User_Requirement_Spec (2).docx](../user-requirements/Leave_Request_User_Requirement_Spec%20(2).docx) — "User Requirement Specification, Leave Request Management System", v1.0, prepared for bidding vendors (cited below as *URS*) | User requirement | 2025-05-09 | Client Business Team |
| [MoM 01 Oct 2026.docx](../meeting-minutes/MoM%2001%20Oct%202026.docx) — answers to the blocking questions Q-001 – Q-004 and Q-006 (cited below as *MoM*) | Meeting minutes | 2026-10-01 (from the file name; the document has no date line) | Written by Viet Ngo Dinh (document author). Attendees and the stakeholders who gave the answers are not recorded. |

There are no reference documents. The URS is a bidding document that is short on rules, data and measurable targets. The MoM answers five of the six blocking questions; Q-005 is not addressed.

## Current Need
AS-IS, only as the sources state it:

- **Problem.** Leave requests and approvals are handled manually today. The process lacks consistency and is prone to delays (URS §2).
- **Affected users.** Employees who request leave, the Project Managers and Line Managers who review it, and HR/Admin who manage entitlements (URS §2, §4.6).
- **Existing process and data.** Employees are entitled to various types of leave based on seniority, gender and company policy (URS §2). The company already runs a card scanner time tracking system that records check-in and check-out (URS §2, §4.8). People and organisation data are held in existing HR systems (MoM, Q-001).
- **Limitations and pain points.** The URS's objectives imply the current shortcomings: no automated workflow across levels, no rule-based validation or policy transparency, no regular compliance notifications, and poor visibility into absences without approved leave (URS §3).
- **Organisation.** A multinational company with offices in multiple cities across several countries, up to 33,000 users (URS §4.8).
- **Reason for change.** Automate and standardise the leave process, ensure compliance with company policy, and improve transparency (URS §1, §2).

## Future Need
TO-BE, as the sources describe it:

- **Desired outcome.** One system manages the full lifecycle of a leave request, from submission to approval. It applies the leave policy by rule and stays transparent. It is integrated with the card scanner data and with the HR systems that provide people and organisation data (URS §1–§3; MoM).
- **Future process.**
  1. An employee submits a leave request in full days or half days (morning / afternoon), for a future date or a past date within the current month. Leave from the previous month is not accepted (REQ-001; MoM, Q-003 and Q-006). When submitting, the employee chooses the Project Manager who will confirm the request, from the projects they are assigned to (REQ-001; MoM, Q-002). They attach the documents the leave type requires (REQ-004).
  2. The system validates the request against the policy (REQ-002). A request that violates the policy can still be submitted and is reviewed manually by the Line Manager. Exceeding the remaining entitlement is allowed. If such a request is approved, the balance stays at 0 (REQ-003; MoM, Q-004).
  3. Confirmation: the chosen Project Manager confirms or denies the request (REQ-006). A Project Manager's own request is confirmed automatically (REQ-007).
  4. Approval: the Line Manager approves or rejects the confirmed request (REQ-008).
  5. Both steps finish within the calendar month of the leave start date (REQ-009). A request not confirmed and approved by then is cancelled (REQ-034; MoM, Q-003).
  6. After a denial or rejection, the employee can modify the request and resubmit it (REQ-010). Employees follow their requests' status (REQ-005).
- **Attendance follow-up.** Every Friday, employees are told which days they were off work with and without a leave request (REQ-011, REQ-012). The data comes from the card scanner system (REQ-024), whose own logic stays out of scope (REQ-032).
- **People and organisation data.** Employees, the organisational structure, Line Managers and project assignments with their Project Managers are imported from the existing HR systems (REQ-033; MoM, Q-001).
- **Administration.** Admin/HR import entitlements at the start of each year (REQ-014) and refresh leave data once a year (REQ-015). They also manage leave types with their eligibility rules and required documents (REQ-016 – REQ-019).
- **Screens and reporting.** Project Managers and Line Managers get role-specific dashboards that show what needs their action, with filters (REQ-020, REQ-021). HR and Managers get leave statistics by unit, department, company, country, city or office (REQ-022), on a multinational organisational structure (REQ-023).
- **Qualities.** The system is web-based and mobile-responsive (REQ-025), with secure login and role-based access (REQ-026, REQ-027). It scales to 33,000 users and handles concurrent submissions reliably (REQ-028 – REQ-030). Its notification emails are automated and configurable (REQ-013), and it can be localised in several languages (REQ-031).
- **Business goals.** Policy compliance, transparency, fewer delays, and visibility into absenteeism without approved leave (URS §3).

## Gap Analysis
| Gap | Type (process/system/data/integration/policy) | AS-IS | TO-BE | Requirement / question |
|---|---|---|---|---|
| Leave request and approval workflow | Process | Manual, inconsistent, prone to delays | Submission with a chosen PM, PM confirmation, LM approval, resubmission, all in the system | REQ-001, REQ-005 – REQ-008, REQ-010; Q-002 (answered), Q-031, Q-008, Q-010, Q-011, Q-012 |
| Month-end deadline for reviews | Policy | Not described | Review and approval within the calendar month of the leave start date; otherwise cancelled | REQ-009, REQ-034; Q-003 (answered), Q-034 |
| Policy validation and violations | Policy | Applied manually | Rule-based validation; exceeding the entitlement allowed with LM review, balance stays at 0 | REQ-002, REQ-003; Q-004 (answered), Q-032, Q-033, Q-009 |
| Leave types, eligibility, documents | Data / policy | Policy outside any system | Configurable leave types, eligibility by gender and seniority, required documents | REQ-004, REQ-016 – REQ-019; Q-005, Q-018, Q-027 |
| Entitlements, leave unit and annual refresh | Data | Entitlements by seniority, gender and policy; no system | Full and half days; year-start import and annual refresh by Admin/HR | REQ-001, REQ-014, REQ-015; Q-006 (answered), Q-007, Q-009, Q-017 |
| Absence follow-up | Process / system | Card scanner records presence; no link to leave | Weekly Friday notification of off-work days with and without a request | REQ-011, REQ-012; Q-013, Q-014, Q-015, Q-035 |
| Card scanner data | Integration | Separate time tracking system | Check-in/out times fetched; scanner logic out of scope | REQ-024, REQ-032; Q-016 |
| People, organisation and reporting lines | Data / integration | Held in existing HR systems | Imported from the HR systems; multinational structure for access and reporting | REQ-033, REQ-023, REQ-027; Q-001 (answered), Q-030, Q-019 |
| Role dashboards and reporting | System | None | Action dashboards with filters; leave statistics by organisation level | REQ-020 – REQ-022; Q-020 |
| Notifications | System | None | Automated, configurable notification emails | REQ-013; Q-021 |
| Security and access | System | Not described | Secure login and logout; role-based access scoped by country, city, office | REQ-026, REQ-027; Q-022 |
| Performance, scale, reliability | System | Not described | 33,000 users, concurrent submissions without delay, reliable under heavy usage | REQ-028 – REQ-030; Q-023, Q-024 |
| Platform and language | System | Not described | Web, mobile-responsive, multi-language if needed | REQ-025, REQ-031; Q-025, Q-026 |

**Unresolved decisions** (each is a clarification question):
- per-country leave policy (Q-005);
- confirmation when the employee has no project (Q-031);
- whether violations other than exceeding the entitlement are allowed (Q-032);
- the HR systems, interface and frequency (Q-030);
- whether excess days above the entitlement are recorded (Q-033);
- the exact month-end cut-off and time zone (Q-034);
- half-day leave in the weekly attendance check (Q-035);
- the annual refresh and carry-over (Q-007);
- cancellation by the employee (Q-008);
- when the balance is deducted (Q-009);
- requests by Line Managers and on behalf of others, and delegation (Q-010 – Q-012);
- working-day calendars (Q-013);
- notification details (Q-014, Q-021);
- employees without card scanner records (Q-015);
- the card scanner interface (Q-016);
- the entitlement import details (Q-017);
- the go-live leave types and their rules (Q-018);
- the organisation hierarchy (Q-019);
- report contents and scopes (Q-020);
- the measurable NFR targets (Q-022 – Q-026);
- document privacy (Q-027);
- priorities (Q-028).

## Clarification Questions
The question text lives in [open-questions.yaml](open-questions.yaml).

**Answered by the MoM:** Q-001, Q-002, Q-003, Q-004, Q-006. The answers are recorded verbatim, with what they leave open.

**Blocking, still open: the overview cannot be written responsibly without them.**
- BUSINESS:
  - Q-031 — who confirms when the employee has no project (the part of Q-002 the MoM leaves open)
  - Q-032 — whether ineligible leave types and missing documents are allowed or blocked (the part of Q-004 the MoM leaves open)
- COMPLIANCE:
  - Q-005 — leave policy per country or global (not addressed in the MoM)

**Not blocking**
- BUSINESS: Q-007, Q-008, Q-009 (HIGH); Q-010, Q-011, Q-012, Q-013, Q-014, Q-018, Q-020, Q-021, Q-033, Q-034, Q-035 (MEDIUM); Q-028 (LOW)
- DATA: Q-019 (HIGH); Q-017 (MEDIUM)
- INTEGRATION: Q-016, Q-030 (HIGH)
- OPERATIONS: Q-015, Q-024 (MEDIUM)
- SECURITY: Q-022 (HIGH)
- TECHNICAL: Q-023 (HIGH)
- UX: Q-025 (MEDIUM); Q-026 (LOW)
- COMPLIANCE: Q-027 (MEDIUM)

## Decisions
**Stakeholder decisions** (MoM 01 Oct 2026; the answering stakeholders are not named in the minutes):

| Decision | Source |
|---|---|
| People and organisation data are imported from existing HR systems → REQ-033 | MoM, Q-001 |
| With several projects, the employee chooses the confirming Project Manager from their assigned projects → REQ-001, REQ-006 | MoM, Q-002 |
| A request not confirmed and approved by the end of the leave start month is cancelled → REQ-009, REQ-034 | MoM, Q-003 |
| A request is valid as long as the requested leave is not from the previous month; this confirms ASM-006 → REQ-001 | MoM, Q-003 |
| Policy-violating requests are reviewed by the Line Manager; exceeding the entitlement is allowed; if approved, the balance stays at 0 → REQ-003 | MoM, Q-004 |
| Leave is requested and counted in full days and half days (morning / afternoon) → REQ-001 | MoM, Q-006 |

**Agent readings for the BA to confirm** (assumptions, not decisions):

| Reading | Source |
|---|---|
| Priority: "must" maps to HIGH and "should" to MEDIUM. Requirements stated with "can" or with no modal verb get MEDIUM by default, and so do REQ-033 and REQ-034 (the MoM gives no priority). The BA confirms the priorities through Q-028. | URS §4 – §6 wording; MoM |
| REQ-013 (notification emails) is typed FUNCTIONAL although the URS lists it under Non-Functional Requirements, because it describes system behaviour. | URS §5 |
| Terminology assumptions ASM-001 – ASM-004: "Manager" means Line Manager; Admin/HR is one role; Medical Leave equals Sick Leave (with Hospital Certificate); "request type" means leave type. | URS §3, §4.4 – §4.7 |
| Behaviour assumptions ASM-005, ASM-007, ASM-008: employees see their entitlement; weekly notifications go by email; managers submit their own leave like employees. ASM-006 is now confirmed by the MoM. | URS §3, §4.1 – §4.3, §5 |
| Vendor deliverables (URS §7) are not system requirements (ASM-009). | URS §7 |
| Readings of the MoM: a policy-violating request still goes through PM confirmation before the LM's review (ASM-011); the month-end cancellation is automatic (ASM-012); leave that includes any day of the previous month is refused as a whole (ASM-013); the PM is chosen per request (ASM-014); a half day counts as 0.5 day (ASM-015). | MoM, Q-002 – Q-004, Q-006 |
| NFRs without a measurable target keep the criteria the URS supports, and an open question asks for the target. No number was invented: REQ-025 → Q-026, REQ-026 → Q-022, REQ-028/REQ-029 → Q-023, REQ-030 → Q-024, REQ-031 → Q-025. | URS §4.8, §5, §6 |

**MoM compared with the URS.** The MoM does not contradict the URS. It extends it in three places that the BA should note:
- REQ-033 adds an HR-system integration that the URS does not mention; the URS names only the card scanner system (§2, §4.8).
- Half-day leave (Q-006) meets the URS's 4-hour off-work rule (§4.3), which was written without half days (Q-035).
- With the cancellation rule, a past-date request submitted on the last day of the month is cancelled at the month-end cut-off unless the PM and the LM both act on it the same day (Q-034).

## Requirements Summary
| REQ | Name | Type | Priority | Source |
|---|---|---|---|---|
| REQ-001 | Submit leave request | FUNCTIONAL | MEDIUM | URS §4.1, §4.6; MoM (Q-002, Q-003, Q-006) |
| REQ-002 | Validate leave requests against leave policy | FUNCTIONAL | MEDIUM | URS §1, §3, §4.5 |
| REQ-003 | Accept policy-violating leave requests for manual review | FUNCTIONAL | MEDIUM | URS §3, §4.1; MoM (Q-004) |
| REQ-004 | Attach required supporting documents to a leave request | FUNCTIONAL | HIGH | URS §4.5 |
| REQ-005 | View own leave requests and their status | FUNCTIONAL | MEDIUM | URS §4.6 |
| REQ-006 | Confirm or deny a leave request | FUNCTIONAL | MEDIUM | URS §4.2, §4.6; MoM (Q-002) |
| REQ-007 | Auto-confirm a Project Manager's own leave request | FUNCTIONAL | MEDIUM | URS §4.2 |
| REQ-008 | Approve or reject a confirmed leave request | FUNCTIONAL | MEDIUM | URS §4.2, §4.6 |
| REQ-009 | Complete review and approval within the leave start month | FUNCTIONAL | HIGH | URS §4.2, §6; MoM (Q-003) |
| REQ-010 | Modify and resubmit a denied or rejected leave request | FUNCTIONAL | MEDIUM | URS §4.2 |
| REQ-011 | Determine off-work days from attendance data | FUNCTIONAL | MEDIUM | URS §4.3 |
| REQ-012 | Send weekly attendance notification | FUNCTIONAL | MEDIUM | URS §3, §4.3 |
| REQ-013 | Automated and configurable notification emails | FUNCTIONAL | HIGH | URS §3, §5 |
| REQ-014 | Import annual leave entitlements | FUNCTIONAL | MEDIUM | URS §4.4, §4.6 |
| REQ-015 | Refresh leave data annually | FUNCTIONAL | MEDIUM | URS §4.1, §4.6 |
| REQ-016 | Manage leave types | FUNCTIONAL | HIGH | URS §4.5 |
| REQ-017 | Configure leave type eligibility rules | FUNCTIONAL | HIGH | URS §4.5 |
| REQ-018 | Configure required documentation per leave type | FUNCTIONAL | HIGH | URS §4.5 |
| REQ-019 | Support the suggested set of leave types | FUNCTIONAL | MEDIUM | URS §4.1, §4.7 |
| REQ-020 | Action dashboards for Project Managers and Line Managers | FUNCTIONAL | HIGH | URS §4.7 |
| REQ-021 | Filter leave request views | FUNCTIONAL | HIGH | URS §4.7 |
| REQ-022 | Report leave statistics | FUNCTIONAL | MEDIUM | URS §4.7, §4.8 |
| REQ-023 | Support a multinational organisational structure | FUNCTIONAL | HIGH | URS §4.7, §4.8 |
| REQ-024 | Fetch check-in and check-out times from the card scanner system | FUNCTIONAL | MEDIUM | URS §2, §4.8 |
| REQ-025 | Web-based and mobile-responsive | NON_FUNCTIONAL · PLATFORM | MEDIUM | URS §5 |
| REQ-026 | Secure login and logout for all roles | NON_FUNCTIONAL · SECURITY | HIGH | URS §5 |
| REQ-027 | Role-based access rights | NON_FUNCTIONAL · SECURITY | HIGH | URS §3, §4.6, §4.8, §5 |
| REQ-028 | Scale to 33,000 users | NON_FUNCTIONAL · SCALABILITY | HIGH | URS §4.8 |
| REQ-029 | Handle concurrent submissions without delay | NON_FUNCTIONAL · PERFORMANCE | MEDIUM | URS §4.8, §5 |
| REQ-030 | Reliable under heavy usage | NON_FUNCTIONAL · RELIABILITY | HIGH | URS §4.8 |
| REQ-031 | Multi-language localisation | NON_FUNCTIONAL · INTERNATIONALISATION | MEDIUM | URS §6 |
| REQ-032 | Use card scanner data as provided | NON_FUNCTIONAL · CONSTRAINT | MEDIUM | URS §4.8, §6 |
| REQ-033 | Import people and organisation data from the HR systems | FUNCTIONAL | MEDIUM | MoM (Q-001); URS §4.2, §4.5, §4.8 |
| REQ-034 | Cancel leave requests not completed by the end of the leave start month | FUNCTIONAL | MEDIUM | MoM (Q-003); URS §4.2, §6 |
