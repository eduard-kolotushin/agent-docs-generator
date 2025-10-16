#!/usr/bin/env python3
"""Test script to verify the installation and basic functionality."""

import sys
import os

def test_python_version():
    """Test that Python version is 3.12 or higher."""
    version = sys.version_info
    if version.major == 3 and version.minor >= 12:
        print("✅ Python version is 3.12+")
        assert True
    else:
        print(f"❌ Python version {version.major}.{version.minor} is not supported. Requires Python 3.12+")
        assert False, f"Python {version.major}.{version.minor} is not supported. Requires Python 3.12+"

def test_imports():
    """Test that all modules can be imported."""
    try:
        from src.config import settings
        from src.schemas import AgentState, JiraIssue
        from src.tools.jira_tool import JiraTool
        from src.tools.bitbucket_tool import BitbucketTool
        from src.tools.confluence_tool import ConfluenceTool
        from src.tools.docs_pr_tool import DocsPRTool
        from src.generators.release_notes import generate_release_notes
        from src.generators.guide_edits import plan_guide_edits
        from src.graph.release_docs_graph import create_release_docs_graph
        print("✅ All imports successful")
        assert True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        assert False, f"Import error: {e}"

def test_schemas():
    """Test that schemas work correctly."""
    try:
        from src.schemas import AgentState, JiraIssue
        from datetime import datetime
        
        # Test AgentState
        state = AgentState(
            release_branch="release/1.2.3",
            version="1.2.3",
            dry_run=True
        )
        assert state.version == "1.2.3"
        
        # Test JiraIssue
        issue = JiraIssue(
            key="PROJ-123",
            summary="Test issue",
            issue_type="Story",
            status="Done",
            priority="High",
            components=[],
            labels=[],
            fix_version="1.2.3",
            epic_key=None,
            changelog=None,
            breaking_change=False,
            assignee=None,
            reporter=None,
            created=datetime.now(),
            updated=datetime.now()
        )
        assert issue.key == "PROJ-123"
        
        print("✅ Schema validation successful")
        assert True
    except Exception as e:
        print(f"❌ Schema error: {e}")
        assert False, f"Schema error: {e}"

def test_config():
    """Test configuration loading."""
    try:
        from src.config import settings
        
        # Check that settings object exists
        assert hasattr(settings, 'jira_base_url')
        assert hasattr(settings, 'bitbucket_workspace')
        assert hasattr(settings, 'confluence_base_url')
        assert hasattr(settings, 'openai_api_key')
        
        print("✅ Configuration loading successful")
        assert True
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        assert False, f"Configuration error: {e}"

def main():
    """Run all tests."""
    print("Testing Release Documentation Agent Installation...")
    print(f"Python version: {sys.version}")
    print("=" * 50)
    
    tests = [
        test_python_version,
        test_imports,
        test_schemas,
        test_config,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"❌ Test failed: {e}")
        except Exception as e:
            print(f"❌ Test error: {e}")
        print()
    
    print("=" * 50)
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All tests passed! The installation is working correctly.")
        return 0
    else:
        print("❌ Some tests failed. Please check the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
