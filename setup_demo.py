"""
╔══════════════════════════════════════════════════════════════════╗
║          ZELIS PROVIDER SUPPORT — DEMO SETUP SCRIPT             ║
║          Built by Meghana Padullaparthi                          ║
║                                                                  ║
║  This script creates the full demo environment in your           ║
║  Jira Cloud sandbox:                                             ║
║    1. Assets schema — Provider Registry                          ║
║    2. Sample provider objects with realistic data                ║
║    3. JSM project — Provider Support Operations                  ║
║    4. Automation rules (configured manually — see GUIDE.md)      ║
║    5. Instructions for queue and SLA setup                        ║
╚══════════════════════════════════════════════════════════════════╝

HOW TO RUN:
  1. Fill in your credentials in config.py
  2. pip install requests
  3. python setup_zelis_demo.py

WHAT YOU NEED:
  - Free Jira Cloud account at atlassian.com
  - Jira Service Management enabled (free tier includes it)
  - API token from id.atlassian.com/manage-profile/security/api-tokens
"""

import requests
import json
import sys
import time
from requests.auth import HTTPBasicAuth

# ── LOAD CONFIG ───────────────────────────────────────────────────────────────
try:
    import config
    JIRA_URL   = config.JIRA_URL        # e.g. https://yoursite.atlassian.net
    EMAIL      = config.EMAIL           # your Atlassian account email
    API_TOKEN  = config.API_TOKEN       # from id.atlassian.com
    WORKSPACE_ID = getattr(config, 'WORKSPACE_ID', None)
except ImportError:
    print("\n❌  config.py not found.")
    print("    Copy config_template.py to config.py and fill in your details.\n")
    sys.exit(1)

auth    = HTTPBasicAuth(EMAIL, API_TOKEN)
headers = {"Accept": "application/json", "Content-Type": "application/json"}

def jira(method, path, **kwargs):
    url = f"{JIRA_URL}/rest/api/3/{path}"
    r   = requests.request(method, url, auth=auth, headers=headers, **kwargs)
    if not r.ok:
        print(f"  ✗ {method} {path} → {r.status_code}: {r.text[:300]}")
    return r

def assets(method, path, **kwargs):
    """Call the Atlassian Assets (JSM) API"""
    base = f"https://api.atlassian.com/jsm/assets/workspace/{WORKSPACE_ID}/v1"
    url  = f"{base}/{path}"
    r    = requests.request(method, url, auth=auth, headers=headers, **kwargs)
    if not r.ok:
        print(f"  ✗ ASSETS {method} {path} → {r.status_code}: {r.text[:300]}")
    return r

def ok(label):
    print(f"  ✓ {label}")

def section(title):
    print(f"\n{'─'*60}")
    print(f"  {title}")
    print(f"{'─'*60}")

# ══════════════════════════════════════════════════════════════════
# STEP 1 — VERIFY CONNECTION
# ══════════════════════════════════════════════════════════════════
section("Step 1 — Verifying Jira connection")

r = jira("GET", "myself")
if not r.ok:
    print("\n❌  Cannot connect to Jira. Check your JIRA_URL, EMAIL, and API_TOKEN in config.py")
    sys.exit(1)
me = r.json()
ok(f"Connected as {me.get('displayName')} ({me.get('emailAddress')})")

# Get cloud ID (needed for some API calls)
r = requests.get(f"{JIRA_URL}/_edge/tenant_info", auth=auth, headers=headers)
cloud_id = r.json().get("cloudId") if r.ok else None
if cloud_id:
    ok(f"Cloud ID: {cloud_id}")

# ══════════════════════════════════════════════════════════════════
# STEP 2 — CREATE JSM PROJECT
# ══════════════════════════════════════════════════════════════════
section("Step 2 — Creating JSM Project: Provider Support Operations")

# Check if project already exists
r = jira("GET", "project/PSO")
if r.ok:
    print("  → Project PSO already exists, skipping creation")
    project_key = "PSO"
    project_id  = r.json().get("id")
