# ZELIS DEMO — Manual Setup Guide
## Everything you configure by hand in Jira Cloud

This guide covers everything the Python script cannot do automatically
because Jira's UI-based features (Assets schema, queues, automation rules,
SLAs) require manual configuration through the browser.

Follow these steps after running setup_zelis_demo.py.

---

## PART 1 — ATLASSIAN ASSETS SCHEMA

### Step 1.1 — Create the schema

1. Go to your Jira Cloud site
2. Click **Settings** (gear icon, top right) → **Assets**
3. Click **Create schema**
4. Name: `Healthcare Provider Support Provider Registry`
5. Key: `ZPR`
6. Description: `Healthcare provider registry for Healthcare Provider Support Provider Support Operations`
7. Click **Create**

---

### Step 1.2 — Create the Healthcare Provider object type

Inside your new schema, click **Create object type**

**Object type name:** Healthcare Provider
**Icon:** Choose the person or building icon
**Description:** Healthcare providers enrolled in or seeking enrollment with the Healthcare Provider Support payment network

Now add these attributes one by one (click **Create attribute** for each):

| Attribute Name | Type | Options / Notes |
|---|---|---|
| NPI Number | Text | National Provider Identifier — unique to each provider |
| Provider Name | Text | Full legal name of the practice or facility |
| Enrollment Status | Select | Options: Not Enrolled, Enrolled ACH, Enrolled Virtual Card, Enrolled Paper Check, Suspended |
| Contract Type | Select | Options: In-Network, Out-of-Network, Pending Contracting |
| Payment Volume | Select | Options: Low, Medium, High, Enterprise |
| Preferred Payment Method | Select | Options: ACH, Virtual Card, Paper Check |
| Last Payment Date | Date | |
| Open Disputes | Integer | Manually maintained count |
| Assigned Account Manager | User | Links to Jira user directory |
| Annual Payment Volume | Text | e.g. $2.1M |
| Payer Count | Integer | Number of Healthcare Provider Support payers they receive payments from |
| Notes | Text area | Free text for agent context |

---

### Step 1.3 — Create 5 sample provider objects

Click **Create object** for each of these:

**Provider 1 — Valley Medical Group**
- NPI Number: 1234567890
- Enrollment Status: Enrolled ACH
- Contract Type: In-Network
- Payment Volume: Enterprise
- Preferred Payment Method: ACH
- Open Disputes: 1
- Annual Payment Volume: $4.2M
- Payer Count: 14
- Notes: Long-standing enterprise client. Priority escalation path through Senior Account Manager.

**Provider 2 — Sunrise Cardiology Associates**
- NPI Number: 2345678901
- Enrollment Status: Enrolled ACH
- Contract Type: Out-of-Network
- Payment Volume: High
- Preferred Payment Method: ACH
- Open Disputes: 1
- Annual Payment Volume: $1.8M
- Payer Count: 8

**Provider 3 — Metro Orthopedics**
- NPI Number: 3456789012
- Enrollment Status: Enrolled ACH
- Contract Type: In-Network
- Payment Volume: Enterprise
- Preferred Payment Method: ACH
- Open Disputes: 2
- Annual Payment Volume: $2.1M
- Payer Count: 11
- Notes: URGENT — 45-day overdue payment. Legal escalation risk. Requires senior review.

**Provider 4 — Blue Ridge Family Medicine**
- NPI Number: 4567890123
- Enrollment Status: Enrolled Paper Check
- Contract Type: Out-of-Network
- Payment Volume: Medium
- Preferred Payment Method: Paper Check
- Open Disputes: 1
- Annual Payment Volume: $420K
- Payer Count: 4
- Notes: Candidate for ACH enrollment conversion — currently on paper check.

**Provider 5 — Riverside Community Health Center**
- NPI Number: 9876543210
- Enrollment Status: Not Enrolled
- Contract Type: Pending Contracting
- Payment Volume: High
- Preferred Payment Method: ACH (requested)
- Open Disputes: 0
- Annual Payment Volume: Pending
- Notes: New enrollment request. 340 providers in their system. High-value prospect.

---

## PART 2 — JSM PROJECT CONFIGURATION

### Step 2.1 — Set up request types

Go to your **PSO project** → **Project Settings** → **Request types**

