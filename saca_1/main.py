"""
SACA — Smart Adaptive Clinical Assistant
Entry point.  Run:  python main.py
"""
import os, sys, shutil

# Clear __pycache__ so Python always uses the latest .py files
# This prevents stale cached bytecode from running old versions
_dir = os.path.dirname(os.path.abspath(__file__))
_cache = os.path.join(_dir, "__pycache__")
if os.path.exists(_cache):
    shutil.rmtree(_cache, ignore_errors=True)

# Auto-install rapidfuzz for accurate Yolnu Matha fuzzy matching
import subprocess, sys
try:
    import rapidfuzz
except ImportError:
    print("[SACA] Installing rapidfuzz for Yolnu Matha accuracy...")
    subprocess.run([sys.executable, "-m", "pip", "install",
                    "rapidfuzz", "-q"], capture_output=True)

from app import App

if __name__ == "__main__":
    app = App()
    app.mainloop()