else:
    # Get a service desk project type
    payload = {
        "name": "Provider Support Operations",
        "key":  "PSO",
        "projectTypeKey": "service_desk",
        "description": "Healthcare Provider Support internal service desk for provider payment support, enrollment inquiries, and dispute resolution.",
        "leadAccountId": me.get("accountId"),
        "assigneeType": "UNASSIGNED"
    }
    r = jira("POST", "project", json=payload)
    if r.ok:
        project_key = r.json().get("key")
        project_id  = r.json().get("id")
        ok(f"Created project {project_key} (ID: {project_id})")
    else:
        print("  → Could not auto-create JSM project via API.")
        print("    Create it manually in Jira: Projects → Create Project → Service Management")
        print("    Project name: Provider Support Operations | Key: PSO")
        project_key = "PSO"
        project_id  = None

# ══════════════════════════════════════════════════════════════════
# STEP 3 — CREATE JIRA ISSUES AS SAMPLE TICKETS
# ══════════════════════════════════════════════════════════════════
section("Step 3 — Creating sample support tickets in project PSO")

# Fetch valid issue types for this project
r = jira("GET", f"project/{project_key}/issuetypes")
valid_types = []
if r.ok:
    valid_types = [t.get("name") for t in r.json()]
    ok(f"Valid issue types: {', '.join(valid_types)}")
else:
    r2 = jira("GET", f"issue/createmeta?projectKeys={project_key}&expand=projects.issuetypes")
    if r2.ok:
        projects_meta = r2.json().get("projects", [])
        if projects_meta:
            valid_types = [t.get("name") for t in projects_meta[0].get("issuetypes", [])]
            ok(f"Valid issue types: {', '.join(valid_types)}")

def pick_type(preferred_list):
    for name in preferred_list:
        if name in valid_types:
            return {"name": name}
    return {"name": valid_types[0]} if valid_types else {"name": "Task"}

incident_type = pick_type(["Incident", "Bug", "Support", "Issue", "Task", "Service Request"])
task_type     = pick_type(["Service Request", "Task", "Support", "Issue", "Incident"])

