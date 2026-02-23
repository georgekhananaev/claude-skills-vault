#!/usr/bin/env python3
"""Prompt Compressor - Reduce token count in prompts/context.

Usage:
    python compress_prompt.py "your prompt text"
    python compress_prompt.py --file prompt.txt
    python compress_prompt.py --level heavy "text"
    echo "text" | python compress_prompt.py
"""

import argparse
import re
import sys
from pathlib import Path

# Phrases to remove completely (order matters - longer patterns first)
REMOVE_PHRASES = [
    # Greetings (at start of text) - must include punctuation
    (r"^hello[!,.]?\s*", re.IGNORECASE | re.MULTILINE),
    (r"^hi[!,.]?\s*there[!,.]?\s*", re.IGNORECASE | re.MULTILINE),
    (r"^hi[!,.]?\s*", re.IGNORECASE | re.MULTILINE),
    (r"^hey[!,.]?\s*there[!,.]?\s*", re.IGNORECASE | re.MULTILINE),
    (r"^hey[!,.]?\s*", re.IGNORECASE | re.MULTILINE),
    # Pleasantries
    (r"i hope you(?:'re| are) doing well[^.]*\.\s*", re.IGNORECASE),
    # Verbose request patterns (longer first)
    (r"i was wondering if you could\s*", re.IGNORECASE),
    (r"i was wondering if\s*", re.IGNORECASE),
    (r"please help me with\s*", re.IGNORECASE),
    (r"help me with\s*", re.IGNORECASE),
    (r"i need you to\s*", re.IGNORECASE),
    (r"could you please\s*", re.IGNORECASE),
    (r"i would like you to\s*", re.IGNORECASE),
    (r"i would like to\s*", re.IGNORECASE),
    (r"can you please\s*", re.IGNORECASE),
    (r"would you mind\s*", re.IGNORECASE),
    # Thank you patterns
    (r"thanks in advance[^.]*\.\s*", re.IGNORECASE),
    (r"thank you for your help[^.]*\.\s*", re.IGNORECASE),
    # Hedging words
    (r"\bi think\s+", re.IGNORECASE),
    (r"\bmaybe\s+", re.IGNORECASE),
    (r"\bperhaps\s+", re.IGNORECASE),
    (r"\bi believe\s+", re.IGNORECASE),
    (r"i'm pretty sure\s+", re.IGNORECASE),
    # Meta commentary
    (r"this might be a (?:dumb|stupid|silly) question[^.]*[.,]\s*", re.IGNORECASE),
    (r"as i mentioned (?:before|earlier|previously)[^.]*[.,]\s*", re.IGNORECASE),
    (r"for your (?:reference|information)[^.]*[.,]\s*", re.IGNORECASE),
    (r"as you (?:can|may) know[^.]*[.,]\s*", re.IGNORECASE),
    (r"it is important to note that\s*", re.IGNORECASE),
    (r"please note that\s*", re.IGNORECASE),
    # Trying phrases
    (r"i'm trying to\s+", re.IGNORECASE),
    # Filler words
    (r"\bbasically[,]?\s+", re.IGNORECASE),
    (r"\bessentially[,]?\s+", re.IGNORECASE),
    (r"\bactually[,]?\s+", re.IGNORECASE),
    (r"\breally\s+", re.IGNORECASE),
    # Unnecessary words
    (r"\bsomething\.\s*", re.IGNORECASE),
]

# Phrase transformations
TRANSFORM_PHRASES = [
    (r"(?i)the error (message )?(says|is)[:\s]+", "Error: "),
    (r"(?i)in the file (located )?at[:\s]+", "File: "),
    (r"(?i)the problem is that\s+", "Issue: "),
    (r"(?i)here is my code[:\s]+", "Code:\n"),
    (r"(?i)here's my code[:\s]+", "Code:\n"),
    (r"(?i)in order to\s+", "to "),
    (r"(?i)due to the fact that\s+", "because "),
    (r"(?i)at this point in time\s+", "now "),
    (r"(?i)in the event that\s+", "if "),
    (r"(?i)for the purpose of\s+", "for "),
    (r"(?i)has the ability to\s+", "can "),
    (r"(?i)is able to\s+", "can "),
    (r"(?i)a lot of\s+", "many "),
    (r"(?i)in addition to\s+", "also "),
    (r"(?i)as well as\s+", "and "),
]

# Abbreviations (light/medium level)
ABBREVIATIONS_MEDIUM = {
    "function": "fn",
    "string": "str",
    "number": "num",
    "boolean": "bool",
    "array": "arr",
    "object": "obj",
    "parameter": "param",
    "parameters": "params",
    "configuration": "config",
    "environment": "env",
    "authentication": "auth",
    "authorization": "authz",
    "application": "app",
    "database": "db",
    "repository": "repo",
    "directory": "dir",
    "reference": "ref",
    "implementation": "impl",
    "documentation": "docs",
    "information": "info",
    "required": "req",
    "optional": "opt",
    "default": "def",
    "maximum": "max",
    "minimum": "min",
}

# Additional abbreviations for heavy compression
ABBREVIATIONS_HEAVY = {
    **ABBREVIATIONS_MEDIUM,
    "returns": "→",
    "return": "ret",
    "and": "&",
    "or": "|",
    "with": "w/",
    "without": "w/o",
    "versus": "vs",
    "approximately": "~",
    "example": "ex",
    "request": "req",
    "response": "res",
    "message": "msg",
    "component": "comp",
    "variable": "var",
    "constant": "const",
}

