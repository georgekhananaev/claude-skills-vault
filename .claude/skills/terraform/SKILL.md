---
name: terraform
description: Terraform infrastructure-as-code skills from HashiCorp. Covers HCL code generation with style conventions, testing with .tftest.hcl files, and module refactoring. Use when writing, reviewing, generating, or refactoring Terraform configurations, creating tests, or designing modules.
metadata:
  author: HashiCorp
  source: https://github.com/hashicorp/agent-skills
  version: "1.0"
---

# Terraform Skills

HashiCorp's official Terraform agent skills for infrastructure-as-code development.

## Available Sub-Skills

| Skill | File | Use When |
|-------|------|----------|
| Style Guide | [terraform-style-guide-SKILL.md](terraform-style-guide-SKILL.md) | Writing or reviewing Terraform HCL code |
| Testing | [terraform-test-SKILL.md](terraform-test-SKILL.md) | Creating .tftest.hcl test files, writing assertions, mocking |
| Module Refactoring | [refactor-module-SKILL.md](refactor-module-SKILL.md) | Transforming monolithic configs into reusable modules |

## Quick Reference

### File Organization
| File | Purpose |
|------|---------|
| `terraform.tf` | Version requirements |
| `providers.tf` | Provider configurations |
| `main.tf` | Primary resources |
| `variables.tf` | Input variables (alphabetical) |
| `outputs.tf` | Output values (alphabetical) |
| `locals.tf` | Local values |

### Key Conventions
- Two spaces per indent, no tabs
- Lowercase with underscores for names
- Every variable needs `type` and `description`
- Every output needs `description`
- Prefer `for_each` over `count`
- Never hardcode credentials

### Validation
```bash
terraform fmt -recursive
terraform validate
```

## Source

From [hashicorp/agent-skills](https://github.com/hashicorp/agent-skills) - terraform code-generation and module-generation plugins.
