"""
╔══════════════════════════════════════════════════════════════════╗
║         ZELIS PROVIDER SUPPORT — AI MANAGEMENT REPORT           ║
║         Built by Meghana Padullaparthi                           ║
║                                                                  ║
║  Queries all open JSM tickets, analyzes patterns, and            ║
║  generates an AI-powered management summary using Groq.          ║
║  Auto-publishes to Confluence when configured.                   ║
╚══════════════════════════════════════════════════════════════════╝

HOW TO RUN:
  python3 ai_report.py

OUTPUT:
  - Console summary with key metrics
  - zelis_provider_report.md  (local markdown file)
  - Confluence page updated automatically (if configured)
  - AI-generated insight paragraph from Groq
"""

import requests
import json
from requests.auth import HTTPBasicAuth
from collections import Counter
from datetime import datetime
import sys
import base64

try:
    import config
    JIRA_URL       = config.JIRA_URL
    EMAIL          = config.EMAIL
    API_TOKEN      = config.API_TOKEN
    GROQ_KEY       = config.GROQ_API_KEY
    CONFLUENCE_SPACE = getattr(config, 'CONFLUENCE_SPACE_KEY', None)
    CONFLUENCE_PAGE  = getattr(config, 'CONFLUENCE_PAGE_ID', None)
except ImportError:
    print("\n❌  config.py not found. Copy config_template.py to config.py\n")
    sys.exit(1)

auth    = HTTPBasicAuth(EMAIL, API_TOKEN)
headers = {"Accept": "application/json", "Content-Type": "application/json"}

def jira_get(path, params=None):
    r = requests.get(f"{JIRA_URL}/rest/api/3/{path}", auth=auth, headers=headers, params=params)
    return r.json() if r.ok else {}

def section(title):
    print(f"\n{'═'*60}")
    print(f"  {title}")
    print(f"{'═'*60}")

# ══════════════════════════════════════════════════════════════════
# STEP 1 — FETCH ALL TICKETS FROM PSO PROJECT
# ══════════════════════════════════════════════════════════════════
section("Step 1 — Fetching tickets from Provider Support Operations")

params = {
    "jql":        "project = PSO ORDER BY created DESC",
    "maxResults": 100,
    "fields":     "summary,status,priority,labels,created,issuetype,assignee"
}
r = requests.get(f"{JIRA_URL}/rest/api/3/search", auth=auth, headers=headers, params=params)

if r.status_code == 410:
    r = requests.post(
        f"{JIRA_URL}/rest/api/3/search/jql",
        auth=auth,
        headers=headers,
        json={
            "jql":        "project = PSO ORDER BY created DESC",
            "maxResults": 100,
            "fields":     ["summary","status","priority","labels","created","issuetype","assignee"]
        }
    )

if not r.ok:
    print(f"❌  Could not fetch tickets: {r.status_code}")
    print("    Make sure the PSO project exists and your config.py is correct.")
    sys.exit(1)

data   = r.json()
issues = data.get("issues", [])
total  = len(issues)
print(f"  ✓ Found {total} tickets in Provider Support Operations")

# ══════════════════════════════════════════════════════════════════
# STEP 2 — ANALYZE TICKET PATTERNS
# ══════════════════════════════════════════════════════════════════
section("Step 2 — Analyzing ticket patterns")

category_map = {
    "payment-dispute":        "Payment Not Received",
    "payment-not-received":   "Payment Not Received",
    "remittance-discrepancy": "Remittance Discrepancy",
    "enrollment":             "Enrollment Request",
    "pricing-dispute":        "Contract Pricing Dispute",
    "contract-review":        "Contract Pricing Dispute",
    "escalation":             "Escalation",
}

categories       = Counter()
priorities       = Counter()
payment_methods  = Counter()
escalations      = []
enterprise_issues= []
open_count       = 0
high_priority    = 0
unassigned_count = 0

for issue in issues:
    fields   = issue.get("fields", {})
    summary  = fields.get("summary", "")
    status   = fields.get("status", {}).get("name", "")
    priority = fields.get("priority", {}).get("name", "Unknown")
    labels   = fields.get("labels", [])
    assignee = fields.get("assignee")

    if status not in ["Done", "Closed", "Resolved"]:
        open_count += 1

    if not assignee:
        unassigned_count += 1

    if priority in ["High", "Highest"]:
        high_priority += 1

    priorities[priority] += 1

    categorized = False
    for label in labels:
        if label in category_map:
            categories[category_map[label]] += 1
            categorized = True
            break
    if not categorized:
        categories["Other"] += 1

    if "escalation" in labels or "legal-risk" in labels:
        escalations.append(summary[:70])

    if "enterprise-provider" in labels:
        enterprise_issues.append(summary[:70])

    for label in labels:
        if label == "ACH":
            payment_methods["ACH"] += 1
        elif label == "virtual-card":
            payment_methods["Virtual Card"] += 1
        elif label in ["paper-check", "check"]:
            payment_methods["Paper Check"] += 1

