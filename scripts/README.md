# Development Scripts

This directory contains scripts to help with local development and testing.

## CI Check Scripts

These scripts run all the same checks that are performed in the CI/CD pipeline locally, helping you catch issues before pushing to GitHub.

### Available Scripts

1. **`run_ci_checks.py`** - Cross-platform Python script with full features
2. **`run_ci_checks.sh`** - Bash script for Unix/Linux/macOS
3. **`run_ci_checks.ps1`** - PowerShell script for Windows

### Usage

#### Python Script (Recommended)
```bash
# Run all checks
python scripts/run_ci_checks.py

# Skip slower checks (mypy, pytest)
python scripts/run_ci_checks.py --fast

# Skip specific checks
python scripts/run_ci_checks.py --skip mypy,bandit

# Show help
python scripts/run_ci_checks.py --help
```

#### Bash Script (Unix/Linux/macOS)
```bash
# Make executable first
chmod +x scripts/run_ci_checks.sh

# Run all checks
./scripts/run_ci_checks.sh

# Skip slower checks
./scripts/run_ci_checks.sh --fast

# Skip specific checks
./scripts/run_ci_checks.sh --skip mypy,bandit
```

#### PowerShell Script (Windows)
```powershell
# Run all checks
.\scripts\run_ci_checks.ps1

# Skip slower checks
.\scripts\run_ci_checks.ps1 -Fast

# Skip specific checks
.\scripts\run_ci_checks.ps1 -Skip "mypy,bandit"

# Show help
.\scripts\run_ci_checks.ps1 -Help
```

### What Gets Checked

The scripts run the following checks in order:

1. **Ruff** - Code linting and style checking
2. **Black** - Code formatting verification
3. **MyPy** - Static type checking
4. **Bandit** - Security vulnerability scanning
5. **Pytest** - Unit tests with coverage reporting
6. **Build** - Package building and installation test

### Options

- `--fast` / `-Fast`: Skips the slower checks (mypy and pytest)
- `--skip` / `-Skip`: Comma-separated list of specific checks to skip
  - Available checks: `ruff`, `black`, `mypy`, `bandit`, `pytest`, `build`

### Output

The scripts provide:
- ✅ Green checkmarks for passing checks
- ❌ Red X marks for failing checks  
- ⏭️ Yellow arrows for skipped checks
- Timing information for each check
- Final summary with total time and any failures

### Examples

```bash
# Quick check before committing (skips slow tests)
python scripts/run_ci_checks.py --fast

# Check everything except security scan
python scripts/run_ci_checks.py --skip bandit

# Only run linting and formatting
python scripts/run_ci_checks.py --skip mypy,bandit,pytest,build
```

### Tips

- Run with `--fast` for quick feedback during development
- Run the full suite before creating pull requests
- The scripts will install missing tools (like `build`) automatically
- All scripts exit with code 0 on success, non-zero on failure (good for CI/automation)

### Requirements

- Python 3.9+ with the project's dev dependencies installed
- All tools should be available in your PATH after running `pip install -e .[dev,full]`
