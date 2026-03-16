---
name: multi-agent-patterns
description: "Master orchestrator, peer-to-peer, and hierarchical multi-agent architectures"
source: "https://github.com/muratcankoylan/Agent-Skills-for-Context-Engineering/tree/main/skills/multi-agent-patterns"
risk: safe
---

# Multi-Agent Architecture Patterns

Distribute work across multiple LM instances w/ isolated context windows. Sub-agents exist to isolate context, not to anthropomorphize roles.

## When to Activate

- Single-agent context limits constrain task complexity
- Tasks decompose into parallel subtasks
- Different subtasks need different tools | system prompts
- Building multi-domain agent systems

## Core Concepts

Three patterns: supervisor/orchestrator (centralized), peer-to-peer/swarm (flexible handoffs), hierarchical (layered abstraction). Key principle: context isolation — sub-agents partition context, not simulate org roles. Requires explicit coordination protocols & consensus mechanisms avoiding sycophancy.

## Token Economics

| Architecture | Token Multiplier | Use Case |
|---|---|---|
| Single agent | 1x | Simple queries |
| Agent w/ tools | ~4x | Tool-using tasks |
| Multi-agent | ~15x | Complex research/coordination |

BrowseComp: token usage explains 80% of performance variance. Model upgrades often outperform doubling token budgets — model selection & multi-agent architecture are complementary.

## Parallelization

Tasks w/ independent subtasks: assign each to dedicated agent w/ fresh context. All work simultaneously -> total time approaches longest subtask, not sum of all.

## Architectural Patterns

### Pattern 1: Supervisor/Orchestrator

```
User Query -> Supervisor -> [Specialist, Specialist, Specialist] -> Aggregation -> Final Output
```

**Use when:** Clear decomposition, cross-domain coordination, human oversight needed
**Pros:** Strict workflow control, easier human-in-the-loop
**Cons:** Supervisor context bottleneck, cascade failures, "telephone game" problem

**Telephone Game Fix:** `forward_message` tool lets sub-agents pass responses directly to users:

```python
def forward_message(message: str, to_user: bool = True):
    """Forward sub-agent response directly to user w/o supervisor synthesis."""
    if to_user:
        return {"type": "direct_response", "content": message}
    return {"type": "supervisor_input", "content": message}
```

### Pattern 2: Peer-to-Peer/Swarm

Agents communicate directly via handoff mechanisms. No central control.

```python
def transfer_to_agent_b():
    return agent_b  # Handoff via fn return

agent_a = Agent(name="Agent A", functions=[transfer_to_agent_b])
```

**Use when:** Flexible exploration, emergent requirements
**Pros:** No single point of failure, scales for breadth-first exploration
**Cons:** Coordination complexity grows w/ agent count, divergence risk

### Pattern 3: Hierarchical

```
Strategy Layer (Goals) -> Planning Layer (Decomposition) -> Execution Layer (Atomic Tasks)
```

**Use when:** Large-scale projects, enterprise workflows, mixed high/low-level tasks
**Pros:** Clear separation of concerns, different context per level
**Cons:** Inter-layer coordination overhead, strategy-execution misalignment

## Context Isolation

Primary purpose of multi-agent architecture. Three mechanisms:

- **Full context delegation:** Planner shares entire context -> max capability but defeats isolation purpose
- **Instruction passing:** Planner creates instructions via fn call -> maintains isolation, limits flexibility
- **File system memory:** Agents read/write persistent storage -> shared state w/o context bloat, adds latency

## Consensus & Coordination

- **Weighted voting:** Weight by confidence/expertise (not simple majority)
- **Debate protocols:** Adversarial critique > collaborative consensus for complex reasoning
- **Trigger-based intervention:** Stall triggers (no progress), sycophancy triggers (mimicked answers)

## Failure Modes

| Failure | Mitigation |
|---|---|
| Supervisor bottleneck | Output schema constraints, workers return distilled summaries, checkpointing |
| Coordination overhead | Clear handoff protocols, batch results, async communication |
| Divergence | Objective boundaries per agent, convergence checks, TTL limits |
| Error propagation | Validate outputs before passing, retry w/ circuit breakers, idempotent ops |

## Examples

```text
Supervisor
├── Researcher (web search, doc retrieval)
├── Analyzer (data analysis, statistics)
├── Fact-checker (verification)
└── Writer (report generation)
```

```python
def handle_customer_request(request):
    if request.type == "billing":
        return transfer_to(billing_agent)
    elif request.type == "technical":
        return transfer_to(technical_agent)
    elif request.type == "sales":
        return transfer_to(sales_agent)
    else:
        return handle_general(request)
```

## Guidelines

1. Design for context isolation as primary benefit
2. Choose pattern by coordination needs, not org metaphor
3. Explicit handoff protocols w/ state passing
4. Weighted voting | debate for consensus
5. Monitor supervisor bottlenecks, use checkpointing
6. Validate outputs between agents
7. Set TTL limits to prevent infinite loops
8. Test failure scenarios explicitly

## Integration

Builds on context-fundamentals & context-degradation:
- memory-systems — shared state across agents
- tool-design — tool specialization per agent
- context-optimization — context partitioning strategies

## References

- [LangGraph](https://langchain-ai.github.io/langgraph/) — Multi-agent patterns & state management
- [AutoGen](https://microsoft.github.io/autogen/) — GroupChat & conversational patterns
- [CrewAI](https://docs.crewai.com/) — Hierarchical agent processes
- [Multi-Agent Coordination Survey](https://arxiv.org/abs/2308.00352)
