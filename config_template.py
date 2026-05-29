# ─────────────────────────────────────────────────────────────────
#  ZELIS DEMO — CONFIG FILE
#  Step 1: Copy this file to config.py
#  Step 2: Fill in every value below
#  Step 3: Run: python3 setup_zelis_demo.py
# ─────────────────────────────────────────────────────────────────

# Your Jira Cloud site URL — no trailing slash
# Example: https://meghana-demo.atlassian.net
JIRA_URL = "https://YOUR-SITE.atlassian.net"

# Your Atlassian account email
EMAIL = "your-email@example.com"

# API token — get it here: id.atlassian.com/manage-profile/security/api-tokens
# Click "Create API token" and name it Healthcare Provider SupportDemo
API_TOKEN = "your-api-token-here"

# Groq API key — get it free at console.groq.com (sign in with Google)
GROQ_API_KEY = "gsk_your-groq-api-key-here"

# Atlassian Assets Workspace ID
# How to find it:
#   1. Go to your Jira Cloud site
#   2. Settings (gear icon top right) → Assets
#   3. Look at the URL — it contains your workspace ID
#      Example: .../assets/workspace/a1b2c3d4-e5f6.../
#   4. Copy that long ID here
WORKSPACE_ID = None  # e.g. "a1b2c3d4-e5f6-7890-abcd-ef1234567890"

# Confluence space key — for auto-publishing the AI report
# How to find it:
#   1. Open Confluence on your Atlassian site
#   2. Create a new space called "Healthcare Provider Support Provider Support"
#   3. Look at the URL: /wiki/spaces/ZPS/ — ZPS is the key
CONFLUENCE_SPACE_KEY = None  # e.g. "ZPS"

# Confluence page ID — the page where the report publishes
# How to find it:
#   1. Create a blank page called "Healthcare Provider Support Provider Support — Weekly Operations Report"
#   2. Open the page
#   3. Click the three dots (...) menu top right → Page information
#   4. The page ID is in the URL: /pages/123456789/
CONFLUENCE_PAGE_ID = None  # e.g. "123456789"
