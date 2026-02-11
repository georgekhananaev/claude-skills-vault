# Package Upgrade Skill

Safely upgrade JavaScript/TypeScript packages with breaking change detection, migration guidance, and automated code migrations.

## Features

- **Cross-platform** - Works on Windows, macOS, and Linux
- **Package manager agnostic** - Supports npm, pnpm, and yarn
- **Git safety** - Creates branches, never modifies main directly
- **Breaking change detection** - Checks migration docs before major upgrades
- **Automatic web search** - Searches for migration guides when docs not found
- **ESM/CJS compatibility** - Warns about module system conflicts
- **Blocker detection** - Automatically detects ESM/CJS conflicts, Node.js requirements, deprecations

## Quick Start

Simply ask Claude to upgrade packages:

```
upgrade packages
```

Or be more specific:

```
upgrade react to latest
upgrade all dev dependencies
check for outdated packages
```

## Workflow Flowchart

```mermaid
flowchart TD
    Start([Start]) --> LangDetect{Language Detection}

    LangDetect -->|package.json found| JSProject[JavaScript/TypeScript Project]
    LangDetect -->|go.mod found| GoProject[Go Project - Use go get]
    LangDetect -->|Other| OtherLang[Show Alternative Command]

    GoProject --> Stop([Stop])
    OtherLang --> Stop

    JSProject --> GitCheck{Git Clean?}

    GitCheck -->|No| CommitFirst[Commit or Stash Changes]
    CommitFirst --> GitCheck

    GitCheck -->|Yes| CreateBranch[Create Upgrade Branch]

    CreateBranch --> DetectPM{Detect Package Manager}

    DetectPM -->|npm| NPM[npm detected]
    DetectPM -->|pnpm| PNPM[pnpm detected]
    DetectPM -->|yarn| Yarn[yarn detected]
    DetectPM -->|Multiple lockfiles| PMError[Error: Multiple lockfiles]

    PMError --> Stop

    NPM --> CheckOutdated
    PNPM --> CheckOutdated
    Yarn --> CheckOutdated

    CheckOutdated[Check Outdated Packages] --> AnalyzeUpdates{Analyze Updates}

    AnalyzeUpdates --> PatchMinor[Patch/Minor Updates]
    AnalyzeUpdates --> MajorUpdates[Major Updates]

    PatchMinor --> UpgradePatch[Upgrade Patches First]
    UpgradePatch --> VerifyBuild1{Build OK?}

    VerifyBuild1 -->|Yes| MajorUpdates
    VerifyBuild1 -->|No| FixErrors1[Fix Errors]
    FixErrors1 --> VerifyBuild1

    MajorUpdates --> CheckBlockers{Known Blocker?}

    CheckBlockers -->|Yes - ESM/CJS| SkipPackage[Skip & Document]
    CheckBlockers -->|Yes - Other| SkipPackage
    CheckBlockers -->|No| CheckBreaking{Check Breaking Changes}

    SkipPackage --> NextMajor{More Majors?}

    CheckBreaking --> FetchMigration[Fetch Migration Docs]
    FetchMigration --> DocsFound{Docs Found?}

    DocsFound -->|Yes| UpgradeMajor[Upgrade Package]
    DocsFound -->|No| WebSearch[Web Search Migration Guide]

    WebSearch --> SearchFound{Search Found?}
    SearchFound -->|Yes| UpgradeMajor
    SearchFound -->|No| AskUser{Ask User}

    AskUser -->|Proceed| UpgradeMajor
    AskUser -->|Skip| SkipPackage

    UpgradeMajor --> RunCodemods{Codemods Available?}

    RunCodemods -->|Yes| ApplyCodemods[Apply Codemods]
    RunCodemods -->|No| ManualFixes[Apply Manual Fixes]

    ApplyCodemods --> VerifyBuild2{Build OK?}
    ManualFixes --> VerifyBuild2

    VerifyBuild2 -->|Yes| CommitMajor[Commit Upgrade]
    VerifyBuild2 -->|No| FixMigration[Fix Migration Issues]
    FixMigration --> VerifyBuild2

    CommitMajor --> NextMajor

    NextMajor -->|Yes| CheckBlockers
    NextMajor -->|No| GenerateReport[Generate Upgrade Report]

    GenerateReport --> Done([Done])

    style Start fill:#10b981,color:#fff
    style Done fill:#10b981,color:#fff
    style Stop fill:#ef4444,color:#fff
    style PMError fill:#ef4444,color:#fff
    style SkipPackage fill:#f59e0b,color:#fff
    style JSProject fill:#3b82f6,color:#fff
    style CommitMajor fill:#8b5cf6,color:#fff
    style WebSearch fill:#06b6d4,color:#fff
```

## Upgrade Order

The skill follows a specific order to minimize risk:

```mermaid
flowchart LR
    A[1. Dev Dependencies] --> B[2. Patch Versions]
    B --> C[3. Minor Versions]
    C --> D[4. Major Versions]
    D --> E[5. Framework Packages]

    style A fill:#10b981,color:#fff
    style B fill:#22c55e,color:#fff
    style C fill:#84cc16,color:#fff
    style D fill:#f59e0b,color:#fff
    style E fill:#ef4444,color:#fff
```

