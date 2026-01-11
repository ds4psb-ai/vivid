#!/bin/bash
# Chrome launch script for Vivid Project (Port 9223)
# Uses a specific user-data-dir (/tmp/chrome-debug-9223) to avoid conflicts with 9222

PORT=9223
# Use a distinctive directory name
DIR="/tmp/chrome-debug-$PORT"

echo "🚀 Launching Chrome on port $PORT..."
echo "📂 User Data Dir: $DIR"

# Kill existing instance on this port if any
pkill -f "remote-debugging-port=$PORT" && echo "♻️  Killed existing Chrome instance on port $PORT"

# Ensure directory exists with correct permissions
mkdir -p "$DIR"

# macOS path
CHROME_PATH="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

"$CHROME_PATH" \
  --remote-debugging-port=$PORT \
  --user-data-dir="$DIR" \
  --no-first-run \
  https://notebooklm.google.com/ &

echo "✅ Chrome launched!"
echo "👉 Login to NotebookLM in the new window, then run your tests."