sample_tickets = [
    {
        "summary": "Payment Not Received — Valley Medical Group (NPI: 1234567890)",
        "description": {
            "type": "doc", "version": 1,
            "content": [{"type": "paragraph", "content": [{"type": "text",
                "text": "Valley Medical Group has not received their ACH payment for claim batch submitted March 10. Payment amount expected: $48,200. Provider is Enterprise tier. Last confirmed payment was February 28. Please investigate and confirm ETA for payment delivery."}]}]
        },
        "issuetype": incident_type,
        "priority": {"name": "High"},
        "labels": ["payment-dispute", "enterprise-provider", "ACH"]
    },
    {
        "summary": "Remittance Data Discrepancy — Sunrise Cardiology Associates",
        "description": {
            "type": "doc", "version": 1,
            "content": [{"type": "paragraph", "content": [{"type": "text",
                "text": "Sunrise Cardiology received remittance showing $12,450 but expected $18,200 based on submitted claims. Three claims appear to have been repriced without notification. Provider is requesting itemized explanation of repricing methodology."}]}]
        },
        "issuetype": incident_type,
        "priority": {"name": "Medium"},
        "labels": ["remittance-discrepancy", "repricing", "out-of-network"]
    },
    {
        "summary": "Enrollment Request — Riverside Community Health Center",
        "description": {
            "type": "doc", "version": 1,
            "content": [{"type": "paragraph", "content": [{"type": "text",
                "text": "New provider requesting enrollment in Healthcare Provider Support electronic payment network. Currently receiving paper checks from 4 payers in the Healthcare Provider Support network. Wants to consolidate to ACH via single platform. NPI: 9876543210. 340 providers in their system."}]}]
        },
        "issuetype": task_type,
        "priority": {"name": "Low"},
        "labels": ["enrollment", "new-provider", "ACH"]
    },
    {
        "summary": "Payment Not Received — Metro Orthopedics (URGENT — 45 days overdue)",
        "description": {
            "type": "doc", "version": 1,
            "content": [{"type": "paragraph", "content": [{"type": "text",
                "text": "Metro Orthopedics reports 45-day-overdue payment for $92,100 claim batch. Provider is threatening to escalate to legal. Account manager has been unresponsive. Enterprise tier provider with $2.1M annual payment volume through Healthcare Provider Support network. Requires immediate senior review."}]}]
        },
        "issuetype": incident_type,
        "priority": {"name": "Highest"},
        "labels": ["payment-dispute", "enterprise-provider", "escalation", "legal-risk"]
    },
    {
        "summary": "Contract Pricing Dispute — Blue Ridge Family Medicine",
        "description": {
            "type": "doc", "version": 1,
            "content": [{"type": "paragraph", "content": [{"type": "text",
                "text": "Blue Ridge Family Medicine disputes out-of-network pricing on 12 claims. Healthcare Provider Support repriced at 140% of Medicare. Provider argues correct rate should be 175% based on their contract with the payer. Requesting formal dispute review under NSA guidelines."}]}]
        },
        "issuetype": task_type,
        "priority": {"name": "Medium"},
        "labels": ["pricing-dispute", "out-of-network", "NSA", "contract-review"]
    },
    {
        "summary": "Payment Not Received — Children's Wellness Clinic",
        "description": {
            "type": "doc", "version": 1,
            "content": [{"type": "paragraph", "content": [{"type": "text",
                "text": "Children's Wellness Clinic has not received virtual card payment issued March 5. Card was sent to previous office manager who has since left. Requesting reissue to current billing contact. Amount: $8,450."}]}]
        },
        "issuetype": incident_type,
        "priority": {"name": "Medium"},
        "labels": ["payment-not-received", "virtual-card", "reissue"]
    },
    {
        "summary": "Enrollment Request — Summit Neurology Group (bulk enrollment — 8 locations)",
        "description": {
            "type": "doc", "version": 1,
            "content": [{"type": "paragraph", "content": [{"type": "text",
                "text": "Summit Neurology Group requesting enrollment for all 8 practice locations under one consolidated ACH account. Currently receiving paper checks from 11 payers. Annual payment volume approximately $4.8M. Primary contact: billing director Sarah Chen."}]}]
        },
        "issuetype": task_type,
        "priority": {"name": "Low"},
        "labels": ["enrollment", "bulk-enrollment", "high-volume"]
    },
    {
        "summary": "Remittance Data Discrepancy — Harbor View Radiology",
        "description": {
            "type": "doc", "version": 1,
            "content": [{"type": "paragraph", "content": [{"type": "text",
                "text": "Harbor View Radiology unable to reconcile remittance for February. 23 claims listed as paid in remittance data but funds not showing in bank account. Possible ACH routing issue. Amount: $31,200."}]}]
        },
        "issuetype": incident_type,
        "priority": {"name": "High"},
        "labels": ["remittance-discrepancy", "ACH", "reconciliation"]
    },
]

created_tickets = []
for ticket in sample_tickets:
    payload = {
        "fields": {
            "project":     {"key": project_key},
            "summary":     ticket["summary"],
            "description": ticket["description"],
            "issuetype":   ticket["issuetype"],
            "priority":    ticket["priority"],
            "labels":      ticket["labels"],
        }
    }
    r = jira("POST", "issue", json=payload)
    if r.ok:
        key = r.json().get("key")
        created_tickets.append(key)
        ok(f"Ticket {key}: {ticket['summary'][:55]}...")
    time.sleep(0.3)

# ══════════════════════════════════════════════════════════════════
# STEP 4 — ADD COMMENTS TO TICKETS (simulating real history)
# ══════════════════════════════════════════════════════════════════
section("Step 4 — Adding realistic ticket history and comments")

comments = {
    0: [  # Valley Medical Group
        "Confirmed with Finance: ACH batch was processed March 12. Tracing with bank — 3-5 business days expected.",
        "Bank trace returned: funds held by intermediary bank. Releasing by EOD. Provider notified.",
    ],
    1: [  # Sunrise Cardiology
        "Reviewed repricing: 3 claims were out-of-network and repriced per payer contract. Preparing itemized explanation.",
    ],
    3: [  # Metro Orthopedics URGENT
        "Escalated to Director of Provider Relations. Senior account manager assigned. Emergency call scheduled for tomorrow 9am.",
        "Call completed. Payment confirmed in next ACH run — Thursday March 20. Provider satisfied, legal escalation withdrawn.",
    ],
}

