#!/usr/bin/env python3
"""Cross-platform utilities for native library loading and encoding detection."""

import codecs
import os
import platform
import sys


def setup_native_lib_paths():
    """Configure library paths for native deps (cairo, pango, gobject) across all platforms.

    macOS: DYLD_FALLBACK_LIBRARY_PATH (homebrew /opt/homebrew/lib or /usr/local/lib)
    Linux: LD_LIBRARY_PATH (common paths: /usr/local/lib, /usr/lib)
    Windows: PATH + os.add_dll_directory (GTK runtime, MSYS2, Conda)
    """
    system = platform.system()

    if system == 'Darwin':
        candidates = ['/opt/homebrew/lib', '/usr/local/lib']
        env_var = 'DYLD_FALLBACK_LIBRARY_PATH'
        current = os.environ.get(env_var, '')
        for lib_path in candidates:
            if os.path.isdir(lib_path) and lib_path not in current:
                os.environ[env_var] = f"{lib_path}:{current}" if current else lib_path
                current = os.environ[env_var]

    elif system == 'Linux':
        candidates = ['/usr/local/lib', '/usr/lib/x86_64-linux-gnu', '/usr/lib']
        env_var = 'LD_LIBRARY_PATH'
        current = os.environ.get(env_var, '')
        for lib_path in candidates:
            if os.path.isdir(lib_path) and lib_path not in current:
                os.environ[env_var] = f"{lib_path}:{current}" if current else lib_path
                current = os.environ[env_var]

    elif system == 'Windows':
        candidates = []
        # GTK runtime (common for weasyprint/cairo on Windows)
        gtk_path = os.environ.get('GTK_PATH')
        if gtk_path:
            candidates.append(os.path.join(gtk_path, 'bin'))
        # MSYS2 common paths
        for msys_root in [r'C:\msys64\mingw64\bin', r'C:\msys64\ucrt64\bin']:
            if os.path.isdir(msys_root):
                candidates.append(msys_root)
        # Conda env
        conda_prefix = os.environ.get('CONDA_PREFIX')
        if conda_prefix:
            candidates.append(os.path.join(conda_prefix, 'Library', 'bin'))

        current_path = os.environ.get('PATH', '')
        for lib_path in candidates:
            if os.path.isdir(lib_path) and lib_path not in current_path:
                os.environ['PATH'] = f"{lib_path}{os.pathsep}{current_path}"
                current_path = os.environ['PATH']
                if hasattr(os, 'add_dll_directory'):
                    try:
                        os.add_dll_directory(lib_path)
                    except OSError:
                        pass


def read_text_safe(path, encoding=None):
    """Read text file w/ encoding fallback chain: specified -> utf-8-sig -> utf-8 -> latin-1."""
    from pathlib import Path
    p = Path(path)
    encodings = [encoding] if encoding else []
    encodings.extend(['utf-8-sig', 'utf-8', 'latin-1'])

    for enc in encodings:
        if not enc:
            continue
        try:
            return p.read_text(encoding=enc), enc
        except (UnicodeDecodeError, LookupError):
            continue

    return p.read_text(encoding='latin-1', errors='replace'), 'latin-1'


def validate_encoding(name):
    """Validate encoding name exists. Returns normalized name or raises ValueError."""
    try:
        info = codecs.lookup(name)
        return info.name
    except LookupError:
        raise ValueError(f"Unknown encoding: '{name}'. Common encodings: utf-8, latin-1, ascii, utf-16, cp1252")
