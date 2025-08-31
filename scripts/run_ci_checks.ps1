# Local CI Check Runner for Windows PowerShell
# This script runs all CI checks locally

param(
    [switch]$Fast,
    [string]$Skip = "",
    [switch]$Help
)

# Show help
if ($Help) {
    Write-Host @"
Usage: .\scripts\run_ci_checks.ps1 [-Fast] [-Skip CHECKS] [-Help]

Options:
  -Fast          Skip slower checks (mypy, pytest)
  -Skip CHECKS   Comma-separated list of checks to skip
                Available: ruff,black,mypy,bandit,pytest,build
  -Help         Show this help message

Examples:
  .\scripts\run_ci_checks.ps1
  .\scripts\run_ci_checks.ps1 -Fast
  .\scripts\run_ci_checks.ps1 -Skip "mypy,bandit"
"@
    exit 0
}

# Colors for output (Windows PowerShell)
$RED = "`e[31m"
$GREEN = "`e[32m"
$YELLOW = "`e[33m"
$BLUE = "`e[34m"
$PURPLE = "`e[35m"
$CYAN = "`e[36m"
$BOLD = "`e[1m"
$NC = "`e[0m"  # No Color

# Function to print headers
function Write-Header {
    param([string]$title)
    Write-Host ""
    Write-Host "${BOLD}${BLUE}============================================================${NC}"
    Write-Host "${BOLD}${BLUE}$($title.PadLeft(30 + ($title.Length / 2)))${NC}"
    Write-Host "${BOLD}${BLUE}============================================================${NC}"
}

# Function to print steps
function Write-Step {
    param([string]$step)
    Write-Host ""
    Write-Host "${BOLD}${CYAN}🔍 $step${NC}"
}

# Function to run a command with timing
function Invoke-Check {
    param(
        [string]$Description,
        [string]$Command,
        [string[]]$Arguments = @()
    )
    
    $fullCommand = if ($Arguments.Count -gt 0) { "$Command $($Arguments -join ' ')" } else { $Command }
    Write-Host "${YELLOW}Running: $fullCommand${NC}"
    
    $startTime = Get-Date
    
    try {
        if ($Arguments.Count -gt 0) {
            & $Command @Arguments
        } else {
            Invoke-Expression $Command
        }
        
        $endTime = Get-Date
        $elapsed = ($endTime - $startTime).TotalSeconds
        Write-Host "${GREEN}✅ $Description passed ($([math]::Round($elapsed, 1))s)${NC}"
        return $true
    }
    catch {
        $endTime = Get-Date
        $elapsed = ($endTime - $startTime).TotalSeconds
        Write-Host "${RED}❌ $Description failed ($([math]::Round($elapsed, 1))s)${NC}"
        Write-Host "${RED}Error: $($_.Exception.Message)${NC}"
        return $false
    }
}

# Parse skip list
$skipChecks = @()
if ($Skip) {
    $skipChecks = $Skip -split "," | ForEach-Object { $_.Trim() }
}

if ($Fast) {
    $skipChecks += @("mypy", "pytest")
}

# Function to check if we should skip a check
function Test-ShouldSkip {
    param([string]$check)
    return $skipChecks -contains $check
}

# Find project root (script is in scripts/ subdirectory)
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptDir

# Validate project structure
$pyprojectPath = Join-Path $projectRoot "pyproject.toml"
if (-not (Test-Path $pyprojectPath)) {
    Write-Host "${RED}Error: pyproject.toml not found in $projectRoot${NC}"
    exit 1
}

Set-Location $projectRoot

# Track failures
$failedChecks = @()
$totalStart = Get-Date

Write-Header "LOCAL CI CHECKS"
Write-Host "${PURPLE}Project: $projectRoot${NC}"
Write-Host "${PURPLE}Python: $(Get-Command python -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source)${NC}"

if ($skipChecks.Count -gt 0) {
    Write-Host "${YELLOW}Skipping: $($skipChecks -join ', ')${NC}"
}

# Run checks
if (-not (Test-ShouldSkip "ruff")) {
    Write-Step "Linting with ruff"
    if (-not (Invoke-Check "Ruff linting" "ruff" @("check", "src/", "tests/"))) {
        $failedChecks += "ruff"
    }
} else {
    Write-Host ""
    Write-Host "${YELLOW}⏭️  Skipping ruff${NC}"
}

if (-not (Test-ShouldSkip "black")) {
    Write-Step "Checking formatting with black"
    if (-not (Invoke-Check "Black formatting" "black" @("--check", "src/", "tests/"))) {
        $failedChecks += "black"
    }
} else {
    Write-Host ""
    Write-Host "${YELLOW}⏭️  Skipping black${NC}"
}

if (-not (Test-ShouldSkip "mypy")) {
    Write-Step "Type checking with mypy"
    if (-not (Invoke-Check "MyPy type checking" "mypy" @("src/safellm"))) {
        $failedChecks += "mypy"
    }
} else {
    Write-Host ""
    Write-Host "${YELLOW}⏭️  Skipping mypy${NC}"
}

if (-not (Test-ShouldSkip "bandit")) {
    Write-Step "Security checking with bandit"
    if (-not (Invoke-Check "Bandit security check" "bandit" @("-r", "src/safellm"))) {
        $failedChecks += "bandit"
    }
} else {
    Write-Host ""
    Write-Host "${YELLOW}⏭️  Skipping bandit${NC}"
}

if (-not (Test-ShouldSkip "pytest")) {
    Write-Step "Running tests with pytest"
    if (-not (Invoke-Check "Pytest tests with coverage" "pytest" @("--cov=safellm", "--cov-report=term-missing", "--cov-report=html"))) {
        $failedChecks += "pytest"
    }
} else {
    Write-Host ""
    Write-Host "${YELLOW}⏭️  Skipping pytest${NC}"
}

if (-not (Test-ShouldSkip "build")) {
    Write-Step "Building package"
    
    # Check if build tool is available
    try {
        python -m build --help > $null 2>&1
    }
    catch {
        Write-Host "${YELLOW}Installing build tool...${NC}"
        if (-not (Invoke-Check "Install build tool" "pip" @("install", "build"))) {
            $failedChecks += "build-install"
        }
    }
    
    if (-not (Invoke-Check "Package build" "python" @("-m", "build"))) {
        $failedChecks += "build"
    } else {
        Write-Step "Testing built package"
        if (-not (Invoke-Check "Built package test" "python" @("-c", "import safellm; print(f'SafeLLM version: {safellm.__version__}')"))) {
            $failedChecks += "build-test"
        }
    }
} else {
    Write-Host ""
    Write-Host "${YELLOW}⏭️  Skipping build${NC}"
}

# Summary
$totalEnd = Get-Date
$totalTime = ($totalEnd - $totalStart).TotalSeconds

Write-Header "CI CHECKS SUMMARY"

if ($failedChecks.Count -eq 0) {
    Write-Host "${GREEN}${BOLD}🎉 All checks passed! 🎉${NC}"
    Write-Host "${GREEN}Total time: $([math]::Round($totalTime, 1))s${NC}"
    exit 0
} else {
    Write-Host "${RED}${BOLD}❌ $($failedChecks.Count) check(s) failed:${NC}"
    foreach ($check in $failedChecks) {
        Write-Host "${RED}  • $check${NC}"
    }
    Write-Host "${YELLOW}Total time: $([math]::Round($totalTime, 1))s${NC}"
    Write-Host ""
    Write-Host "${YELLOW}💡 Fix the issues above and run again${NC}"
    exit 1
}