## Breaking Change Detection

For major version upgrades, the skill checks:

```mermaid
flowchart TD
    Major[Major Version Detected] --> Sources{Check Sources}

    Sources --> Releases[GitHub Releases]
    Sources --> Changelog[CHANGELOG.md]
    Sources --> Migration[MIGRATION.md]
    Sources --> Engines[package.json engines]

    Releases --> Keywords{Scan for Keywords}
    Changelog --> Keywords
    Migration --> Keywords
    Engines --> NodeCheck{Node.js Compatible?}

    Keywords --> |BREAKING, Removed, Deprecated| BreakingFound[Breaking Changes Found]
    Keywords --> |None found| WebSearch[Web Search Migration Guide]

    NodeCheck -->|No| Skip[Skip Package]
    NodeCheck -->|Yes| ESMCheck{ESM/CJS Compatible?}

    ESMCheck -->|No| Skip
    ESMCheck -->|Yes| Proceed[Proceed with Upgrade]

    BreakingFound --> ApplyMigration[Apply Migration Steps]
    WebSearch --> SearchResult{Found Guide?}
    SearchResult -->|Yes| ApplyMigration
    SearchResult -->|No| AskUser[Ask User to Confirm]

    style Major fill:#f59e0b,color:#fff
    style Skip fill:#ef4444,color:#fff
    style Proceed fill:#10b981,color:#fff
    style WebSearch fill:#06b6d4,color:#fff
```

## Detecting Major Version Blockers

The skill automatically detects blockers before upgrading:

### Detection Commands

```bash
# Check if package is ESM-only
npm view {package}@{version} type
# Returns "module" = ESM-only, empty = CommonJS compatible

# Check your project type
node -e "console.log(require('./package.json').type || 'commonjs')"

# Check Node.js requirements
npm view {package}@{version} engines

# Check if deprecated
npm view {package} deprecated
```

### Decision Flow for ESM Packages

```mermaid
flowchart TD
    Check[Check Package Type] --> ESM{Is ESM-only?}

    ESM -->|No| Safe[Safe to Upgrade]
    ESM -->|Yes| ProjectType{Project Module Type?}

    ProjectType -->|ESM| Safe
    ProjectType -->|CommonJS| Bundler{Using Bundler?}

    Bundler -->|Yes - Webpack/Vite| Maybe[Maybe - Test Thoroughly]
    Bundler -->|No| Skip[Skip Upgrade]

    Safe --> Upgrade[Proceed with Upgrade]
    Maybe --> Upgrade
    Skip --> Document[Document in Skipped Packages]

    style Safe fill:#10b981,color:#fff
    style Skip fill:#ef4444,color:#fff
    style Maybe fill:#f59e0b,color:#fff
```

## Dependency Groups

These packages must be upgraded together:

```mermaid
flowchart LR
    subgraph React
        react --> react-dom
        react-dom --> types-react["@types/react"]
    end

    subgraph Next.js
        next --> eslint-config-next
    end

    subgraph Prisma
        prisma --> prisma-client["@prisma/client"]
    end

    subgraph TypeScript
        typescript --> types-node["@types/node"]
    end

    subgraph Tailwind
        tailwindcss --> postcss
        postcss --> autoprefixer
    end
```

## Upgrade Report Template

After upgrades, the skill generates a report:

```markdown
# Package Upgrade Report
**Date:** {date} | **PM:** {npm|pnpm|yarn} | **Branch:** {branch-name}

## Summary
- Upgraded: {count} | Major: {count} | Minor: {count} | Patch: {count} | Skipped: {count}

## Upgrades
| Package | From | To | Breaking | Migration |
|---------|------|-----|----------|-----------|
| {package} | {old} | {new} | Yes/No | {details} |

## Skipped
| Package | Reason |
|---------|--------|
| {package} | {reason} |

## Verification
- [ ] Type check
- [ ] Lint
- [ ] Tests
- [ ] Build
```

## Rollback

If something goes wrong:

```bash
# Rollback to before upgrade
git checkout main -- package.json {lockfile}
{pm} install
```

Or simply:

```bash
# Delete the upgrade branch and return to main
git checkout main
git branch -D chore/upgrade-packages-{date}
```

## Configuration

The skill automatically detects:

| Setting | Detection Method |
|---------|------------------|
| Package manager | Lockfile presence (`package-lock.json`, `pnpm-lock.yaml`, `yarn.lock`) |
| Project type | `package.json` field `"type": "module"` or CommonJS (default) |
| Node.js version | `package.json` engines field |
| Monorepo | `package.json` workspaces field |

## Supported Languages

This skill is specifically for JavaScript/TypeScript projects. For other languages, use:

| Language | Command |
|----------|---------|
| Go | `go get -u ./...` |
| Rust | `cargo update` |
| Python | `pip-review --auto` or `poetry update` |
| PHP | `composer update` |
| Ruby | `bundle update` |
| Java (Maven) | `mvn versions:use-latest-releases` |
| Java (Gradle) | `gradle dependencyUpdates` |
| .NET | `dotnet outdated` |

## Related Files

- [`SKILL.md`](./SKILL.md) - Full skill instructions and commands
