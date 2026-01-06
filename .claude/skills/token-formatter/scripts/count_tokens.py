#!/usr/bin/env python3
import sys
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

def main():
    parser = argparse.ArgumentParser(description="Count tokens in text or file.")
    parser.add_argument("files", nargs="*", help="Input file paths")
    
    args = parser.parse_args()

    tokenizer = get_tokenizer()
    method = "tiktoken (cl100k_base)" if tokenizer else "heuristic (chars/4)"
    
    if not tokenizer:
        print("Warning: 'tiktoken' library not found. Using heuristic estimation.", file=sys.stderr)
        print("Install with: pip install tiktoken", file=sys.stderr)

    total_tokens = 0

    if args.files:
        print(f"{'File':<40} | {'Tokens':>10}")
        print("-" * 53)
        for file_path in args.files:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    count = count_tokens(content, tokenizer)
                    print(f"{file_path[:40]:<40} | {count:>10}")
                    total_tokens += count
            except Exception as e:
                print(f"{file_path[:40]:<40} | Error: {e}")
        print("-" * 53)
        print(f"{'Total':<40} | {total_tokens:>10}")
    else:
        # Read from stdin
        if sys.stdin.isatty():
             print("Usage: python count_tokens.py <files> OR cat file.txt | python count_tokens.py", file=sys.stderr)
             sys.exit(1)
        content = sys.stdin.read()
        total_tokens = count_tokens(content, tokenizer)
        print(f"Tokens: {total_tokens} ({method})")

if __name__ == "__main__":
    main()
