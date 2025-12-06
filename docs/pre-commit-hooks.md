# Pre-commit Hooks Setup Guide

This guide explains how to set up and use pre-commit hooks for black, flake8, and mypy in this project.

## Overview

Pre-commit hooks automatically run code quality checks (formatting, linting, and type checking) on staged Python files before each commit. This ensures code quality and consistency across the project.

## Prerequisites

Before setting up the hooks, ensure you have the required tools installed:

```bash
pip install black flake8 mypy
```

## Installation

1. **Install the git hooks:**
   ```bash
   ./setup-hooks.sh
   ```

   This script:
   - Copies `.githooks/pre-commit` to `.git/hooks/pre-commit`
   - Makes the hook executable
   - Verifies the installation

2. **Verify installation:**
   ```bash
   ls -la .git/hooks/pre-commit
   ```
   You should see the pre-commit file listed and executable.

## How It Works

### Automatic Execution

Once installed, the hook runs **automatically** on every `git commit`:

```bash
git add myfile.py
git commit -m "Update myfile"
# Hook runs automatically here - checks black, flake8, and mypy
```

### What Gets Checked

The hook runs three checks on all staged Python files (`.py`):

1. **Black** - Code formatting check
   - Verifies code follows black's formatting standards
   - Uses 88 character line length (configured in `pyproject.toml`)

2. **Flake8** - Linting check
   - Checks for code style violations
   - Uses configuration from `.flake8`

3. **Mypy** - Type checking
   - Validates type annotations and catches type errors
   - Uses configuration from `pyproject.toml`

### Behavior

- **If all checks pass:** Commit proceeds normally
- **If any check fails:** Commit is blocked with error messages
- **If no Python files are staged:** Hook exits successfully (nothing to check)

## Configuration Files

### `pyproject.toml`

Contains configuration for:
- **Black**: Line length (88), Python version (3.12+), file patterns
- **Mypy**: Python version, strictness settings, ignore patterns

### `.flake8`

Contains configuration for:
- Max line length (88, matching black)
- Ignore patterns for common directories
- Error code selections

## Testing the Hooks

### Test with a Problematic File

Create a test file with intentional issues:

```bash
# Create file with formatting, linting, and type issues
cat > test_file.py << 'EOF'
def bad_function(x,y):
    unused_var=42
    return x+y
EOF

# Stage it
git add test_file.py

# Try to commit (should fail)
git commit -m "Test commit"
```

The commit should be blocked with error messages from black, flake8, and mypy.

### Test with a Valid File

```bash
cat > test_valid.py << 'EOF'
def add_numbers(x: int, y: int) -> int:
    """Add two numbers together."""
    return x + y
EOF

git add test_valid.py
git commit -m "Test valid file"
# Should succeed
```

### Manual Testing

You can also run the hook manually without committing:

```bash
.git/hooks/pre-commit
```

## Bypassing Hooks (Not Recommended)

If you need to bypass the hook in an emergency:

```bash
git commit --no-verify -m "Skip hooks"
```

**Warning:** Only use this when absolutely necessary. It defeats the purpose of having quality checks.

## Troubleshooting

### Hook Not Running

1. Verify it's installed:
   ```bash
   ls -la .git/hooks/pre-commit
   ```

2. Check it's executable:
   ```bash
   chmod +x .git/hooks/pre-commit
   ```

3. Reinstall if needed:
   ```bash
   ./setup-hooks.sh
   ```

### Tools Not Found

If you see errors like "black is not installed":
```bash
pip install black flake8 mypy
```

### Hook Fails on Valid Code

- Check your `pyproject.toml` and `.flake8` configurations
- Verify Python version compatibility
- Run tools individually to debug:
  ```bash
  black --check yourfile.py
  flake8 yourfile.py
  mypy yourfile.py
  ```

## Costs

**There are no costs associated with these hooks:**
- They run locally on your machine
- No GitHub server resources used
- No GitHub Actions minutes consumed
- Completely free to use

## Files in This Setup

- `.githooks/pre-commit` - The hook script that runs the checks
- `pyproject.toml` - Configuration for black and mypy
- `.flake8` - Configuration for flake8
- `setup-hooks.sh` - Installation script

## Additional Resources

- [Black Documentation](https://black.readthedocs.io/)
- [Flake8 Documentation](https://flake8.pycqa.org/)
- [Mypy Documentation](https://mypy.readthedocs.io/)
- [Git Hooks Documentation](https://git-scm.com/book/en/v2/Customizing-Git-Git-Hooks)

