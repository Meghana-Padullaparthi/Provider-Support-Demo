# Healthcare Provider Support Provider Support Demo
Built by Meghana Padullaparthi

A proof of concept demonstrating Atlassian Assets, JSM, and AI integration
for healthcare provider support operations.

---

## What this demo shows

- JSM queues, automation rules, and SLA configuration for provider support
- Atlassian Assets provider registry with structured healthcare provider objects
- AI-powered operations report generated from live JSM ticket data
- Auto-publish to Confluence — one script run updates the page live

---

## Step 1 — Create your free Atlassian account

1. Go to atlassian.com/try/cloud/signup
2. Create a free Jira Cloud site
3. When asked, enable Jira Service Management (free tier includes it)
4. Note your site URL — it will look like: https://your-name.atlassian.net

---

## Step 2 — Get your API token

1. Go to: id.atlassian.com/manage-profile/security/api-tokens
2. Click "Create API token"
3. Name it: Healthcare Provider SupportDemo
4. Copy the token — you will not see it again

---

## Step 3 — Get your Groq API key (free)

1. Go to: console.groq.com
2. Sign in with Google
3. Click "API Keys" → "Create API Key"
4. Copy the key — starts with gsk_

---

## Step 4 — Set up Confluence (for auto-publish)

1. Open your Atlassian site → click the grid icon top left → Confluence
2. Create a new space called "Healthcare Provider Support Provider Support"
   - Note the space key from the URL: /wiki/spaces/ZPS/ → key is ZPS
3. Inside that space, create a blank page called:
   "Healthcare Provider Support Provider Support — Weekly Operations Report"
4. Open the page → click three dots (...) → Page information
   - The page ID is in the URL: /pages/123456789/ → ID is 123456789

---

## Step 5 — Get your Assets Workspace ID

1. On your Jira site → Settings (gear icon) → Assets
2. Click any schema or create one called "Healthcare Provider Support Provider Registry"
3. Look at the URL in your browser
   It will contain: /assets/workspace/YOUR-WORKSPACE-ID/
4. Copy that ID

---

## Step 6 — Configure config.py

1. Copy config_template.py to config.py
   Mac/Linux: cp config_template.py config.py
   Windows:   copy config_template.py config.py

2. Open config.py and fill in all values:
   - JIRA_URL              your Atlassian site URL
   - EMAIL                 your Atlassian account email
   - API_TOKEN             from Step 2
   - GROQ_API_KEY          from Step 3
   - CONFLUENCE_SPACE_KEY  from Step 4
   - CONFLUENCE_PAGE_ID    from Step 4
   - WORKSPACE_ID          from Step 5

---

## Step 7 — Install dependencies

pip3 install requests

---

## Step 8 — Run the setup script

python3 setup_zelis_demo.py

This creates:
  - PSO project (Jira Service Management)
  - 5 sample provider tickets with realistic healthcare scenarios
  - Ticket comments simulating real resolution history
  - Assets schema (if WORKSPACE_ID is configured)

---

## Step 9 — Manual setup in Jira UI

Some things cannot be automated via API and must be done in the browser.
After running setup_zelis_demo.py, do these steps manually:

### Assets — create provider objects
1. Settings → Assets → Healthcare Provider Support Provider Registry
2. Create object type: Healthcare Provider
3. Add attributes: NPI Number, Provider Name, Enrollment Status,
   Contract Type, Payment Volume, Preferred Payment Method,
   Last Payment Date, Open Disputes, Annual Payment Volume, Notes
4. Create 3-5 provider objects (see MANUAL_SETUP.md for sample data)

### JSM — create queues
Go to PSO project → Project Settings → Queues → Create queue

Queue 1: Enterprise Provider Issues
JQL: project = PSO AND labels = "enterprise-provider" AND status != Done ORDER BY priority DESC

Queue 2: Active Escalations
JQL: project = PSO AND labels in ("escalation","legal-risk") AND status != Done ORDER BY created ASC