Create these 4 request types:

**Request type 1: Payment Not Received**
- Issue type: Bug (or Incident if available)
- Description: Report a missing or delayed payment from the Healthcare Provider Support network
- Fields to show on form: Summary, Description, Provider name (Assets lookup), Payment amount, Expected payment date
- Portal group: Payment Issues

**Request type 2: Remittance Data Discrepancy**
- Issue type: Bug
- Description: Report a mismatch between remittance data and actual payment received
- Fields to show on form: Summary, Description, Claim batch reference
- Portal group: Payment Issues

**Request type 3: Enrollment Request**
- Issue type: Task
- Description: Request to join the Healthcare Provider Support electronic payment network
- Fields to show on form: Summary, Description, NPI Number, Preferred payment method, Number of practice locations
- Portal group: Enrollment

**Request type 4: Contract Pricing Dispute**
- Issue type: Task
- Description: Dispute the pricing applied to an out-of-network claim
- Fields to show on form: Summary, Description, Claim reference number, Expected vs received amount
- Portal group: Pricing

---

### Step 2.2 — Create queues

Go to **PSO project** → **Project Settings** → **Queues** → **Create queue**

**Queue 1: Enterprise Provider Issues**
- JQL: `project = PSO AND labels = "enterprise-provider" AND status != Done ORDER BY priority DESC`
- Columns: Issue key, Summary, Priority, Created, Assignee, Labels
- Purpose: Enterprise providers always get priority handling

**Queue 2: Active Escalations**
- JQL: `project = PSO AND labels in ("escalation", "legal-risk") AND status != Done ORDER BY created ASC`
- Columns: Issue key, Summary, Priority, Created, Labels
- Purpose: Immediate visibility on at-risk provider relationships

**Queue 3: Payment Disputes — All Open**
- JQL: `project = PSO AND labels in ("payment-dispute", "payment-not-received") AND status != Done ORDER BY priority DESC, created ASC`
- Columns: Issue key, Summary, Priority, Created, Assignee
- Purpose: Most common ticket type in one view

**Queue 4: Enrollment Requests**
- JQL: `project = PSO AND labels = "enrollment" AND status != Done ORDER BY created ASC`
- Columns: Issue key, Summary, Created, Assignee
- Purpose: Track new provider enrollment pipeline

**Queue 5: All Unassigned**
- JQL: `project = PSO AND assignee is EMPTY AND status != Done ORDER BY priority DESC`
- Columns: Issue key, Summary, Priority, Created, Labels
- Purpose: Catch anything that was not auto-assigned

---

### Step 2.3 — Configure SLAs

Go to **PSO project** → **Project Settings** → **SLAs** → **Create SLA**

**SLA 1: Time to First Response**

| Condition | Goal |
|---|---|
| Priority = Highest | 30 minutes |
| Priority = High AND label = enterprise-provider | 1 hour |
| Priority = High | 2 hours |
| All other issues | 8 business hours |

Start condition: Issue created
Pause condition: Status = Waiting for Provider Response
Stop condition: Comment added by agent OR status changes to In Progress

**SLA 2: Time to Resolution**

| Condition | Goal |
|---|---|
| Priority = Highest | 4 hours |
| Priority = High AND label = enterprise-provider | 1 business day |
| Priority = High | 2 business days |
| All other issues | 5 business days |

---

## PART 3 — AUTOMATION RULES

Go to **PSO project** → **Project Settings** → **Automation** → **Create rule**

---

**Rule 1: Auto-assign Enterprise Provider tickets to Priority Queue**

Trigger: Issue created
Condition: Label contains "enterprise-provider"
Action: Set priority to Highest
Action: Add comment (internal): "⚠️ ENTERPRISE PROVIDER — This ticket requires priority handling. Please respond within 1 hour per enterprise SLA."

---

**Rule 2: Escalation Alert — Flag legal risk tickets**

Trigger: Issue created OR label added
Condition: Label contains "legal-risk" OR label contains "escalation"
Action: Set priority to Highest
Action: Add comment (internal): "🚨 ESCALATION ACTIVE — This ticket has been flagged as an escalation risk. Senior account manager must be notified within 30 minutes."

---

**Rule 3: Auto-comment on payment disputes with context prompt**