top_category = categories.most_common(1)[0] if categories else ("Unknown", 0)
top_pct      = round((top_category[1] / max(total, 1)) * 100)

print(f"\n  TICKET SUMMARY")
print(f"  {'─'*45}")
print(f"  Total tickets          : {total}")
print(f"  Open tickets           : {open_count}")
print(f"  High or urgent priority: {high_priority}")
print(f"  Active escalations     : {len(escalations)}")
print(f"  Enterprise provider    : {len(enterprise_issues)}")
print(f"  Unassigned tickets     : {unassigned_count}")

print(f"\n  CATEGORY BREAKDOWN")
print(f"  {'─'*45}")
for cat, count in categories.most_common():
    pct = round((count / max(total, 1)) * 100)
    bar = "█" * (pct // 5)
    print(f"  {cat:<32} {count:>3}  {bar} {pct}%")

print(f"\n  PRIORITY DISTRIBUTION")
print(f"  {'─'*45}")
for pri, count in priorities.most_common():
    print(f"  {pri:<20} {count}")

if payment_methods:
    print(f"\n  PAYMENT METHOD ISSUES")
    print(f"  {'─'*45}")
    for method, count in payment_methods.most_common():
        print(f"  {method:<20} {count}")

if escalations:
    print(f"\n  ACTIVE ESCALATIONS ⚠️")
    print(f"  {'─'*45}")
    for e in escalations:
        print(f"  • {e}")

if enterprise_issues:
    print(f"\n  ENTERPRISE PROVIDER ISSUES")
    print(f"  {'─'*45}")
    for e in enterprise_issues:
        print(f"  • {e}")

# ══════════════════════════════════════════════════════════════════
# STEP 3 — GENERATE AI INSIGHT WITH GROQ
# ══════════════════════════════════════════════════════════════════
section("Step 3 — Generating AI insight with Groq")

data_summary = f"""
Healthcare Provider Support Provider Support Operations — Ticket Analysis

Total tickets: {total}
Open tickets: {open_count}
High or urgent priority: {high_priority}
Active escalations: {len(escalations)}
Enterprise provider issues: {len(enterprise_issues)}
Unassigned tickets: {unassigned_count}
Top issue category: {top_category[0]} at {top_pct}% of all tickets

Category breakdown:
{chr(10).join([f"- {cat}: {count} tickets ({round((count/max(total,1))*100)}%)" for cat, count in categories.most_common()])}

Priority distribution:
{chr(10).join([f"- {pri}: {count}" for pri, count in priorities.most_common()])}

Payment method issues:
{chr(10).join([f"- {method}: {count}" for method, count in payment_methods.most_common()])}

Active escalations: {len(escalations)}
"""

prompt = f"""You are an operations analyst at Healthcare Provider Support Healthcare, a healthcare financial technology company.
You have been given a summary of the current provider support ticket queue.

Write a 3-4 sentence executive summary that:
1. States the most significant operational finding
2. Identifies the highest-risk situation requiring immediate attention
3. Suggests one specific action that would reduce ticket volume
4. Uses plain English a non-technical operations director can act on immediately

Write only the summary paragraph. No headers, no bullets, no preamble.

Data:
{data_summary}"""

ai_insight = None

if GROQ_KEY and GROQ_KEY != "gsk_your-groq-api-key-here":
    print("  Calling Groq API...")
    try:
        groq_r = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Content-Type":  "application/json",
                "Authorization": f"Bearer {GROQ_KEY}"
            },
            json={
                "model":       "llama-3.3-70b-versatile",
                "messages": [
                    {"role": "system",  "content": "You are an operations analyst. Write clear, actionable executive summaries."},
                    {"role": "user",    "content": prompt}
                ],
                "temperature": 0.3,
                "max_tokens":  300
            },
            timeout=30
        )
        if groq_r.ok:
            ai_insight = groq_r.json()["choices"][0]["message"]["content"].strip()
            print(f"\n  AI INSIGHT (Groq — llama-3.3-70b):")
            print(f"  {'─'*50}")
            words, line = ai_insight.split(), "  "
            for word in words:
                if len(line) + len(word) > 72:
                    print(line)
                    line = "  " + word + " "
                else:
                    line += word + " "
            if line.strip():
                print(line)
        else:
            print(f"  ⚠️  Groq returned {groq_r.status_code}")
    except Exception as e:
        print(f"  ⚠️  Groq call failed: {e}")
