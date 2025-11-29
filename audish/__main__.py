"""
Main entry point for the audish CLI.
This module allows running the package with `python -m audish`.
Also used as the PyInstaller entry point for bundled builds.
"""

from audish.cli import cli

if __name__ == '__main__':
    cli()

