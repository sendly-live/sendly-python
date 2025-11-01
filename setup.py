#!/usr/bin/env python3
"""
Setup configuration for Sendly Python SDK

This file contains the package metadata and dependencies for the Sendly Python SDK.
It follows Python packaging best practices and supports installation via pip.
"""

from pathlib import Path
from setuptools import setup, find_packages

# Read the README file for the long description
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding='utf-8')

# Read the version from the package
def get_version():
    """Get version from the package __init__.py file."""
    version_file = this_directory / "sendly" / "__init__.py"
    version_content = version_file.read_text(encoding='utf-8')
    
    for line in version_content.splitlines():
        if line.startswith('__version__'):
            # Extract version string from __version__ = "x.y.z"
            version = line.split('=')[1].strip().strip('"').strip("'")
            return version
    
    raise RuntimeError("Unable to find version string in sendly/__init__.py")

# Core dependencies required for the SDK
install_requires = [
    "requests>=2.25.0",  # HTTP library for API communication
    "typing-extensions>=3.7.4; python_version<'3.8'",  # Type hints for Python 3.7
]

# Development dependencies for testing, linting, and building
extras_require = {
    "dev": [
        # Testing frameworks
        "pytest>=6.0.0",
        "pytest-cov>=2.10.0",
        "pytest-mock>=3.6.0",
        "responses>=0.18.0",  # For mocking HTTP responses in tests
        
        # Code quality and formatting
        "black>=22.0.0",      # Code formatter
        "isort>=5.10.0",      # Import sorter
        "flake8>=4.0.0",      # Linter
        "mypy>=0.950",        # Type checker
        
        # Documentation
        "sphinx>=4.0.0",      # Documentation generator
        "sphinx-rtd-theme>=1.0.0",  # Read the Docs theme
        
        # Build and distribution
        "build>=0.8.0",       # Modern Python build tool
        "twine>=4.0.0",       # Package uploader for PyPI
        "wheel>=0.37.0",      # Wheel format support
    ],
    "docs": [
        "sphinx>=4.0.0",
        "sphinx-rtd-theme>=1.0.0",
        "myst-parser>=0.18.0",  # Markdown support for Sphinx
    ],
    "test": [
        "pytest>=6.0.0",
        "pytest-cov>=2.10.0",
        "pytest-mock>=3.6.0",
        "responses>=0.18.0",
    ]
}

# Add an 'all' extra that includes everything
extras_require['all'] = list(set(sum(extras_require.values(), [])))

setup(
    # Basic package information
    name="sendly",
    version=get_version(),
    author="Sendly Team",
    author_email="support@sendly.live",
    description="The official Python SDK for Sendly - the Resend of SMS",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/sendly/sendly-python",
    project_urls={
        "Documentation": "https://docs.sendly.live/sdks/python",
        "Source": "https://github.com/sendly/sendly-python",
        "Tracker": "https://github.com/sendly/sendly-python/issues",
        "Homepage": "https://sendly.live",
        "Dashboard": "https://dashboard.sendly.live",
    },
    
    # Package discovery and structure
    packages=find_packages(exclude=["tests", "tests.*", "examples", "examples.*"]),
    package_data={
        "sendly": ["py.typed"],  # Include type hint marker file
    },
    include_package_data=True,
    
    # Dependencies
    install_requires=install_requires,
    extras_require=extras_require,
    python_requires=">=3.7",
    
    # Package classification
    classifiers=[
        # Development status
        "Development Status :: 4 - Beta",
        
        # Intended audience
        "Intended Audience :: Developers",
        "Intended Audience :: Information Technology",
        
        # Topic
        "Topic :: Communications",
        "Topic :: Communications :: Telephony",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Internet :: WWW/HTTP",
        
        # License
        "License :: OSI Approved :: MIT License",
        
        # Programming language
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3 :: Only",
        
        # Operating system
        "Operating System :: OS Independent",
        
        # Typing
        "Typing :: Typed",
    ],
    
    # Keywords for package discovery
    keywords=[
        "sms", "mms", "messaging", "text", "sendly", "api", "sdk",
        "notifications", "communications", "mobile", "phone", "twilio",
        "resend", "email", "webhook", "international", "routing"
    ],
    
    # Entry points (none needed for this SDK)
    entry_points={},
    
    # Additional metadata
    zip_safe=False,  # Allow inspection of package contents
    
    # Test configuration
    test_suite="tests",
    tests_require=extras_require["test"],
    
    # Custom commands (can be extended)
    cmdclass={},
)