Trigger: Issue created
Condition: Label contains "payment-dispute" OR label contains "payment-not-received"
Action: Add comment (internal):
```
📋 PAYMENT DISPUTE CHECKLIST — complete before responding to provider:
□ Look up provider in Assets: Healthcare Provider Support Provider Registry
□ Confirm enrollment status and preferred payment method
□ Check last payment date in Assets record
□ Verify ACH routing details are current
□ Check for other open disputes from same provider
□ Confirm contract type (in-network vs out-of-network)
```

---

**Rule 4: Route enrollment requests to enrollment team**

Trigger: Issue created
Condition: Label contains "enrollment"
Action: Add label: "new-intake"
Action: Add comment (internal): "New enrollment request received. Standard processing time: 3-5 business days. Assign to enrollment specialist."

---

**Rule 5: Auto-close resolved tickets after 5 days with no response**

Trigger: Issue transitioned to Waiting for Provider Response
Wait: 5 days (business days only)
Condition: Status still = Waiting for Provider Response
Action: Transition to Resolved
Action: Add comment: "This ticket has been automatically resolved after 5 business days with no provider response. Please reopen if you still need assistance."

---

## PART 4 — VERIFY YOUR SETUP

Before the demo, run through this checklist:

- [ ] PSO project exists and you can access it
- [ ] At least 5 tickets exist with realistic provider names and labels
- [ ] All 5 queues show the correct tickets
- [ ] The Enterprise Provider Issues queue shows Metro Orthopedics and Valley Medical Group
- [ ] The Active Escalations queue shows the Metro Orthopedics ticket
- [ ] Assets schema exists with at least 3 provider objects
- [ ] Automation rules are active (green toggle)
- [ ] You have run python ai_report.py and it generated zelis_provider_report.md
- [ ] The Groq AI insight paragraph appears in the report

If all checked: you are ready to demo. Run through the demo script once before the interview.

---

## PART 5 — DEMO SCRIPT (8 minutes)

### Opening (30 seconds)
"I built a proof of concept in my Jira Cloud sandbox based on what I understand about Healthcare Provider Support's provider support operations. The problem I modeled is one of the most common in healthcare financial services — when a provider calls about a payment issue, the agent has no context before the call starts. I built a solution using Assets and JSM. Can I show you?"

### Act 1 — The ticket queue (2 minutes)
- Open the PSO project
- Show the Enterprise Provider Issues queue — point out the Metro Orthopedics ticket
- Click into it — show the urgency, the labels, the 45-day overdue context
- Say: "This is the kind of ticket that generates a complaint call to the account manager an hour later if it is not handled first."
- Show the Active Escalations queue — same ticket appears there too

### Act 2 — Assets context (3 minutes)
- Open Assets → Healthcare Provider Support Provider Registry
- Click on Metro Orthopedics
- Show every attribute — NPI, enrollment status, payment volume (Enterprise), open disputes (2), annual volume ($2.1M), the notes flagging legal risk
- Say: "This is what an agent should see the moment a ticket opens. Not after 10 minutes of asking questions. The moment it opens."
- Go back to the Metro Orthopedics ticket
- Say: "When Assets is linked to JSM, this provider profile would appear in the sidebar of this ticket automatically. The agent walks into every interaction already knowing the situation."

### Act 3 — The AI report (3 minutes)
- Open a terminal
- Say: "The last thing I want to show you is the documentation and AI layer on top of this."
- Run: python ai_report.py
- Let the output scroll — show the metrics analysis happening in real time
- Show the AI insight paragraph appearing at the end
- Open zelis_provider_report.md
- Say: "This report took 30 seconds to generate. Without this tool someone would spend 2 hours compiling this manually before a weekly operations meeting. I built the same thing at Citi for release governance. The tool is different. The problem is identical."

### Close (30 seconds)
"This is a proof of concept built in a free Jira Cloud sandbox. The production version — with Assets fully linked to JSM, real provider data, and SLAs calibrated to Healthcare Provider Support's actual contracts — is what I want to build with your team. What does your current environment look like?"

---

*Built by Meghana Padullaparthi — DevSecOps Engineer*
*Demonstrating Atlassian Assets + JSM + AI proficiency for Healthcare Provider Support interview*
