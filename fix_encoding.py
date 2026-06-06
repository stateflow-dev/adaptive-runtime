"""
fix_encoding.py  v3
--------------------
Fixes mojibake in adaptive_runtime source files.

Two corruption patterns found in this repo:

  Pattern A — ÔåÆ  (arrow →, U+2192)
    This is UTF-8 bytes E2 86 92 mis-read as cp1252,
    then written back as those 3 cp1252 chars.
    The file now contains the cp1252 bytes for Ô å Æ.
    cp1252: D4 E5 C6  (or nearby variant)

  Pattern B — ├óÔÇØ┬ü  (box drawing ═, U+2550)
    UTF-8 bytes E2 95 90 mis-read as cp1252.

Strategy: open file as cp1252, find the mojibake strings,
replace with correct Unicode, save as UTF-8.

Run from project root:
  python fix_encoding.py
"""

import os
import shutil

TARGET_DIR = "adaptive_runtime"

# ---------------------------------------------------------------------------
# String-level replacements (read file as cp1252, fix, write as UTF-8)
# Key = what you see when file is decoded as cp1252
# Val = correct Unicode character
# ---------------------------------------------------------------------------
STRING_FIXES = [
    # Pattern A: arrow right →
    # When UTF-8 E2 86 92 is decoded as cp1252: â†'
    # After a second round of mis-encoding, may appear as ÔåÆ or â†'
    ("\u00e2\u0086\u0092", "\u2192"),   # â†'  (most common form)
    ("\u00d4\u00e5\u00c6", "\u2192"),   # ÔåÆ  (second-round corruption)
    # Fallback variants seen in CMD output
    ("\u0413\u00f3\u00d4\u00c7\u00e1\u00d4\u00c7\u00d6", "\u2192"),

    # Pattern B: box drawing ═ (U+2550)
    # UTF-8 E2 95 90 decoded as cp1252: â•
    ("\u00e2\u0095\u0090", "\u2550"),
    # CMD shows ├óÔÇØ┬ü — cp1252 bytes for that sequence:
    ("\u251c\u00f3\u00d4\u00c7\u00d8\u00b0\u00fc", "\u2550"),

    # Pattern B alt: the 3-byte cp1252 read of E2 95 90
    # E2=â  95=\x95(bullet in cp1252)  90=\x90(unused, often ?)
    ("\u00e2\u0095\u0090", "\u2550"),

    # em dash — (U+2014)  UTF-8: E2 80 94
    ("\u00e2\u0080\u0094", "\u2014"),

    # box drawing ─ (U+2500)  UTF-8: E2 94 80
    ("\u00e2\u0094\u0080", "\u2500"),
]

# Also do a direct byte-level pass for the ═ separator lines
# Runtime_manager uses a long line of ═ chars; bytes after first fix attempt:
BOX_EQ_BYTE_PATTERNS = [
    # Original corrupt form (before any fix attempt)
    b"\xc3\xa2\xe2\x80\xa2\xc2\xac",
    # After partial fix attempt, may be stored as these cp1252 bytes
    b"\xe2\x95\x90",   # actual UTF-8 for ═ — this is already correct, skip
]


def fix_via_cp1252(filepath: str) -> int:
    """Read as cp1252, apply string replacements, write as UTF-8."""
    try:
        with open(filepath, "r", encoding="cp1252") as f:
            content = f.read()
    except Exception as e:
        print(f"  WARNING: could not read {filepath} as cp1252: {e}")
        return 0

    original = content
    for bad, good in STRING_FIXES:
        content = content.replace(bad, good)

    if content != original:
        shutil.copy2(filepath, filepath + ".bak")
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        changed = sum(original.count(bad) for bad, _ in STRING_FIXES)
        return max(changed, 1)
    return 0


def fix_via_bytes(filepath: str) -> int:
    """Byte-level pass for ═ separator lines that survived string pass."""
    with open(filepath, "rb") as f:
        raw = f.read()
    original = raw

    # After the cp1252 pass the file is UTF-8.
    # ÔåÆ in cp1252 is bytes D4 E5 C6
    raw = raw.replace(b"\xd4\xe5\xc6", "\u2192".encode("utf-8"))
    # ├óÔÇØ┬ü read as raw cp1252 bytes
    raw = raw.replace(b"\xc3\xa2\xe2\x80\xa2\xc2\xac", "\u2550".encode("utf-8"))
    # â†' as raw bytes (E2 86 92 misread)
    raw = raw.replace(b"\xc3\xa2\xe2\x80\xa0\xe2\x80\x99", "\u2192".encode("utf-8"))

    if raw != original:
        with open(filepath, "wb") as f:
            f.write(raw)
        return raw.count("\u2192".encode()) + raw.count("\u2550".encode())
    return 0


