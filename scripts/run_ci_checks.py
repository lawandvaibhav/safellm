#!/usr/bin/env python3
"""
Local CI Check Runner

This script runs all the same checks that are performed in CI/CD pipeline
to help catch issues locally before pushing to GitHub.

Usage:
    python scripts/run_ci_checks.py [--fast] [--skip CHECKS]

Options:
    --fast          Skip slower checks (mypy, pytest)
    --skip CHECKS   Comma-separated list of checks to skip
                   Available: ruff,black,mypy,bandit,pytest,build

Examples:
    python scripts/run_ci_checks.py
    python scripts/run_ci_checks.py --fast
    python scripts/run_ci_checks.py --skip mypy,bandit
"""

import argparse
import subprocess
import sys
import time
from pathlib import Path
from typing import List, Optional


class Colors:
    """ANSI color codes for terminal output"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    END = '\033[0m'


class CIRunner:
    """Runs CI checks locally"""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.failed_checks = []
        self.total_time = 0
    
    def print_header(self, title: str):
        """Print a formatted section header"""
        print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}")
        print(f"{Colors.BOLD}{Colors.BLUE}{title:^60}{Colors.END}")
        print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}")
    
    def print_step(self, step: str):
        """Print a step description"""
        print(f"\n{Colors.BOLD}{Colors.CYAN}🔍 {step}{Colors.END}")
    
    def run_command(self, cmd: List[str], description: str, timeout: int = 300) -> bool:
        """Run a command and return success status"""
        start_time = time.time()
        
        try:
            print(f"{Colors.YELLOW}Running: {' '.join(cmd)}{Colors.END}")
            
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            elapsed = time.time() - start_time
            self.total_time += elapsed
            
            if result.returncode == 0:
                print(f"{Colors.GREEN}✅ {description} passed ({elapsed:.1f}s){Colors.END}")
                if result.stdout.strip():
                    print(f"{Colors.WHITE}{result.stdout}{Colors.END}")
                return True
            else:
                print(f"{Colors.RED}❌ {description} failed ({elapsed:.1f}s){Colors.END}")
                if result.stdout.strip():
                    print(f"{Colors.WHITE}STDOUT:\n{result.stdout}{Colors.END}")
                if result.stderr.strip():
                    print(f"{Colors.RED}STDERR:\n{result.stderr}{Colors.END}")
                self.failed_checks.append(description)
                return False
                
        except subprocess.TimeoutExpired:
            elapsed = time.time() - start_time
            self.total_time += elapsed
            print(f"{Colors.RED}❌ {description} timed out after {timeout}s{Colors.END}")
            self.failed_checks.append(f"{description} (timeout)")
            return False
        except Exception as e:
            elapsed = time.time() - start_time
            self.total_time += elapsed
            print(f"{Colors.RED}❌ {description} failed with error: {e}{Colors.END}")
            self.failed_checks.append(f"{description} (error)")
            return False
    
    def check_ruff(self) -> bool:
        """Run ruff linting"""
        self.print_step("Linting with ruff")
        return self.run_command(
            [sys.executable, "-m", "ruff", "check", "src/", "tests/"],
            "Ruff linting"
        )
    
    def check_black(self) -> bool:
        """Run black formatting check"""
        self.print_step("Checking formatting with black")
        return self.run_command(
            [sys.executable, "-m", "black", "--check", "src/", "tests/"],
            "Black formatting"
        )
    
    def check_mypy(self) -> bool:
        """Run mypy type checking"""
        self.print_step("Type checking with mypy")
        return self.run_command(
            [sys.executable, "-m", "mypy", "src/safellm"],
            "MyPy type checking"
        )
    
    def check_bandit(self) -> bool:
        """Run bandit security check"""
        self.print_step("Security checking with bandit")
        return self.run_command(
            [sys.executable, "-m", "bandit", "-r", "src/safellm"],
            "Bandit security check"
        )
    
    def run_tests(self) -> bool:
        """Run pytest with coverage"""
        self.print_step("Running tests with pytest")
        return self.run_command(
            [sys.executable, "-m", "pytest", "--cov=safellm", "--cov-report=term-missing", "--cov-report=html"],
            "Pytest tests with coverage",
            timeout=600  # Tests can take longer
        )
    
    def build_package(self) -> bool:
        """Build the package"""
        self.print_step("Building package")
        
        # First install build if not available
        try:
            subprocess.run([sys.executable, "-m", "build", "--help"], 
                         capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            print(f"{Colors.YELLOW}Installing build tool...{Colors.END}")
            if not self.run_command(
                [sys.executable, "-m", "pip", "install", "build"],
                "Install build tool"
            ):
                return False
        
        success = self.run_command(
            [sys.executable, "-m", "build"],
            "Package build"
        )
        
        if success:
            # Test the built package
            print(f"\n{Colors.CYAN}Testing built package installation...{Colors.END}")
            success = self.run_command(
                [sys.executable, "-c", "import safellm; print(f'SafeLLM version: {safellm.__version__}')"],
                "Built package test"
            )
        
        return success
    
    def print_summary(self):
        """Print final summary"""
        self.print_header("CI CHECKS SUMMARY")
        
        if not self.failed_checks:
            print(f"{Colors.GREEN}{Colors.BOLD}🎉 All checks passed! 🎉{Colors.END}")
            print(f"{Colors.GREEN}Total time: {self.total_time:.1f}s{Colors.END}")
        else:
            print(f"{Colors.RED}{Colors.BOLD}❌ {len(self.failed_checks)} check(s) failed:{Colors.END}")
            for check in self.failed_checks:
                print(f"{Colors.RED}  • {check}{Colors.END}")
            print(f"{Colors.YELLOW}Total time: {self.total_time:.1f}s{Colors.END}")
            print(f"\n{Colors.YELLOW}💡 Fix the issues above and run again{Colors.END}")
        
        print()


def main():
    parser = argparse.ArgumentParser(
        description="Run CI checks locally",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__.split("Usage:")[1] if "Usage:" in __doc__ else ""
    )
    
    parser.add_argument(
        "--fast", 
        action="store_true",
        help="Skip slower checks (mypy, pytest)"
    )
    
    parser.add_argument(
        "--skip",
        type=str,
        help="Comma-separated list of checks to skip (ruff,black,mypy,bandit,pytest,build)"
    )
    
    args = parser.parse_args()
    
    # Find project root
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    
    # Validate project structure
    if not (project_root / "pyproject.toml").exists():
        print(f"{Colors.RED}Error: pyproject.toml not found in {project_root}{Colors.END}")
        sys.exit(1)
    
    # Parse skip list
    skip_checks = set()
    if args.skip:
        skip_checks = set(check.strip() for check in args.skip.split(","))
    
    if args.fast:
        skip_checks.update(["mypy", "pytest"])
    
    # Initialize runner
    runner = CIRunner(project_root)
    
    runner.print_header("LOCAL CI CHECKS")
    print(f"{Colors.PURPLE}Project: {project_root}{Colors.END}")
    print(f"{Colors.PURPLE}Python: {sys.executable}{Colors.END}")
    if skip_checks:
        print(f"{Colors.YELLOW}Skipping: {', '.join(sorted(skip_checks))}{Colors.END}")
    
    # Run checks in order
    checks = [
        ("ruff", runner.check_ruff),
        ("black", runner.check_black),
        ("mypy", runner.check_mypy),
        ("bandit", runner.check_bandit),
        ("pytest", runner.run_tests),
        ("build", runner.build_package),
    ]
    
    for check_name, check_func in checks:
        if check_name not in skip_checks:
            check_func()
        else:
            print(f"\n{Colors.YELLOW}⏭️  Skipping {check_name}{Colors.END}")
    
    # Print summary
    runner.print_summary()
    
    # Exit with error code if any checks failed
    sys.exit(len(runner.failed_checks))


if __name__ == "__main__":
    main()