else:
    print("  ⚠️  No Groq API key — using template insight")

if not ai_insight:
    ai_insight = (
        f"Provider support volume currently stands at {total} tickets with {open_count} open cases. "
        f"The highest-risk situation involves {len(escalations)} active escalation(s) requiring immediate "
        f"senior review to prevent provider relationship damage. {top_category[0]} accounts for {top_pct}% "
        f"of all tickets — a targeted process review for this category would have the greatest impact on "
        f"reducing overall support volume. Proactive outreach to the {len(enterprise_issues)} enterprise "
        f"providers with open issues is recommended before end of business today."
    )

# ══════════════════════════════════════════════════════════════════
# STEP 4 — BUILD THE REPORT
# ══════════════════════════════════════════════════════════════════
section("Step 4 — Building Confluence-ready report")

now    = datetime.now().strftime("%B %d, %Y at %H:%M")
report = f"""# Healthcare Provider Support Provider Support — Operations Report
**Generated:** {now}
**Project:** Provider Support Operations (PSO)
**Prepared by:** Meghana Padullaparthi — Atlassian Administrator

---

## Executive Summary

{ai_insight}

---

## Ticket Volume Overview

| Metric | Count |
|--------|-------|
| Total tickets | {total} |
| Open tickets | {open_count} |
| High or urgent priority | {high_priority} |
| Active escalations | {len(escalations)} |
| Enterprise provider issues | {len(enterprise_issues)} |
| Unassigned tickets | {unassigned_count} |

---

## Category Breakdown

| Category | Count | % of Total |
|----------|-------|------------|
"""
for cat, count in categories.most_common():
    pct = round((count / max(total, 1)) * 100)
    report += f"| {cat} | {count} | {pct}% |\n"

report += f"""
---

## Priority Distribution

| Priority | Count |
|----------|-------|
"""
for pri, count in priorities.most_common():
    report += f"| {pri} | {count} |\n"

if payment_methods:
    report += f"""
---

## Payment Method Issue Breakdown

| Payment Method | Open Issues |
|----------------|-------------|
"""
    for method, count in payment_methods.most_common():
        report += f"| {method} | {count} |\n"

if escalations:
    report += f"""
---

## ⚠️ Active Escalations — Requires Immediate Attention

"""
    for e in escalations:
        report += f"- {e}\n"

if enterprise_issues:
    report += f"""
---

## Enterprise Provider Issues

"""
    for e in enterprise_issues:
        report += f"- {e}\n"

report += f"""
---

## Recommended Actions

"""
for i, (cat, count) in enumerate(categories.most_common(3), 1):
    pct = round((count / max(total, 1)) * 100)
    actions = {
        "Payment Not Received":     "Review ACH processing pipeline for batch failures. Proactively notify affected providers before they call in.",
        "Enrollment Request":       "Assign dedicated enrollment specialist to clear backlog. Consider bulk enrollment for multi-location providers.",
        "Remittance Discrepancy":   "Audit repricing notifications — providers should receive advance notice when claims are repriced.",
        "Contract Pricing Dispute": "Schedule monthly pricing review calls with top 10 providers by dispute volume.",
        "Escalation":               "Immediate senior review required. Assign account manager and schedule provider call within 24 hours.",
    }
    action = actions.get(cat, "Review SLA targets and ensure adequate staffing for this category.")
    report += f"{i}. **{cat}** ({pct}% of tickets): {action}\n"

report += f"""
---

*This report was generated automatically from Jira Service Management using a Python automation tool.*
*AI insights generated using Groq (llama-3.3-70b-versatile).*
*Built by Meghana Padullaparthi — demonstrating Atlassian Assets, JSM, and AI proficiency.*
"""

# Save markdown file
with open("zelis_provider_report.md", "w") as f:
    f.write(report)
print("  ✓ Saved: zelis_provider_report.md")

# ══════════════════════════════════════════════════════════════════
# STEP 5 — PUBLISH TO CONFLUENCE
# ══════════════════════════════════════════════════════════════════
section("Step 5 — Publishing to Confluence")

if not CONFLUENCE_SPACE or not CONFLUENCE_PAGE:
    print("  ⚠️  Confluence not configured in config.py")
    print("  → Add CONFLUENCE_SPACE_KEY and CONFLUENCE_PAGE_ID to publish automatically")
    print("  → See README.md for how to find these values")
