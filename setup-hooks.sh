#!/bin/bash

# Script to install git pre-commit hooks

set -e

HOOKS_DIR=".githooks"
GIT_HOOKS_DIR=".git/hooks"
PRE_COMMIT_HOOK="pre-commit"

# Check if .githooks directory exists
if [ ! -d "$HOOKS_DIR" ]; then
    echo "Error: $HOOKS_DIR directory not found!"
    exit 1
fi

# Check if pre-commit hook exists
if [ ! -f "$HOOKS_DIR/$PRE_COMMIT_HOOK" ]; then
    echo "Error: $HOOKS_DIR/$PRE_COMMIT_HOOK not found!"
    exit 1
fi

# Check if .git directory exists
if [ ! -d ".git" ]; then
    echo "Error: .git directory not found! Are you in a git repository?"
    exit 1
fi

# Create .git/hooks directory if it doesn't exist
mkdir -p "$GIT_HOOKS_DIR"

# Copy the pre-commit hook
echo "Installing pre-commit hook..."
cp "$HOOKS_DIR/$PRE_COMMIT_HOOK" "$GIT_HOOKS_DIR/$PRE_COMMIT_HOOK"

# Make the hook executable
chmod +x "$GIT_HOOKS_DIR/$PRE_COMMIT_HOOK"

echo "Pre-commit hook installed successfully!"
echo "The hook will now run black, flake8, and mypy on staged Python files before each commit."

