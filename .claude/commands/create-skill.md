# Create Skill Command

Goal: Create production-ready skills w/ validation, testing & optimization.

## 1. Required Skills

Use these skills during creation:

| Skill | Path | Purpose |
|-------|------|---------|
| `skill-creator` | `.claude/skills/skill-creator/` | Core creation workflow |
| `token-formatter` | `.claude/skills/token-formatter/` | Compress SKILL.md content |
| `md` | `.claude/skills/document-skills/md/` | Clean markdown w/o errors |

## 2. Creation Flow

### Step 1: Understand Requirements

Ask user:
1. "What should this skill do?"
2. "Example usage scenarios?"
3. "Any scripts/assets needed?"

### Step 2: Init Skill

```bash
python scripts/init_skill.py <skill-name> --path .claude/skills/<skill-name>
```

Creates:
```
skill-name/
├── SKILL.md
├── scripts/
├── references/
└── assets/
```

### Step 3: Plan Resources

Analyze examples → identify:

| Resource | When |
|----------|------|
| `scripts/` | Repeated code, deterministic tasks |
| `references/` | Docs, schemas, API specs |
| `assets/` | Templates, images, fonts |

### Step 4: Write Content

**SKILL.md rules:**
- YAML frontmatter: `name` & `description` (req)
- Imperative form ("To do X" not "You should")
- Keep lean → move details to `references/`
- Apply `token-formatter` compression

**Writing style:**
```markdown
# Skill Name

Brief purpose (1-2 sentences).

## When to Use

Invoke when:
- Condition 1
- Condition 2

## Process

1. Step one
2. Step two
```

### Step 5: Optimize

Apply `token-formatter`:
- Abbreviations: fn, str, num, config, auth, db, etc.
- Remove filler words
- Compress tables & lists
- Use symbols: `→`, `|`, `&`, `w/`, `w/o`

Apply `md` skill:
- Proper fence nesting (use ```` for outer)
- Match opening/closing fences
- Escape `|` in tables
- Consistent list indentation
- Blank lines around code blocks

## 3. Testing (REQUIRED)

### Test Location

```
tests/<skill-name>/
├── test_*.py          # Python tests
├── test_*.sh          # Bash tests
├── fixtures/          # Test data
└── expected/          # Expected outputs
```

### Script Testing

For EVERY script in `scripts/`:

1. **Syntax check:**
```bash
# Python
python -m py_compile scripts/<script>.py

# Bash
bash -n scripts/<script>.sh

# Node
node --check scripts/<script>.js
```

2. **Execution test:**
```bash
# Run w/ test fixtures
python scripts/<script>.py tests/<skill>/fixtures/input.txt
```

3. **Output validation:**
```bash
# Compare output to expected
diff output.txt tests/<skill>/expected/output.txt
```

### Validation Checklist

Before completion, verify:

- [ ] SKILL.md has valid YAML frontmatter
- [ ] `name` & `description` present in frontmatter
- [ ] All scripts execute w/o errors
- [ ] All scripts have proper shebang
- [ ] References files are valid markdown
- [ ] No hardcoded paths (use relative)
- [ ] Token-optimized (check w/ `count_tokens.py`)
- [ ] No markdown linting errors

### Automated Validation

```bash
# Package & validate skill
python scripts/package_skill.py .claude/skills/<skill-name>
```

Checks:
- YAML frontmatter format
- Required fields present
- Directory structure
- File organization

## 4. Test Script Template

Create `tests/<skill>/test_skill.py`:

```python
#!/usr/bin/env python3
"""Tests for <skill-name> skill."""

import subprocess
import os
from pathlib import Path

SKILL_DIR = Path(__file__).parent.parent.parent / ".claude/skills/<skill>"
FIXTURES = Path(__file__).parent / "fixtures"
EXPECTED = Path(__file__).parent / "expected"

def test_script_syntax():
    """Verify all scripts have valid syntax."""
    for script in (SKILL_DIR / "scripts").glob("*.py"):
        result = subprocess.run(
            ["python", "-m", "py_compile", str(script)],
            capture_output=True
        )
        assert result.returncode == 0, f"Syntax error: {script}"

def test_script_execution():
    """Verify scripts run w/o errors."""
    # Add script-specific tests
    pass

def test_skill_md_valid():
    """Verify SKILL.md has valid frontmatter."""
    skill_md = SKILL_DIR / "SKILL.md"
    content = skill_md.read_text()
    assert content.startswith("---"), "Missing YAML frontmatter"
    assert "name:" in content, "Missing name field"
    assert "description:" in content, "Missing description field"

if __name__ == "__main__":
    test_script_syntax()
    test_skill_md_valid()
    print("All tests passed!")
```

## 5. Execution Summary

```
1. Understand     → Ask user, clarify scope
2. Init           → Run init_skill.py
3. Plan           → Identify scripts/refs/assets
4. Write          → SKILL.md + resources
5. Optimize       → token-formatter + md skill
6. Test           → Create tests, run validation
7. Package        → package_skill.py
8. Iterate        → Fix issues, re-test
```

## 6. Quick Reference

### Abbreviations (token-formatter)

```
fn=function  str=string  num=number  bool=boolean
arr=array    obj=object  param=parameter
config=configuration     env=environment
auth=authentication      db=database
req=required opt=optional def=default
w/=with      w/o=without  &=and  |=or
```

### Frontmatter Template

```yaml
---
name: skill-name
description: Brief desc. Use third-person ("This skill should be used when...")
license: Complete terms in LICENSE.txt
---
```

### Directory Structure

```
.claude/skills/<skill>/
├── SKILL.md              # Core instructions (req)
├── scripts/              # Executable code (opt)
├── references/           # Docs to load as needed (opt)
└── assets/               # Output files (opt)

tests/<skill>/
├── test_*.py             # Test scripts
├── fixtures/             # Test inputs
└── expected/             # Expected outputs
```

---
Ref: `.claude/skills/skill-creator/SKILL.md`, `.claude/skills/token-formatter/SKILL.md`, `.claude/skills/document-skills/md/SKILL.md`