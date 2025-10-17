"""
Test suite to validate the project setup and configuration.
"""

import os
import sys
from pathlib import Path
import pytest


class TestProjectStructure:
    """Test that the project structure is set up correctly."""

    def test_src_directory_exists(self):
        """Verify src directory exists."""
        assert Path("src").exists()

    def test_agents_directory_exists(self):
        """Verify agents directory exists."""
        assert Path("src/agents").exists()

    def test_tools_directory_exists(self):
        """Verify tools directory exists."""
        assert Path("src/tools").exists()

    def test_utils_directory_exists(self):
        """Verify utils directory exists."""
        assert Path("src/utils").exists()

    def test_config_directory_exists(self):
        """Verify config directory exists."""
        assert Path("src/config").exists()

    def test_tests_directory_exists(self):
        """Verify tests directory exists."""
        assert Path("tests").exists()

    def test_docs_directory_exists(self):
        """Verify docs directory exists."""
        assert Path("docs").exists()

    def test_deployment_directory_exists(self):
        """Verify deployment directory exists."""
        assert Path("deployment").exists()


class TestConfigurationFiles:
    """Test that configuration files are present."""

    def test_requirements_txt_exists(self):
        """Verify requirements.txt exists."""
        assert Path("requirements.txt").exists()

    def test_readme_exists(self):
        """Verify README.md exists."""
        assert Path("README.md").exists()

    def test_gitignore_exists(self):
        """Verify .gitignore exists."""
        assert Path(".gitignore").exists()

    def test_env_example_exists(self):
        """Verify .env.example exists."""
        assert Path(".env.example").exists()

    def test_setup_script_exists(self):
        """Verify setup.sh exists."""
        assert Path("setup.sh").exists()

    def test_setup_script_executable(self):
        """Verify setup.sh is executable."""
        setup_script = Path("setup.sh")
        assert setup_script.exists()
        assert os.access(setup_script, os.X_OK)


class TestDeploymentConfiguration:
    """Test deployment configuration files."""

    def test_dev_config_exists(self):
        """Verify dev config exists."""
        assert Path("deployment/dev/config.yaml").exists()

    def test_prod_config_exists(self):
        """Verify prod config exists."""
        assert Path("deployment/prod/config.yaml").exists()


class TestDocumentation:
    """Test that documentation files are present."""

    def test_aws_credentials_setup_doc_exists(self):
        """Verify AWS credentials setup documentation exists."""
        assert Path("docs/AWS_CREDENTIALS_SETUP.md").exists()

    def test_quick_start_doc_exists(self):
        """Verify quick start documentation exists."""
        assert Path("docs/QUICK_START.md").exists()


class TestPythonPackages:
    """Test that Python packages are properly set up."""

    def test_src_is_package(self):
        """Verify src has __init__.py."""
        assert Path("src/__init__.py").exists()

    def test_agents_is_package(self):
        """Verify agents has __init__.py."""
        assert Path("src/agents/__init__.py").exists()

    def test_tools_is_package(self):
        """Verify tools has __init__.py."""
        assert Path("src/tools/__init__.py").exists()

    def test_utils_is_package(self):
        """Verify utils has __init__.py."""
        assert Path("src/utils/__init__.py").exists()

    def test_config_is_package(self):
        """Verify config has __init__.py."""
        assert Path("src/config/__init__.py").exists()

    def test_tests_is_package(self):
        """Verify tests has __init__.py."""
        assert Path("tests/__init__.py").exists()


class TestPythonVersion:
    """Test Python version requirements."""

    def test_python_version(self):
        """Verify Python 3.11+ is being used."""
        assert sys.version_info >= (3, 11), f"Python 3.11+ required, found {sys.version_info}"


class TestRequirements:
    """Test that requirements.txt has necessary packages."""

    def test_requirements_content(self):
        """Verify requirements.txt contains key packages."""
        requirements = Path("requirements.txt").read_text()

        # Check for essential packages
        assert "strands-agents" in requirements
        assert "boto3" in requirements
        assert "neo4j" in requirements
        assert "fastapi" in requirements
        assert "anthropic" in requirements
        assert "pytest" in requirements


class TestEnvironmentTemplate:
    """Test .env.example template."""

    def test_env_example_has_neo4j_config(self):
        """Verify .env.example has Neo4j configuration."""
        env_example = Path(".env.example").read_text()

        assert "NEO4J_URI" in env_example
        assert "NEO4J_USERNAME" in env_example
        assert "NEO4J_PASSWORD" in env_example
        assert "NEO4J_DATABASE" in env_example

    def test_env_example_has_aws_config(self):
        """Verify .env.example has AWS configuration."""
        env_example = Path(".env.example").read_text()

        assert "AWS_REGION" in env_example
        assert "AWS_PROFILE" in env_example


if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main([__file__, "-v"])
