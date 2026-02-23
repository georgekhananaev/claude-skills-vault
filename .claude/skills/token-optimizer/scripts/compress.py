#!/usr/bin/env python3
import sys
import re
import argparse

def get_tokenizer():
    try:
        import tiktoken
        return tiktoken.get_encoding("cl100k_base")
    except ImportError:
        return None

def count_tokens(text, tokenizer=None):
    if tokenizer:
        return len(tokenizer.encode(text))
    else:
        # Fallback: approximation (4 chars ~= 1 token)
        return len(text) // 4

def compress_text(text, level=2):
    """
    Compresses text based on the level.
    Level 1: Remove fillers, basic substitutions.
    Level 2: Abbreviations, symbols, extensive substitutions.
    Level 3: Aggressive (not fully implemented in this regex version, assumes Level 2 + more)
    """
    original_text = text
    
    # 1. Remove Filler Words (Level 1+)
    fillers = [
        r"\bbasically\b", r"\besentially\b", r"\bactually\b", r"\breally\b",
        r"\bvery\b", r"\bquite\b", r"\brather\b", r"\bsomewhat\b",
        r"\bplease note that\b", r"\bit is important to\b", r"\bas mentioned previously\b",
        r"\bas we discussed\b", r"\bin this section\b", r"\bthe following\b",
        r"\bbelow you will find\b"
    ]
    for filler in fillers:
        text = re.sub(filler, "", text, flags=re.IGNORECASE)

    # Phrase Replacements (Level 1+)
    phrase_replacements = {
        r"\bin order to\b": "to",
        r"\bdue to the fact that\b": "bc",
        r"\bat this point in time\b": "now",
        r"\bin the event that\b": "if",
        r"\bfor the purpose of\b": "for",
        r"\bhas the ability to\b": "can",
        r"\bit is necessary to\b": "must",
        r"\bis able to\b": "can",
        r"\bin addition to\b": "+",
        r"\bas well as\b": "&",
        r"\bon the other hand\b": "vs",
        r"\bin contrast to\b": "vs",
        r"\bfor example\b": "ex:",
        r"\bsuch as\b": "e.g.",
        r"\bthat is\b": "i.e.",
        r"\band so on\b": "etc",
        r"\bin other words\b": "=>",
        r"\bas a result\b": "=>",
        r"\btherefore\b": "=>",
        r"\bhowever\b": "but",
        r"\bnevertheless\b": "but",
        r"\bfurthermore\b": "+",
        r"\bmoreover\b": "+",
        r"\bconsequently\b": "=>"
    }
    for pattern, replacement in phrase_replacements.items():
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)

    if level >= 2:
        # Symbols (Level 2+)
        symbols = {
            r"\band\b": "&",
            r"\bor\b": "|",
            r"\bwith\b": "w/",
            r"\bwithout\b": "w/o",
            r"\bversus\b": "vs",
            r"\bapproximately\b": "~",
            r"\bbecause\b": "bc",
            r"\bgreater than\b": ">",
            r"\bless than\b": "<",
            r"\bequals\b": "=",
            r"\bnot equals\b": "!=",
            r"\byes\b": "Y",
            r"\bno\b": "N"
        }
        for pattern, replacement in symbols.items():
            # Use strict word boundaries to avoid replacing partial words
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)

        # Abbreviations (Level 2+)
        # Grouped by category for easier maintenance
        abbrevs = {
            # Types
            r"\bstring\b": "str", r"\bnumber\b": "num", r"\bboolean\b": "bool",
            r"\barray\b": "arr", r"\bobject\b": "obj", r"\binteger\b": "int",
            
            # Code
            r"\bfunction\b": "fn", r"\breturn\b": "ret", r"\bparameter\b": "param",
            r"\bargument\b": "arg", r"\bvariable\b": "var", r"\binterface\b": "iface",
            r"\bimplementation\b": "impl", r"\bsynchronous\b": "sync", r"\basynchronous\b": "async",

            # System
            r"\bconfiguration\b": "config", r"\benvironment\b": "env", r"\bapplication\b": "app",
            r"\bdatabase\b": "db", r"\brequest\b": "req", r"\bresponse\b": "res",
            r"\bdirectory\b": "dir", r"\bdevelopment\b": "dev", r"\bproduction\b": "prod",

            # Auth
            r"\bauthentication\b": "auth", r"\bauthorization\b": "authz", r"\bpassword\b": "pwd",
            
            # Status
            r"\brequired\b": "req", r"\boptional\b": "opt", r"\bdefault\b": "def",
            r"\bmessage\b": "msg", r"\binformation\b": "info",

            # Action
            r"\binitialize\b": "init", r"\bexecute\b": "exec", r"\bcalculate\b": "calc",
            r"\bdelete\b": "del", r"\bremove\b": "rm", r"\bupdate\b": "upd"
        }
        for pattern, replacement in abbrevs.items():
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)

    # Clean up multiple spaces and newlines
    text = re.sub(r" +", " ", text)
    text = re.sub(r"\n\n+", "\n\n", text)
    
    return text.strip()

def main():
    parser = argparse.ArgumentParser(description="Compress text for LLM context optimization.")
    parser.add_argument("file", nargs="?", help="Input file path (optional, reads from stdin if not provided)")
    parser.add_argument("--level", type=int, choices=[1, 2], default=2, help="Compression level (1=Light, 2=Medium/Heavy)")
    parser.add_argument("--stats", action="store_true", help="Show token statistics")
    
    args = parser.parse_args()

    # Read input
    if args.file:
        try:
            with open(args.file, "r", encoding="utf-8") as f:
                content = f.read()
        except FileNotFoundError:
            print(f"Error: File '{args.file}' not found.", file=sys.stderr)
            sys.exit(1)
    else:
        if sys.stdin.isatty():
             print("Please provide text via stdin or a file argument.", file=sys.stderr)
             sys.exit(1)
        content = sys.stdin.read()

    # Compress
    compressed = compress_text(content, level=args.level)
    
    # Output
    print(compressed)

    # Stats
    if args.stats:
        tokenizer = get_tokenizer()
        orig_tokens = count_tokens(content, tokenizer)
        comp_tokens = count_tokens(compressed, tokenizer)
        saved = orig_tokens - comp_tokens
        percent = (saved / orig_tokens * 100) if orig_tokens > 0 else 0
        
        method = "tiktoken (cl100k_base)" if tokenizer else "heuristic (chars/4)"
        print(f"\n--- Statistics ({method}) ---", file=sys.stderr)
        print(f"Original:   {orig_tokens} tokens", file=sys.stderr)
        print(f"Compressed: {comp_tokens} tokens", file=sys.stderr)
        print(f"Saved:      {saved} tokens ({percent:.1f}%)", file=sys.stderr)

if __name__ == "__main__":
    main()