else:
    confluence_base = f"{JIRA_URL}/wiki"

    # Get current page version first
    page_r = requests.get(
        f"{confluence_base}/rest/api/content/{CONFLUENCE_PAGE}",
        auth=auth,
        headers={"Accept": "application/json"}
    )

    if not page_r.ok:
        print(f"  ❌  Could not fetch Confluence page: {page_r.status_code}")
        print("  → Check your CONFLUENCE_PAGE_ID in config.py")
    else:
        page_data   = page_r.json()
        current_ver = page_data["version"]["number"]
        new_version = current_ver + 1
        page_title  = page_data["title"]

        # Convert markdown report to Confluence storage format
        # Confluence storage format uses XHTML-like markup
        action_map = {
            "Payment Not Received": "Review ACH processing pipeline for batch failures. Proactively notify affected providers before they call in.",
            "Enrollment Request": "Assign dedicated enrollment specialist to clear backlog.",
            "Remittance Discrepancy": "Audit repricing notifications.",
            "Contract Pricing Dispute": "Schedule monthly pricing review calls with top providers.",
            "Escalation": "Immediate senior review required within 24 hours."
        }
        actions_html = "".join([
            f"<li><strong>{cat}</strong> ({round((count/max(total,1))*100)}% of tickets): {action_map.get(cat, 'Review SLA targets and staffing.')}</li>"
            for cat, count in categories.most_common(3)
        ])

        confluence_body = f"""<p><strong>Generated:</strong> {now}</p>
<p><strong>Project:</strong> Provider Support Operations (PSO)</p>
<p><strong>Prepared by:</strong> Meghana Padullaparthi — Atlassian Administrator</p>
<hr/>
<h2>Executive Summary</h2>
<p>{ai_insight}</p>
<hr/>
<h2>Ticket Volume Overview</h2>
<table><tbody>
<tr><th>Metric</th><th>Count</th></tr>
<tr><td>Total tickets</td><td>{total}</td></tr>
<tr><td>Open tickets</td><td>{open_count}</td></tr>
<tr><td>High or urgent priority</td><td>{high_priority}</td></tr>
<tr><td>Active escalations</td><td>{len(escalations)}</td></tr>
<tr><td>Enterprise provider issues</td><td>{len(enterprise_issues)}</td></tr>
<tr><td>Unassigned tickets</td><td>{unassigned_count}</td></tr>
</tbody></table>
<hr/>
<h2>Category Breakdown</h2>
<table><tbody>
<tr><th>Category</th><th>Count</th><th>% of Total</th></tr>
{"".join([f"<tr><td>{cat}</td><td>{count}</td><td>{round((count/max(total,1))*100)}%</td></tr>" for cat, count in categories.most_common()])}
</tbody></table>
<hr/>
<h2>Priority Distribution</h2>
<table><tbody>
<tr><th>Priority</th><th>Count</th></tr>
{"".join([f"<tr><td>{pri}</td><td>{count}</td></tr>" for pri, count in priorities.most_common()])}
</tbody></table>
{"<hr/><h2>⚠️ Active Escalations — Requires Immediate Attention</h2><ul>" + "".join([f"<li>{e}</li>" for e in escalations]) + "</ul>" if escalations else ""}
{"<hr/><h2>Enterprise Provider Issues</h2><ul>" + "".join([f"<li>{e}</li>" for e in enterprise_issues]) + "</ul>" if enterprise_issues else ""}
<hr/>
<h2>Recommended Actions</h2>
<ol>
{actions_html}
</ol>
<hr/>
<p><em>Auto-generated from Jira Service Management. AI insights by Groq (llama-3.3-70b). Built by Meghana Padullaparthi.</em></p>"""

        update_payload = {
            "version": {"number": new_version},
            "title":   page_title,
            "type":    "page",
            "body": {
                "storage": {
                    "value":          confluence_body,
                    "representation": "storage"
                }
            }
        }

        update_r = requests.put(
            f"{confluence_base}/rest/api/content/{CONFLUENCE_PAGE}",
            auth=auth,
            headers={"Accept": "application/json", "Content-Type": "application/json"},
            json=update_payload
        )

        if update_r.ok:
            page_url = f"{JIRA_URL}/wiki/spaces/{CONFLUENCE_SPACE}/pages/{CONFLUENCE_PAGE}"
            print(f"  ✓ Confluence page updated successfully")
            print(f"  ✓ View it here: {page_url}")
        else:
            print(f"  ❌  Confluence update failed: {update_r.status_code}")
            print(f"      {update_r.text[:200]}")

# ══════════════════════════════════════════════════════════════════
# DONE
# ══════════════════════════════════════════════════════════════════
section("Complete")
print(f"""
  ✓ zelis_provider_report.md  — local markdown file ready
  ✓ Confluence page           — {"updated live" if (CONFLUENCE_SPACE and CONFLUENCE_PAGE) else "not configured (see README.md)"}
""")