# Protected patterns (never modify)
PROTECTED_PATTERNS = [
    r"Bearer\s+\S+",  # Auth tokens
    r"api[_-]?key[:\s]+\S+",  # API keys
    r"password[:\s]+\S+",  # Passwords
    r"secret[:\s]+\S+",  # Secrets
    r"token[:\s]+\S+",  # Tokens
    r"https?://[^\s]+",  # URLs
    r"`[^`]+`",  # Inline code
    r"```[\s\S]*?```",  # Code blocks
    r'"[^"]*"',  # Quoted strings
    r"'[^']*'",  # Single-quoted strings
]


def estimate_tokens(text: str) -> int:
    """Estimate token count (~4 chars per token for English)."""
    return len(text) // 4


def protect_content(text: str) -> tuple[str, dict]:
    """Replace protected content with placeholders."""
    placeholders = {}
    for i, pattern in enumerate(PROTECTED_PATTERNS):
        for j, match in enumerate(re.finditer(pattern, text, re.IGNORECASE)):
            placeholder = f"__PROTECTED_{i}_{j}__"
            placeholders[placeholder] = match.group()
            text = text.replace(match.group(), placeholder, 1)
    return text, placeholders


def restore_content(text: str, placeholders: dict) -> str:
    """Restore protected content from placeholders."""
    for placeholder, original in placeholders.items():
        text = text.replace(placeholder, original)
    return text


def remove_phrases(text: str) -> str:
    """Remove unnecessary phrases."""
    for item in REMOVE_PHRASES:
        if isinstance(item, tuple):
            pattern, flags = item
            text = re.sub(pattern, "", text, flags=flags)
        else:
            text = re.sub(item, "", text, flags=re.IGNORECASE)
    return text


def transform_phrases(text: str) -> str:
    """Transform verbose phrases to compact forms."""
    for pattern, replacement in TRANSFORM_PHRASES:
        text = re.sub(pattern, replacement, text)
    return text


def apply_abbreviations(text: str, level: str) -> str:
    """Apply abbreviations based on compression level."""
    abbrevs = ABBREVIATIONS_HEAVY if level == "heavy" else ABBREVIATIONS_MEDIUM

    for full, short in abbrevs.items():
        # Only replace whole words, case-insensitive
        text = re.sub(rf"\b{full}\b", short, text, flags=re.IGNORECASE)

    return text


def clean_whitespace(text: str) -> str:
    """Clean up excessive whitespace."""
    # Multiple spaces to single
    text = re.sub(r" +", " ", text)
    # Multiple newlines to double
    text = re.sub(r"\n{3,}", "\n\n", text)
    # Strip lines
    lines = [line.strip() for line in text.split("\n")]
    text = "\n".join(lines)
    return text.strip()


def compress_prompt(text: str, level: str = "medium") -> tuple[str, dict]:
    """Compress prompt text.

    Args:
        text: Input prompt text
        level: Compression level (light, medium, heavy)

    Returns:
        Tuple of (compressed_text, stats_dict)
    """
    original_tokens = estimate_tokens(text)

    # Protect content that shouldn't be modified
    text, placeholders = protect_content(text)

    # Apply compression based on level
    if level in ("light", "medium", "heavy"):
        text = remove_phrases(text)
        text = transform_phrases(text)

    if level in ("medium", "heavy"):
        text = apply_abbreviations(text, level)

    # Clean up
    text = clean_whitespace(text)

    # Restore protected content
    text = restore_content(text, placeholders)

    compressed_tokens = estimate_tokens(text)
    saved = original_tokens - compressed_tokens
    saved_pct = (saved / original_tokens * 100) if original_tokens > 0 else 0

    stats = {
        "original_tokens": original_tokens,
        "compressed_tokens": compressed_tokens,
        "saved_tokens": saved,
        "saved_percent": round(saved_pct, 1),
    }

    return text, stats


def main():
    parser = argparse.ArgumentParser(
        description="Compress prompt text to reduce token count"
    )
    parser.add_argument("text", nargs="?", help="Text to compress")
    parser.add_argument("--file", "-f", help="Read from file")
    parser.add_argument(
        "--level", "-l",
        choices=["light", "medium", "heavy"],
        default="medium",
        help="Compression level (default: medium)"
    )
    parser.add_argument(
        "--stats", "-s",
        action="store_true",
        help="Show compression stats"
    )
    parser.add_argument(
        "--output", "-o",
        help="Output file (default: stdout)"
    )

    args = parser.parse_args()

    # Get input text
    if args.file:
        text = Path(args.file).read_text()
    elif args.text:
        text = args.text
    elif not sys.stdin.isatty():
        text = sys.stdin.read()
    else:
        parser.print_help()
        sys.exit(1)

    # Compress
    compressed, stats = compress_prompt(text, args.level)

    # Output
    output = compressed
    if args.stats:
        output += f"\n\n---\nOriginal: {stats['original_tokens']} tokens | "
        output += f"Compressed: {stats['compressed_tokens']} tokens | "
        output += f"Saved: {stats['saved_percent']}%"

    if args.output:
        Path(args.output).write_text(output)
        print(f"Written to {args.output}")
    else:
        print(output)


if __name__ == "__main__":
    main()