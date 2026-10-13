#!/usr/bin/env python3
"""
Token Guard: Trims raw data, isolates diffs, and computes token savings
before invoking LLMs via Antigravity.
"""
import sys
import argparse
import re

def estimate_tokens(text: str) -> int:
    # Heuristic: 1 token ≈ 4 characters or ~0.75 words
    words = len(text.split())
    chars = len(text)
    return max(int(chars / 3.8), int(words / 0.75))

def compress_payload(raw_text: str, max_tokens: int = 500) -> str:
    lines = raw_text.splitlines()
    # Filter blank lines and comments if code
    clean_lines = [l for l in lines if l.strip() and not l.strip().startswith("#")]
    
    compact_text = "\n".join(clean_lines)
    est = estimate_tokens(compact_text)
    
    if est <= max_tokens:
        return compact_text
    
    # Head + Tail summarization
    keep_lines = int((max_tokens * 3.8) / 80) // 2
    head = "\n".join(clean_lines[:keep_lines])
    tail = "\n".join(clean_lines[-keep_lines:])
    return f"{head}\n\n[... AUTO-TRIMMED BY TOKEN GUARD: SAVED ~{est - max_tokens} TOKENS ...]\n\n{tail}"

def main():
    parser = argparse.ArgumentParser(description="Antigravity Token Guard")
    parser.add_argument("--text", type=str, help="Text to compress")
    parser.add_argument("--max-tokens", type=int, default=500, help="Max tokens allowed")
    args = parser.parse_args()

    input_text = args.text or sys.stdin.read()
    if not input_text:
        print("No input provided.")
        return

    raw_tokens = estimate_tokens(input_text)
    compressed = compress_payload(input_text, args.max_tokens)
    final_tokens = estimate_tokens(compressed)
    savings_pct = round(((raw_tokens - final_tokens) / max(raw_tokens, 1)) * 100, 1)

    print("=" * 60)
    print(f"⚡ TOKEN GUARD AUDIT REPORT")
    print(f"• Raw Input Tokens      : ~{raw_tokens:,}")
    print(f"• Compressed Tokens     : ~{final_tokens:,}")
    print(f"• Saved Tokens          : ~{raw_tokens - final_tokens:,} ({savings_pct}% Saved)")
    print("=" * 60)
    print("\n--- COMPRESSED PAYLOAD READY FOR AGENT ---")
    print(compressed)

if __name__ == "__main__":
    main()
