/plan-to-tdd docs/plan/2024/03/2024_03_15_1430__hotel_booking.md
```

This single command executes the entire workflow:
```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         /plan-to-tdd EXECUTION                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   PHASE 0         PHASE 1         PHASE 2         PHASE 3        PHASE 4   │
│   ────────        ────────        ────────        ────────       ────────  │
│   Load Plan  ───▶  Design   ───▶   Plan    ───▶  Scaffold  ───▶  Verify   │
│                                                                             │
│   ┌────────┐     ┌────────┐     ┌────────┐     ┌────────┐     ┌────────┐  │
│   │ docs-  │     │ docs-  │     │ test-  │     │Generate│     │  ux-   │  │
│   │  nav   │     │  nav   │     │ levels │     │  tests │     │toolkit │  │
│   └────────┘     └────────┘     └────────┘     └────────┘     └────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Skill Structure
```
plan-to-tdd/
├── CLAUDE.md                          # Command definition for Claude Code
├── SKILL.md                           # Main documentation
├── COMMANDS.md                        # All commands reference
├── commands/
│   ├── plan-to-tdd.md                 # Primary command spec
│   └── follow-up-commands.md          # /tdd-next, /tdd-status, etc.
└── templates/
├── manus-workflow.md              # 5-phase workflow
├── plan-template.md               # Expected plan format
├── hotel-booking-example.md       # Complete example
└── test-levels-reference.md       # Unit/Integration/E2E guide