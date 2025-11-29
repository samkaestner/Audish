# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for bundling the audish CLI into a standalone executable.
This bundles Python, all dependencies, and the audish package into a single file.

Usage:
    pyinstaller audish.spec
    
Output:
    dist/audish (or dist/audish.exe on Windows)
"""

import sys
from pathlib import Path

# Paths
project_root = Path(SPECPATH)

# Hidden imports that PyInstaller might miss
hidden_imports = [
    'click',
    'openpyxl',
    'yaml',
    'dateutil',
    'dateutil.parser',
    'dateutil.tz',
    'dateutil.relativedelta',
    'difflib',  # Used in validation for fuzzy matching
    # openpyxl sub-modules
    'openpyxl.workbook',
    'openpyxl.worksheet',
    'openpyxl.cell',
    'openpyxl.styles',
    'openpyxl.utils',
    'openpyxl.reader',
    'openpyxl.writer',
    # Our package
    'audish',
    'audish.cli',
    'audish.io_excel',
    'audish.mapping',
    'audish.faculty',
    'audish.faculty_names',
    'audish.rules',
    'audish.scheduler',
    'audish.reason_codes',
    'audish.excel_reader',
    'audish.validation',  # Configuration validation
]

# Data files to include (school configurations, etc.)
datas = [
    # Include the schools configuration directory
    (str(project_root / 'schools'), 'schools'),
]

# Analysis
# Use __main__.py as entry point to handle relative imports correctly
a = Analysis(
    [str(project_root / 'audish' / '__main__.py')],
    pathex=[str(project_root)],
    binaries=[],
    datas=datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Exclude unnecessary large packages
        'tkinter',
        'matplotlib',
        'numpy',
        'scipy',
        'PIL',
        'cv2',
        'torch',
        'tensorflow',
    ],
    noarchive=False,
)

# Remove duplicate entries
pyz = PYZ(a.pure)

# Create executable
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='audish',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # CLI application needs console
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