Queue 3: Payment Disputes
JQL: project = PSO AND labels in ("payment-dispute","payment-not-received") AND status != Done ORDER BY priority DESC

Queue 4: Enrollment Requests
JQL: project = PSO AND labels = "enrollment" AND status != Done ORDER BY created ASC

Queue 5: All Unassigned
JQL: project = PSO AND assignee is EMPTY AND status != Done ORDER BY priority DESC

### JSM — configure SLAs
Go to PSO project → Project Settings → SLAs → Create SLA

SLA 1: Time to First Response
- Priority = Highest → 30 minutes
- Priority = High AND label = enterprise-provider → 1 hour
- Priority = High → 2 hours
- All others → 8 business hours

SLA 2: Time to Resolution
- Priority = Highest → 4 hours
- Priority = High AND enterprise-provider → 1 business day
- Priority = High → 2 business days
- All others → 5 business days

### JSM — configure automation rules
Go to PSO project → Project Settings → Automation → Create rule

Rule 1: Enterprise provider auto-escalation
- Trigger: Issue created
- Condition: Label contains "enterprise-provider"
- Action: Set priority to Highest
- Action: Add internal comment — "ENTERPRISE PROVIDER — 1 hour SLA response required"

Rule 2: Legal risk escalation alert
- Trigger: Issue created OR label added
- Condition: Label contains "legal-risk" OR "escalation"
- Action: Set priority to Highest
- Action: Add internal comment — "ESCALATION ACTIVE — notify senior account manager within 30 minutes"

Rule 3: Payment dispute checklist
- Trigger: Issue created
- Condition: Label contains "payment-dispute" OR "payment-not-received"
- Action: Add internal comment — "PAYMENT DISPUTE CHECKLIST: Check provider in Assets, confirm enrollment status, verify ACH routing, check last payment date, check for other open disputes"

Rule 4: Enrollment request routing
- Trigger: Issue created
- Condition: Label contains "enrollment"
- Action: Add internal comment — "New enrollment request. Standard processing: 3-5 business days. Assign to enrollment specialist."

Rule 5: Auto-close after 5 days no response
- Trigger: Issue transitioned to Waiting for Provider Response
- Wait: 5 business days
- Condition: Status still = Waiting for Provider Response
- Action: Transition to Resolved
- Action: Add comment — "Auto-resolved after 5 days with no provider response. Reopen if needed."

---

## Step 10 — Run the AI report

python3 ai_report.py

This will:
  1. Query all tickets from the PSO project
  2. Analyze patterns across categories, priorities, and escalations
  3. Generate an AI executive summary using Groq
  4. Save zelis_provider_report.md locally
  5. Update your Confluence page automatically (if configured)

---

## Pre-demo checklist

Before recording or presenting, verify:

- [ ] PSO project exists and has at least 5 tickets
- [ ] All 5 queues show the correct tickets
- [ ] Enterprise Provider Issues queue shows Metro Orthopedics
- [ ] Active Escalations queue shows the escalation ticket
- [ ] Automation rules are active (green toggle)
- [ ] SLAs are configured
- [ ] Assets schema exists with at least 3 provider objects
- [ ] Metro Orthopedics object has all attributes filled
- [ ] python3 ai_report.py runs without errors
- [ ] Confluence page exists and is accessible
- [ ] Groq AI insight paragraph appears in the report
- [ ] Confluence page updates when you run the script

---

## Files in this package

| File | Purpose |
|------|---------|
| config_template.py | Copy to config.py and fill in your credentials |
| config.py | Your credentials — never share or commit this file |
| setup_zelis_demo.py | Creates the JSM project and sample tickets |
| ai_report.py | Generates the AI report and publishes to Confluence |
| README.md | This file — full setup instructions |
| MANUAL_SETUP.md | Detailed manual setup guide for Jira UI steps |
| zelis_provider_report.md | Generated report — created when you run ai_report.py |

