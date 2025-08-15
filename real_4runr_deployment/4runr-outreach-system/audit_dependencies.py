#!/usr/bin/env python3
"""
Dependency Audit Script for 4runr Outreach System

Scans all Python files to identify imported packages and compares
against current requirements.txt to find missing dependencies.
"""

import os
import re
import sys
from pathlib import Path
from typing import Set, Dict, List
from collections import defaultdict

def get_all_python_files(directory: str) -> List[Path]:
    """Get all Python files in the directory recursively."""
    python_files = []
    for root, dirs, files in os.walk(directory):
        # Skip __pycache__ directories
        dirs[:] = [d for d in dirs if d != '__pycache__']
        
        for file in files:
            if file.endswith('.py'):
                python_files.append(Path(root) / file)
    
    return python_files

def extract_imports_from_file(file_path: Path) -> Set[str]:
    """Extract all import statements from a Python file."""
    imports = set()
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except (UnicodeDecodeError, FileNotFoundError):
        print(f"Warning: Could not read {file_path}")
        return imports
    
    # Patterns to match import statements
    import_patterns = [
        r'^import\s+([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)*)',
        r'^from\s+([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)*)\s+import'
    ]
    
    lines = content.split('\n')
    for line in lines:
        line = line.strip()
        
        for pattern in import_patterns:
            match = re.match(pattern, line)
            if match:
                module_name = match.group(1)
                # Get the top-level package name
                top_level = module_name.split('.')[0]
                imports.add(top_level)
    
    return imports

def get_current_requirements(requirements_file: str) -> Set[str]:
    """Parse current requirements.txt file."""
    requirements = set()
    
    try:
        with open(requirements_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    # Extract package name (before == or >= etc.)
                    package_name = re.split(r'[>=<!=]', line)[0].strip()
                    requirements.add(package_name)
    except FileNotFoundError:
        print(f"Warning: {requirements_file} not found")
    
    return requirements

def is_standard_library(module_name: str) -> bool:
    """Check if a module is part of Python standard library."""
    standard_libs = {
        'sys', 'os', 'pathlib', 'typing', 'json', 'datetime', 'time',
        'logging', 'argparse', 'uuid', 'sqlite3', 'asyncio', 're',
        'urllib', 'collections', 'importlib', 'smtplib', 'email',
        'functools', 'itertools', 'math', 'random', 'string', 'io',
        'csv', 'base64', 'hashlib', 'hmac', 'secrets', 'tempfile',
        'shutil', 'glob', 'fnmatch', 'pickle', 'copy', 'pprint',
        'warnings', 'traceback', 'inspect', 'gc', 'weakref', 'abc',
        'contextlib', 'threading', 'multiprocessing', 'subprocess',
        'signal', 'socket', 'ssl', 'http', 'ftplib', 'poplib',
        'imaplib', 'nntplib', 'smtpd', 'telnetlib', 'xmlrpc',
        'html', 'xml', 'webbrowser', 'cgi', 'wsgiref', 'unittest',
        'doctest', 'test', 'bdb', 'faulthandler', 'pdb', 'profile',
        'pstats', 'timeit', 'trace', 'tracemalloc', 'distutils',
        'ensurepip', 'venv', 'zipapp', 'platform', 'ctypes', 'winreg',
        'winsound', 'posix', 'pwd', 'spwd', 'grp', 'crypt', 'termios',
        'tty', 'pty', 'fcntl', 'pipes', 'resource', 'nis', 'syslog',
        'optparse', 'getopt', 'getpass', 'curses', 'readline', 'rlcompleter'
    }
    
    return module_name in standard_libs

def main():
    """Main audit function."""
    print("🔍 Auditing 4runr Outreach System Dependencies")
    print("=" * 50)
    
    # Get all Python files
    project_root = Path(__file__).parent
    python_files = get_all_python_files(str(project_root))
    
    print(f"Found {len(python_files)} Python files to analyze")
    
    # Extract all imports
    all_imports = set()
    file_imports = defaultdict(set)
    
    for file_path in python_files:
        imports = extract_imports_from_file(file_path)
        all_imports.update(imports)
        if imports:
            file_imports[file_path] = imports
    
    # Filter out standard library modules
    third_party_imports = {imp for imp in all_imports if not is_standard_library(imp)}
    
    print(f"\n📦 Found {len(third_party_imports)} third-party packages:")
    for imp in sorted(third_party_imports):
        print(f"  - {imp}")
    
    # Get current requirements
    requirements_file = project_root / "requirements.txt"
    current_requirements = get_current_requirements(str(requirements_file))
    
    print(f"\n📋 Current requirements.txt contains {len(current_requirements)} packages:")
    for req in sorted(current_requirements):
        print(f"  - {req}")
    
    # Find missing dependencies
    missing_deps = third_party_imports - current_requirements
    
    print(f"\n❌ Missing from requirements.txt ({len(missing_deps)} packages):")
    if missing_deps:
        for dep in sorted(missing_deps):
            print(f"  - {dep}")
            # Show which files use this dependency
            using_files = [str(f.relative_to(project_root)) for f, imports in file_imports.items() if dep in imports]
            for file in using_files[:3]:  # Show first 3 files
                print(f"    Used in: {file}")
            if len(using_files) > 3:
                print(f"    ... and {len(using_files) - 3} more files")
    else:
        print("  ✅ All dependencies are documented!")
    
    # Find potentially unused requirements
    unused_reqs = current_requirements - third_party_imports
    
    print(f"\n⚠️  Potentially unused in requirements.txt ({len(unused_reqs)} packages):")
    if unused_reqs:
        for req in sorted(unused_reqs):
            print(f"  - {req}")
    else:
        print("  ✅ All requirements appear to be used!")
    
    # Summary
    print(f"\n📊 Summary:")
    print(f"  Total Python files analyzed: {len(python_files)}")
    print(f"  Third-party packages found: {len(third_party_imports)}")
    print(f"  Packages in requirements.txt: {len(current_requirements)}")
    print(f"  Missing from requirements.txt: {len(missing_deps)}")
    print(f"  Potentially unused: {len(unused_reqs)}")
    
    if missing_deps:
        print(f"\n🔧 Recommended action:")
        print(f"  Add these packages to requirements.txt:")
        for dep in sorted(missing_deps):
            print(f"    {dep}==<version>")

if __name__ == "__main__":
    main()