"""PyInstaller packaging script for BookEase Windows Desktop Executable."""

import os
import sys
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


def build():
    print("=" * 60)
    print("Building BookEase Desktop Application with PyInstaller")
    print("=" * 60)

    # Ensure output directories exist
    dist_dir = BASE_DIR / "dist"
    build_dir = BASE_DIR / "build"
    assets_dir = BASE_DIR / "assets"
    assets_dir.mkdir(exist_ok=True)

    pyinstaller_exe = BASE_DIR / ".venv" / "Scripts" / "pyinstaller.exe"
    if not pyinstaller_exe.exists():
        pyinstaller_exe = "pyinstaller"

    cmd = [
        str(pyinstaller_exe),
        "--noconfirm",
        "--onedir",
        "--windowed",
        "--name", "BookEase",
        "--clean",
        "--collect-all", "customtkinter",
        "--collect-all", "babel",
        "--collect-all", "reportlab",
        "--hidden-import", "sqlalchemy.dialects.sqlite",
        "--hidden-import", "openpyxl",
        "--hidden-import", "matplotlib",
        "--hidden-import", "pandas",
        "--add-data", f"{assets_dir};assets",
        str(BASE_DIR / "main.py"),
    ]

    print(f"Running command:\n{' '.join(cmd)}\n")
    result = subprocess.run(cmd, cwd=str(BASE_DIR))
    if result.returncode == 0:
        exe_path = dist_dir / "BookEase" / "BookEase.exe"
        print("\n" + "=" * 60)
        print(f"BUILD SUCCESSFUL! Executable located at:")
        print(exe_path)
        print("=" * 60)
    else:
        print("\nBUILD FAILED. See log output above.")
        sys.exit(result.returncode)


if __name__ == "__main__":
    build()