for idx, comment_list in comments.items():
    if idx < len(created_tickets):
        ticket_key = created_tickets[idx]
        for comment in comment_list:
            payload = {
                "body": {
                    "type": "doc", "version": 1,
                    "content": [{"type": "paragraph", "content": [{"type": "text", "text": comment}]}]
                }
            }
            r = jira("POST", f"issue/{ticket_key}/comment", json=payload)
            if r.ok:
                ok(f"Comment added to {ticket_key}")
            time.sleep(0.2)

# ══════════════════════════════════════════════════════════════════
# STEP 5 — ASSETS SCHEMA SETUP INSTRUCTIONS
# ══════════════════════════════════════════════════════════════════
section("Step 5 — Assets Schema Setup")

if not WORKSPACE_ID:
    print("""
  ⚠️  WORKSPACE_ID not set in config.py.

  To get your workspace ID:
    1. Go to your Jira Cloud site
    2. Click Settings → Assets
    3. Click any schema (or create one)
    4. Look at the URL: it will contain your workspace ID
       Example: https://yoursite.atlassian.net/jira/servicedesk/assets/workspace/ABC123/...
    5. Copy that ID and add it to config.py as WORKSPACE_ID

  Once you have the workspace ID, re-run this script and the
  Assets schema will be created automatically.
  
  Alternatively, create the schema manually — see MANUAL_SETUP.md
""")
else:
    print("  Creating Assets schema via API...")

    # Create the schema
    schema_payload = {
        "name": "Healthcare Provider Support Provider Registry",
        "objectSchemaKey": "ZPR",
        "description": "Healthcare provider asset registry for Healthcare Provider Support Provider Support Operations. Tracks provider enrollment status, payment methods, contract tiers, and open disputes."
    }
    r = assets("POST", "objectschema/create", json=schema_payload)
    if r.ok:
        schema_id = r.json().get("id")
        ok(f"Created schema: Healthcare Provider Support Provider Registry (ID: {schema_id})")
    else:
        print("  → Schema may already exist or workspace ID may be incorrect")
        schema_id = None

# ══════════════════════════════════════════════════════════════════
# STEP 6 — WRITE SUMMARY REPORT
# ══════════════════════════════════════════════════════════════════
section("Step 6 — Writing setup summary")

summary = f"""
╔══════════════════════════════════════════════════════════════╗
║              ZELIS DEMO SETUP COMPLETE                       ║
╚══════════════════════════════════════════════════════════════╝

Project created:  Provider Support Operations (PSO)
Tickets created:  {len(created_tickets)}

Ticket keys: {', '.join(created_tickets)}

NEXT STEPS — complete these manually in your Jira Cloud:

1. ASSETS SCHEMA
   Go to Settings → Assets → Create Schema
   Name: Healthcare Provider Support Provider Registry
   See MANUAL_SETUP.md for the full object type and attribute list

2. JSM REQUEST TYPES
   Go to your PSO project → Project Settings → Request types
   Create: Payment Not Received, Remittance Discrepancy, 
           Enrollment Request, Contract Pricing Dispute

3. QUEUES
   Project Settings → Queues → Create queue
   See MANUAL_SETUP.md for JQL filters for each queue

4. AUTOMATION RULES
   Project Settings → Automation → Create rule
   See MANUAL_SETUP.md for all 5 automation rules

5. RUN THE AI REPORT
   python ai_report.py
   (generates Confluence-ready management summary with AI insights)

6. DEMO SCRIPT
   See DEMO_SCRIPT.md for the exact 8-minute demo walkthrough

Your Jira site: {JIRA_URL}
"""

print(summary)

with open("SETUP_SUMMARY.txt", "w") as f:
    f.write(summary)
ok("Summary written to SETUP_SUMMARY.txt")

