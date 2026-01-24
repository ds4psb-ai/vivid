#!/usr/bin/env bash
# Stitch MCP CLI Utility
# Usage: ./stitch_mcp_check.sh [command] [args...]
#
# Commands:
#   check     - Verify Stitch MCP setup (default)
#   list      - List all projects
#   create    - Create new project: create "Title"
#   screens   - List screens: screens <project_id>
#   generate  - Generate screen: generate <project_id> "description"
#   tools     - List available tools

set -euo pipefail

PROJECT_ID="${PROJECT_ID:-shorti-api-v2-prod-2026}"
ADC_EMAIL="${ADC_EMAIL:-ds4psbted@gmail.com}"

# Get token
get_token() {
  gcloud auth application-default print-access-token 2>/dev/null || {
    echo "ADC token missing. Run: gcloud auth application-default login" >&2
    exit 1
  }
}

# Call Stitch API
stitch_call() {
  local method="$1"
  local args="${2:-\{\}}"
  local TOKEN
  TOKEN="$(get_token)"
  local payload

  # Build JSON payload using printf for proper escaping
  payload=$(printf '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"%s","arguments":%s}}' "$method" "$args")

  curl -s -X POST "https://stitch.googleapis.com/mcp" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -H "X-Goog-User-Project: $PROJECT_ID" \
    -d "$payload"
}

# Commands
cmd_check() {
  echo "=== Stitch MCP Setup Check ==="
  echo "Project: $PROJECT_ID"
  echo "Email: $ADC_EMAIL"
  echo ""

  # Token check
  if get_token > /dev/null 2>&1; then
    echo "✅ ADC token: OK"
  else
    echo "❌ ADC token: MISSING"
    exit 1
  fi

  # API test
  local result
  result=$(stitch_call "list_projects" "{}" 2>/dev/null)
  if echo "$result" | grep -q '"projects"'; then
    local count
    count=$(echo "$result" | grep -o '"name":"projects/' | wc -l | tr -d ' ')
    echo "✅ Stitch API: OK ($count projects)"
  else
    echo "❌ Stitch API: FAILED"
    echo "$result"
    exit 1
  fi
}

cmd_list() {
  stitch_call "list_projects" "{}" | python3 -c "
import sys, json
data = json.load(sys.stdin)
projects = data.get('result', {}).get('structuredContent', {}).get('projects', [])
for p in projects:
    pid = p['name'].replace('projects/', '')
    title = p.get('title', 'Untitled')
    device = p.get('deviceType', 'DESKTOP')
    print(f'{pid}: {title} ({device})')
"
}

cmd_create() {
  local title="${1:-New Project}"
  stitch_call "create_project" "{\"title\":\"$title\"}" | python3 -c "
import sys, json
data = json.load(sys.stdin)
content = data.get('result', {}).get('structuredContent', {})
if 'name' in content:
    pid = content['name'].replace('projects/', '')
    print(f'Created project: {pid}')
    print(f'Title: {content.get(\"title\", \"Untitled\")}')
else:
    print('Error:', data)
"
}

cmd_screens() {
  local project_id="$1"
  stitch_call "list_screens" "{\"parent\":\"projects/$project_id\"}" | python3 -c "
import sys, json
data = json.load(sys.stdin)
screens = data.get('result', {}).get('structuredContent', {}).get('screens', [])
if not screens:
    print('No screens found')
else:
    for s in screens:
        sid = s['name'].split('/')[-1]
        title = s.get('title', 'Untitled')
        print(f'{sid}: {title}')
"
}

cmd_generate() {
  local project_id="$1"
  local description="$2"
  echo "Generating screen (this may take 30-120 seconds)..."
  stitch_call "generate_screen_from_text" "{\"parent\":\"projects/$project_id\",\"prompt\":\"$description\"}" | python3 -c "
import sys, json
data = json.load(sys.stdin)
content = data.get('result', {}).get('structuredContent', {})
if 'name' in content:
    sid = content['name'].split('/')[-1]
    title = content.get('title', 'Generated')
    print(f'Generated screen: {sid}')
    print(f'Title: {title}')
else:
    print('Result:', json.dumps(data, indent=2)[:500])
"
}

cmd_tools() {
  local TOKEN
  TOKEN="$(get_token)"
  curl -s -X POST "https://stitch.googleapis.com/mcp" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -H "X-Goog-User-Project: $PROJECT_ID" \
    -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' | python3 -c "
import sys, json
data = json.load(sys.stdin)
tools = data.get('result', {}).get('tools', [])
print(f'Available tools ({len(tools)}):')
for t in tools:
    print(f'  - {t[\"name\"]}: {t.get(\"description\", \"\")[:60]}...')
"
}

# Main
case "${1:-check}" in
  check)    cmd_check ;;
  list)     cmd_list ;;
  create)   cmd_create "${2:-}" ;;
  screens)  cmd_screens "${2:?'Usage: screens <project_id>'}" ;;
  generate) cmd_generate "${2:?'Usage: generate <project_id> \"description\"'}" "${3:-}" ;;
  tools)    cmd_tools ;;
  *)
    echo "Usage: $0 [check|list|create|screens|generate|tools]"
    exit 1
    ;;
esac
