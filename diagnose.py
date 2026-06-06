"""
diagnose.py
-----------
Prints hex bytes around corrupt characters in the source files.
Run from project root:
  python diagnose.py
"""
import os

FILES = [
    "adaptive_runtime/core/confidence_engine.py",
    "adaptive_runtime/runtime/runtime_manager.py",
]

for fpath in FILES:
    if not os.path.exists(fpath):
        print(f"NOT FOUND: {fpath}")
        continue

    with open(fpath, "rb") as f:
        raw = f.read()

    print(f"\n{'='*60}")
    print(f"FILE: {fpath}")
    print(f"Size: {len(raw)} bytes")

    # Print first non-ASCII sequence found
    i = 0
    shown = 0
    while i < len(raw) and shown < 5:
        if raw[i] > 0x7f:
            start = max(0, i - 4)
            chunk = raw[start:i+12]
            try:
                context = raw[max(0,i-20):i+20].decode("cp1252", errors="replace")
            except Exception:
                context = "?"
            print(f"  pos={i:5d}  hex={chunk.hex(' ')}")
            print(f"  context (cp1252): {repr(context)}")
            shown += 1
            i += 3
        else:
            i += 1

    if shown == 0:
        print("  No non-ASCII bytes found — file may already be clean UTF-8")
        # Show a sample of bytes around known keywords
        for keyword in [b"arrow", b"Event", b"Confidence", b"base="]:
            idx = raw.find(keyword)
            if idx >= 0:
                chunk = raw[max(0,idx-5):idx+20]
                print(f"  '{keyword.decode()}' at pos {idx}: {chunk.hex(' ')}")
                break