def get_hex_sample(filepath: str, search: bytes = b"\xe2\x86\x92") -> str:
    """Return hex of first 6 bytes around search pattern, or first 12 bytes."""
    with open(filepath, "rb") as f:
        raw = f.read()
    idx = raw.find(search)
    if idx >= 0:
        start = max(0, idx - 2)
        return raw[start:start+9].hex(" ")
    # fallback: find any high byte
    for i, b in enumerate(raw):
        if b > 0x7f:
            return raw[i:i+9].hex(" ")
    return "(no high bytes found)"


def probe_encoding(filepath: str) -> str:
    with open(filepath, "rb") as f:
        raw = f.read(256)
    if raw.startswith(b"\xef\xbb\xbf"):
        return "UTF-8 BOM"
    try:
        raw.decode("utf-8")
        return "UTF-8"
    except UnicodeDecodeError:
        return "non-UTF-8"


def main():
    if not os.path.isdir(TARGET_DIR):
        print(f"ERROR: '{TARGET_DIR}' not found. Run from project root.")
        return

    # --- Diagnostic first ---
    print("=" * 60)
    print("DIAGNOSTIC: encoding and byte samples")
    print("=" * 60)
    problem_files = []
    for root, _, files in os.walk(TARGET_DIR):
        for fname in sorted(files):
            if not fname.endswith(".py"):
                continue
            fpath = os.path.join(root, fname)
            enc = probe_encoding(fpath)
            with open(fpath, "rb") as f:
                raw = f.read()
            has_problem = any(b > 0x7f for b in raw[:50]) or b"\xd4\xe5\xc6" in raw or b"\xc3\xa2" in raw
            # Check for known corrupt sequences
            corrupt = b"\xd4\xe5\xc6" in raw or b"\xc3\xa2\xe2\x80\xa2\xc2\xac" in raw or b"\xc3\xa2\xe2\x80\xa0" in raw
            if corrupt:
                problem_files.append(fpath)
                sample = get_hex_sample(fpath)
                print(f"  CORRUPT  {os.path.relpath(fpath):50s}  {enc}  hex={sample}")
            else:
                print(f"  ok       {os.path.relpath(fpath):50s}  {enc}")

    print()

    if not problem_files:
        # Try a different approach: check for ÔåÆ as cp1252-decoded text
        print("No known byte patterns found.")
        print("Trying cp1252 text scan for ÔåÆ and ├óÔÇØ┬ü ...\n")
        problem_files = []
        for root, _, files in os.walk(TARGET_DIR):
            for fname in sorted(files):
                if not fname.endswith(".py"):
                    continue
                fpath = os.path.join(root, fname)
                try:
                    with open(fpath, "r", encoding="cp1252") as f:
                        content = f.read()
                    # Look for any of the corrupt char sequences
                    if any(bad in content for bad, _ in STRING_FIXES):
                        problem_files.append(fpath)
                        print(f"  cp1252 corrupt: {os.path.relpath(fpath)}")
                except Exception:
                    pass

    if not problem_files:
        print("No corrupt sequences found by any method.")
        print("Files may already be clean after previous fix run.")
        print("Check GitHub to confirm characters render correctly.")
        return

    print(f"\nFixing {len(problem_files)} file(s)...\n")
    total_fixed = 0
    for fpath in problem_files:
        n = fix_via_cp1252(fpath)
        if n:
            print(f"  FIXED (string pass): {os.path.relpath(fpath)}  ({n} replacements)")
            total_fixed += n
        n2 = fix_via_bytes(fpath)
        if n2:
            print(f"  FIXED (byte pass):   {os.path.relpath(fpath)}  ({n2} replacements)")
            total_fixed += n2

    print()
    print("=" * 60)
    if total_fixed:
        print(f"Done. {total_fixed} replacement(s) made.")
        print("Originals backed up as .bak")
        print()
        print("Verify:")
        print(r'  findstr /s /n "Ô" adaptive_runtime\*.py adaptive_runtime\*\*.py')
        print("Expected: no output")
    else:
        print("No replacements made. Files may already be clean.")


if __name__ == "__main__":
    main()
