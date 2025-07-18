#!/bin/bash

# watch_claude_changes.sh
# Script to watch for Claude Code changes and refresh VS Code

WATCH_DIR=${1:-"."}
EXCLUDE_PATTERNS="node_modules|\.git|\.vscode|__pycache__|\.pyc"

echo "Watching directory: $WATCH_DIR"
echo "Excluding patterns: $EXCLUDE_PATTERNS"

# Install fswatch if not available``
if ! command -v fswatch &> /dev/null; then
    echo "Installing fswatch..."
    if [[ "$OSTYPE" == "darwin"* ]]; then
        brew install fswatch
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        sudo apt-get install fswatch || sudo yum install fswatch
    fi
fi

# Watch for file changes
fswatch -o "$WATCH_DIR" --exclude="$EXCLUDE_PATTERNS" | while read f; do
    echo "$(date): Files changed in $WATCH_DIR"

    # Send refresh command to VS Code if it's running
    if pgrep -f "Visual Studio Code" > /dev/null; then
        echo "Refreshing VS Code workspace..."
        # This requires VS Code command line tools
        code --reload-window 2>/dev/null || echo "VS Code reload failed"
    fi
done
