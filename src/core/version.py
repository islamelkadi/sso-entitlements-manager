"""
Version information for the SSO Manager CLI.

This module provides version information for the application using the most
pythonic approach - reading from package metadata when installed, falling back
to pyproject.toml during development.
"""

import re
from pathlib import Path
from typing import Dict, Any

try:
    # Try to get version from installed package metadata (most pythonic)
    import importlib.metadata
    __version__ = importlib.metadata.version("sso_manager")
except (importlib.metadata.PackageNotFoundError, ImportError):
    # Fallback to reading from pyproject.toml during development
    try:
        project_root = Path(__file__).parent.parent.parent
        pyproject_path = project_root / "pyproject.toml"
        
        if pyproject_path.exists():
            with open(pyproject_path, 'r', encoding='utf-8') as f:
                content = f.read()
                # Use regex to find version line
                version_match = re.search(r'version\s*=\s*["\']([^"\']+)["\']', content)
                if version_match:
                    __version__ = version_match.group(1)
                else:
                    __version__ = '0.1.0'
        else:
            __version__ = '0.1.0'
    except Exception:
        # Final fallback
        __version__ = '0.1.0'


def get_version() -> str:
    """
    Get the current version of the application.
    
    Returns:
        str: The version string
    """
    return __version__


def get_version_info() -> Dict[str, Any]:
    """
    Get detailed version information.
    
    Returns:
        dict: Dictionary containing version details
    """
    return {
        'version': get_version(),
        'name': 'sso-manager',
        'description': 'Multi-Cloud Access Management Tool'
    }