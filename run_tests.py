#!/usr/bin/env python
"""Script to run tests with coverage reporting."""

import subprocess
import sys

def main():
    """Run pytest with coverage reporting."""
    cmd = [
        "pytest",
        "--cov=ynab_sync",
        "--cov-report=term",
        "--cov-report=html:coverage_html",
        "tests/"
    ]
    
    result = subprocess.run(cmd)
    return result.returncode

if __name__ == "__main__":
    sys.exit(main()) 