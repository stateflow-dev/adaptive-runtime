"""
verify.py - restore remaining .bak files and verify all UTF-8 clean
Run: python verify.py
"""
import os
import shutil

FILES = [
    "adaptive_runtime/core/confidence_engine.py",
    "adaptive_runtime/core/context_engine.py",
    "adaptive_runtime/core/decision_engine.py",
    "adaptive_runtime/runtime/cache.py",
    "adaptive_runtime/runtime/runtime_manager.py",
]

print("Step 1 — Restore .bak files (skip if no .bak exists)")
for f in FILES:
    bak = f + ".bak"
    if os.path.exists(bak):
        shutil.copy2(bak, f)
        print(f"  restored: {f}")
    else:
        print(f"  no bak:   {f} (skipped)")

print()
print("Step 2 — Verify all files are valid UTF-8")
all_ok = True
for f in FILES:
    try:
        open(f, encoding="utf-8").read()
        print(f"  OK  {f}")
    except UnicodeDecodeError as e:
        print(f"  FAIL {f} — {e}")
        all_ok = False

print()
if all_ok:
    print("All files clean. Safe to commit to GitHub.")
else:
    print("Some files still have issues. Paste output here for next fix.")
