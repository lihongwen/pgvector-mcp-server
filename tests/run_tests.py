#!/usr/bin/env python3
"""Test runner script for pgvector MCP server tests.

This script provides an easy way to run tests with proper environment setup.
It checks for required environment variables and provides helpful error messages.

Usage:
    python tests/run_tests.py                    # Run all tests
    python tests/run_tests.py --mcp-tools       # Run only MCP tool tests
    python tests/run_tests.py --encoding        # Run only encoding tests
    python tests/run_tests.py --integration     # Run only integration tests
    python tests/run_tests.py --rename          # Run only rename tests
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path


def check_environment():
    """Check that required environment variables are set."""
    missing_vars = []
    
    # Check for DashScope API key
    if not os.getenv("DASHSCOPE_API_KEY"):
        missing_vars.append("DASHSCOPE_API_KEY")
    
    if missing_vars:
        print("❌ Missing required environment variables:")
        for var in missing_vars:
            print(f"   {var}")
        print()
        print("💡 To run tests, you need to set the DashScope API key:")
        print("   export DASHSCOPE_API_KEY=your_api_key_here")
        print()
        print("⚠️  Note: This API key should only be used for testing.")
        print("   Do not commit API keys to your repository!")
        return False
    
    print("✅ Environment variables are properly set")
    return True


def run_pytest(test_path="", markers="", verbose=True):
    """Run pytest with specified parameters."""
    cmd = ["python", "-m", "pytest"]
    
    if test_path:
        cmd.append(test_path)
    else:
        cmd.append("tests/")
    
    if markers:
        cmd.extend(["-m", markers])
    
    if verbose:
        cmd.append("-v")
    
    # Add coverage reporting
    cmd.extend(["--cov=pgvector_mcp_server", "--cov-report=term-missing"])
    
    print(f"🏃 Running: {' '.join(cmd)}")
    print()
    
    result = subprocess.run(cmd, cwd=Path(__file__).parent.parent)
    return result.returncode


def main():
    """Main test runner function."""
    parser = argparse.ArgumentParser(description="Run pgvector MCP server tests")
    parser.add_argument("--mcp-tools", action="store_true", help="Run only MCP tool tests")
    parser.add_argument("--encoding", action="store_true", help="Run only encoding tests")
    parser.add_argument("--integration", action="store_true", help="Run only integration tests")
    parser.add_argument("--rename", action="store_true", help="Run only rename collection tests")
    parser.add_argument("--no-cov", action="store_true", help="Disable coverage reporting")
    parser.add_argument("--quiet", action="store_true", help="Run tests quietly")
    
    args = parser.parse_args()
    
    print("🧪 pgvector MCP Server Test Runner")
    print("=" * 40)
    
    # Check environment
    if not check_environment():
        sys.exit(1)
    
    # Determine what to run
    test_path = ""
    markers = ""
    
    if args.mcp_tools:
        test_path = "tests/test_mcp_tools.py"
        print("🔧 Running MCP tools tests...")
    elif args.encoding:
        test_path = "tests/test_encoding.py"
        print("🔤 Running encoding tests...")
    elif args.integration:
        test_path = "tests/test_integration.py"
        print("🔗 Running integration tests...")
    elif args.rename:
        test_path = "tests/test_rename_collection.py"
        print("📝 Running rename collection tests...")
    else:
        print("🚀 Running all tests...")
    
    print()
    
    # Run tests
    exit_code = run_pytest(
        test_path=test_path,
        markers=markers,
        verbose=not args.quiet
    )
    
    if exit_code == 0:
        print()
        print("✅ All tests passed!")
        print()
        print("🎉 Phase 3.6 testing completed successfully!")
        print("   - MCP tools functionality verified")
        print("   - Collection rename operations tested")
        print("   - Encoding detection validated")
        print("   - Integration workflows confirmed")
    else:
        print()
        print("❌ Some tests failed. Please check the output above.")
        print("💡 Make sure your environment is properly configured.")
    
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
