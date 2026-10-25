#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys
from pathlib import Path

# Add paths to sys.path before Django loads
# Base directory is apps/api
BASE_DIR = Path(__file__).resolve().parent
# Add packages directory
PACKAGES_DIR = BASE_DIR.parent.parent / 'packages'
if str(PACKAGES_DIR) not in sys.path:
    sys.path.insert(0, str(PACKAGES_DIR))
# Add apps directory (so 'core', 'orchestration', etc. can be imported)
# Force to the front even if already present, so packages/core can't shadow it.
if str(BASE_DIR) in sys.path:
    sys.path.remove(str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR))


def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schedularos.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on the PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
